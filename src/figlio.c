/*
 * figlio.c — un processo per utente, che gira come lui e tiene il palco.
 *
 * La ragione, le tre differenze dall'aiutante e gli invarianti stanno per
 * esteso in `figlio.h`.  Qui ci sono le scelte che si vedono solo nel codice.
 *
 * ---------------------------------------------------------------------------
 * ⛔⭐ LA SCELTA PIU' IMPORTANTE DI QUESTO FILE: `fork()` **E POI `exec()`**
 *
 * Un `fork()` da solo sarebbe bastato a far girare il figlio come l'utente.  Si
 * fa anche l'`exec` per tre ragioni, e la prima da sola decide:
 *
 *   1. ⛔ **la memoria del padre contiene la chiave privata TLS del server**
 *      (`certificati.c`), la tabella dei ban e lo stato di tutte le altre
 *      sessioni.  Un figlio che girasse come l'utente **senza** `exec` gliela
 *      regalerebbe: `/proc/self/mem` e' leggibile dal proprietario del
 *      processo, e l'utente e' il proprietario.  ⇒ Sarebbe il difetto peggiore
 *      che questo lavoro possa produrre — l'isolamento fra utenti costruito e
 *      poi consegnato in mano al primo che entra;
 *   2. ⭐ **l'ambiente si compone da zero** (`CODER.md` §4.5) — e con `execve`
 *      non e' una disciplina, e' la firma della chiamata: l'`envp` si scrive
 *      variabile per variabile, e quel che non si scrive non c'e';
 *   3. ⚠ **il figlio apre PipeWire e GLib, che fanno thread.**  Il padre non li
 *      tocca mai (e' root: non avrebbe con chi parlare), quindi il `fork` parte
 *      da un processo a un filo solo — ma un'immagine nuova toglie la domanda
 *      invece di rispondere «oggi va bene».
 *
 * ⛔ E si scende all'utente PRIMA di `exec`, non dopo: cosi' l'immagine nuova
 *    nasce gia' senza privilegi, e non esiste nessun istante in cui il codice
 *    dell'utente potrebbe girare da root.
 *
 * ---------------------------------------------------------------------------
 * ⛔⭐ IL CONTROLLO CHE SAREBBE SEMBRATO UN CONTROLLO — `SO_PEERCRED`
 *
 * La domanda «chi c'e' dall'altro capo di questo socket?» ha una risposta
 * ovvia, `getsockopt(SO_PEERCRED)`, ⛔ **e su un `socketpair()` e' la risposta
 * sbagliata**: il nucleo ci mette le credenziali del processo che ha chiamato
 * `socketpair()` — cioe' il padre, root — su **tutt'e due** i capi, e non le
 * aggiorna mai piu'.  ⇒ Un padre che avesse controllato cosi' avrebbe letto
 * `uid 0` per un figlio sceso a `uid 1001`, avrebbe visto un numero, e non
 * avrebbe controllato niente.
 *
 * ⭐ Quel che si usa e' `SO_PASSCRED` + `SCM_CREDENTIALS`: il nucleo timbra
 *    **ogni messaggio** con pid/uid/gid **del mittente al momento della
 *    scrittura**, e un processo non privilegiato non ne puo' dichiarare di
 *    falsi.  E' l'unico modo per cui «verificato a ogni messaggio» sia un fatto
 *    e non una promessa.
 */
#include "figlio.h"

/* ⛔ SOLO per `RCP_TETTO_SESSIONI` — vedi il riquadro sopra `MAX_FIGLI`.  ⚠ Il
 *    figlio NON parla RCP: parla col padre su un `SOCK_SEQPACKET`.  Questo
 *    include e' la dichiarazione del legame fra due tetti, non una dipendenza
 *    dal protocollo. */
#include "rcp.h"
#include "registro.h"

#include <dirent.h>
#include <errno.h>
#include <fcntl.h>
#include <sched.h>
#include <stdatomic.h>
#include <grp.h>
#include <poll.h>
#include <pthread.h>
#include <pwd.h>
#include <security/pam_appl.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/prctl.h>
#include <sys/resource.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

/* Solo il figlio ha bisogno del palco.  Il padre non include niente di tutto
 * questo, e non e' pulizia: e' la dichiarazione che root non ci parla. */
#include "appunti.h"
#include "audio.h"
#include "cattura.h"
#include "sentinella.h"
#include "suono.h"
#include "codificatore.h"
#include "input.h"
#include "mutter.h"
#include "sessione.h"

/* ⛔⭐ LO STESSO TETTO DELLE SESSIONI DI `rcp.c`, E ADESSO E' VERO — 25 agosto
 *     2026.  Un utente per figlio (I2), quindi il numero e' lo stesso.
 *
 * ⛔ Fino a ieri questo commento diceva *«quando quello diventera' un budget di
 *    pixel, questo lo seguira' dallo stesso posto»*, e ⛔ **il legame non
 *    esisteva**: `MAX_ATTACCATE` era un `static` di `rcp.c` e questo era un
 *    letterale indipendente.  `[M]` §6.4 l'ha misurato: albero compilato con
 *    `MAX_ATTACCATE=2`, e `MAX_FIGLI` e' rimasto **16**.
 * ⇒ Adesso il numero viene da `rcp.h`, e il compilatore conosce il legame che
 *   il commento dichiarava.  ⚠ Questo file include `rcp.h` **solo** per questo:
 *   il figlio non parla RCP, parla col padre. */
#define MAX_FIGLI RCP_TETTO_SESSIONI

/* ⛔ Quanto si aspetta che un figlio appena nato dica CHI E'.  Oltre, si
 * dichiara guasto e si abbatte: un processo che gira come un utente e non
 * risponde non e' un palco, e' un processo dimenticato.
 * ⚠ Dopo il primo «sono», NON c'e' nessuna scadenza: e' l'invariante I4 — il
 *   palco sopravvive al distacco, e un figlio che tace perche' nessuno gli sta
 *   chiedendo niente sta facendo il suo mestiere. */
#define SCADENZA_SONO_MS 15000

/* ⛔ §6.2 di `RCP.md`: un fotogramma legale arriva a 16 MiB.  Il tetto e' qui
 * perche' i byte passano di qui, e un tetto NOSTRO piu' basso morderebbe al
 * posto di quello del protocollo — la forma d'errore che il montaggio ha gia'
 * pagato con `WT_CODA_MAX` (`P2-6-montaggio.md` §5.6). */
#define FOTOGRAMMA_MAX (16u * 1024u * 1024u)

/* Quanto entra in un messaggio SEQPACKET.  ⚠ Non e' un tetto del protocollo:
 * e' il pezzo con cui si taglia un fotogramma che nel socket non ci starebbe. */
#define PEZZO_MAX 32768u

#define FIGLIO_VERSIONE 1

enum {
	MSG_CHI_SEI = 1,      /* padre → figlio */
	MSG_SPEGNITI = 2,     /* padre → figlio */
	MSG_RIMANDA_PALCO = 3,/* padre → figlio */
	/* ⭐⭐ FASE 3 — «cattura, e questa dev'essere una chiave».  ⛔ E' la
	 *     cucitura che mancava: `codificatore_chiedi_chiave()` non aveva
	 *     nessun chiamante nel prodotto, e il palco sta in un ALTRO PROCESSO —
	 *     questa e' la riga che attraversa il confine. */
	MSG_VIDEO = 4,        /* padre → figlio */
	/* ⭐⭐ FASE 4 — L'INPUT.  ⛔ E la ragione per cui attraversa il socket e'
	 *     la stessa di `MSG_VIDEO`, ed e' un fatto dell'architettura, non una
	 *     scelta: **`libei` parla con la sessione dell'utente, e la sessione
	 *     dell'utente e' in QUESTO processo**, mentre QUIC, RCP e i byte del
	 *     client stanno nel padre.  ⇒ Fra il tasto premuto nel browser e il
	 *     tasto premuto sul desktop c'e' un confine di processo, e questa e'
	 *     la riga che lo attraversa. */
	MSG_INPUT = 5,        /* padre → figlio */
	/* ⭐⭐ §5-bis.7 — LA DISPOSIZIONE DI TASTIERA, e attraversa il confine
	 *     per la stessa ragione dell'input: la disposizione la applica la
	 *     SESSIONE dell'utente, che sta in questo processo, e a chiederla e'
	 *     il client, che parla col padre.
	 * ⛔ E ha una busta SUA invece di viaggiare dentro `MSG_INPUT` come
	 *    `RITELA`: il nome e' una stringa di 64 byte, e infilarla nel corpo
	 *    dell'input vorrebbe dire pagarla su OGNI movimento del mouse —
	 *    decine al secondo — per una cosa che succede una volta per attacco.
	 *    `CODER.md` §1-bis: ogni byte in piu' sul cammino caldo si paga in
	 *    ritardo, ed e' il numero che pesa piu' dei fotogrammi. */
	MSG_DISPOSIZIONE = 6, /* padre → figlio */
	/* ⭐⭐ FASE 7 — L'AUDIO, e attraversa il confine per la TERZA volta con la
	 *     stessa ragione di `MSG_VIDEO` e `MSG_INPUT`, che ormai e' una legge
	 *     dell'architettura e non una scelta:
	 *
	 *       **PipeWire parla con la sessione dell'utente, e la sessione
	 *       dell'utente e' in QUESTO processo**; i datagram di `RCP.md` §6.3
	 *       li scrive il padre, che tiene QUIC.
	 *
	 * ⛔ E il figlio CODIFICA prima di mandare, invece di spedire i campioni
	 *    crudi.  Non e' un'ottimizzazione qualunque: 20 ms di PCM stereo sono
	 *    **3840 byte**, lo stesso blocco in Opus ne misura `[M]` **241-439**.
	 *    Spedire crudo vorrebbe dire pagare **dieci volte** il socket per
	 *    ogni blocco, cinquanta volte al secondo, su un percorso che
	 *    `CODER.md` §1-bis dice di misurare in ritardo.
	 * ⚠ Il prezzo, dichiarato: il codec lo negozia il PADRE (§4.3) e a
	 *   codificare e' il figlio, quindi il numero deve attraversare il
	 *   confine — ed e' esattamente quel che questo messaggio porta. */
	MSG_AUDIO = 7,        /* padre → figlio */
	/* ⭐⭐ FASE 7 — GLI APPUNTI, e attraversano il confine per la QUARTA volta
	 *     con la stessa ragione del video, dell'input e dell'audio: **la
	 *     clipboard e' del compositore** (`STUDI.md` §gnome §10), e col
	 *     compositore parla questo processo; §7.4 lo scrive il padre.
	 *
	 * ⛔ `MSG_APPUNTI_OFFERTA` NON porta il testo, ed e' il «si annuncia e poi
	 *    si tira» di §7.4 applicato di qua: il testo del client si chiede
	 *    quando qualcuno nella sessione incolla davvero.  ⚠ Chi copia un
	 *    documento intero sul telefono non lo fa attraversare il socket finche'
	 *    quel momento non arriva — e nella maggior parte dei casi non arriva. */
	MSG_APPUNTI_OFFERTA = 8,  /* padre → figlio */
	/* ⛔ E questo invece lo porta, **a pezzi**: e' la risposta a una richiesta
	 *    della sessione, e il tetto di §5.4 e' 1 000 000 byte — trenta volte
	 *    `PEZZO_MAX`. */
	MSG_APPUNTI_DAL_CLIENT = 9, /* padre → figlio */
	MSG_SONO = 10,      /* figlio → padre */
	MSG_PALCO = 11,     /* figlio → padre */
	MSG_FOTOGRAMMA = 12,/* figlio → padre */
	/* ⭐⭐ FASE 4 — LA FORMA DEL CURSORE, e attraversa il confine nel verso
	 *     OPPOSTO all'input.  ⛔ Per la stessa ragione: il metadato del cursore
	 *     arriva da PipeWire, cioe' nel figlio, e il canale su cui va spedito
	 *     (`CURSORE_FORMA`, `RCP.md` §7.2) vive nel padre.
	 * ⚠ E come il fotogramma va A PEZZI: un cursore 256x256 in BGRA fa 262 144
	 *   byte, otto volte `PEZZO_MAX`. */
	MSG_CURSORE = 13,   /* figlio → padre */
	/* ⭐⭐ LA RISPOSTA ALLA TELA — 15 agosto 2026, ed e' nata da una refutazione.
	 *
	 * ⛔ La prima stesura non aveva questo messaggio: il padre CHIEDEVA la tela e
	 *    poi INDOVINAVA la risposta dai fotogrammi — «se ne arriva uno di misura
	 *    diversa, allora il palco ha obbedito».  ⚠ E indovinare non bastava, per
	 *    tre casi che non si distinguono guardando i pixel:
	 *
	 *      · il palco ha GIA' quella misura ⇒ non arrivera' nessun fotogramma
	 *        nuovo, e il padre aspetterebbe il fondo dei tre secondi per niente;
	 *      · il palco non c'e' o non ce l'ha fatta ⇒ il fatto e' noto SUBITO, e
	 *        nel processo sbagliato;
	 *      · due richieste incatenate (l'utente trascina il bordo) ⇒ il
	 *        fotogramma della PRIMA sarebbe stato preso per la risposta della
	 *        SECONDA, e il desktop si sarebbe assestato sulla misura sbagliata
	 *        **senza che nessun conto se ne accorgesse**.
	 *
	 * ⇒ Il figlio risponde, e porta TUTT'E DUE i numeri: che cosa gli era stato
	 *   chiesto (cosi' il padre riconosce a quale richiesta risponde) e che cosa
	 *   il palco ha davvero (`0x0` = non ce l'ha fatta).  ⭐ E lo manda solo dopo
	 *   aver VISTO un fotogramma a quella misura, tranne nel caso «ce l'ho gia'»:
	 *   la verita' resta il fotogramma, questo e' il modo di dirla. */
	MSG_TELA = 14,      /* figlio → padre */
	/* ⭐ §7.6 — «la sessione grafica e' finita», e non l'ha chiesta nessun
	 * client: l'utente ha scelto «Esci…» dal menu del desktop. */
	MSG_SESSIONE_FINITA = 15, /* figlio → padre */
	/* ⭐⭐ FASE 7 — UN BLOCCO D'AUDIO GIA' CODIFICATO, pronto per il datagram.
	 *
	 * ⛔ NON va a pezzi come il fotogramma e il cursore, e non e' una
	 *    semplificazione: un blocco che non entra in un datagram **non si puo'
	 *    spedire affatto** (`RCP.md` §6.3, «un datagram, un blocco»), quindi un
	 *    blocco piu' grande di `PEZZO_MAX` sarebbe gia' un difetto a monte.
	 *    ⚠ Il piu' grosso che RCP/1 preveda e' il PCM: 960 byte.
	 *
	 * ⛔ E se il socket e' pieno il blocco SI BUTTA invece di aspettare: §6.3
	 *    vieta la ritrasmissione, e un figlio che si bloccasse a scrivere
	 *    fermerebbe la CATTURA DEL DESKTOP — l'audio in ritardo costerebbe i
	 *    fotogrammi. */
	MSG_BLOCCO = 16, /* figlio → padre */
	/* ⭐⭐ FASE 7 — «LA SESSIONE HA COPIATO QUESTO TESTO», e va **a pezzi** come
	 *     il fotogramma e il cursore.
	 *
	 * ⛔ Arriva GIA' LETTO, e non e' una comodita': l'annuncio di §7.4 porta
	 *    `u32 lunghezza`, e nessuno sa quanto e' lungo un testo senza averlo
	 *    letto.  ⇒ Il «si annuncia e poi si tira» vive sul FILO, dove serve;
	 *    di qua il testo c'e' gia'.
	 * ⛔ E arriva gia' convalidato UTF-8, gia' senza zeri in mezzo e gia' entro
	 *    il tetto: quei tre controlli stanno in `appunti.c`, dove il testo
	 *    esiste ancora intero e dove si sa QUALE dei tre ha morso. */
	MSG_APPUNTI_DALLA_SESSIONE = 17, /* figlio → padre */
	/* ⭐⭐ «QUALCUNO NELLA SESSIONE STA INCOLLANDO» — e il padre DEVE rispondere,
	 *     anche a mani vuote: un `SelectionTransfer` senza risposta lascia
	 *     appesa a tempo indeterminato l'applicazione che incolla, e il sintomo
	 *     e' «il desktop si e' piantato» (`src/appunti.h`). */
	MSG_APPUNTI_VUOLE = 18 /* figlio → padre */
};

struct testa {
	uint8_t magia[4]; /* 'F','I','G','1' */
	uint16_t tipo;
	uint16_t versione;
	uint64_t matricola;
	/* ⛔ Chi il MITTENTE crede che sia il figlio.  Non e' una prova di niente —
	 *    la prova la scrive il nucleo — ed e' qui perche' un disallineamento fra
	 *    quel che uno crede e quel che il nucleo dice si veda **subito**,
	 *    invece di diventare pixel consegnati alla persona sbagliata. */
	uint32_t uid_dichiarato;
	uint32_t byte; /* byte di corpo dopo questa struttura */
};

struct corpo_sono {
	uint32_t uid, euid, suid;
	uint32_t gid, egid, sgid;
	uint32_t pid, ppid;
	uint32_t descrittori;   /* quanti ne restano aperti dopo `close_range` */
	uint32_t runtime_c_e;   /* la cartella di runtime esiste ed e' sua */
	uint32_t socket_bus_c_e;/* il socket del bus di sessione esiste */
	char utente[64];
	char runtime[160];
};

struct corpo_palco {
	uint32_t bus_aperto;      /* la CONNESSIONE al bus e' riuscita */
	uint32_t stato_sessione;  /* SessioneStato, 0 = SANA */
	uint32_t presa;           /* CatturaPresa */
	uint32_t monitor_prima, monitor_dopo;
	uint32_t larghezza, altezza, stride, bit;
	uint32_t flussi;          /* quanti codec hanno consegnato */
	char monitor[64];
	char guasto[224];
};

/* ⛔⭐ La risposta del palco alla richiesta di tela.  ⚠ `avuta_l == 0` vuol dire
 *     «non ce l'ho fatta», e NON e' una misura: e' l'altra faccia dello zero di
 *     `CODER.md` §3.10, dichiarata invece che dedotta dal silenzio. */
struct corpo_tela {
	uint32_t voluta_l, voluta_a;
	uint32_t avuta_l, avuta_a;
	/* ⭐⭐ «NON ANCORA» — 16 agosto 2026, e non e' un terzo numero: e' un terzo
	 *     FATTO.  `avuta = 0x0` vuol dire «non ce l'ho fatta»; il silenzio
	 *     voleva dire «sto ancora provando», ⛔ e il padre lo DEDUCEVA — cioe'
	 *     non lo sapeva.  `LEZIONI.md` §7.5: una deduzione al posto di un
	 *     messaggio e' un difetto che aspetta.
	 *
	 * ⇒ Con questo bit il padre RIMANDA il fondo di §7.1 invece di rispondere
	 *   `NON_ORA` a una domanda che sta per avere una risposta vera. */
	uint32_t attendi;
};

/* ⛔ Che cosa il padre chiede al palco.  ⚠ `codec` a **0** vuol dire «smetti di
 *    catturare»: non e' un sentinella implicito, e' il valore che §4.3/§6.2
 *    riservano a «nessun codec negoziato», e qui vuol dire la stessa cosa —
 *    nessuno sta guardando. */
struct corpo_video {
	uint8_t codec;  /* 1 = HEVC, 2 = AV1, 0 = spegni */
	uint8_t chiave; /* ⛔ §5.2: il prossimo DEVE essere una chiave */
	/* ⛔⭐⭐ LA PROFONDITA' NEGOZIATA — 17 agosto 2026, e questo campo e' la cura
	 *      di un difetto misurato, non un'aggiunta di comodita'.
	 *
	 *      Fino a stasera il codec attraversava questo confine e la profondita'
	 *      NO: il figlio scriveva `r.profondita = 10` a mano, per ogni codec.
	 *      ⇒ Il flusso usciva a **10 bit mentre `ECCOMI` ne dichiarava 8**
	 *      (§4.3), e nessun banco poteva vederlo — i due numeri vivono in due
	 *      PROCESSI diversi.
	 *
	 * ⚠ Su Chrome+HEVC non si vedeva: HEVC porta i suoi parametri nel flusso
	 *   (VPS/SPS) e il decodificatore si riconfigura da se'.
	 * ⛔ Su Firefox+AV1 sì: la pagina configura la stringa con la profondita'
	 *   NEGOZIATA (`av01.0.12M.08`) e dav1d si fida di quella.  `[M]` prima
	 *   artefatti, poi il decodificatore si pianta e il desktop si ferma.
	 *
	 * ⚠ `0` = non negoziata, e NON vuol dire 8: chi riceve NON deve sceglierne
	 *   una per conto suo — sarebbe rifare a mano il difetto appena tolto. */
	uint8_t profondita;
	/* ⛔⭐⭐ IL LIVELLO CHIESTO DAL CLIENT — 23 agosto 2026, e questo campo era
	 *      il byte `riempi`, tenuto libero apposta e nominato in DUE riquadri
	 *      (`rcp.c` §4.3 e «LIVELLO PRODOTTO» piu' giu') come il posto dove il
	 *      livello sarebbe passato il giorno in cui fosse servito.
	 *
	 *      Serve, ed e' MISURATO: `[M]` 23 agosto 2026, tela 3840x2160, H.264 —
	 *      il client dichiara `video.livello=5.1` e il server produce un flusso
	 *      di livello **5.2**.  `RCP.md` §4.3 riga 701 e' un DEVE, e il sintomo
	 *      di un livello sforato NON e' un errore: e' il decodificatore del
	 *      browser che rifiuta la configurazione — «non si vede niente» senza
	 *      una riga che dica perche'.
	 *
	 * ⚠ In DECIMI, l'alfabeto di §4.3: `5.1` ⇒ **51**.  Chi apre il
	 *   codificatore lo riconverte codec per codec (H.264 tale e quale, HEVC
	 *   per tre): la traduzione sta in `codificatore.c` e in nessun altro
	 *   posto.
	 * ⛔ `0` = il client non l'ha dichiarato — §4.3 non lo obbliga — e vuol
	 *   dire NESSUN TETTO, non «basso»: chi riceve non ne inventa uno, che e'
	 *   la stessa regola scritta sopra per `profondita`. */
	uint8_t livello_x10;
};

/* ⛔ Che cosa il padre chiede al desktop.  Le azioni sono quelle di `RCP.md`
 *    §7.3 e i campi hanno i suoi tipi — ⚠ ma qui viaggiano gia' CONVALIDATI:
 *    `rcp.c` ha fatto il suo mestiere, e questo confine non lo rifa'.
 *
 * ⭐ `id` c'e' perche' e' l'unica cosa che rende onesto il campo `input` dei
 *    fotogrammi (§6.2): senza, il figlio saprebbe di aver iniettato **qualcosa**
 *    e non **quale**. */
struct corpo_input {
	uint32_t id;       /* §7.3: cresce di almeno uno su tutto il canale */
	uint8_t azione;    /* FIGLI_INPUT_* di `figlio.h` */
	uint8_t premuto;   /* 1 premuto, 0 rilasciato */
	uint16_t codice;   /* evdev: BTN_LEFT = 0x110, KEY_A = 30 */
	int32_t a, b;      /* puntatore x/y · rotella assi · lettera in `a` */
};

/* ⭐ §5-bis.7: il nome di una disposizione XKB — `it`, `de(neo)`.  ⚠ 64
 *    byte piu' il NUL, che e' il tetto che `RCP.md` §4.5 pone alla
 *    stringa: la busta e' a misura fissa perche' cosi' il figlio non deve
 *    fidarsi di una lunghezza che gli arriva dal socket. */
struct corpo_disposizione {
	char nome[65];
};

/* ⛔ La forma del cursore che attraversa il confine.  ⚠ I limiti di `RCP.md`
 *    §5.5 e §7.2 li ha gia' fatti rispettare `cursore.c`, dall'altra parte del
 *    tubo: qui non si ricontrollano — ⛔ tranne quel che serve a non fidarsi di
 *    un mittente, che nel padre e' un'altra cosa dal fidarsi di un modulo. */
struct corpo_cursore {
	uint16_t larghezza, altezza; /* 0x0 = nascosto (§5.5) */
	int16_t attivo_x, attivo_y;
	uint32_t totale;  /* byte dell'immagine intera: l x a x 4 */
	uint32_t offset;
	uint32_t pezzo;
};

/* ⛔ Che cosa il padre chiede all'audio.  `codec` sono i numeri di `RCP.md`
 *    §6.3 — 1 = Opus, 2 = PCM — e ⚠ **non** quelli di §6.2: li' 1 e' HEVC.
 *    `0` = «spegni»: nessuno sta ascoltando, e la cattura si ferma mentre il
 *    sink resta (invariante I4, come il palco). */
struct corpo_audio {
	uint8_t codec;
	uint8_t riempi[3];
};

/* Un blocco gia' codificato.  `istante_us` e' l'orologio monotono del figlio,
 * del PRIMO campione del blocco (§6.3) — ⛔ e lo mette il figlio per la stessa
 * ragione per cui mette `input` nei fotogrammi: e' l'unico che sappia quando i
 * campioni sono stati presi davvero. */
struct corpo_blocco {
	uint8_t codec;
	uint8_t riempi[3];
	uint32_t byte;
	uint64_t istante_us;
};

/* ⛔ IL TESTO DEGLI APPUNTI, e va a pezzi nei DUE versi.
 *
 * ⚠ Una struttura sola per i due versi, e non e' pigrizia: i due messaggi
 *   portano lo stesso oggetto — un testo lungo fino a 1 000 000 byte — e
 *   `serial` e' l'unica differenza.  ⛔ Nel verso figlio → padre vale **0** e
 *   non vuol dire niente: la sessione ha copiato, non ha chiesto.
 *
 * ⛔ E il `totale` NON e' ridondante rispetto a `pezzo`: chi riceve alloca sul
 *    primo pezzo e rifiuta i pezzi fuori ordine, esattamente come per il
 *    fotogramma — ricucire un buco vorrebbe dire indovinare che cosa mancava,
 *    e un testo con un buco indovinato incollato in un terminale e' peggio di
 *    un testo mancante (§5.4, con le sue parole). */
struct corpo_appunti {
	uint32_t serial; /* padre → figlio: la richiesta di Mutter.  Altrimenti 0 */
	uint32_t totale; /* byte del testo intero, zero finale ESCLUSO */
	uint32_t offset;
	uint32_t pezzo;
	/* ⛔ «Non ce l'ho», e va detto con un campo invece che con `totale = 0`.
	 *    Un testo vuoto e' un fatto LECITO — la clipboard svuotata — e «non ho
	 *    quel che mi hai chiesto» e' un altro fatto: schiacciarli sullo stesso
	 *    valore e' la faccia comune di «vuoto» e «proibito» che `LEZIONI.md`
	 *    §1.9 vieta.  ⚠ E i due portano a due chiamate diverse verso Mutter. */
	uint8_t niente;
	uint8_t riempi[3];
};

struct corpo_fotogramma {
	uint8_t codec; /* 1 = HEVC, 2 = AV1 — gli stessi numeri di §4.3/§6.2 */
	uint8_t chiave;
	uint16_t riempi;
	uint32_t larghezza, altezza;
	uint64_t istante_us;
	uint32_t totale; /* byte del fotogramma intero */
	uint32_t offset; /* dove va questo pezzo */
	uint32_t pezzo;  /* quanti byte in questo pezzo */
	/* ⭐⭐ §6.2 — «l'identificatore dell'ultimo input INIETTATO prima della
	 *     cattura, 0 se nessuno».
	 *
	 * ⛔⛔ E VIAGGIA DI QUI, non dal padre, ed e' la scelta che rende vero il
	 *      campo invece di plausibile.  Il padre sa che cosa ha **mandato**;
	 *      solo il figlio sa che cosa il compositore ha **preso**, e sa in che
	 *      istante ha catturato.  ⇒ Riempirlo nel padre direbbe «l'ultimo
	 *      input SPEDITO al palco prima della spedizione del fotogramma»: un
	 *      numero piu' alto, e una promessa piu' grande di quella che il
	 *      fotogramma puo' mantenere — cioe' l'anello del ritardo misurerebbe
	 *      un ritardo piu' corto del vero, in nostro favore.
	 * ⚠ `CODER.md` §1-bis: «il confine si sposta nella direzione SCOMODA». */
	uint32_t input;
};

/* Il messaggio piu' lungo che passa di qui. */
#define BUSTA_MAX (sizeof(struct testa) + sizeof(struct corpo_fotogramma) + PEZZO_MAX)
_Static_assert(sizeof(struct corpo_cursore) <= sizeof(struct corpo_fotogramma),
               "la busta e' dimensionata sul fotogramma: il cursore ci deve stare");
_Static_assert(sizeof(struct corpo_appunti) <= sizeof(struct corpo_fotogramma),
               "la busta e' dimensionata sul fotogramma: gli appunti ci devono stare");

/* ========================================================================== */
/* IL PADRE                                                                    */

struct figlio {
	bool usato;
	char utente[64];
	uid_t uid;
	gid_t gid;
	pid_t pid;
	int fd;
	uint64_t matricola;
	uint64_t nato_ms;
	uint64_t ultimo_ricontrollo_ms;
	bool si_e_presentato;
	/* ⛔⭐ «Gli ho detto di andarsene» e «se n'e' andato» sono due fatti
	 *     diversi, e tenerne uno solo e' il difetto che questo banco ha
	 *     trovato al primo giro (12 agosto 2026, caso `muore`).  Vedi il
	 *     riquadro sopra `figlio_congeda()`. */
	bool uscendo;
	uint64_t congedato_ms;
	/* Il fotogramma in arrivo, un pezzo per volta. */
	uint8_t *monta;
	size_t monta_totale, monta_avuti;
	uint8_t monta_codec, monta_chiave;
	uint32_t monta_l, monta_a;
	uint64_t monta_istante;
	uint32_t monta_input; /* §6.2, e lo TIMBRA il figlio: vedi `corpo_fotogramma` */
	/* ⭐ Il montaggio del CURSORE e' separato da quello del fotogramma, e non e'
	 *    una comodita': i due arrivano **intrecciati** sullo stesso socket, e un
	 *    montaggio solo farebbe di ogni cambio di forma un fotogramma buttato
	 *    (e viceversa).  ⛔ E' la trappola dei pezzi fuori ordine vista da
	 *    sopra: non e' il mittente a sbagliare, e' il ricevente a non avere
	 *    due tavoli. */
	uint8_t *cur_monta;
	size_t cur_totale, cur_avuti;
	uint16_t cur_l, cur_a;
	int16_t cur_ax, cur_ay;
	/* ⛔ Il conto dei fotogrammi arrivati da questo figlio.  ⚠ Sta qui e non
	 *    in una variabile di modulo perche' e' PER FIGLIO: sommato fra due
	 *    utenti direbbe che il palco funziona anche quando ne funziona uno
	 *    solo — due misure sotto la stessa etichetta. */
	uint64_t fotogrammi_avuti, byte_avuti, chiavi_avute;
	uint64_t detto_conto_ms;
	/* ⛔ Che cosa il padre ha gia' chiesto a questo palco: si tiene per non
	 *    ripetere lo stesso comando a ogni giro di `poll`. */
	uint8_t video_codec_chiesto;
	/* ⛔ E la profondita' con lui: vedi `corpo_video`.  ⚠ `0` = mai chiesta. */
	uint8_t video_prof_chiesta;
	/* ⛔ E il LIVELLO con loro (§4.3, 23 agosto 2026), per la stessa ragione:
	 *    e' della SESSIONE, cambia da client a client, e un secondo client che
	 *    dichiarasse 4.1 dove il primo aveva 5.1 e' «qualcosa di nuovo da
	 *    dire» anche a codec e profondita' invariati.  ⚠ `0` = mai chiesto. */
	uint8_t video_liv_chiesto;
	/* ⛔ L'ultimo codec d'audio chiesto a questo figlio, per non ripetere la
	 *    stessa richiesta a ogni battito — e per scrivere la riga di registro
	 *    solo quando il fatto CAMBIA.  ⚠ `0` = spento, ed e' lo stato iniziale
	 *    di ogni figlio: nessuno ascolta finche' qualcuno non si attacca. */
	uint8_t audio_codec_chiesto;
	/* ⭐ FASE 7 — il TERZO tavolo di montaggio, e la ragione e' quella scritta
	 *    sopra `cur_monta`: fotogrammi, cursori e appunti arrivano
	 *    **intrecciati** sullo stesso socket, e chi ne avesse due soli farebbe
	 *    di ogni testo copiato un fotogramma buttato.  ⚠ Un tavolo per tipo, e
	 *    il conto torna qualunque cosa arrivi prima. */
	uint8_t *app_monta;
	size_t app_totale, app_avuti;
};

struct figli {
	struct figlio v[MAX_FIGLI];
	uint64_t prossima_matricola;
	uint32_t tela_l, tela_a;
	char dir_rilievo[256];
	bool c_e_rilievo;
	/* ⭐ FASE 9 — quel che ogni figlio dovra' ripetere a se stesso dopo
	 *    l'`execve`, perche' il codificatore sta di la'.  ⚠ Non si USA qui: si
	 *    trascrive nella riga di comando del figlio (`diventa_ed_esegui()`). */
	bool fase9_qualita_risale;
	uint32_t fase9_tetto_banda_mbit;
	/* ⭐ La TERZA, 24 agosto 2026, e nasce ACCESA: un blocco d'audio tutto a
	 *    zero non diventa un datagram.  ⚠ Si passa NEGATA nell'`argv` del
	 *    figlio (`--niente-audio-silenzio`), perche' quel che si scrive in coda
	 *    e' l'ECCEZIONE al predefinito, non il predefinito. */
	bool fase9_audio_silenzio;
	char percorso_mio[512]; /* /proc/self/exe risolto, per l'`exec` */
	FiglioSessioneFinita su_sessione_finita;
	void *ctx_sessione_finita;
	FiglioTelaAttendi su_tela_attendi;
	void *ctx_tela_attendi;
	/* ⭐ FASE 7 — i blocchi d'audio.  ⚠ Ha un contesto SUO e non usa `ctx`
	 *    come `deposita`/`congeda`/`cursore`: quelli li aggancia `main.c` in
	 *    blocco, questo lo aggancia chi possiede il canale audio, e legarli
	 *    insieme vorrebbe dire accendere l'audio per forza dove c'e' il video. */
	FiglioBlocco su_blocco;
	void *ctx_blocco;
	/* ⭐ FASE 7 — gli appunti.  ⚠ Contesto SUO come quello dei blocchi, e per
	 *    la stessa ragione: chi possiede il canale degli appunti non e' chi
	 *    aggancia il video, e legarli vorrebbe dire accendere gli appunti per
	 *    forza dove c'e' il video.
	 * ⛔ I due ganci si agganciano insieme o per niente (`figlio.h`): uno che
	 *    sapesse ricevere il testo della sessione e non sapesse servire chi
	 *    incolla lascerebbe appesa l'applicazione che incolla. */
	FiglioAppuntiTesto su_appunti_testo;
	FiglioAppuntiRichiesta su_appunti_richiesta;
	void *ctx_appunti;
	FiglioDeposito deposita;
	FiglioCongedo congeda;
	FiglioCursore cursore;
	FiglioTela tela;
	void *ctx;
};

static void magia_scrivi(struct testa *t)
{
	t->magia[0] = 'F';
	t->magia[1] = 'I';
	t->magia[2] = 'G';
	t->magia[3] = '1';
}

static bool magia_giusta(const struct testa *t)
{
	return t->magia[0] == 'F' && t->magia[1] == 'I' && t->magia[2] == 'G'
	       && t->magia[3] == '1' && t->versione == FIGLIO_VERSIONE;
}

/* ⛔ Legge un messaggio E le credenziali che il NUCLEO gli ha attaccato.
 *
 * ⚠ `credenziali` esce vera solo se il messaggio ne portava davvero: un
 *   messaggio **senza** credenziali non e' un messaggio con credenziali giuste
 *   — «vuoto» e «proibito» hanno lo stesso aspetto (`LEZIONI.md` §1.9), e qui
 *   la faccia comune costerebbe l'isolamento fra utenti. */
static ssize_t ricevi_con_credenziali(int fd, void *buf, size_t cap,
                                      struct ucred *chi, bool *credenziali)
{
	struct msghdr m;
	struct iovec io;
	union {
		struct cmsghdr allinea;
		char spazio[CMSG_SPACE(sizeof(struct ucred))];
	} controllo;
	struct cmsghdr *c;
	ssize_t letti;

	*credenziali = false;
	memset(&m, 0, sizeof m);
	memset(&controllo, 0, sizeof controllo);
	io.iov_base = buf;
	io.iov_len = cap;
	m.msg_iov = &io;
	m.msg_iovlen = 1;
	m.msg_control = controllo.spazio;
	m.msg_controllen = sizeof controllo.spazio;

	letti = recvmsg(fd, &m, 0);
	if (letti <= 0)
		return letti;

	for (c = CMSG_FIRSTHDR(&m); c; c = CMSG_NXTHDR(&m, c)) {
		if (c->cmsg_level == SOL_SOCKET && c->cmsg_type == SCM_CREDENTIALS
		    && c->cmsg_len == CMSG_LEN(sizeof(struct ucred))) {
			memcpy(chi, CMSG_DATA(c), sizeof *chi);
			*credenziali = true;
		}
	}
	/* ⚠ Un messaggio troncato dal nucleo (`MSG_TRUNC`) e' un messaggio che non
	 *   e' quello che dice di essere: si butta.  Con SEQPACKET succede solo se
	 *   il mittente ha scritto piu' del nostro buffer, cioe' se non e' il
	 *   nostro codice o se le due parti non sono la stessa versione. */
	if (m.msg_flags & MSG_TRUNC)
		return -2;
	return letti;
}

/* ⛔⭐ IL MURO, ED E' UNO SOLO — invariante I3.
 *
 * Perche' un messaggio conti, tutte queste cose devono essere vere insieme:
 *
 *   · il nucleo ci ha attaccato le credenziali (non «non ce n'erano»);
 *   · il pid del mittente e' **quel figlio li'**, non un altro processo che ha
 *     in mano lo stesso descrittore;
 *   · l'uid e il gid timbrati dal nucleo sono quelli che il padre ha risolto
 *     dal NOME dell'utente della sessione RCP;
 *   · la matricola e' la sua — l'equivalente del numero di pratica
 *     dell'aiutante, e serve allo stesso: che la risposta di uno non ammetta
 *     un altro;
 *   · il nome dell'utente risolve **ancora oggi** a quell'uid.  ⚠ Questa e'
 *     l'unica delle cinque che puo' cambiare mentre il figlio e' vivo (NSS,
 *     `/etc/passwd` riscritto, un dominio che risponde diverso): se cambia, il
 *     legame fra la sessione RCP e il figlio non e' piu' dimostrabile, e un
 *     legame non dimostrabile e' un no.
 *
 * ⛔ Non c'e' nessuna strada che consegni un byte a chi non passa di qui. */
static bool credenziali_combaciano(const struct figlio *g, const struct testa *t,
                                   bool c_e, const struct ucred *chi,
                                   char *perche_no, size_t cap_perche)
{
	struct passwd pw, *ris = NULL;
	char scorta[1024];

	if (!c_e) {
		snprintf(perche_no, cap_perche,
		         "il nucleo non ha attaccato le credenziali al messaggio");
		return false;
	}
	if (chi->pid != g->pid) {
		snprintf(perche_no, cap_perche,
		         "l'ha scritto il pid %ld, e il figlio di «%s» e' il pid %ld",
		         (long)chi->pid, g->utente, (long)g->pid);
		return false;
	}
	if (chi->uid != g->uid || chi->gid != g->gid) {
		snprintf(perche_no, cap_perche,
		         "il nucleo dice uid %ld gid %ld, e «%s» e' uid %ld gid %ld",
		         (long)chi->uid, (long)chi->gid, g->utente, (long)g->uid,
		         (long)g->gid);
		return false;
	}
	if (t->matricola != g->matricola) {
		snprintf(perche_no, cap_perche, "matricola %llu invece di %llu",
		         (unsigned long long)t->matricola,
		         (unsigned long long)g->matricola);
		return false;
	}
	if (t->uid_dichiarato != (uint32_t)g->uid) {
		snprintf(perche_no, cap_perche,
		         "il messaggio dichiara uid %lu e il figlio e' uid %ld",
		         (unsigned long)t->uid_dichiarato, (long)g->uid);
		return false;
	}
	if (getpwnam_r(g->utente, &pw, scorta, sizeof scorta, &ris) != 0 || !ris) {
		snprintf(perche_no, cap_perche,
		         "il nome «%s» adesso non risolve piu' a nessun utente: il "
		         "legame non e' piu' dimostrabile",
		         g->utente);
		return false;
	}
	if (ris->pw_uid != g->uid) {
		snprintf(perche_no, cap_perche,
		         "«%s» adesso e' uid %ld, e il figlio e' uid %ld: il nome e "
		         "l'uid si sono scollati",
		         g->utente, (long)ris->pw_uid, (long)g->uid);
		return false;
	}
	return true;
}

/* ⛔⭐ IL CONGEDO NON E' LA LIBERAZIONE, E TENERLI INSIEME E' UN DIFETTO —
 *     trovato dal banco `02-figlio-prova.py --caso muore` al PRIMO giro, il 12
 *     agosto 2026, e curato qui.
 *
 *     Che cosa faceva prima: il figlio veniva ucciso, il suo socket dava EOF, e
 *     il padre liberava la casella **subito**, azzerando il pid.  ⛔ Cosi' il
 *     `waitpid()` che sta piu' sotto non aveva piu' nessun pid da raccogliere,
 *     e il figlio restava **zombie**.  `[M]` il banco: *«dopo 15 s il pid c'e'
 *     ancora, stato Z»*.
 *
 * ⚠ Ed e' LA STESSA LEZIONE che l'aiutante aveva gia' pagato oggi, ricomparsa
 *   di un passo piu' in la': in `/proc` uno zombie e un processo vivo hanno la
 *   stessa faccia, quindi «il figlio e' morto» e «il figlio non muore» sono
 *   indistinguibili per chi diagnostica — ed erano indistinguibili anche per il
 *   PADRE, che nella casella non aveva piu' niente da guardare.
 *
 * ⇒ Da qui in poi sono due passi:
 *     `figlio_congeda()`  chiude il socket, chiede al figlio di andarsene, e
 *                         lascia la casella occupata **col pid dentro**;
 *     la raccolta          in `figli_muovi()`, `waitpid(WNOHANG)`: quando il
 *                         nucleo conferma la morte, ALLORA la casella si
 *                         libera — e la riga del registro porta la CAUSA vera
 *                         (il segnale, o il numero d'uscita), non «ha chiuso
 *                         il socket».
 */
/* ⛔⭐ I NUMERI D'USCITA DEL FIGLIO, TRADOTTI IN PAROLE — e non e' cosmesi.
 *
 *     `[M]` 12 agosto 2026, primo giro del guasto `uid`: il figlio e' uscito
 *     **35**, e il registro diceva soltanto *«e' uscito con 35»*.  ⛔ Il numero
 *     e' un fatto e non e' una diagnosi: chi legge non sa se il figlio non e'
 *     sceso all'utente, se non ha trovato il binario o se non e' riuscito a
 *     presentarsi — e sono tre guasti diversi con tre cure diverse.
 *
 * ⚠ E fra il `fork` e l'`exec` non si scrive nel registro: si sta in un
 *   processo appena forcato, e l'unico modo onesto di parlare e' il numero
 *   d'uscita.  ⇒ La traduzione sta QUI, nel padre, che il registro ce l'ha.
 *
 * ⭐ E la tabella ha anche il valore di dire quanti muri ci sono: il 35 e il 42
 *    sono lo STESSO controllo fatto due volte, prima e dopo l'`exec`, e il
 *    terzo muro — le credenziali timbrate dal nucleo — non compare qui perche'
 *    non fa uscire il figlio: lo abbatte il padre. */
static const char *perche_uscito(int codice)
{
	switch (codice) {
	case 0:  return "ha finito il suo mestiere";
	case 30: return "non ha potuto mettere il socket al posto convenuto";
	case 31: return "non ha potuto prendere i gruppi dell'utente";
	case 32: return "non ha potuto scendere al gid dell'utente";
	case 33: return "non ha potuto scendere all'uid dell'utente";
	case 34: return "non ha potuto CHIEDERE al nucleo chi e' (getresuid)";
	case 35: return "⛔ NON E' SCESO all'utente: il nucleo dice un uid diverso "
	                "da quello chiesto, e il figlio si e' fermato PRIMA di "
	                "eseguire qualunque cosa";
	case 36: return "⛔ non e' sceso al gid dell'utente";
	case 37: return "non ha potuto eseguire il binario del server";
	case 40: return "e' stato lanciato con una riga di comando che non e' la sua";
	case 41: return "non ha potuto chiedere al nucleo chi e', dopo l'exec";
	case 42: return "⛔ NON E' CHI DOVREBBE ESSERE: se n'e' accorto da se', "
	                "dopo l'exec, e non ha toccato niente";
	case 43: return "non e' riuscito a presentarsi al padre";
	default: return "(numero che questo padre non conosce)";
	}
}

/* La seconda meta': il nucleo ha confermato, la casella si libera. */
static void figlio_libera(struct figli *f, struct figlio *g, const char *perche)
{
	if (!g->usato)
		return;
	registro_dice(REG_FIGLIO,
	              "⭐ il figlio di «%s» (uid %ld) e' stato RACCOLTO: %s.  Da "
	              "adesso «morto» e «vivo» non hanno piu' la stessa faccia in "
	              "/proc, e la casella e' di nuovo libera",
	              g->utente, (long)g->uid, perche);
	if (g->fd >= 0)
		close(g->fd);
	free(g->monta);
	/* ⛔ E il deposito si lascia anche di qui, per le strade che non passano
	 *    dal congedo (un figlio morto senza che nessuno l'abbia mandato via).
	 *    ⚠ `congeda_figlio()` in `main.c` non fa niente se il deposito non era
	 *    suo: chiamarlo due volte non e' un difetto, non chiamarlo mai si'. */
	if (f->congeda)
		f->congeda(f->ctx, g->utente, g->uid);
	memset(g, 0, sizeof *g);
	g->fd = -1;
}

static void figlio_congeda(struct figli *f, struct figlio *g, const char *perche)
{
	if (!g->usato || g->uscendo)
		return;
	registro_dice(REG_FIGLIO,
	              "il figlio di «%s» (uid %ld, pid %ld, matricola %llu) se ne "
	              "va: %s — aspetto che il nucleo me lo confermi prima di "
	              "liberare la casella",
	              g->utente, (long)g->uid, (long)g->pid,
	              (unsigned long long)g->matricola, perche);
	g->uscendo = true;
	g->congedato_ms = registro_ora_ms();
	if (g->fd >= 0) {
		close(g->fd);
		g->fd = -1;
	}
	/* ⛔ Il socket chiuso e' gia' un congedo — il figlio legge EOF ed esce — ma
	 *    «basterebbe» non e' «l'ho fatto»: il segnale rende lo spegnimento un
	 *    fatto invece di una corsa. */
	if (g->pid > 0)
		kill(g->pid, SIGTERM);
	/* ⛔ E il deposito si lascia SUBITO, non alla raccolta: da questo istante
	 *    non c'e' piu' nessun palco dietro quei pixel, e tenerli sarebbe
	 *    mostrare l'immagine di un utente il cui processo non c'e' piu'. */
	if (f->congeda)
		f->congeda(f->ctx, g->utente, g->uid);
}

static struct figlio *cerca(struct figli *f, const char *utente)
{
	for (int i = 0; i < MAX_FIGLI; i++)
		if (f->v[i].usato && strcmp(f->v[i].utente, utente) == 0)
			return &f->v[i];
	return NULL;
}

/* ⭐ Lo scatto arriva al PADRE e va girato ai figli: vedi il riquadro dentro
 *    `figli_muovi()`.  ⛔ Qui si segna e basta — il lavoro si fa nel giro, non
 *    dentro un gestore di segnale. */
static volatile sig_atomic_t scatto_da_inoltrare = 0;

static void scatto_inoltro_segnale(int quale)
{
	scatto_da_inoltrare = (quale == SIGUSR2) ? 2 : 1;
}

figli *figli_accendi(uint32_t tela_l, uint32_t tela_a, const char *dir_rilievo,
                     FiglioDeposito deposita, FiglioCongedo congeda,
                     FiglioCursore cursore, FiglioTela tela, void *ctx)
{
	figli *f = (figli *)calloc(1, sizeof *f);
	ssize_t n;

	if (!f)
		return NULL;
	for (int i = 0; i < MAX_FIGLI; i++)
		f->v[i].fd = -1;
	f->prossima_matricola = 1;
	/* ⭐ Lo scatto a comando: il riquadro sta dentro `figli_muovi()`. */
	signal(SIGUSR1, scatto_inoltro_segnale);
	signal(SIGUSR2, scatto_inoltro_segnale);
	f->tela_l = tela_l;
	f->tela_a = tela_a;
	f->deposita = deposita;
	f->congeda = congeda;
	f->cursore = cursore;
	f->tela = tela;
	f->ctx = ctx;
	if (dir_rilievo && dir_rilievo[0]) {
		snprintf(f->dir_rilievo, sizeof f->dir_rilievo, "%s", dir_rilievo);
		f->c_e_rilievo = true;
	}

	/* ⛔ Il percorso del binario si CHIEDE AL NUCLEO, non si deduce da
	 *    `argv[0]`: `argv[0]` lo sceglie chi lancia, e un `exec` su un percorso
	 *    scelto da chi lancia sarebbe un modo di far girare come l'utente un
	 *    programma che non e' questo. */
	n = readlink("/proc/self/exe", f->percorso_mio, sizeof f->percorso_mio - 1);
	if (n <= 0) {
		registro_dice(REG_FIGLIO,
		              "⛔ non so quale binario sto eseguendo (/proc/self/exe: "
		              "%s): NESSUN figlio potra' nascere, e ogni utente ammesso "
		              "restera' senza palco (invariante I3: il fallimento e' un "
		              "no, non un forse)",
		              strerror(errno));
		free(f);
		return NULL;
	}
	f->percorso_mio[n] = 0;
	if (strstr(f->percorso_mio, " (deleted)")) {
		registro_dice(REG_FIGLIO,
		              "⛔ il binario in esecuzione e' stato cancellato o "
		              "sostituito sotto i piedi («%s»): NON genero figli, "
		              "perche' non posso dimostrare quale programma girerebbe "
		              "come l'utente",
		              f->percorso_mio);
		free(f);
		return NULL;
	}
	registro_dice(REG_FIGLIO,
	              "⭐ tabella dei figli accesa: fino a %d, uno per utente (I2), "
	              "tela %ux%u, binario «%s»",
	              MAX_FIGLI, tela_l, tela_a, f->percorso_mio);
	return f;
}

/* ⭐⭐ Il riquadro sta in `figlio.h`: qui si prende nota e basta, e chi non ha
 *     una tabella dei figli (`figli_accendi()` fallito) non si rompe. */
void figli_fase9(figli *f, bool qualita_risale, uint32_t tetto_banda_mbit,
                 bool audio_silenzio)
{
	if (!f)
		return;
	f->fase9_qualita_risale = qualita_risale;
	f->fase9_tetto_banda_mbit = tetto_banda_mbit;
	f->fase9_audio_silenzio = audio_silenzio;
	/* ⛔ E QUESTA RIGA NON E' LA DICHIARAZIONE DEL VALORE IN VIGORE — e' il
	 *    contrario: dice che cosa il padre si e' impegnato a PASSARE.  Il
	 *    valore in vigore lo scrive `codificatore.c` all'apertura di ogni
	 *    codificatore, dentro il figlio.  ⚠ Le due righe si leggono in coppia:
	 *    se questa dice «acceso» e quella dice «spento», l'opzione e' caduta
	 *    nel passaggio padre → figlio, e non e' la cura a non funzionare. */
	registro_dice(REG_FIGLIO,
	              "⭐ FASE 9, quel che il padre PASSERA' a ogni figlio nella sua "
	              "riga di comando: risalita della qualita' %s · tetto di banda "
	              "%s.  ⚠ Il valore IN VIGORE lo scrive il figlio, riga "
	              "«codificatore APERTO»: se li' dicesse un'altra cosa, il "
	              "passaggio si e' perso",
	              qualita_risale ? "ACCESA (--qualita-risale)"
	                             : "spenta (I6, --qualita-risale assente)",
	              tetto_banda_mbit ? "ACCESO" : "spento (I6, pavimento 0)");
	/* ⛔⭐⭐ E LA TERZA HA UNA RIGA SUA, perche' e' l'unica delle tre che nasce
	 *      ACCESA — 24 agosto 2026, decisione dell'utente.  ⚠ Va scritta anche
	 *      accesa: e' la riga da cui un banco legge lo stato del silenzio
	 *      dell'audio **senza aprire una sessione**, e le altre due righe della
	 *      terna (il figlio che dichiara di averla RICEVUTA, e `audio.c` che
	 *      dichiara il valore IN VIGORE) arrivano solo col primo codificatore. */
	registro_dice(REG_FIGLIO,
	              "⭐ FASE 9, il silenzio dell'audio che il padre PASSERA' a ogni "
	              "figlio: %s.  ⚠ `[M]` 09-b84: 102,1 volte meno traffico a "
	              "schermo fermo (557,6 → 5,5 kbit/s), 1 248 blocchi taciuti su "
	              "1 248; il prezzo e' +2 «mancati» su 5 000 al cliente",
	              audio_silenzio
	                  ? "ACCESO, ed e' il PREDEFINITO dal 24 agosto 2026 "
	                    "(decisione dell'utente) — si spegne con "
	                    "`--niente-audio-silenzio`"
	                  : "⛔ SPENTO a mano (`--niente-audio-silenzio`): si spedisce "
	                    "anche il silenzio, cioe' il prodotto fino al 23 agosto "
	                    "2026.  ⚠ E NON e' il predefinito");
	if (tetto_banda_mbit)
		registro_dice(REG_FIGLIO,
		              "⭐ FASE 9, il tetto di banda: pavimento %u Mbit/s "
		              "(--tetto-banda-mbit) — filo, punto di lavoro e serbatoio "
		              "si derivano di la', e li scrive codificatore.c",
		              tetto_banda_mbit);
}

/*
 * ⛔ La conversazione di PAM per l'apertura della sessione: NON deve chiedere
 *    niente.  `pam_open_session` non fa domande — e se ne facesse, rispondere a
 *    caso sarebbe peggio che fallire (`CODER.md` §3.9: il fallimento si
 *    dichiara).
 */
static int conversazione_muta_figlio(int n, const struct pam_message **m,
                                     struct pam_response **r, void *dati)
{
	(void)n;
	(void)m;
	(void)dati;
	*r = NULL;
	return PAM_CONV_ERR;
}

/* ⛔ Quel che si fa DOPO il `fork` e PRIMA dell'`exec`, e in quest'ordine.
 *    Ogni permuta e' punita con un difetto diverso, e nessuno dei tre dice
 *    «hai sbagliato l'ordine» (forma d'errore E4):
 *
 *      · i gruppi PRIMA dell'uid, o non si ha piu' il diritto di cambiarli;
 *      · `setgid` prima di `setuid`, o si perde il privilegio di farlo;
 *      · i descrittori si chiudono PRIMA di scendere, ma DOPO aver messo il
 *        socket al posto suo.
 *
 * ⚠ Questa funzione non torna mai: o fa `exec`, o esce con un numero. */
static void diventa_ed_esegui(const struct figli *f, const struct figlio *g,
                              int socket_figlio, const struct passwd *pw,
                              const gid_t *gruppi, int ngruppi)
{
	char a_utente[80], a_uid[32], a_gid[32], a_l[32], a_a[32], a_matr[40];
	char a_tetto[32];
	char e_home[512], e_user[96], e_log[96], e_path[128], e_runtime[160],
		e_bus[224], e_shell[16];
	/* ⚠ Quindici: le nove fisse, il NULL, e le CINQUE parole facoltative in
	 *   coda — `--parlantina`, `--qualita-risale`, `--tetto-banda-mbit` e il suo
	 *   numero, e `--niente-audio-silenzio`.  Si aggiungono solo se il padre le
	 *   ha (vedi sotto).  ⛔ Il conto si rifa' a ogni parola nuova: un `argv[]`
	 *   troppo corto non da' un errore, scrive oltre la fine dello stack. */
	char *argv[15];
	/* ⚠ 16 e non 9: alle sette che componiamo noi si aggiungono quelle che
	 *   `pam_systemd` mette nell'ambiente della sessione — `XDG_SESSION_ID` in
	 *   testa, che e' quel che a Mutter mancava. */
	char *envp[16];
	char **ambiente_pam = NULL;
	int na = 0, ne = 0;
	uid_t r, e, s;
	gid_t rg, eg, sg;

	/* 1. il socket al posto convenuto (fd 3), e senza CLOEXEC: e' l'unica
	 *    cosa che deve attraversare l'`exec`. */
	if (socket_figlio != 3) {
		if (dup2(socket_figlio, 3) < 0)
			_exit(30);
		close(socket_figlio);
	}
	fcntl(3, F_SETFD, 0);

	/* 2. ⛔ TUTTO IL RESTO SI CHIUDE, e questa riga e' la meta' della cura che
	 *    l'aiutante compra nascendo presto.  Un figlio che si portasse dietro
	 *    il socket UDP e l'ascoltatore TCP terrebbe occupata la porta anche
	 *    dopo la morte del server, e il sintomo sarebbe «indirizzo gia' in
	 *    uso» senza nessun server in vista.
	 * ⚠ 0,1,2 restano: il registro del figlio esce dallo stesso stderr del
	 *   padre, ed e' quel che rende leggibile «chi ha detto che cosa».
	 * ⚠ E l'`exec` chiuderebbe comunque i CLOEXEC — ma «li avrebbe chiusi
	 *   qualcun altro» non e' «li ho chiusi io», e non tutti lo sono. */
	if (close_range(4, ~0U, 0) != 0) {
		/* Ripiego dichiarato: la strada lenta, un descrittore per volta. */
		for (int i = 4; i < 4096; i++)
			close(i);
	}

	/*
	 * 2-bis. ⛔⭐⭐ LA SESSIONE PAM — e questa riga il 15 agosto 2026 non c'era.
	 *
	 * ⛔ IL DIFETTO CHE CURA, misurato la sera del 15 agosto: senza una sessione
	 *    logind il compositore **non parte affatto**.  Mutter chiede
	 *    `sd_pid_get_session()`, si sente rispondere **ENXIO** — «questo processo
	 *    non sta in nessuna sessione» — e muore con *«Failed to find any matching
	 *    session»*.  ⚠ E il `linger` NON basta: da' `/run/user/<uid>` e il bus, ma
	 *    mette i processi in `user@<uid>.service`, che e' uno scope di classe
	 *    `manager` — non una sessione.
	 *
	 * ⛔ QUI C'ERA SCRITTO IL CONTRARIO, ed era giusto per un'altra fase: «far
	 *    NASCERE una sessione e' del login vero, non di questo mandato».  ⭐ Alla
	 *    fase 5 quel mandato **e' questo**: `PIANO.md` scrive «Produce: **PAM per
	 *    intero**».
	 *
	 * ⭐ E LE TRE COSE CHE SI DICONO A `pam_systemd` hanno ciascuna un perche':
	 *
	 *   · `XDG_SESSION_TYPE=wayland` — l'unita' della Shell porta
	 *     `ConditionEnvironment=XDG_SESSION_TYPE=wayland`: senza, il compositore
	 *     non viene avviato AFFATTO, e non c'e' nessuna riga che dica perche';
	 *   · `XDG_SESSION_CLASS=user` — `manager` e' quel che da' il linger, ed e'
	 *     proprio la classe che a Mutter non basta;
	 *   · ⛔ **nessun `XDG_SEAT`, e non e' una dimenticanza**: una sessione senza
	 *     seat e' headless **per costruzione**, che e' quel che `DECISIONI.md`
	 *     §4.3-bis chiede da agosto e che fino a oggi avevamo per accidente.
	 *
	 * ⚠ E `PAM_RHOST`: logind segna la sessione `Remote=yes`.  ⭐ Ripaga due volte
	 *   — e' la seconda cintura del guardiano di §5.1 (`sentinella.c` discrimina
	 *   sul seat, e questa e' la conferma indipendente) e fa comparire la
	 *   provenienza nei registri di sistema.
	 *
	 * ⛔ `pam_end()` SENZA `pam_close_session()`, ed e' voluto: chiudere la
	 *    sessione la porterebbe via subito.  La sessione logind appartiene al
	 *    processo GUIDA — che e' questo, dopo l'`exec` — e logind se la riprende
	 *    quando lui muore.  ⚠ Il che rende vera l'invariante I4 dal lato del
	 *    sistema: il palco sopravvive al client perche' il figlio sopravvive.
	 *
	 * ⚠ E se PAM non ce la fa NON si esce: si prosegue e lo si scrive.  Una
	 *   sessione senza logind e' rotta, ⛔ ma un figlio che muore qui non lascia
	 *   nemmeno una riga a chi legge il registro (invariante I1).
	 */
	{
		struct pam_conv conv_muta = { conversazione_muta_figlio, NULL };
		pam_handle_t *pam = NULL;
		int rv;

		rv = pam_start("remotix", pw->pw_name, &conv_muta, &pam);
		if (rv != PAM_SUCCESS) {
			fprintf(stderr, "figlio: ⛔ pam_start: %s\n",
			        pam_strerror(NULL, rv));
		} else {
			pam_putenv(pam, "XDG_SESSION_TYPE=wayland");
			pam_putenv(pam, "XDG_SESSION_CLASS=user");
			pam_set_item(pam, PAM_RHOST, "remotix");
			pam_set_item(pam, PAM_TTY, "remotix");

			rv = pam_open_session(pam, PAM_SILENT);
			if (rv != PAM_SUCCESS) {
				fprintf(stderr,
				        "figlio: ⛔ pam_open_session: %s — il "
				        "compositore non partira'\n",
				        pam_strerror(pam, rv));
			} else {
				ambiente_pam = pam_getenvlist(pam);
			}
			/* ⛔ `pam_end` e non `pam_close_session`: vedi sopra. */
			pam_end(pam, PAM_SUCCESS);
		}
	}

	/* 3. i gruppi, poi il gid, poi l'uid — e mai al contrario. */
	if (setgroups((size_t)ngruppi, gruppi) != 0)
		_exit(31);
	if (setgid(pw->pw_gid) != 0)
		_exit(32);
	if (setuid(pw->pw_uid) != 0)
		_exit(33);

	/* 4. ⛔⭐ E SI VERIFICA DI ESSERE SCESO DAVVERO, CHIEDENDOLO AL NUCLEO.
	 *
	 *    `setuid()` che ritorna 0 dice che la chiamata e' riuscita, non che
	 *    **tutti e tre** gli uid sono cambiati: se restasse un saved-set-uid a
	 *    zero, questo processo potrebbe tornare root con una riga.  ⇒ Si
	 *    leggono tutti e sei con `getresuid`/`getresgid`, e se uno solo non e'
	 *    quello atteso il figlio NON parte.  ⚠ E' l'invariante I7 letta da
	 *    dentro: la protezione sta nel programma. */
	if (getresuid(&r, &e, &s) != 0 || getresgid(&rg, &eg, &sg) != 0)
		_exit(34);
	if (r != pw->pw_uid || e != pw->pw_uid || s != pw->pw_uid)
		_exit(35);
	if (rg != pw->pw_gid || eg != pw->pw_gid || sg != pw->pw_gid)
		_exit(36);

	/* 5. ⛔ L'ambiente si compone da zero, una variabile per volta
	 *    (`CODER.md` §4.5).  ⚠ E con `execve` non c'e' modo di sbagliarlo per
	 *    distrazione: quel che non sta in questo elenco non esiste dall'altra
	 *    parte.
	 *
	 * ⚠ `SHELL` VUOTA di sua mano, come fa `sessione.c`: una `SHELL` ereditata
	 *   fa ripartire le sessioni dentro una shell di login, ed e' lo stato 7
	 *   del banco della sessione.
	 * ⚠ E NESSUNA variabile di lingua: qui non si avvia nessuna applicazione,
	 *   quindi non c'e' niente che una locale sbagliata possa impedire.  Il
	 *   giorno in cui questo figlio facesse NASCERE una sessione, vale la
	 *   regola di `sessione.c` — e va scritta li', non indovinata qui. */
	snprintf(e_home, sizeof e_home, "HOME=%s", pw->pw_dir);
	snprintf(e_user, sizeof e_user, "USER=%s", pw->pw_name);
	snprintf(e_log, sizeof e_log, "LOGNAME=%s", pw->pw_name);
	snprintf(e_path, sizeof e_path, "PATH=/usr/local/bin:/usr/bin:/bin");
	snprintf(e_shell, sizeof e_shell, "SHELL=");
	snprintf(e_runtime, sizeof e_runtime, "XDG_RUNTIME_DIR=/run/user/%ld",
	         (long)pw->pw_uid);
	snprintf(e_bus, sizeof e_bus,
	         "DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/%ld/bus",
	         (long)pw->pw_uid);
	envp[ne++] = e_home;
	envp[ne++] = e_user;
	envp[ne++] = e_log;
	envp[ne++] = e_path;
	envp[ne++] = e_shell;
	envp[ne++] = e_runtime;
	envp[ne++] = e_bus;
	/* ⭐⭐ E QUI SI SMETTE DI INVENTARLE — l'osservazione dell'utente del 15
	 *     agosto 2026: *«le variabili XDG dovrebbe impostarle il session
	 *     manager, e in REMOTIX sembra che non vengano impostate»*.  Aveva
	 *     ragione: nessuno le impostava perche' nessuno apriva la sessione.
	 *     Adesso la apriamo, e quel che `pam_systemd` ci mette dentro si
	 *     **legge** invece di dedurlo.
	 * ⛔ `XDG_SESSION_ID` e' quella che conta: e' il filo che lega questo
	 *    processo alla sessione logind, ed e' quel che Mutter cercava. */
	for (int i = 0; ambiente_pam && ambiente_pam[i] && ne < 14; i++)
		if (strncmp(ambiente_pam[i], "XDG_SESSION_ID=", 15) == 0)
			envp[ne++] = ambiente_pam[i];
	envp[ne] = NULL;

	/* 6. la riga di comando del figlio, che e' quel che il banco leggera' in
	 *    `/proc/<pid>/cmdline`.  ⛔ Niente segreti qui dentro: la parola
	 *    d'ordine e' gia' morta con l'aiutante, e non passa di qui. */
	snprintf(a_utente, sizeof a_utente, "%s", pw->pw_name);
	snprintf(a_uid, sizeof a_uid, "%ld", (long)pw->pw_uid);
	snprintf(a_gid, sizeof a_gid, "%ld", (long)pw->pw_gid);
	snprintf(a_l, sizeof a_l, "%u", f->tela_l);
	snprintf(a_a, sizeof a_a, "%u", f->tela_a);
	snprintf(a_matr, sizeof a_matr, "%llu", (unsigned long long)g->matricola);
	argv[na++] = (char *)"remotix-figlio";
	argv[na++] = (char *)"--figlio-interno";
	argv[na++] = a_utente;
	argv[na++] = a_uid;
	argv[na++] = a_gid;
	argv[na++] = a_l;
	argv[na++] = a_a;
	argv[na++] = a_matr;
	argv[na++] = f->c_e_rilievo ? (char *)f->dir_rilievo : (char *)"-";
	/*
	 * ⛔⭐⭐⭐ E LA PARLANTINA SI PASSA AL FIGLIO — 16 agosto 2026, ed e' il
	 *        difetto che mi ha fatto perdere una giornata intera.
	 *
	 * ⛔ Il figlio NON e' un fork: e' un `execve` di `remotix-figlio`.  ⇒ Non
	 *    eredita le variabili del padre, e `registro_parlantina()` nel figlio
	 *    restava **spenta** — anche quando il server era partito con
	 *    `--parlantina`.
	 *
	 * ⚠ Quindi **ogni `registro_dettaglio()` di `figlio.c` finiva nel nulla**,
	 *   in silenzio, senza un errore.  `[M]` Ed e' costato caro: cercando la
	 *   coda dei tempi di login ho concluso per ore che certi rami «non
	 *   scattavano mai», perche' la loro riga non compariva — mentre scattavano
	 *   eccome.  ⭐ La diagnostica che tace non e' neutra: **mente**, e mente
	 *   nella direzione peggiore, cioe' «quel codice non gira».
	 *
	 * ⇒ E' la forma E8 (`LEZIONI.md` §1.9) dentro lo strumento che serve a
	 *   smascherarla: «non l'ha fatto» e «non me l'ha detto» con la stessa
	 *   faccia.
	 *
	 * ⚠ In coda e opzionale: il figlio legge `argc >= 9` e questo e' il decimo,
	 *   quindi una riga di comando senza non si rompe.
	 */
	if (registro_parla_molto())
		argv[na++] = (char *)"--parlantina";
	/*
	 * ⛔⭐⭐ E LE **TRE** CURE DELLA FASE 9 PASSANO DI QUI, per la stessa ragione
	 *      esatta della parlantina qui sopra — e non e' un'analogia, e' lo
	 *      stesso difetto.  ⚠ La terza (il silenzio dell'audio) e' arrivata il
	 *      24 agosto 2026, e viaggia NEGATA: vedi il riquadro piu' sotto.
	 *
	 * ⛔ `codificatore_qualita_risale()` e `codificatore_tetto_banda()` sono
	 *    statiche del PROCESSO: chiamarle nel padre non accende niente, perche'
	 *    il padre un codificatore non lo apre mai.  ⚠ E l'ambiente qui sopra e'
	 *    composto da zero (punto 5): una `REMOTIX_...` non arriva dall'altra
	 *    parte, e non lascerebbe nemmeno una riga a dire che non e' arrivata.
	 *
	 * ⇒ L'unico canale che attraversa l'`exec` insieme al socket e' questo, e
	 *   il figlio le rilegge in `figlio_vive()`.
	 *
	 * ⚠ In coda e facoltative: il figlio legge le prime nove per posizione e
	 *   scorre il resto per nome, quindi una riga di comando senza non si
	 *   rompe.  ⭐ E compaiono in `/proc/<pid>/cmdline`: chi guarda un banco
	 *   vede con che cosa quel figlio e' nato, senza fidarsi di un registro.
	 */
	if (f->fase9_qualita_risale)
		argv[na++] = (char *)"--qualita-risale";
	if (f->fase9_tetto_banda_mbit) {
		snprintf(a_tetto, sizeof a_tetto, "%u", f->fase9_tetto_banda_mbit);
		argv[na++] = (char *)"--tetto-banda-mbit";
		argv[na++] = a_tetto;
	}
	/* ⛔⭐⭐ E LA TERZA VIAGGIA NEGATA, che e' l'unica forma che non mente.
	 *
	 *      Le due qui sopra nascono spente: quel che si scrive in coda e'
	 *      «accendila».  Questa nasce ACCESA (24 agosto 2026), quindi quel che
	 *      si scrive e' «spegnila» — ⛔ e la parola in `argv` e' la STESSA che
	 *      il server ha ricevuto (`--niente-audio-silenzio`), perche' chi guarda
	 *      `/proc/<pid>/cmdline` di un figlio deve poterla confrontare a occhio
	 *      con la riga di comando del padre.  ⚠ Se qui comparisse un
	 *      `--audio-silenzio` positivo ci sarebbero DUE nomi per la stessa cura,
	 *      ed e' esattamente quel che questa fase ha tolto. */
	if (!f->fase9_audio_silenzio)
		argv[na++] = (char *)"--niente-audio-silenzio";
	argv[na] = NULL;

	execve(f->percorso_mio, argv, envp);
	_exit(37);
}

bool figli_assicura(figli *f, const char *utente)
{
	struct figlio *g;
	struct passwd pw, *ris = NULL;
	char scorta[1024];
	gid_t gruppi[64];
	int ngruppi = (int)(sizeof gruppi / sizeof gruppi[0]);
	int sv[2];
	int uno = 1;
	int libero = -1;
	pid_t p;

	if (!f || !utente || !utente[0])
		return false;

	/* ⛔⭐ I2 — «una sola sessione grafica per utente».  Due connessioni dello
	 *     stesso utente NON fanno due figli: la seconda trova il primo, e vede
	 *     lo stesso palco.  ⚠ E se il primo e' morto, la casella e' gia' stata
	 *     liberata da `figli_muovi()`: qui non si resuscita niente. */
	g = cerca(f, utente);
	if (g) {
		registro_dice(REG_FIGLIO,
		              "«%s» e' gia' servito dal figlio pid %ld (uid %ld): NON "
		              "ne nasce un secondo — invariante I2, e il palco e' lo "
		              "stesso perche' e' della SESSIONE (I4)",
		              utente, (long)g->pid, (long)g->uid);
		return true;
	}

	for (int i = 0; i < MAX_FIGLI; i++)
		if (!f->v[i].usato) {
			libero = i;
			break;
		}
	if (libero < 0) {
		registro_dice(REG_FIGLIO,
		              "⛔ %d figli gia' vivi: «%s» NON ne avra' uno, e quindi "
		              "non avra' un palco.  E' un no dichiarato, non un forse "
		              "(invariante I3)",
		              MAX_FIGLI, utente);
		return false;
	}

	/* ⛔ Il nome si risolve QUI, nel padre, e l'uid che ne esce e' quello che
	 *    il nucleo dovra' timbrare su ogni messaggio.  ⚠ Risolverlo nel figlio
	 *    sarebbe far dire a chi deve essere controllato chi e'. */
	if (getpwnam_r(utente, &pw, scorta, sizeof scorta, &ris) != 0 || !ris) {
		registro_dice(REG_FIGLIO,
		              "⛔ «%s» ha superato PAM ma non e' un utente di questo "
		              "sistema (getpwnam: %s): NESSUN figlio.  ⚠ Non e' un "
		              "controsenso — PAM puo' ammettere un nome che NSS non "
		              "risolve, e in quel caso non c'e' nessun uid a cui "
		              "scendere",
		              utente, strerror(errno));
		return false;
	}
	if (pw.pw_uid == 0) {
		/* ⛔ Un figlio a uid 0 non sarebbe un figlio: sarebbe il padre con un
		 *    altro nome, e la ragione per cui questo file esiste — root non
		 *    parla col bus di sessione — varrebbe identica per lui. */
		registro_dice(REG_FIGLIO,
		              "⛔ «%s» e' uid 0: NON genero un figlio privilegiato.  Il "
		              "figlio esiste per NON essere root (DECISIONI.md "
		              "§1.10-bis), e uno a uid 0 non avrebbe comunque il bus di "
		              "sessione di nessuno",
		              utente);
		return false;
	}
	if (getgrouplist(pw.pw_name, pw.pw_gid, gruppi, &ngruppi) < 0) {
		/* Piu' gruppi di quanti ne tenga la scorta: si prende quel che c'e' e
		 * si DICHIARA, perche' un figlio con meno gruppi del dovuto puo'
		 * trovare un permesso negato molto piu' tardi e molto piu' lontano. */
		ngruppi = (int)(sizeof gruppi / sizeof gruppi[0]);
		registro_dice(REG_FIGLIO,
		              "⚠ «%s» ha piu' di %d gruppi: il figlio ne portera' %d.  "
		              "Se qualcosa gli sara' negato, la causa e' questa riga",
		              utente, ngruppi, ngruppi);
	}

	/* ⛔ `SOCK_SEQPACKET` per la stessa ragione dell'aiutante: i confini dei
	 *    messaggi li tiene il nucleo.  Con uno stream l'inquadramento sarebbe
	 *    nostro, e un difetto li' dentro vorrebbe dire «i pixel di un altro» —
	 *    cioe' I3 rotta da un errore di lettura.
	 * ⛔ E `CLOEXEC` sul capo del padre: il figlio NON deve avere in mano il
	 *    capo di suo padre, o non si accorgerebbe mai che il padre e' morto. */
	if (socketpair(AF_UNIX, SOCK_SEQPACKET | SOCK_CLOEXEC, 0, sv) != 0) {
		registro_dice(REG_FIGLIO,
		              "⛔ niente socketpair per «%s» (%s): nessun figlio, "
		              "nessun palco",
		              utente, strerror(errno));
		return false;
	}
	/* ⛔⭐ QUESTA RIGA E' L'INVARIANTE I3 DI TUTTO IL FILE.  Senza
	 *     `SO_PASSCRED`, il nucleo non timbra le credenziali e ogni messaggio
	 *     arriverebbe «senza mittente»: il padre potrebbe solo credere alla
	 *     parola del figlio, cioe' non controllare niente. */
	if (setsockopt(sv[0], SOL_SOCKET, SO_PASSCRED, &uno, sizeof uno) != 0) {
		registro_dice(REG_FIGLIO,
		              "⛔ SO_PASSCRED non si accende (%s): senza, il nucleo non "
		              "firma i messaggi del figlio e l'identita' sarebbe una "
		              "SUA dichiarazione.  NON genero il figlio: meglio nessun "
		              "palco che un palco di cui non so di chi e'",
		              strerror(errno));
		close(sv[0]);
		close(sv[1]);
		return false;
	}

	g = &f->v[libero];
	memset(g, 0, sizeof *g);
	g->matricola = f->prossima_matricola;
	snprintf(g->utente, sizeof g->utente, "%s", pw.pw_name);
	g->uid = pw.pw_uid;
	g->gid = pw.pw_gid;

	p = fork();
	if (p < 0) {
		registro_dice(REG_FIGLIO, "⛔ fork per «%s»: %s — nessun palco", utente,
		              strerror(errno));
		close(sv[0]);
		close(sv[1]);
		memset(g, 0, sizeof *g);
		g->fd = -1;
		return false;
	}
	if (p == 0) {
		close(sv[0]);
		diventa_ed_esegui(f, g, sv[1], &pw, gruppi, ngruppi);
		_exit(38); /* non ci si arriva */
	}

	close(sv[1]);
	g->usato = true;
	g->pid = p;
	g->fd = sv[0];
	/* ⛔ Non bloccante dal lato del PADRE, e solo da quello: qui si sta dentro
	 *    l'unico ciclo `poll` del server, e una lettura che aspetta ferma tutte
	 *    le connessioni insieme (`CODER.md` §4.4) — il difetto appena curato su
	 *    PAM, rimesso da un'altra porta.  ⚠ Il capo del FIGLIO resta bloccante
	 *    apposta: li' aspettare e' il mestiere. */
	fcntl(g->fd, F_SETFL, O_NONBLOCK);
	g->nato_ms = registro_ora_ms();
	g->ultimo_ricontrollo_ms = g->nato_ms;
	f->prossima_matricola++;

	registro_dice(REG_FIGLIO,
	              "⭐ figlio generato per «%s»: pid %ld, uid %ld, gid %ld, "
	              "matricola %llu.  ⛔ Che sia DAVVERO quell'uid non lo dico "
	              "io: lo dira' il nucleo su ogni suo messaggio (SO_PASSCRED)",
	              g->utente, (long)g->pid, (long)g->uid, (long)g->gid,
	              (unsigned long long)g->matricola);
	return true;
}

size_t figli_descrittori(figli *f, struct pollfd *fds, size_t max)
{
	size_t n = 0;
	if (!f)
		return 0;
	for (int i = 0; i < MAX_FIGLI && n < max; i++) {
		if (!f->v[i].usato || f->v[i].fd < 0)
			continue;
		fds[n].fd = f->v[i].fd;
		fds[n].events = POLLIN;
		fds[n].revents = 0;
		n++;
	}
	return n;
}

int figli_quanti(const figli *f)
{
	int n = 0;
	if (!f)
		return 0;
	for (int i = 0; i < MAX_FIGLI; i++)
		if (f->v[i].usato)
			n++;
	return n;
}

pid_t figli_pid_di(const figli *f, const char *utente)
{
	const struct figlio *g;
	if (!f || !utente)
		return -1;
	g = cerca((figli *)f, utente);
	return g ? g->pid : -1;
}

/* Un pezzo di fotogramma e' arrivato, e le credenziali erano giuste. */
static void monta_pezzo(struct figli *f, struct figlio *g,
                        const struct corpo_fotogramma *c, const uint8_t *dati)
{
	if (c->totale == 0 || c->totale > FOTOGRAMMA_MAX) {
		registro_dice(REG_FIGLIO,
		              "⛔ «%s» annuncia un fotogramma di %u byte: fuori dal "
		              "tetto di §6.2 (1..%u).  Si butta, e NON si tronca: un "
		              "fotogramma tagliato consegnato come intero e' un "
		              "fotogramma che mente",
		              g->utente, c->totale, FOTOGRAMMA_MAX);
		return;
	}
	if (c->pezzo > PEZZO_MAX || (uint64_t)c->offset + c->pezzo > c->totale) {
		registro_dice(REG_FIGLIO,
		              "⛔ «%s»: pezzo fuori misura (offset %u + %u su %u): "
		              "scartato",
		              g->utente, c->offset, c->pezzo, c->totale);
		free(g->monta);
		g->monta = NULL;
		g->monta_totale = g->monta_avuti = 0;
		return;
	}

	if (c->offset == 0) {
		free(g->monta);
		g->monta = (uint8_t *)malloc(c->totale);
		if (!g->monta) {
			registro_dice(REG_FIGLIO,
			              "⛔ «%s»: %u byte di fotogramma non entrano in "
			              "memoria",
			              g->utente, c->totale);
			g->monta_totale = g->monta_avuti = 0;
			return;
		}
		g->monta_totale = c->totale;
		g->monta_avuti = 0;
		g->monta_codec = c->codec;
		g->monta_chiave = c->chiave;
		g->monta_l = c->larghezza;
		g->monta_a = c->altezza;
		g->monta_istante = c->istante_us;
		g->monta_input = c->input;
	}
	/* ⛔ I pezzi si accettano SOLO in ordine, e uno fuori posto butta tutto:
	 *    ricucire un buco vorrebbe dire indovinare che cosa mancava, ed e'
	 *    l'indulgenza che nasconde (`REVIEWER.md` §5). */
	if (!g->monta || c->offset != g->monta_avuti || c->codec != g->monta_codec
	    || c->totale != g->monta_totale) {
		registro_dice(REG_FIGLIO,
		              "⛔ «%s»: pezzo fuori ordine (aspettavo %zu, e' arrivato "
		              "%u): il fotogramma si BUTTA intero",
		              g->utente, g->monta_avuti, c->offset);
		free(g->monta);
		g->monta = NULL;
		g->monta_totale = g->monta_avuti = 0;
		return;
	}
	memcpy(g->monta + c->offset, dati, c->pezzo);
	g->monta_avuti += c->pezzo;
	if (g->monta_avuti < g->monta_totale)
		return;

	/* ⛔⭐ E QUESTA RIGA E' PASSATA IN PARLANTINA CON LA FASE 3.
	 *
	 *     Con un fotogramma solo era la riga che dimostrava tutta la fase 2.
	 *     ⛔ A sessanta al secondo diventa sessanta righe al secondo per
	 *     utente, e un registro che ripete non si legge piu' — cioe' la stessa
	 *     ragione per cui esisteva `bool video_fatto`.  ⚠ Il fatto NON sparisce:
	 *     resta nella parlantina, e il conto riassunto lo scrive `contati` qui
	 *     sotto una volta al secondo.  Il primo, quello che dice se il palco
	 *     funziona, si scrive comunque. */
	if (g->fotogrammi_avuti == 0)
		registro_dice(REG_FIGLIO,
		              "⭐ PRIMO fotogramma completo da «%s» (uid %ld, timbro del "
		              "nucleo): codec %u, %zu byte, %ux%u, %s",
		              g->utente, (long)g->uid, g->monta_codec, g->monta_totale,
		              g->monta_l, g->monta_a,
		              g->monta_chiave ? "CHIAVE" : "delta");
	else
		registro_dettaglio(REG_FIGLIO,
		                   "fotogramma da «%s»: codec %u, %zu byte, %s",
		                   g->utente, g->monta_codec, g->monta_totale,
		                   g->monta_chiave ? "CHIAVE" : "delta");
	g->fotogrammi_avuti++;
	g->byte_avuti += g->monta_totale;
	if (g->monta_chiave)
		g->chiavi_avute++;
	if (f->deposita)
		f->deposita(f->ctx, g->utente, g->uid, g->monta_codec,
		            g->monta_chiave != 0, g->monta, g->monta_totale, g->monta_l,
		            g->monta_a, g->monta_istante, g->monta_input);
	free(g->monta);
	g->monta = NULL;
	g->monta_totale = g->monta_avuti = 0;
}

/* ⭐⭐ Un pezzo di CURSORE e' arrivato, e le credenziali erano giuste.
 *
 * ⚠ Perche' ha un montaggio suo e non riusa quello del fotogramma: i due
 *   arrivano intrecciati sullo stesso socket, e con un tavolo solo ogni cambio
 *   di forma butterebbe il fotogramma a meta' e viceversa. */
/* ⭐⭐ FASE 7 — il testo degli appunti che la SESSIONE ha copiato, un pezzo per
 *     volta.  Stesso stampo del cursore, e le differenze sono due e dichiarate:
 *
 *       · il tetto e' quello di `RCP.md` §5.4 — **1 000 000 byte** — e si fa
 *         rispettare QUI perche' qui il mittente e' un altro processo.  ⚠ Non
 *         e' un doppione del controllo di `appunti.c`: quello e' un modulo di
 *         cui ci fidiamo, questo e' un socket;
 *       · si alloca **un byte in piu'** e ci si mette lo zero: da qui in poi il
 *         testo viaggia come stringa, e `appunti.c` ha gia' garantito che non
 *         ne contenga uno in mezzo.
 */
static void monta_appunti(struct figli *f, struct figlio *g,
                          const struct corpo_appunti *c, const uint8_t *dati)
{
	if (c->totale > APPUNTI_TETTO) {
		registro_dice(REG_FIGLIO,
		              "⛔ «%s» annuncia %u byte di appunti: oltre il tetto di "
		              "§5.4 (%u).  Si butta, e NON si tronca — un testo tagliato "
		              "incollato in un terminale e' peggio di un testo mancante",
		              g->utente, c->totale, APPUNTI_TETTO);
		return;
	}
	/* ⚠ Zero byte e' un fatto LECITO: la clipboard svuotata.  Si consegna, e
	 *   chi riceve decide — non e' compito di questo tavolo. */
	if (c->totale == 0) {
		if (f->su_appunti_testo)
			f->su_appunti_testo(f->ctx_appunti, g->utente, g->uid, "", 0);
		return;
	}
	if (c->pezzo > PEZZO_MAX || (uint64_t)c->offset + c->pezzo > c->totale) {
		registro_dice(REG_FIGLIO,
		              "⛔ «%s»: pezzo di appunti fuori misura (offset %u + %u su "
		              "%u): scartato",
		              g->utente, c->offset, c->pezzo, c->totale);
		free(g->app_monta);
		g->app_monta = NULL;
		g->app_totale = g->app_avuti = 0;
		return;
	}
	if (c->offset == 0) {
		free(g->app_monta);
		g->app_monta = (uint8_t *)malloc((size_t)c->totale + 1u);
		if (!g->app_monta) {
			registro_dice(REG_FIGLIO,
			              "⛔ «%s»: %u byte di appunti non entrano in memoria",
			              g->utente, c->totale);
			g->app_totale = g->app_avuti = 0;
			return;
		}
		g->app_totale = c->totale;
		g->app_avuti = 0;
	}
	/* ⛔ In ordine e basta, come il fotogramma e il cursore.  ⚠ E qui il buco
	 *    indovinato sarebbe **peggio**: un fotogramma sbagliato dura 20 ms, un
	 *    testo sbagliato lo si incolla in un terminale. */
	if (!g->app_monta || c->offset != g->app_avuti
	    || c->totale != g->app_totale) {
		registro_dice(REG_FIGLIO,
		              "⛔ «%s»: pezzo di appunti fuori ordine (aspettavo %zu, e' "
		              "arrivato %u): il testo si BUTTA intero",
		              g->utente, g->app_avuti, c->offset);
		free(g->app_monta);
		g->app_monta = NULL;
		g->app_totale = g->app_avuti = 0;
		return;
	}
	memcpy(g->app_monta + c->offset, dati, c->pezzo);
	g->app_avuti += c->pezzo;
	if (g->app_avuti < g->app_totale)
		return;

	g->app_monta[g->app_totale] = 0;
	registro_dice(REG_FIGLIO,
	              "⭐ «%s» ha copiato %zu byte di testo nella sessione: al "
	              "client (§7.4)",
	              g->utente, g->app_totale);
	if (f->su_appunti_testo)
		f->su_appunti_testo(f->ctx_appunti, g->utente, g->uid,
		                    (const char *)g->app_monta, g->app_totale);
	free(g->app_monta);
	g->app_monta = NULL;
	g->app_totale = g->app_avuti = 0;
}

static void monta_cursore(struct figli *f, struct figlio *g,
                          const struct corpo_cursore *c, const uint8_t *dati)
{
	/* ⛔ Il tetto e' quello di `RCP.md` §5.5 — 256x256 in BGRA — e si fa
	 *    rispettare QUI perche' qui il mittente e' un altro processo.  ⚠ Non e'
	 *    un doppione dei limiti di `cursore.c`: quello e' un modulo di cui ci
	 *    fidiamo, questo e' un socket. */
	if (c->totale > (uint32_t)CURSORE_MAX_LATO * CURSORE_MAX_LATO * 4u) {
		registro_dice(REG_FIGLIO,
		              "⛔ «%s» annuncia un cursore di %u byte: oltre il tetto di "
		              "§5.5 (%ux%u in BGRA).  Si butta",
		              g->utente, c->totale, CURSORE_MAX_LATO, CURSORE_MAX_LATO);
		return;
	}

	/* ⭐ Il nascosto arriva senza immagine, e si consegna subito: e' l'unico
	 *    modo che il client ha di sapere che il puntatore e' sparito. */
	if (c->totale == 0) {
		if (f->cursore)
			f->cursore(f->ctx, g->utente, g->uid, c->larghezza, c->altezza,
			           c->attivo_x, c->attivo_y, NULL, 0);
		return;
	}
	if (c->pezzo > PEZZO_MAX || (uint64_t)c->offset + c->pezzo > c->totale) {
		registro_dice(REG_FIGLIO,
		              "⛔ «%s»: pezzo di cursore fuori misura (offset %u + %u su "
		              "%u): scartato",
		              g->utente, c->offset, c->pezzo, c->totale);
		free(g->cur_monta);
		g->cur_monta = NULL;
		g->cur_totale = g->cur_avuti = 0;
		return;
	}
	if (c->offset == 0) {
		free(g->cur_monta);
		g->cur_monta = (uint8_t *)malloc(c->totale);
		if (!g->cur_monta) {
			g->cur_totale = g->cur_avuti = 0;
			return;
		}
		g->cur_totale = c->totale;
		g->cur_avuti = 0;
		g->cur_l = c->larghezza;
		g->cur_a = c->altezza;
		g->cur_ax = c->attivo_x;
		g->cur_ay = c->attivo_y;
	}
	/* ⛔ In ordine e basta, come il fotogramma: ricucire un buco vorrebbe dire
	 *    indovinare che cosa mancava — e un cursore indovinato e' un cursore
	 *    fatto di memoria altrui. */
	if (!g->cur_monta || c->offset != g->cur_avuti || c->totale != g->cur_totale
	    || c->larghezza != g->cur_l || c->altezza != g->cur_a) {
		registro_dettaglio(REG_FIGLIO,
		                   "«%s»: pezzo di cursore fuori ordine: butto la forma "
		                   "a meta' (il client tiene quella di prima)",
		                   g->utente);
		free(g->cur_monta);
		g->cur_monta = NULL;
		g->cur_totale = g->cur_avuti = 0;
		return;
	}
	memcpy(g->cur_monta + c->offset, dati, c->pezzo);
	g->cur_avuti += c->pezzo;
	if (g->cur_avuti < g->cur_totale)
		return;

	if (f->cursore)
		f->cursore(f->ctx, g->utente, g->uid, g->cur_l, g->cur_a, g->cur_ax,
		           g->cur_ay, g->cur_monta, g->cur_totale);
	free(g->cur_monta);
	g->cur_monta = NULL;
	g->cur_totale = g->cur_avuti = 0;
}

/* ⛔ Restituisce `false` quando il figlio non c'e' piu' — e chi chiama DEVE
 * smettere di leggere il suo descrittore.  ⚠ Senza questo valore, il ciclo di
 * `figli_muovi()` continuerebbe a leggere una casella appena azzerata: il tipo
 * di difetto che si legge bene e non si vede mai. */
static bool tratta(struct figli *f, struct figlio *g, const struct testa *t,
                   const uint8_t *corpo, size_t byte)
{
	switch (t->tipo) {
	case MSG_SONO: {
		struct corpo_sono s;
		if (byte < sizeof s)
			return true;
		memcpy(&s, corpo, sizeof s);
		/* ⛔ E QUI SI CHIUDE IL CERCHIO: il figlio dice quel che il NUCLEO gli
		 *    ha risposto su di se' (`getresuid`), e il padre lo confronta con
		 *    quel che il NUCLEO ha timbrato sul messaggio.  Se i due
		 *    divergessero, uno dei due sta leggendo una variabile invece di
		 *    chiedere — e il figlio verrebbe abbattuto. */
		if (s.uid != (uint32_t)g->uid || s.euid != (uint32_t)g->uid
		    || s.suid != (uint32_t)g->uid) {
			registro_dice(REG_FIGLIO,
			              "⛔⛔ «%s» dice di essere uid %u/%u/%u e il nucleo lo "
			              "ha timbrato come %ld: il figlio si abbatte",
			              g->utente, s.uid, s.euid, s.suid, (long)g->uid);
			if (g->pid > 0)
				kill(g->pid, SIGKILL);
			figlio_congeda(f, g, "si dichiara un uid diverso da quello timbrato");
			return false;
		}
		if (g->si_e_presentato) {
			registro_dettaglio(REG_FIGLIO,
			                   "«%s» ricontrollato: uid %u, pid %u, padre %u, "
			                   "%u descrittori — il legame regge",
			                   g->utente, s.euid, s.pid, s.ppid, s.descrittori);
			return true;
		}
		g->si_e_presentato = true;
		registro_dice(REG_FIGLIO,
		              "⭐ «%s» si presenta: pid %u (padre %u), uid %u/%u/%u, "
		              "gid %u/%u/%u, %u descrittori aperti, runtime «%s» %s, "
		              "socket del bus %s",
		              g->utente, s.pid, s.ppid, s.uid, s.euid, s.suid, s.gid,
		              s.egid, s.sgid, s.descrittori, s.runtime,
		              s.runtime_c_e ? "c'e' ed e' sua" : "⛔ NON c'e' o non e' sua",
		              s.socket_bus_c_e ? "c'e'" : "⛔ non c'e'");
		return true;
	}
	case MSG_SESSIONE_FINITA:
		/*
		 * ⭐⭐ §7.6, il gemello: la sessione grafica e' finita e non gliel'ha
		 *     chiesto nessun client — l'utente ha scelto «Esci…» nel menu del
		 *     desktop.
		 *
		 * ⛔ E chi guarda deve saperlo ADESSO: tacendo, i client resterebbero
		 *    su uno schermo fermo fino ai trenta secondi del silenzio, e poi
		 *    leggerebbero «errore di rete» — che e' esattamente il rilievo B-7.
		 */
		registro_dice(REG_FIGLIO,
		              "⭐ §7.6: la sessione grafica di «%s» E' FINITA (nessun "
		              "client l'ha chiesta: l'utente e' uscito dal menu del "
		              "desktop).  Chi guarda viene congedato con 0x10",
		              g->utente);
		if (f->su_sessione_finita)
			f->su_sessione_finita(f->ctx_sessione_finita, g->utente, g->uid);
		else
			registro_dice(REG_FIGLIO,
			              "⚠ nessun gancio «sessione finita»: i client di «%s» "
			              "NON sono stati avvisati, e aspetteranno i trenta "
			              "secondi del silenzio",
			              g->utente);
		return true;
	case MSG_PALCO: {
		struct corpo_palco p;
		if (byte < sizeof p)
			return true;
		memcpy(&p, corpo, sizeof p);
		registro_dice(REG_FIGLIO,
		              "%s il palco di «%s»: bus %s, sessione %u, presa %u, "
		              "monitor «%s» (%u prima, %u dopo), %ux%u stride %u a %u "
		              "bit, %u flussi in consegna%s%s",
		              p.flussi > 0 ? "⭐" : "⛔", g->utente,
		              p.bus_aperto ? "APERTO" : "⛔ NO", p.stato_sessione,
		              p.presa, p.monitor, p.monitor_prima, p.monitor_dopo,
		              p.larghezza, p.altezza, p.stride, p.bit, p.flussi,
		              p.guasto[0] ? " — " : "", p.guasto);
		return true;
	}
	case MSG_CURSORE: {
		struct corpo_cursore c;
		if (byte < sizeof c)
			return true;
		memcpy(&c, corpo, sizeof c);
		if (byte < sizeof c + c.pezzo)
			return true;
		monta_cursore(f, g, &c, corpo + sizeof c);
		return true;
	}
	case MSG_FOTOGRAMMA: {
		struct corpo_fotogramma c;
		if (byte < sizeof c)
			return true;
		memcpy(&c, corpo, sizeof c);
		if (byte < sizeof c + c.pezzo)
			return true;
		monta_pezzo(f, g, &c, corpo + sizeof c);
		return true;
	}
	case MSG_BLOCCO: {
		struct corpo_blocco c;
		if (byte < sizeof c)
			return true;
		memcpy(&c, corpo, sizeof c);
		if (byte < sizeof c + c.byte)
			return true;
		/* ⛔⭐ E QUI IL CODEC SI CONTROLLA, invece di fidarsi.
		 *
		 *     Il figlio gira come l'utente e il padre e' privilegiato: un
		 *     numero che attraversa quel confine e' un ingresso, non un dato.
		 *     ⚠ Un `codec` che §6.3 non definisce finirebbe **dentro il
		 *     datagram** e il client lo scarterebbe — cioe' l'audio non
		 *     arriverebbe, senza che nessuna riga dica il perche'. */
		if (c.codec != 1 && c.codec != 2) {
			registro_dice(REG_FIGLIO,
			              "⛔ «%s» manda un blocco d'audio con codec %u, che "
			              "§6.3 non definisce (1 = Opus, 2 = PCM): BUTTATO",
			              g->utente, c.codec);
			return true;
		}
		if (f->su_blocco)
			f->su_blocco(f->ctx_blocco, g->utente, g->uid, c.codec,
			             c.istante_us, corpo + sizeof c, c.byte);
		return true;
	}
	case MSG_APPUNTI_DALLA_SESSIONE: {
		struct corpo_appunti c;
		if (byte < sizeof c)
			return true;
		memcpy(&c, corpo, sizeof c);
		if (byte < sizeof c + c.pezzo)
			return true;
		monta_appunti(f, g, &c, corpo + sizeof c);
		return true;
	}
	case MSG_APPUNTI_VUOLE: {
		struct corpo_appunti c;
		if (byte < sizeof c)
			return true;
		memcpy(&c, corpo, sizeof c);
		/* ⛔⛔ E SE NESSUNO ASCOLTA SI RISPONDE COMUNQUE, subito e a mani vuote.
		 *
		 *      Il caso e' reale e frequente: la sessione sopravvive al client
		 *      (invariante I4), quindi qualcuno puo' incollare **quando non c'e'
		 *      nessun client attaccato**.  ⚠ Tacere qui lascerebbe appesa a
		 *      tempo indeterminato l'applicazione che incolla, e il sintomo —
		 *      «il desktop si e' piantato» — non nomina ne' gli appunti ne' il
		 *      distacco.  ⇒ Il fondo di tempo non basta: si risponde ORA. */
		if (!f->su_appunti_richiesta) {
			registro_dice(REG_FIGLIO,
			              "«%s» sta incollando (richiesta %u) e nessuno serve "
			              "gli appunti: rispondo «non ce l'ho» subito, invece di "
			              "lasciare appeso chi incolla",
			              g->utente, c.serial);
			figli_appunti_risposta(f, g->utente, c.serial, NULL, 0);
			return true;
		}
		f->su_appunti_richiesta(f->ctx_appunti, g->utente, g->uid, c.serial);
		return true;
	}
	case MSG_TELA: {
		struct corpo_tela c;
		if (byte < sizeof c)
			return true;
		memcpy(&c, corpo, sizeof c);
		/* ⭐⭐ «ATTENDI» prima di tutto: non e' una risposta, e' la notizia che
		 *     una risposta sta arrivando.  ⛔ Trattarla come le altre farebbe
		 *     scattare il ramo «non ce l'ha fatta» — cioe' proprio la deduzione
		 *     che questo messaggio esiste per togliere. */
		if (c.attendi) {
			registro_dice(REG_FIGLIO,
			              "«%s»: il palco per la tela %ux%u non c'e' ANCORA — "
			              "il fondo di §7.1 si rimanda",
			              g->utente, c.voluta_l, c.voluta_a);
			if (f->su_tela_attendi)
				f->su_tela_attendi(f->ctx_tela_attendi, g->utente, g->uid,
				                   c.voluta_l, c.voluta_a);
			return true;
		}
		/* ⛔⭐ §7.1 — LA RISPOSTA ALLA TELA, e il padre non la INDOVINA piu' dai
		 *     fotogrammi: porta la misura CHIESTA (per riconoscere a quale
		 *     richiesta risponde) e quella AVUTA (`0x0` = non ce l'ha fatta).
		 * ⚠ La riga la scrive qui il padre perche' e' il lato che decide: il
		 *   figlio ha gia' scritto la sua, con il perche'. */
		registro_dice(REG_FIGLIO,
		              c.avuta_l && c.avuta_a
		                  ? "«%s»: il palco risponde alla tela — chiesta %ux%u, "
		                    "AVUTA %ux%u"
		                  : "«%s»: il palco NON ce l'ha fatta sulla tela %ux%u "
		                    "(%ux%u): il client lo sapra' adesso invece che dopo "
		                    "il fondo di §7.1",
		              g->utente, c.voluta_l, c.voluta_a, c.avuta_l, c.avuta_a);
		if (f->tela)
			f->tela(f->ctx, g->utente, g->uid, c.voluta_l, c.voluta_a, c.avuta_l,
			        c.avuta_a);
		return true;
	}
	default:
		registro_dice(REG_FIGLIO, "⚠ «%s» ha mandato un tipo che non conosco (%u)",
		              g->utente, t->tipo);
		return true;
	}
}

void figli_muovi(figli *f, struct pollfd *fds, size_t n, uint64_t ora_ms)
{
	if (!f)
		return;

	/* ⭐ L'INOLTRO DELLO SCATTO — il padre non fotografa niente: sa soltanto
	 *    dove stanno i figli, e li' i pixel ci sono.
	 *
	 * ⛔ E l'inoltro esiste per una ragione precisa, non per eleganza: il figlio
	 *    gira con l'uid dell'utente e chi diagnostica non e' quell'utente;
	 *    l'unica strada senza parola d'ordine e' `systemctl kill --kill-whom=main`,
	 *    che consegna il segnale AL SOLO PADRE.  ⚠ La strada `--kill-whom=all`
	 *    consegnerebbe anche a `gnome-shell`, per cui `SIGUSR1` vuol dire
	 *    «muori»: si spegnerebbe la scena che si voleva fotografare. */
	if (scatto_da_inoltrare) {
		int quale = scatto_da_inoltrare == 2 ? SIGUSR2 : SIGUSR1;

		scatto_da_inoltrare = 0;
		for (int i = 0; i < MAX_FIGLI; i++) {
			struct figlio *g = &f->v[i];

			if (!g->usato || g->uscendo || g->pid <= 0)
				continue;
			kill(g->pid, quale);
			registro_dice(REG_FIGLIO,
			              "⭐ scatto: %s inoltrato al figlio di «%s» (pid %ld)",
			              quale == SIGUSR2 ? "SIGUSR2" : "SIGUSR1", g->utente,
			              (long)g->pid);
		}
	}

	for (int i = 0; i < MAX_FIGLI; i++) {
		struct figlio *g = &f->v[i];
		bool leggibile = false;

		if (!g->usato)
			continue;

		for (size_t k = 0; k < n; k++)
			if (fds[k].fd == g->fd && (fds[k].revents & (POLLIN | POLLHUP)))
				leggibile = true;

		while (leggibile) {
			uint8_t busta[BUSTA_MAX];
			struct testa t;
			struct ucred chi;
			bool c_e = false;
			char perche[256];
			ssize_t letti = ricevi_con_credenziali(g->fd, busta, sizeof busta,
			                                       &chi, &c_e);

			if (letti == 0) {
				figlio_congeda(f, g, "ha chiuso il socket (o e' morto)");
				break;
			}
			if (letti == -2) {
				/* ⛔ Prima di `errno`, e non dopo: `-2` e' un fatto NOSTRO
				 *    (messaggio troncato dal nucleo) e `errno` in quel punto
				 *    porta ancora l'esito di qualcos'altro. */
				registro_dice(REG_FIGLIO,
				              "⛔ «%s» ha mandato un messaggio piu' lungo del "
				              "previsto: SCARTATO",
				              g->utente);
				continue;
			}
			if (letti < 0) {
				if (errno == EINTR)
					continue;
				if (errno == EAGAIN || errno == EWOULDBLOCK)
					break;
				figlio_congeda(f, g, strerror(errno));
				break;
			}
			if ((size_t)letti < sizeof t) {
				registro_dice(REG_FIGLIO,
				              "⛔ «%s»: messaggio di %zd byte, troppo corto per "
				              "una testa: SCARTATO",
				              g->utente, letti);
				continue;
			}
			memcpy(&t, busta, sizeof t);
			if (!magia_giusta(&t)) {
				registro_dice(REG_FIGLIO,
				              "⛔ «%s»: messaggio senza la firma di questo "
				              "protocollo: SCARTATO",
				              g->utente);
				continue;
			}
			/* ⛔⭐ E QUI, PRIMA DI GUARDARE UN SOLO BYTE DEL CORPO. */
			perche[0] = 0;
			if (!credenziali_combaciano(g, &t, c_e, &chi, perche,
			                            sizeof perche)) {
				registro_dice(REG_FIGLIO,
				              "⛔⛔ MESSAGGIO RIFIUTATO da «%s»: %s.  ⚠ Non e' "
				              "un messaggio da buttare e basta: e' il legame "
				              "fra la sessione RCP e l'identita' del figlio che "
				              "non si dimostra piu' — e un figlio che gira come "
				              "l'utente sbagliato e' I3 violata in modo "
				              "invisibile.  Il figlio si abbatte.",
				              g->utente, perche);
				if (g->pid > 0)
					kill(g->pid, SIGKILL);
				figlio_congeda(f, g, "le credenziali del nucleo non combaciavano");
				break;
			}
			if ((size_t)letti < sizeof t + t.byte) {
				registro_dice(REG_FIGLIO,
				              "⛔ «%s»: la testa annuncia %u byte di corpo e ne "
				              "sono arrivati %zd: SCARTATO",
				              g->utente, t.byte, letti - (ssize_t)sizeof t);
				continue;
			}
			if (!tratta(f, g, &t, busta + sizeof t, t.byte))
				break;
		}

		if (!g->usato)
			continue;

		/* ⛔⭐ SI RACCOLGONO I MORTI, E NON E' PULIZIA — `[M]` 12 agosto 2026,
		 *     dall'aiutante: in `/proc` uno zombie e un processo vivo hanno **la
		 *     stessa faccia**, e un banco che chiede «il figlio e' ancora vivo?»
		 *     riceverebbe «si'» da un cadavere.  ⛔ `WNOHANG`, perche' si e'
		 *     dentro il ciclo asincrono (`CODER.md` §4.4). */
		if (g->pid > 0) {
			int stato = 0;
			pid_t chiuso = waitpid(g->pid, &stato, WNOHANG);
			if (chiuso == g->pid) {
				char detto[160];
				/* ⛔ LA CAUSA, non «e' finito»: chi legge il registro sei ore
				 *    dopo deve poter distinguere un figlio che e' uscito da
				 *    solo da uno che qualcuno ha ammazzato, e da quale
				 *    segnale.  ⚠ I numeri d'uscita del figlio sono in
				 *    `figlio_vive()`: 42 = «non sono chi dovrei essere». */
				if (WIFEXITED(stato))
					snprintf(detto, sizeof detto, "e' uscito con %d — %s",
					         WEXITSTATUS(stato),
					         perche_uscito(WEXITSTATUS(stato)));
				else if (WIFSIGNALED(stato))
					snprintf(detto, sizeof detto, "l'ha ucciso il segnale %d",
					         WTERMSIG(stato));
				else
					snprintf(detto, sizeof detto, "e' finito (stato %d)", stato);
				g->pid = 0;
				figlio_libera(f, g, detto);
				continue;
			}
			/* ⛔ E se non muore, si insiste — ma solo dopo averglielo chiesto.
			 *    ⚠ Un figlio che ignora `SIGTERM` mentre tiene il monitor
			 *    virtuale di un utente e' un orfano in preparazione. */
			if (g->uscendo && ora_ms >= g->congedato_ms + 3000) {
				registro_dice(REG_FIGLIO,
				              "⛔ il figlio di «%s» (pid %ld) non e' morto in 3 s "
				              "dal congedo: SIGKILL",
				              g->utente, (long)g->pid);
				kill(g->pid, SIGKILL);
				g->congedato_ms = ora_ms;
			}
			/* ⚠ E finche' e' in uscita non gli si chiede piu' niente: la
			 *   casella resta sua fino alla conferma del nucleo. */
			if (g->uscendo)
				continue;
		}

		/* ⛔ La scadenza della PRESENTAZIONE, e solo quella.  ⚠ Dopo, nessuna:
		 *    I4 — il palco sopravvive al distacco, e un figlio zitto e' un
		 *    figlio a cui nessuno sta chiedendo niente. */
		if (!g->si_e_presentato && ora_ms >= g->nato_ms + SCADENZA_SONO_MS) {
			registro_dice(REG_FIGLIO,
			              "⛔ il figlio di «%s» (pid %ld) non ha detto chi e' in "
			              "%d ms: lo abbatto.  Un processo che gira come un "
			              "utente e non risponde non e' un palco",
			              g->utente, (long)g->pid, SCADENZA_SONO_MS);
			if (g->pid > 0)
				kill(g->pid, SIGKILL);
			/* ⚠ Non si aspetta qui: la raccolta e' del giro dopo. */
			figlio_congeda(f, g, "non si e' presentato in tempo");
		}
	}
}

/* ⛔ Ogni quanto il padre ridomanda «chi sei».  ⚠ Un minuto, e il numero non e'
 * una prudenza: e' il tempo massimo per cui un figlio che avesse cambiato
 * identita' — o un pid riciclato dopo una morte che non abbiamo raccolto —
 * resterebbe in tabella senza che nessuno lo abbia rimesso alla prova. */
#define RICONTROLLO_MS 60000

void figli_ricontrolla(figli *f, uint64_t ora_ms)
{
	if (!f)
		return;
	for (int i = 0; i < MAX_FIGLI; i++) {
		struct figlio *g = &f->v[i];
		struct testa t;

		if (!g->usato || g->fd < 0 || !g->si_e_presentato)
			continue;
		if (ora_ms < g->ultimo_ricontrollo_ms + RICONTROLLO_MS)
			continue;
		g->ultimo_ricontrollo_ms = ora_ms;

		memset(&t, 0, sizeof t);
		magia_scrivi(&t);
		t.tipo = MSG_CHI_SEI;
		t.versione = FIGLIO_VERSIONE;
		t.matricola = g->matricola;
		t.uid_dichiarato = (uint32_t)g->uid;
		t.byte = 0;
		/* ⚠ Se la domanda non parte non si conclude niente: l'assenza di una
		 *   risposta non e' una risposta, e il figlio resta dov'e'.  ⛔ Quel che
		 *   NON si fa e' dedurre da un `EAGAIN` che il figlio sia morto. */
		if (send(g->fd, &t, sizeof t, MSG_NOSIGNAL) != (ssize_t)sizeof t)
			registro_dettaglio(REG_FIGLIO,
			                   "la domanda «chi sei» a «%s» non e' partita (%s): "
			                   "si riprova fra un minuto",
			                   g->utente, strerror(errno));
	}
}

bool figli_chiedi_palco(figli *f, const char *utente)
{
	struct figlio *g;
	struct testa t;

	if (!f || !utente)
		return false;
	g = cerca(f, utente);
	if (!g || g->fd < 0 || g->uscendo)
		return false;
	memset(&t, 0, sizeof t);
	magia_scrivi(&t);
	t.tipo = MSG_RIMANDA_PALCO;
	t.versione = FIGLIO_VERSIONE;
	t.matricola = g->matricola;
	t.uid_dichiarato = (uint32_t)g->uid;
	if (send(g->fd, &t, sizeof t, MSG_NOSIGNAL) != (ssize_t)sizeof t) {
		registro_dice(REG_FIGLIO,
		              "⚠ la richiesta del palco a «%s» non e' partita (%s): "
		              "quella sessione non vedra' niente, e questa riga e' il "
		              "perche'",
		              utente, strerror(errno));
		return false;
	}
	registro_dice(REG_FIGLIO,
	              "ho chiesto a «%s» di rimandare il suo palco: il deposito di "
	              "processo e' di chi ha appena superato PAM",
	              utente);
	return true;
}

/* ⛔⭐ FASE 3 — «CATTURA, E QUESTA DEV'ESSERE UNA CHIAVE».
 *
 *     E' la meta' padre della cucitura che mancava.  ⚠ Chi decide non e'
 *     questo file — non sa niente di sessioni RCP — ed e' `webtransport.c`, che
 *     sa quando `SESSIONE` e' partita e quando §5.2 vuole una chiave.  `main.c`
 *     fa da ponte, perche' e' l'unico che conosce tutt'e due.
 *
 * ⛔ E LA RICHIESTA SI RIPETE ANCHE SE IL CODEC NON CAMBIA, quando la chiave e'
 *    chiesta: una chiave chiesta due volte costa un fotogramma grosso, una
 *    chiave chiesta zero volte costa **lo schermo fermo per sempre**.  Il fondo
 *    che evita la raffica sta dall'altra parte (`WT_CHIAVE_RICHIESTA_MS`), dove
 *    c'e' l'orologio della sessione. */
/* ⭐⭐ FASE 4 — la meta' PADRE della cucitura dell'input.
 *
 * ⚠ Quanto e' corta, e perche' e' giusto che lo sia: qui non si convalida
 *   niente e non si trasforma niente.  `rcp.c` ha gia' applicato `RCP.md` §7.3
 *   per intero — intervalli, surrogati, coordinate sulla tela, `id` crescente —
 *   e `input.c` applichera' le regole del compositore.  ⛔ Un controllo in piu'
 *   in mezzo non e' prudenza: e' una **terza** regola che il giorno in cui una
 *   delle due cambia resta indietro in silenzio.
 *
 * ⛔ E NON si tiene nessuno stato: nessun «ultimo id mandato», nessuna cache
 *    del premuto.  Chi tiene il conto e' `input.c`, che e' l'unico che sappia
 *    che cosa il compositore ha davvero preso — e due contatori sulla stessa
 *    grandezza sono due verita' che divergono al primo messaggio perduto. */
/* ⭐⭐ §5-bis.7 — «METTI QUESTA DISPOSIZIONE NELLA SESSIONE».
 *
 * ⛔ Il difetto che questa funzione chiude, misurato dal banco `06-b34` il
 *    16 agosto 2026: la disposizione dichiarata in `ATTACCA` veniva
 *    convalidata e SCRITTA NEL REGISTRO, e li' finiva.  Riattaccandosi a
 *    una sessione `it` dichiarando `us` arrivavano `è` e `ò`, che su `us`
 *    non esistono su nessun tasto.
 *
 * ⭐ E il danno vero non e' l'accento: le scorciatoie viaggiano come
 *    POSIZIONI (`SPECIFICHE.md` §7.3), e su una tastiera tedesca la `Z`
 *    sta dove da noi sta la `Y` — senza rinegoziare, `Ctrl+Z` arriva come
 *    `Ctrl+Y`, cioe' «rifai» invece di «annulla». */
bool figli_disposizione(figli *f, const char *utente, const char *nome)
{
	struct figlio *g;
	struct testa t;
	struct corpo_disposizione c;
	uint8_t busta[sizeof t + sizeof c];

	if (!f || !utente || !nome || !*nome)
		return false;
	g = cerca(f, utente);
	if (!g || g->fd < 0 || g->uscendo)
		return false;

	memset(&t, 0, sizeof t);
	magia_scrivi(&t);
	t.tipo = MSG_DISPOSIZIONE;
	t.versione = FIGLIO_VERSIONE;
	t.matricola = g->matricola;
	t.uid_dichiarato = (uint32_t)g->uid;
	t.byte = (uint32_t)sizeof c;
	memset(&c, 0, sizeof c);
	snprintf(c.nome, sizeof c.nome, "%s", nome);
	memcpy(busta, &t, sizeof t);
	memcpy(busta + sizeof t, &c, sizeof c);
	if (send(g->fd, busta, sizeof busta, MSG_NOSIGNAL) != (ssize_t)sizeof busta) {
		/* ⛔ `registro_dice` e non `dettaglio`: succede una volta per
		 *    attacco, e se non parte l'utente resta con le scorciatoie
		 *    sfasate — che e' precisamente il guasto che nessuno collega. */
		registro_dice(REG_FIGLIO,
		              "⚠ la disposizione «%s» per «%s» NON e' partita: la "
		              "sessione tiene la sua, e le scorciatoie resteranno "
		              "sfasate",
		              nome, utente);
		return false;
	}
	return true;
}

bool figli_input(figli *f, const char *utente, uint32_t id, uint8_t azione,
                 uint16_t codice, int premuto, int32_t a, int32_t b)
{
	struct figlio *g;
	struct testa t;
	struct corpo_input c;
	uint8_t busta[sizeof t + sizeof c];

	if (!f || !utente)
		return false;
	g = cerca(f, utente);
	if (!g || g->fd < 0 || g->uscendo)
		return false;

	memset(&t, 0, sizeof t);
	magia_scrivi(&t);
	t.tipo = MSG_INPUT;
	t.versione = FIGLIO_VERSIONE;
	t.matricola = g->matricola;
	t.uid_dichiarato = (uint32_t)g->uid;
	t.byte = (uint32_t)sizeof c;
	memset(&c, 0, sizeof c);
	c.id = id;
	c.azione = azione;
	c.premuto = premuto ? 1u : 0u;
	c.codice = codice;
	c.a = a;
	c.b = b;
	memcpy(busta, &t, sizeof t);
	memcpy(busta + sizeof t, &c, sizeof c);
	if (send(g->fd, busta, sizeof busta, MSG_NOSIGNAL) != (ssize_t)sizeof busta) {
		/* ⛔ `registro_dettaglio` e non `registro_dice`: un utente che muove il
		 *    mouse produce decine di messaggi al secondo, e una riga per
		 *    ciascuno seppellirebbe il registro proprio nel momento in cui
		 *    serve leggerlo.  ⚠ Ma NON si tace: «l'input non e' arrivato al
		 *    desktop» e' un fatto, e sparisce solo dalla parlantina. */
		registro_dettaglio(REG_FIGLIO,
		                   "⚠ l'input %u (azione %u) per «%s» non e' partito "
		                   "(%s): quel gesto NON e' arrivato al desktop",
		                   (unsigned)id, (unsigned)azione, utente,
		                   strerror(errno));
		return false;
	}
	return true;
}

/* ⭐⭐ LA CATENA CHE MANCAVA — `figli_ritela()`, e da qui in poi il nome che
 *     `DECISIONI.md` §5.0-sexies e il mandato della fase 4 nominano ESISTE.
 *
 * ⛔ E' UNA RIGA SOLA E DELEGA, e le due cose sono volute: il messaggio sul filo
 *    fra padre e figlio resta **uno** (`MSG_INPUT`, azione `RITELA`), quindi nel
 *    figlio c'e' un ramo solo da leggere.  ⚠ Una seconda busta avrebbe voluto un
 *    secondo `struct corpo_*`, un secondo ramo e un secondo modo di sbagliare —
 *    per portare due numeri che quello che c'e' porta gia'.
 *
 * ⛔ MA IL NOME NON E' COSMETICO, e non e' `figli_input()` con un'azione strana:
 *    l'input e' un GESTO gia' convalidato da §7.3 che si inietta e si dimentica;
 *    questa e' una richiesta di **riconfigurazione del palco** il cui esito non
 *    torna da qui — torna con un fotogramma, minuti dopo o mai.  Due mestieri
 *    diversi con due nomi diversi, e chi legge `main.c` vede la catena intera.
 *
 * `false` = non c'e' nessun figlio per quell'utente, o la domanda non e' partita
 * — ⛔ e allora la tela NON cambiera', il che si dichiara invece di aspettare un
 * fotogramma che non arrivera' (`CODER.md` §4.2). */
bool figli_ritela(figli *f, const char *utente, uint32_t larghezza,
                  uint32_t altezza)
{
	/* ⛔ `id = 0` e non l'ultimo id dell'input: §6.2 riserva lo zero a «nessun
	 *    input», e questa non e' un'azione dell'utente su cui l'anello del
	 *    ritardo debba misurare niente. */
	return figli_input(f, utente, 0, FIGLI_INPUT_RITELA, 0, 0,
	                   (int32_t)larghezza, (int32_t)altezza);
}

/* ⭐ §7.6 — e delega a `figli_input()` come `figli_ritela()`, per la stessa
 * ragione: una busta sola sul filo fra padre e figlio.  ⛔ Ma col nome suo,
 * perche' i mestieri sono due e chi legge `main.c` deve vedere la catena. */
void figli_gancio_tela_attendi(figli *f, FiglioTelaAttendi fn, void *ctx)
{
	if (!f)
		return;
	f->su_tela_attendi = fn;
	f->ctx_tela_attendi = ctx;
}

void figli_gancio_blocco(figli *f, FiglioBlocco fn, void *ctx)
{
	if (!f)
		return;
	f->su_blocco = fn;
	f->ctx_blocco = ctx;
}

void figli_gancio_appunti(figli *f, FiglioAppuntiTesto testo,
                          FiglioAppuntiRichiesta richiesta, void *ctx)
{
	if (!f)
		return;
	/* ⛔ Insieme o per niente (`figlio.h`): chi agganciasse il solo `testo`
	 *    saprebbe portare al client quel che la sessione copia e non saprebbe
	 *    servire chi incolla — e quel «non saprebbe» si vede come un desktop
	 *    piantato.  ⇒ Si dichiara e non si aggancia niente, invece di
	 *    agganciare meta' canale. */
	if ((testo != NULL) != (richiesta != NULL)) {
		registro_dice(REG_FIGLIO,
		              "⛔ i due ganci degli appunti si agganciano insieme o per "
		              "niente, e ne e' arrivato uno solo (%s): NON ne aggancio "
		              "nessuno",
		              testo ? "manca chi serve chi incolla"
		                    : "manca chi porta il testo al client");
		return;
	}
	f->su_appunti_testo = testo;
	f->su_appunti_richiesta = richiesta;
	f->ctx_appunti = ctx;
}

bool figli_appunti_offri(figli *f, const char *utente)
{
	struct figlio *g;
	struct testa t;
	uint8_t busta[sizeof t];

	if (!f || !utente)
		return false;
	g = cerca(f, utente);
	if (!g || g->fd < 0 || g->uscendo)
		return false;

	memset(&t, 0, sizeof t);
	magia_scrivi(&t);
	t.tipo = MSG_APPUNTI_OFFERTA;
	t.versione = FIGLIO_VERSIONE;
	t.matricola = g->matricola;
	t.uid_dichiarato = (uint32_t)g->uid;
	t.byte = 0;
	memcpy(busta, &t, sizeof t);
	if (send(g->fd, busta, sizeof busta, MSG_NOSIGNAL) != (ssize_t)sizeof busta) {
		registro_dice(REG_FIGLIO,
		              "⚠ l'offerta degli appunti a «%s» non e' partita (%s): "
		              "dentro quella sessione non si potra' incollare quel che "
		              "il client ha copiato, e questa riga e' il perche'",
		              utente, strerror(errno));
		return false;
	}
	registro_dettaglio(REG_FIGLIO,
	                   "«%s»: offerto alla sessione il testo del client (§7.4)",
	                   utente);
	return true;
}

bool figli_appunti_risposta(figli *f, const char *utente, uint32_t serial,
                            const char *testo, size_t byte)
{
	struct figlio *g;
	size_t off = 0;

	if (!f || !utente)
		return false;
	g = cerca(f, utente);
	if (!g || g->fd < 0 || g->uscendo)
		return false;

	/* ⛔ Il tetto si fa rispettare anche in QUESTO verso, e la ragione e'
	 *    diversa da quella di §5.4: qui il testo viene dal **client**, cioe' da
	 *    fuori.  ⚠ `rcp.c` lo ha gia' rifiutato sul filo; questa e' la seconda
	 *    porta, quella che protegge il figlio da un padre con un difetto. */
	if (testo && byte > APPUNTI_TETTO) {
		registro_dice(REG_FIGLIO,
		              "⛔ «%s»: %zu byte di appunti dal client, oltre il tetto "
		              "di §5.4 (%u): rispondo «non ce l'ho» invece di troncare",
		              utente, byte, APPUNTI_TETTO);
		testo = NULL;
		byte = 0;
	}

	/* ⛔ Il caso «niente» e quello «testo vuoto» partono per strade diverse, e
	 *    la differenza arriva fino a Mutter: `SelectionWriteDone(false)` contro
	 *    un descrittore aperto e chiuso senza byte.  ⚠ Chi incolla vede «non
	 *    c'era niente da incollare» nel primo caso e una riga vuota nel
	 *    secondo, che sono due cose diverse. */
	do {
		struct testa t;
		struct corpo_appunti c;
		uint8_t busta[sizeof t + sizeof c + PEZZO_MAX];
		size_t q = 0;

		if (testo) {
			q = byte - off;
			if (q > PEZZO_MAX)
				q = PEZZO_MAX;
		}

		memset(&t, 0, sizeof t);
		magia_scrivi(&t);
		t.tipo = MSG_APPUNTI_DAL_CLIENT;
		t.versione = FIGLIO_VERSIONE;
		t.matricola = g->matricola;
		t.uid_dichiarato = (uint32_t)g->uid;
		t.byte = (uint32_t)(sizeof c + q);
		memset(&c, 0, sizeof c);
		c.serial = serial;
		c.totale = testo ? (uint32_t)byte : 0;
		c.offset = (uint32_t)off;
		c.pezzo = (uint32_t)q;
		c.niente = testo ? 0 : 1;
		memcpy(busta, &t, sizeof t);
		memcpy(busta + sizeof t, &c, sizeof c);
		if (q)
			memcpy(busta + sizeof t + sizeof c, testo + off, q);
		if (send(g->fd, busta, sizeof t + sizeof c + q, MSG_NOSIGNAL)
		    != (ssize_t)(sizeof t + sizeof c + q)) {
			/* ⛔⛔ E QUESTO E' IL CASO CHE LASCIA APPESO CHI INCOLLA, quindi la
			 *      riga e' in chiaro e dice il sintomo: senza, si cercherebbe
			 *      il difetto nel desktop invece che in un socket pieno. */
			registro_dice(REG_FIGLIO,
			              "⛔ «%s»: la risposta agli appunti (richiesta %u, %zu "
			              "di %zu byte) non e' partita (%s).  ⚠ L'applicazione "
			              "che sta incollando resta appesa finche' il figlio non "
			              "va in fondo al suo tempo",
			              utente, serial, off, byte, strerror(errno));
			return false;
		}
		off += q;
	} while (testo && off < byte);

	registro_dettaglio(REG_FIGLIO,
	                   "«%s»: risposta agli appunti (richiesta %u) — %s",
	                   utente, serial,
	                   testo ? "consegnata" : "«non ce l'ho»");
	return true;
}

void figli_gancio_sessione_finita(figli *f, FiglioSessioneFinita fn, void *ctx)
{
	if (!f)
		return;
	f->su_sessione_finita = fn;
	f->ctx_sessione_finita = ctx;
}

bool figli_termina_sessione(figli *f, const char *utente, int perche)
{
	/* ⛔ Il `perche'` viaggia nel campo `a`, che era libero: la ragione sta su
	 *    `FIGLI_USCITA_*` in `figlio.h`. */
	return figli_input(f, utente, 0, FIGLI_INPUT_TERMINA, 0, 0, perche, 0);
}

bool figli_audio(figli *f, const char *utente, uint8_t codec)
{
	struct figlio *g;
	struct testa t;
	struct corpo_audio c;
	uint8_t busta[sizeof t + sizeof c];

	if (!f || !utente)
		return false;
	g = cerca(f, utente);
	if (!g || g->fd < 0 || g->uscendo)
		return false;
	/* ⛔⭐ E CON IL CODEC INVARIATO IL MESSAGGIO PARTE LO STESSO, se il codec
	 *     non e' zero — ed e' l'INVARIANTE I5, non una svista.
	 *
	 *     «Il volume appartiene alla sessione: chi si collega lo trova al
	 *     massimo.»  ⚠ Con la scorciatoia «niente di nuovo da dire» il secondo
	 *     che si collega non manderebbe niente, e troverebbe il volume dove
	 *     l'aveva lasciato il primo — cioe' uno stato che **il client non puo'
	 *     ne' vedere ne' spiegare**, che e' la ragione per cui I5 esiste.
	 *
	 * ⚠ Il prezzo e' un messaggio da otto byte per attacco: si paga una volta
	 *   per collegamento, non per blocco. */
	if (codec == g->audio_codec_chiesto && codec == 0)
		return true; /* spento, e resta spento: non c'e' niente da dire */

	memset(&t, 0, sizeof t);
	magia_scrivi(&t);
	t.tipo = MSG_AUDIO;
	t.versione = FIGLIO_VERSIONE;
	t.matricola = g->matricola;
	t.uid_dichiarato = (uint32_t)g->uid;
	t.byte = (uint32_t)sizeof c;
	memset(&c, 0, sizeof c);
	c.codec = codec;
	memcpy(busta, &t, sizeof t);
	memcpy(busta + sizeof t, &c, sizeof c);
	if (send(g->fd, busta, sizeof busta, MSG_NOSIGNAL) != (ssize_t)sizeof busta) {
		registro_dice(REG_FIGLIO,
		              "⚠ la richiesta d'audio a «%s» (codec %u) non e' partita "
		              "(%s): quella sessione non sentira' niente, e questa riga "
		              "e' il perche'",
		              utente, codec, strerror(errno));
		return false;
	}
	registro_dice(REG_FIGLIO,
	              codec ? "⭐ FASE 7: alla sessione di «%s» ho chiesto di "
	                      "catturare l'audio, codec %u (%s)"
	                    : "alla sessione di «%s» ho chiesto di SMETTERE di "
	                      "catturare l'audio (codec %u): non ascolta piu' "
	                      "nessuno, e il sink resta in piedi (I4)",
	              utente, codec,
	              codec == 1 ? "Opus" : codec == 2 ? "PCM" : "-");
	g->audio_codec_chiesto = codec;
	return true;
}

bool figli_video(figli *f, const char *utente, uint8_t codec,
                 uint8_t profondita, uint8_t livello_x10, bool chiave)
{
	struct figlio *g;
	struct testa t;
	struct corpo_video c;
	uint8_t busta[sizeof t + sizeof c];

	if (!f || !utente)
		return false;
	g = cerca(f, utente);
	if (!g || g->fd < 0 || g->uscendo)
		return false;
	/* ⛔ E la profondita' entra nel confronto: un secondo client che negozia
	 *    8 bit dove il primo aveva 10 e' «qualcosa di nuovo da dire», anche se
	 *    il codec e' lo stesso.  ⚠ Senza questa riga il messaggio non
	 *    partirebbe, e il flusso resterebbe alla profondita' del PRIMO — cioe'
	 *    esattamente la bugia che questo campo esiste per togliere. */
	/* ⛔ E il LIVELLO entra nel confronto per la stessa ragione della
	 *    profondita' (§4.3, 23 agosto 2026): un secondo client che dichiara 4.1
	 *    dove il primo aveva 5.1 non cambia ne' codec ne' profondita', e senza
	 *    questa riga il messaggio non partirebbe — il flusso resterebbe al
	 *    tetto del PRIMO e il secondo vedrebbe uno schermo nero muto. */
	if (codec == g->video_codec_chiesto && profondita == g->video_prof_chiesta
	    && livello_x10 == g->video_liv_chiesto && !chiave)
		return true; /* niente di nuovo da dire */

	memset(&t, 0, sizeof t);
	magia_scrivi(&t);
	t.tipo = MSG_VIDEO;
	t.versione = FIGLIO_VERSIONE;
	t.matricola = g->matricola;
	t.uid_dichiarato = (uint32_t)g->uid;
	t.byte = (uint32_t)sizeof c;
	memset(&c, 0, sizeof c);
	c.codec = codec;
	c.chiave = chiave ? 1u : 0u;
	c.profondita = profondita;
	c.livello_x10 = livello_x10;
	memcpy(busta, &t, sizeof t);
	memcpy(busta + sizeof t, &c, sizeof c);
	if (send(g->fd, busta, sizeof busta, MSG_NOSIGNAL) != (ssize_t)sizeof busta) {
		registro_dice(REG_FIGLIO,
		              "⚠ la richiesta di video a «%s» (codec %u, chiave %s) non "
		              "e' partita (%s): quella sessione non vedra' niente, e "
		              "questa riga e' il perche'",
		              utente, codec, chiave ? "SI" : "no", strerror(errno));
		return false;
	}
	if (codec != g->video_codec_chiesto)
		registro_dice(REG_FIGLIO,
		              codec ? "⭐ FASE 3: al palco di «%s» ho chiesto di "
		                      "catturare di continuo, codec %u%s"
		                    : "al palco di «%s» ho chiesto di SMETTERE di "
		                      "catturare (codec %u): non lo guarda piu' "
		                      "nessuno%s",
		              utente, codec, chiave ? " — e la prima dev'essere una "
		                                      "CHIAVE (§5.2)" : "");
	g->video_codec_chiesto = codec;
	g->video_prof_chiesta = profondita;
	g->video_liv_chiesto = livello_x10;
	return true;
}

void figli_spegni(figli *f)
{
	if (!f)
		return;
	for (int i = 0; i < MAX_FIGLI; i++) {
		struct figlio *g = &f->v[i];
		if (!g->usato)
			continue;
		/* ⛔ Prima si chiude il socket — che e' il segnale piu' onesto, «non
		 *    c'e' piu' nessuno a cui parlare» — e poi si insiste col segnale. */
		if (g->fd >= 0) {
			close(g->fd);
			g->fd = -1;
		}
		if (g->pid > 0) {
			kill(g->pid, SIGTERM);
			/* ⚠ ASPETTA, e sta fuori dal ciclo `poll`: `CODER.md` §4.4 vieta
			 *   l'attesa DENTRO il ciclo, e questa e' la riga dopo l'ultimo
			 *   giro.  ⛔ Il palco va smontato prima che il processo esca, o il
			 *   monitor virtuale resterebbe attaccato alla sessione
			 *   dell'utente. */
			waitpid(g->pid, NULL, 0);
		}
		registro_dice(REG_FIGLIO, "il figlio di «%s» (pid %ld) e' spento",
		              g->utente, (long)g->pid);
		free(g->monta);
		free(g->cur_monta);
		memset(g, 0, sizeof *g);
		g->fd = -1;
	}
	free(f);
}

/* ========================================================================== */
/* ⭐ IL FIGLIO — da qui in giu' si gira come l'utente, e non si torna indietro */

/* ⭐⭐ FASE 4 — il canale di input vive QUI, e non poteva vivere altrove:
 *     `libei` parla con la sessione grafica, e la sessione grafica e' di questo
 *     processo.
 *
 * ⛔ `input_iniettato` e' l'`id` dell'ultimo input che il COMPOSITORE HA PRESO
 *    — non l'ultimo ricevuto, non l'ultimo tentato.  §6.2 promette che
 *    «l'effetto di quell'input e' gia' nella scena», e di un input rifiutato
 *    non c'e' nessun effetto da vedere.  ⇒ Avanza solo quando `input.c` ha
 *    risposto 0. */
static Input *palco_input;
/* ⭐ §5-bis.7: la disposizione chiesta quando il palco non c'era ancora.
 *    ⛔ Vuota = niente in attesa.  Si applica appena `input_apri()` riesce. */
static char disposizione_in_attesa[65];
static uint32_t input_iniettato;
static uint32_t input_rifiutati;
static uint32_t input_non_producibili;

/* ⭐⭐ FASE 7 — GLI APPUNTI DELLA SESSIONE, e stanno di qua per la stessa
 *     ragione di `palco_input`: la clipboard e' del compositore, e col
 *     compositore parla questo processo (`src/appunti.h`). */
static Appunti *palco_appunti;

/* ⛔⛔⭐ L'OFFERTA CHE E' ARRIVATA TROPPO PRESTO, E CHE SI RIFA' — 21 agosto
 *      2026, difetto misurato col banco `07-b56`.
 *
 * ⚠ Il client annuncia i suoi appunti appena la `SESSIONE` e' nata; gli appunti
 *   della sessione grafica si aprono qualche decina di millisecondi DOPO,
 *   quando Mutter ha risposto.  `[M]` Registro delle 06:00:15 — l'annuncio alle
 *   .868, l'apertura alle .982: 114 ms.
 *   ⛔ In mezzo l'offerta cadeva («gli appunti della sessione non ci sono») e
 *     nessuno la rifaceva mai: il compositore non diventava proprietario della
 *     selezione, e dentro il desktop la voce «Incolla» del menu non aveva
 *     niente da dare.  ⇒ Da fuori: «col mouse non funziona».
 *
 * ⭐ Si ricorda che e' caduta, e si rifa' appena il canale c'e'.  E' la stessa
 *    forma della domanda arretrata di `rcp.c` (`appunti_chiedi_l_arretrato`):
 *    invece di ritardare qualcosa per tutti, si tiene UN bit e si ricuce. */
static bool appunti_offerta_arretrata;

/*
 * ⛔⛔ IL FONDO DI TEMPO DI CHI INCOLLA, E STA NEL FIGLIO — non nel padre.
 *
 * Un `SelectionTransfer` senza risposta lascia appesa **a tempo
 * indeterminato** l'applicazione che sta incollando, e il sintomo e' «il
 * desktop si e' piantato».  ⇒ Qualcuno deve rispondere sempre.
 *
 * ⭐ E quel qualcuno e' QUESTO processo, non il padre, per una ragione che non
 *    e' di comodita': il padre puo' non avere nessun client attaccato (la
 *    sessione sopravvive al client — invariante I4), il client puo' sparire a
 *    meta' trasferimento, e il padre stesso puo' morire.  ⛔ Il debito verso
 *    Mutter invece resta di chi ha la sessione, e la sessione e' qui.
 *
 * ⚠ Il padre risponde SUBITO quando sa gia' di non poter servire (nessun gancio
 *   agganciato): questo fondo copre l'altro caso — il client c'e' e non
 *   risponde.
 */
#define APPUNTI_ATTESA_MS 4000
#define APPUNTI_IN_VOLO 8
static struct {
	bool usato;
	uint32_t serial;
	uint64_t scade_ms;
} appunti_in_volo[APPUNTI_IN_VOLO];

static int fd_figlio = 3; /* il posto convenuto, messo li' da `diventa_ed_esegui` */
static uint64_t mia_matricola;
static uid_t mio_uid;

/* Quanti descrittori ho aperto davvero.  ⛔ Si CONTANO, non si dichiarano: e'
 * la meta' del banco che vive nel prodotto — «il figlio non si e' portato
 * dietro la porta» dev'essere un numero, non una promessa. */
static uint32_t quanti_descrittori(void)
{
	uint32_t n = 0;
	for (int i = 0; i < 4096; i++)
		if (fcntl(i, F_GETFD) >= 0)
			n++;
	return n;
}

static bool manda(uint16_t tipo, const void *corpo, size_t byte,
                  const void *coda, size_t byte_coda)
{
	uint8_t busta[BUSTA_MAX];
	struct testa t;
	size_t n = 0;

	if (sizeof t + byte + byte_coda > sizeof busta)
		return false;
	memset(&t, 0, sizeof t);
	magia_scrivi(&t);
	t.tipo = tipo;
	t.versione = FIGLIO_VERSIONE;
	t.matricola = mia_matricola;
	/* ⛔ L'uid si CHIEDE AL NUCLEO a ogni messaggio, e non si legge da una
	 *    variabile scritta all'avvio: la variabile direbbe quel che credevamo
	 *    di essere, e il padre confrontera' questo campo con quel che il nucleo
	 *    ha timbrato.  ⚠ Se i due non combaciassero, il padre abbatte — ed e'
	 *    giusto: un figlio che non sa piu' chi e' non deve consegnare pixel. */
	t.uid_dichiarato = (uint32_t)geteuid();
	t.byte = (uint32_t)(byte + byte_coda);
	memcpy(busta, &t, sizeof t);
	n = sizeof t;
	if (byte) {
		memcpy(busta + n, corpo, byte);
		n += byte;
	}
	if (byte_coda) {
		memcpy(busta + n, coda, byte_coda);
		n += byte_coda;
	}
	return send(fd_figlio, busta, n, MSG_NOSIGNAL) == (ssize_t)n;
}

/* ⛔⭐ LA TELA CHE IL CLIENT HA CHIESTO, tenuta a parte da quella che il palco
 *     DA'.  Sono due numeri diversi e servono a due cose diverse:
 *
 *       `tela_voluta_*`  quel che il client vuole ⇒ e' quel che si richiede al
 *                        RIMONTAGGIO del palco, o le bande tornerebbero dopo
 *                        ogni caduta della sessione grafica;
 *       `tela_l`/`tela_a` quel che il palco consegna ⇒ e' quel che finisce nei
 *                        28 byte di §6.2, e non si inventa.
 *
 * ⚠ Nascono uguali (la misura della riga di comando) e divergono al primo
 *   `ADATTA_TELA` che il compositore non serve alla lettera (§4.5). */
static uint32_t tela_voluta_l, tela_voluta_a;

/* La risposta di §7.1 al padre.  ⛔ `avuta_l == 0` = «non ce l'ho fatta», ed e'
 * un fatto diverso da «ci sto provando»: senza questa riga il padre aspetterebbe
 * il fondo dei tre secondi per sapere una cosa che qui si sa subito. */
/* ⭐ «ATTENDI»: il palco non c'e' ANCORA, e la domanda avra' una risposta vera.
 * ⛔ Non e' `0x0` — quello e' «non ce l'ho fatta» — ed e' il messaggio che
 *    toglie al padre una deduzione (`LEZIONI.md` §7.5). */
static void attendi_tela(uint32_t voluta_l, uint32_t voluta_a)
{
	struct corpo_tela c;
	memset(&c, 0, sizeof c);
	c.voluta_l = voluta_l;
	c.voluta_a = voluta_a;
	c.attendi = 1;
	if (!manda(MSG_TELA, &c, sizeof c, NULL, 0))
		registro_dice(REG_FIGLIO,
		              "⛔ l'«attendi» sulla tela (%ux%u) non e' partito (%s): il "
		              "padre fara' scadere il fondo di §7.1 su una domanda che "
		              "stava per avere una risposta",
		              voluta_l, voluta_a, strerror(errno));
}

static void rispondi_tela(uint32_t voluta_l, uint32_t voluta_a, uint32_t avuta_l,
                          uint32_t avuta_a)
{
	struct corpo_tela c;
	memset(&c, 0, sizeof c);
	c.voluta_l = voluta_l;
	c.voluta_a = voluta_a;
	c.avuta_l = avuta_l;
	c.avuta_a = avuta_a;
	if (!manda(MSG_TELA, &c, sizeof c, NULL, 0))
		registro_dice(REG_FIGLIO,
		              "⛔ la risposta sulla tela (%ux%u → %ux%u) non e' partita "
		              "(%s): il padre aspettera' il fondo di §7.1 invece di "
		              "saperlo adesso",
		              voluta_l, voluta_a, avuta_l, avuta_a, strerror(errno));
}

static void manda_fotogramma(uint8_t codec, bool chiave, uint32_t l, uint32_t a,
                             uint64_t istante_us, const uint8_t *dati, size_t byte,
                             uint32_t input)
{
	size_t off = 0;
	while (off < byte) {
		struct corpo_fotogramma c;
		size_t q = byte - off;
		if (q > PEZZO_MAX)
			q = PEZZO_MAX;
		memset(&c, 0, sizeof c);
		c.codec = codec;
		c.chiave = chiave ? 1u : 0u;
		c.larghezza = l;
		c.altezza = a;
		c.istante_us = istante_us;
		c.totale = (uint32_t)byte;
		c.offset = (uint32_t)off;
		c.pezzo = (uint32_t)q;
		/* ⭐ §6.2 — e il valore arriva DALL'ISTANTE DELLA CATTURA, non da qui:
		 *    fra la cattura e questa riga passa tutta la codifica, e leggerlo
		 *    adesso direbbe un numero piu' alto del vero. */
		c.input = input;
		if (!manda(MSG_FOTOGRAMMA, &c, sizeof c, dati + off, q)) {
			registro_dice(REG_FIGLIO,
			              "⛔ il pezzo a %zu di %zu non e' partito (%s): il "
			              "padre non ricevera' il fotogramma, e NON ne "
			              "ricevera' uno a meta'",
			              off, byte, strerror(errno));
			return;
		}
		off += q;
	}
}

/* ⭐⭐ LA FORMA DEL CURSORE, dal metadato di PipeWire al filo — e in mezzo c'e'
 *     un confine di processo.
 *
 * ⛔ Questa e' la `CursoreArrivata` di `cursore.h`, e la chiama `cattura.c`
 *    **dal thread di PipeWire**.  ⚠ Percio' NON tocca niente dello stato del
 *    ciclo e non alloca: prende i byte, li spezza e li manda.  Un `malloc` qui
 *    dentro sarebbe un `malloc` sul thread di tempo reale della cattura.
 *
 * ⚠ E l'immagine vive SOLO dentro la chiamata (lo dice `cursore.h`): si copia
 *   nella busta e non se ne tiene nessun puntatore.
 *
 * Restituisce 0: da qui in poi la forma e' del padre, e il figlio non ha modo di
 * sapere se il client l'ha ricevuta — ⛔ dirlo diversamente sarebbe fingere una
 * conferma che non esiste. */
static int cursore_al_padre(void *chi, const CursoreForma *f)
{
	size_t byte, off = 0;

	(void)chi;
	if (!f)
		return -1;
	byte = (size_t)f->larghezza * f->altezza * 4u;
	/* ⭐ Il nascosto e' `0x0` con l'immagine a NULL, e va spedito **come
	 *    messaggio**: e' l'unico modo che il client ha di sapere che il
	 *    puntatore e' sparito, invece di continuare a disegnare l'ultima forma
	 *    per sempre (§5.5). */
	if (byte == 0) {
		struct corpo_cursore c;
		memset(&c, 0, sizeof c);
		c.larghezza = f->larghezza;
		c.altezza = f->altezza;
		c.attivo_x = f->attivo_x;
		c.attivo_y = f->attivo_y;
		return manda(MSG_CURSORE, &c, sizeof c, NULL, 0) ? 0 : -1;
	}
	if (!f->immagine)
		return -1;
	while (off < byte) {
		struct corpo_cursore c;
		size_t q = byte - off;
		if (q > PEZZO_MAX)
			q = PEZZO_MAX;
		memset(&c, 0, sizeof c);
		c.larghezza = f->larghezza;
		c.altezza = f->altezza;
		c.attivo_x = f->attivo_x;
		c.attivo_y = f->attivo_y;
		c.totale = (uint32_t)byte;
		c.offset = (uint32_t)off;
		c.pezzo = (uint32_t)q;
		if (!manda(MSG_CURSORE, &c, sizeof c, f->immagine + off, q)) {
			/* ⛔ In parlantina, e per una ragione precisa: il cursore cambia
			 *    forma decine di volte mentre il puntatore attraversa una
			 *    finestra, e una riga per ciascuno coprirebbe il registro.
			 *    ⚠ Ma NON si tace: una forma perduta a meta' lascia il client
			 *    con il cursore di prima, che e' un difetto visibile. */
			registro_dettaglio(REG_FIGLIO,
			                   "il pezzo del cursore a %zu di %zu non e' "
			                   "partito (%s): il client tiene la forma vecchia",
			                   off, byte, strerror(errno));
			return -1;
		}
		off += q;
	}
	return 0;
}

/* ------------------------------------------------------------------------- */
/* ⭐⭐ FASE 7 — GLI APPUNTI: le due richiamate che attraversano il confine.    */
/*                                                                            */
/* ⛔⛔ E GIRANO SUL THREAD DEGLI APPUNTI, non su questo ciclo — `appunti.h`,  */
/*      «il contratto del thread».  ⇒ Qui dentro si puo' SCRIVERE SUL SOCKET  */
/*      (un `send` su SEQPACKET e' atomico per messaggio) e NIENT'ALTRO:      */
/*      ⛔ `libei` non e' rientrante (`input.h`), e la tabella dei            */
/*      trasferimenti in volo la tocca solo questo thread — vedi sotto.       */

/* ⛔ La tabella la scrivono DUE thread: quello degli appunti, che ci mette i
 *    serial, e il ciclo del figlio, che li scade.  ⚠ Un lucchetto per una
 *    tabella di otto voci e' meno di quel che costa un difetto che si presenta
 *    una volta ogni mille incollate. */
static pthread_mutex_t appunti_lucchetto = PTHREAD_MUTEX_INITIALIZER;

static void appunti_dalla_sessione(const char *testo, size_t byte, void *dati)
{
	size_t off = 0;

	(void)dati;

	/* ⚠ Il tetto l'ha gia' fatto rispettare `appunti.c`, che e' dove il testo
	 *   esiste intero.  ⛔ Questa riga NON e' un doppione: e' la promessa che
	 *   `monta_appunti()` dall'altra parte non riceva mai un `totale` che
	 *   rifiuterebbe — cioe' che il difetto, se ci fosse, si veda **qui** e non
	 *   come un testo sparito senza spiegazione. */
	if (byte > APPUNTI_TETTO) {
		registro_dice(REG_APPUNTI,
		              "⛔ %zu byte oltre il tetto di §5.4 (%u) sono arrivati "
		              "fin qui: NON si spediscono.  ⚠ Se questa riga compare, "
		              "il controllo di `appunti.c` ha una falla",
		              byte, APPUNTI_TETTO);
		return;
	}

	do {
		struct corpo_appunti c;
		size_t q = byte - off;

		if (q > PEZZO_MAX)
			q = PEZZO_MAX;
		memset(&c, 0, sizeof c);
		c.serial = 0; /* la sessione ha copiato, non ha chiesto */
		c.totale = (uint32_t)byte;
		c.offset = (uint32_t)off;
		c.pezzo = (uint32_t)q;
		if (!manda(MSG_APPUNTI_DALLA_SESSIONE, &c, sizeof c,
		           q ? testo + off : NULL, q)) {
			/* ⛔ In chiaro e non in dettaglio: un testo copiato che non arriva
			 *    al client e' un fatto che l'utente VEDE — incolla sul telefono
			 *    e trova quel che c'era prima.  ⚠ E' anche il caso in cui il
			 *    silenzio somiglia di piu' al funzionamento. */
			registro_dice(REG_APPUNTI,
			              "⛔ il pezzo a %zu di %zu byte non e' partito verso il "
			              "padre (%s): quel che la sessione ha copiato NON "
			              "arrivera' al client",
			              off, byte, strerror(errno));
			return;
		}
		off += q;
	} while (off < byte);
}

static void appunti_vuole_incollare(uint32_t serial, void *dati)
{
	struct corpo_appunti c;
	uint64_t adesso = registro_ora_ms();
	int posto = -1;

	(void)dati;

	pthread_mutex_lock(&appunti_lucchetto);
	for (int i = 0; i < APPUNTI_IN_VOLO; i++)
		if (!appunti_in_volo[i].usato) {
			posto = i;
			break;
		}
	if (posto >= 0) {
		appunti_in_volo[posto].usato = true;
		appunti_in_volo[posto].serial = serial;
		appunti_in_volo[posto].scade_ms = adesso + APPUNTI_ATTESA_MS;
	}
	pthread_mutex_unlock(&appunti_lucchetto);

	/* ⛔ La tabella e' piena: si risponde SUBITO «non ce l'ho» invece di
	 *    aggiungere un debito che nessuno scadra'.  ⚠ Otto incollate insieme
	 *    non e' un caso normale — se questa riga compare, o qualcuno tiene giu'
	 *    Ctrl+V, o le risposte non stanno tornando. */
	if (posto < 0) {
		registro_dice(REG_APPUNTI,
		              "⛔ gia' %d richieste di incolla in volo: la %u si chiude "
		              "subito con «non ce l'ho», invece di restare senza "
		              "risposta",
		              APPUNTI_IN_VOLO, serial);
		appunti_rispondi(palco_appunti, serial, NULL, 0);
		return;
	}

	memset(&c, 0, sizeof c);
	c.serial = serial;
	if (!manda(MSG_APPUNTI_VUOLE, &c, sizeof c, NULL, 0)) {
		/* ⛔ Non e' partita: si risponde ADESSO, senza aspettare il fondo.
		 *    Il fondo serve a chi non risponde; qui sappiamo gia' che non
		 *    rispondera' nessuno. */
		registro_dice(REG_APPUNTI,
		              "⛔ la richiesta di incolla %u non e' partita verso il "
		              "padre (%s): rispondo «non ce l'ho» subito, o chi incolla "
		              "resta appeso",
		              serial, strerror(errno));
		pthread_mutex_lock(&appunti_lucchetto);
		appunti_in_volo[posto].usato = false;
		pthread_mutex_unlock(&appunti_lucchetto);
		appunti_rispondi(palco_appunti, serial, NULL, 0);
	}
}

/* Chi era in volo e non ha avuto risposta entro il fondo: si risponde a mani
 * vuote.  ⛔ Gira sul ciclo del figlio, a ogni giro di `poll`. */
static void appunti_scadi(uint64_t adesso)
{
	uint32_t scaduti[APPUNTI_IN_VOLO];
	int quanti = 0;

	pthread_mutex_lock(&appunti_lucchetto);
	for (int i = 0; i < APPUNTI_IN_VOLO; i++)
		if (appunti_in_volo[i].usato && adesso >= appunti_in_volo[i].scade_ms) {
			scaduti[quanti++] = appunti_in_volo[i].serial;
			appunti_in_volo[i].usato = false;
		}
	pthread_mutex_unlock(&appunti_lucchetto);

	/* ⛔ Fuori dal lucchetto: `appunti_rispondi` fa chiamate D-Bus sincrone, e
	 *    tenerlo preso mentre si aspetta il bus bloccherebbe il thread degli
	 *    appunti su ogni segnale nuovo. */
	for (int i = 0; i < quanti; i++) {
		registro_dice(REG_APPUNTI,
		              "⚠ nessuna risposta dal client per la richiesta %u entro "
		              "%d ms: chiudo con «non ce l'ho».  ⛔ Chi incolla vede una "
		              "incollata vuota, che e' molto meglio di un desktop "
		              "appeso",
		              scaduti[i], APPUNTI_ATTESA_MS);
		appunti_rispondi(palco_appunti, scaduti[i], NULL, 0);
	}
}

/*
 * Il testo che il CLIENT ha copiato, montato un pezzo per volta.
 *
 * ⛔ Un tavolo solo, e basta: le richieste si servono **una per volta** sul filo
 *    (`rcp.c` non ne tiene due aperte verso lo stesso client), e due montaggi
 *    intrecciati qui vorrebbero dire due testi mescolati — cioe' esattamente
 *    quel che l'identificatore di trasferimento di §7.4 esiste per evitare.
 *    ⚠ Se un giorno il padre ne aprisse due, questa funzione **lo dice** invece
 *    di mescolare: il `serial` che cambia a meta' montaggio butta tutto.
 */
static struct {
	bool aperto;
	uint32_t serial;
	uint8_t *dati;
	size_t totale, avuti;
} appunti_montaggio;

static void appunti_montaggio_libera(void)
{
	free(appunti_montaggio.dati);
	appunti_montaggio.dati = NULL;
	appunti_montaggio.aperto = false;
	appunti_montaggio.totale = appunti_montaggio.avuti = 0;
}

static bool appunti_riscuoti(uint32_t serial);

static void appunti_dal_client(const struct corpo_appunti *c, const uint8_t *dati)
{
	/* ⛔ «Non ce l'ho» arriva come CAMPO, non come lunghezza zero: un testo
	 *    vuoto e' un fatto lecito e diverso.  ⇒ Due strade, e due chiamate
	 *    diverse verso Mutter. */
	if (c->niente) {
		appunti_montaggio_libera();
		if (appunti_riscuoti(c->serial))
			appunti_rispondi(palco_appunti, c->serial, NULL, 0);
		else
			registro_dettaglio(REG_APPUNTI,
			                   "«non ce l'ho» per la richiesta %u, che non e' "
			                   "piu' in volo: gia' scaduta, e Mutter ha gia' "
			                   "avuto la sua risposta",
			                   c->serial);
		return;
	}

	if (c->totale > APPUNTI_TETTO) {
		registro_dice(REG_APPUNTI,
		              "⛔ il padre annuncia %u byte di appunti, oltre il tetto "
		              "di §5.4 (%u): rispondo «non ce l'ho» invece di troncare",
		              c->totale, APPUNTI_TETTO);
		appunti_montaggio_libera();
		if (appunti_riscuoti(c->serial))
			appunti_rispondi(palco_appunti, c->serial, NULL, 0);
		return;
	}

	if (c->offset == 0) {
		appunti_montaggio_libera();
		appunti_montaggio.dati = (uint8_t *)malloc((size_t)c->totale + 1u);
		if (!appunti_montaggio.dati) {
			registro_dice(REG_APPUNTI,
			              "⛔ %u byte di appunti dal client non entrano in "
			              "memoria: rispondo «non ce l'ho»",
			              c->totale);
			if (appunti_riscuoti(c->serial))
				appunti_rispondi(palco_appunti, c->serial, NULL, 0);
			return;
		}
		appunti_montaggio.aperto = true;
		appunti_montaggio.serial = c->serial;
		appunti_montaggio.totale = c->totale;
		appunti_montaggio.avuti = 0;
	}

	/* ⛔ In ordine, dello stesso trasferimento, e della stessa misura.  Un
	 *    pezzo che non torna butta tutto e RISPONDE: lasciare il montaggio
	 *    aperto a meta' vorrebbe dire un `SelectionTransfer` che aspetta il
	 *    fondo di tempo per niente. */
	if (!appunti_montaggio.aperto || c->serial != appunti_montaggio.serial
	    || c->offset != appunti_montaggio.avuti
	    || c->totale != appunti_montaggio.totale
	    || (uint64_t)c->offset + c->pezzo > c->totale) {
		registro_dice(REG_APPUNTI,
		              "⛔ pezzo di appunti fuori posto (richiesta %u, offset %u "
		              "di %u): butto il testo intero e rispondo «non ce l'ho»",
		              c->serial, c->offset, c->totale);
		appunti_montaggio_libera();
		if (appunti_riscuoti(c->serial))
			appunti_rispondi(palco_appunti, c->serial, NULL, 0);
		return;
	}

	memcpy(appunti_montaggio.dati + c->offset, dati, c->pezzo);
	appunti_montaggio.avuti += c->pezzo;
	if (appunti_montaggio.avuti < appunti_montaggio.totale)
		return;

	appunti_montaggio.dati[appunti_montaggio.totale] = 0;
	/* ⛔ Si riscuote PRIMA di rispondere: se il serial non e' piu' in volo, il
	 *    fondo di tempo lo ha gia' chiuso con Mutter, e una seconda
	 *    `SelectionWriteDone` sullo stesso trasferimento e' un messaggio che
	 *    Mutter non aspetta piu'. */
	if (appunti_riscuoti(appunti_montaggio.serial)) {
		registro_dice(REG_APPUNTI,
		              "⭐ %zu byte dal client consegnati a chi sta incollando "
		              "(richiesta %u)",
		              appunti_montaggio.totale, appunti_montaggio.serial);
		appunti_rispondi(palco_appunti, appunti_montaggio.serial,
		                 (const char *)appunti_montaggio.dati,
		                 appunti_montaggio.totale);
	} else {
		registro_dice(REG_APPUNTI,
		              "⚠ il testo per la richiesta %u e' arrivato DOPO il fondo "
		              "di %d ms: si butta, perche' Mutter ha gia' avuto la sua "
		              "risposta.  ⛔ Chi ha incollato ha visto una incollata "
		              "vuota, ed e' il prezzo dichiarato del fondo",
		              appunti_montaggio.serial, APPUNTI_ATTESA_MS);
	}
	appunti_montaggio_libera();
}

/* Il serial c'era davvero fra quelli in volo?  ⛔ Toglierlo dalla tabella e
 * servirlo sono due cose sole, e stanno qui insieme: un serial servito e
 * lasciato in tabella verrebbe scaduto dopo, e Mutter riceverebbe **due**
 * `SelectionWriteDone` per lo stesso trasferimento. */
static bool appunti_riscuoti(uint32_t serial)
{
	bool c_era = false;

	pthread_mutex_lock(&appunti_lucchetto);
	for (int i = 0; i < APPUNTI_IN_VOLO; i++)
		if (appunti_in_volo[i].usato && appunti_in_volo[i].serial == serial) {
			appunti_in_volo[i].usato = false;
			c_era = true;
			break;
		}
	pthread_mutex_unlock(&appunti_lucchetto);
	return c_era;
}

/* ⛔⭐ IL FIGLIO SI TIENE QUEL CHE HA CODIFICATO, e la ragione non e' la
 *     velocita': e' che il PADRE ha un deposito solo (`webtransport.c`), quindi
 *     quando entra un altro utente il padre lo SVUOTA — e il primo utente, che
 *     ha ancora il suo figlio vivo, dovrebbe poterselo far rimandare senza
 *     ricatturare.
 *
 * ⚠ E si rimanda **lo stesso fotogramma**, non uno nuovo: la fase 2 e'
 *   un'immagine ferma, quella dell'accensione del palco
 *   (`FASI.md` §02-primo-fotogramma), e ricatturare qui vorrebbe dire consegnare
 *   due immagini diverse sotto la stessa etichetta.  ⛔ Il ciclo dei fotogrammi
 *   e' della fase 3. */
static uint8_t *tenuto[3];
static size_t tenuto_byte[3];
static bool tenuto_chiave[3];
static uint32_t tenuto_l, tenuto_a;
static uint64_t tenuto_istante;
/* ⛔ E anche il fotogramma TENUTO porta il suo `input`, quello dell'istante in
 *    cui fu catturato — non quello di adesso.  ⚠ Rimandandolo con il numero
 *    corrente si direbbe a chi rientra che un input appena arrivato e' gia'
 *    nella scena di un'immagine ferma da minuti: e l'anello del ritardo lo
 *    leggerebbe come un ritardo bassissimo.  E' la stessa ragione per cui si
 *    rimanda **lo stesso** fotogramma e non uno nuovo. */
static uint32_t tenuto_input;

/* ═══════════════════════════════════════════════════════════════════════════ */
/* ⭐⭐ FASE 3 — IL CICLO DEI FOTOGRAMMI, DENTRO IL FIGLIO                      */
/*                                                                             */
/* ⛔⭐ IL CODIFICATORE E' UNO SOLO PER CODEC, E VIVE FRA UN FOTOGRAMMA E       */
/*     L'ALTRO.  Fino alla fase 2 se ne creava uno per fotogramma —            */
/*     `codificatore_nuovo()` … `codificatore_libera()` dentro la stessa       */
/*     funzione — e con un fotogramma solo non si vedeva.  ⛔ Con il ciclo,    */
/*     un codificatore nuovo a ogni giro vuol dire che **la predizione non     */
/*     esiste**: ogni fotogramma sarebbe una chiave, cioe' dieci volte la      */
/*     banda di un delta, per sempre.  ⚠ E non e' solo banda: `RCP.md` §5.2    */
/*     costruisce tutta la cura dell'abbandono sulla differenza fra chiave e   */
/*     delta, e senza delta quella cura non ha oggetto.                        */
/*                                                                             */
/* ⛔ E LA CADENZA E' **UNA SOLA**, e prima erano due.  `cattura_avvia()`      */
/*    chiedeva 60 e la richiesta di codifica dichiarava 30: due numeri diversi */
/*    per la stessa grandezza, innocui solo finche' si codificava un           */
/*    fotogramma solo.  ⇒ `MOVIMENTO_FPS`, dichiarata qui e usata in tutt'e    */
/*    due i posti.  ⭐ Il valore e' **60** e non 30 perche' e' il desiderato di */
/*    `SPECIFICHE.md` §3.1, e perche' `LEZIONI.md` §6.1 dice che il numero     */
/*    chiesto alla cattura E' il tetto: chiedendone 30 ne arrivano 18,         */
/*    chiedendone 60 ne arrivano 37.  Un tetto che ci mettiamo noi non e' una  */
/*    misura della macchina.                                                    */
#define MOVIMENTO_FPS 60

/* ═══════════════════════════════════════════════════════════════════════════
 * ⭐⭐⭐ LA STRADA DEI PIXEL — e dal 22 agosto 2026 il difetto e' LA SCHEDA
 *
 * ⛔ FINO A OGGI IL FOTOGRAMMA FACEVA QUESTO GIRO: usciva dalla GPU (dove Mutter
 *    l'aveva composto), veniva COPIATO in memoria di sistema, CONVERTITO in CPU
 *    da `sws_scale`, e RICARICATO sulla GPU per essere codificato.  `[M]` 22
 *    agosto 2026, agente C, dentro il prodotto: copia 1,65 · conversione 8,15 ·
 *    caricamento 1,16 = **10,96 ms su 18,86, il 58 % del tratto**.
 *
 * ⭐ La strada della scheda — il DMA-BUF consegnato da Mutter e importato come
 *    superficie VA-API — toglie tutt'e tre i passaggi: il fotogramma **sulla
 *    GPU ci stava gia'**.  `[M]` Mutter il DMA-BUF lo consegna davvero: 388
 *    fotogrammi, 4 buffer, modificatore LINEAR, stride 7680 letto dal chunk
 *    (`DECISIONI.md` §2.3-ter).
 *
 * ⛔⛔ E VALE **SOLO SE IL CODIFICATORE E' IN HARDWARE**: in software non c'e'
 *      nessun pixel da leggere.  ⇒ La strada si sceglie prima, e se il
 *      codificatore ripiega in CPU il palco si RIMONTA sulla memoria,
 *      dichiarandolo — vedi `scheda_da_abbandonare`.
 *
 * ⚠ E i DIECI BIT non tornano da questa porta: Mutter consegna BGRx, otto bit
 *   per canale, sulla scheda come in memoria (`cattura.h`).  Questa strada
 *   cambia dove sta il fotogramma, non che cosa c'e' dentro.
 *
 * ⭐ Si puo' scavalcare da riga di compilazione (`-DCOPIA_ZERO=0`), e serve a
 *    UNA cosa sola: ricostruire il **prima** con lo stesso sorgente del dopo,
 *    per il confronto A/B alternato.  ⛔ Non e' un interruttore di prodotto e
 *    non ne diventa uno: il prodotto ha un valore solo, quello qui sotto
 *    (`CODER.md` invariante I7).
 * ═══════════════════════════════════════════════════════════════════════════ */
#ifndef COPIA_ZERO
#define COPIA_ZERO 1
#endif

/* La strada che si chiede al produttore al prossimo montaggio del palco.
 * ⛔ E' una variabile e non una costante perche' puo' RETROCEDERE una volta:
 *    quando si scopre che il codificatore di questa macchina e' in software.
 *    ⚠ Non torna mai avanti da se': tornare avanti vorrebbe dire riprovare una
 *    strada gia' misurata impossibile, a ogni rimontaggio. */
static CatturaStrada strada_del_palco =
    COPIA_ZERO ? CATTURA_STRADA_SCHEDA : CATTURA_STRADA_MEMORIA;
/* ⛔ I TRE STATI DEL RIMONTAGGIO, e sono tre perche' rispondono a tre domande
 *    diverse.  ⚠ Nessuno di loro rimonta niente da se': il palco lo tiene il
 *    ciclo, e `codifica_e_manda` non puo' smontarlo mentre ci sta leggendo
 *    dentro.
 *
 *   `scheda_da_abbandonare`  ⇒ rimonta in MEMORIA: questo fotogramma sulla
 *                              scheda non si puo' usare;
 *   `scheda_da_riprovare`    ⇒ rimonta sulla SCHEDA: la tela e' cambiata e la
 *                              negazione di prima non vale piu';
 *   `scheda_mai_piu`         ⛔ il codificatore di questa macchina e' in
 *                              SOFTWARE: non e' una questione di tela, e
 *                              riprovare a ogni ridimensionamento sarebbe
 *                              rimontare il palco per niente, all'infinito.
 */
static bool scheda_da_abbandonare;
static bool scheda_da_riprovare;
static bool scheda_mai_piu;
/* ⛔⛔ E QUESTA E' LA GUARDIA CHE EVITA IL GIRO A VUOTO — e vale una riga di
 *     spiegazione, perche' sembra la stessa cosa e non lo e'.
 *
 * Il passo del DMA-BUF si conosce **solo dopo il primo fotogramma**
 * (`cattura.h` regola 1: lo stride si LEGGE dal chunk, mai si calcola).  ⇒ Con
 * una tela il cui passo non e' importabile il palco nasce sulla scheda,
 * consegna un fotogramma, lo si rifiuta, e si rimonta sulla memoria.  Senza
 * memoria di quel verdetto lo si rifarebbe a ogni giro.
 *
 * ⭐ Qui si tiene la tela per cui la scheda e' stata negata, e non la si
 *    riprova finche' la tela non cambia.  ⛔ E il verdetto resta quello
 *    MISURATO sul passo vero: questa e' la memoria di quel verdetto, non una
 *    previsione che lo sostituisce.
 */
static uint32_t scheda_negata_l, scheda_negata_a;

/* ⛔ Quanto si aspetta un fotogramma dalla cattura dentro un giro del ciclo.
 *
 * ⚠ Non e' un tetto di cadenza: e' quanto si resta fermi PRIMA di tornare a
 *   guardare se il padre ha detto qualcosa.  ⭐ Qui si PUO' aspettare — questo
 *   e' un altro processo, e `CODER.md` §4.4 vieta l'attesa dentro il ciclo
 *   asincrono del server, non qui.
 * ⛔ E su un desktop FERMO Mutter non consegna niente: questa attesa scade
 *    tutta, e il giro dopo ricomincia.  Zero fotogrammi su una scena ferma e'
 *    un RISULTATO (`CatturaPresa` lo distingue dal guasto), non un difetto.
 *
 * ═══════════════════════════════════════════════════════════════════════════
 * ⛔⛔⛔ ED ERA 0,25 — cioe' UN QUARTO DI SECONDO DI RITARDO SU OGNI CLIC.
 *
 *     `[M]` 15 agosto 2026, misurato sui clic VERI dell'utente (registro delle
 *     05:25, venticinque pressioni): **clic → primo fotogramma spedito, mediana
 *     136 ms, peggiore 502 ms**.  E la riga di riassunto del ciclo diceva la
 *     causa senza che nessuno la leggesse: **«3-4 attese a vuoto al secondo»**,
 *     cioe' quattro giri al secondo, cioe' 250 ms per giro.
 *
 * ⛔ IL MECCANISMO, e la riga qui sopra lo diceva quasi: l'input del padre si
 *    legge **prima** dell'attesa.  Un clic che arriva un millisecondo DOPO che
 *    il ciclo e' entrato in `cattura_prendi()` resta fermo nel socket per i 249
 *    ms che restano.  ⚠ Su un desktop che si muove non si vede — il fotogramma
 *    arriva subito e il giro riparte; su un desktop FERMO, che e' il caso in cui
 *    si clicca, si paga tutto.  ⇒ Ritardo medio atteso: **125 ms**, e il
 *    misurato e' 136.
 *
 * ⇒ ⭐ Con 8 ms il ritardo medio aggiunto scende a **4 ms**, e il ciclo si
 *   sveglia 125 volte al secondo invece di 4: e' un `poll()` a vuoto e una
 *   attesa su condizione, cioe' niente accanto a sessanta fotogrammi al secondo
 *   da convertire e comprimere.
 *
 * ⚠ E RESTA UN RIPIEGO, dichiarato: la cura VERA e' non aspettare affatto a
 *   tempo — un descrittore che la cattura scrive quando un fotogramma e' pronto,
 *   messo nello stesso `poll()` del socket del padre e di `libei`.  Allora il
 *   ritardo aggiunto sarebbe **zero** invece di quattro millisecondi, e i
 *   risvegli scenderebbero a quelli utili.  ⛔ Non si e' fatto stanotte perche'
 *   tocca il posto di scambio di `cattura.c` (oggi il fotogramma si copia solo
 *   se qualcuno sta gia' aspettando), e quel pezzo gira sul thread di tempo
 *   reale di PipeWire: e' una cura da misurare, non da improvvisare.
 * ═══════════════════════════════════════════════════════════════════════════ */
#define MOVIMENTO_ATTESA_S 0.008

/* ⛔⭐ QUANTO SI ASPETTA PRIMA DI RIPROVARE A MONTARE IL PALCO, E PERCHE'
 *     CRESCE.
 *
 * `[M]` 14 agosto 2026, sessione vera dell'utente: senza nessuna attesa il
 * ciclo girava a vuoto e scriveva **30,8 GB di registro in pochi minuti**, 112
 * milioni di righe identiche tutte nello stesso millisecondo.  ⇒ Il difetto non
 * era «riprovare»: era **riprovare senza fermarsi mai**.
 *
 * ⚠ Il minimo e' un secondo perche' una sessione grafica che sta nascendo ci
 *   mette secondi, e riprovare dieci volte al secondo non la fa nascere prima.
 * ⚠ Il massimo e' mezzo minuto perche' oltre non si guadagna niente e si
 *   perderebbe il caso vero: un utente che rifa' login su una macchina dove la
 *   sessione e' appena tornata deve trovarla, non aspettare un quarto d'ora. */
#define PALCO_RIPROVA_MIN_MS 1000
#define PALCO_RIPROVA_MAX_MS 30000

/*
 * ⚠ Quanto si aspetta prima di ri-chiedere la NASCITA della sessione grafica.
 *
 * ⛔⛔ ERA UN MINUTO, ED ERA IL DIFETTO — 16 agosto 2026.  Il ragionamento
 *     («`gnome-session` ci mette qualche secondo, e senza briglia ne
 *     avvieremmo una a ogni giro») era giusto; ⛔ il numero no.
 *
 * `[M]` Dopo un logout il gestore d'utente si sta ancora spegnendo, e la
 * sessione che avviamo in quell'istante **muore con lui**.  Con la briglia a un
 * minuto il figlio non riprovava per sessanta secondi: il client aspettava,
 * non vedeva niente e se ne andava.  ⇒ Un giro sì e uno no, che e' esattamente
 * il ritmo che l'utente ha visto cinque volte di fila.
 *
 * ⭐ Dodici secondi: piu' del tempo che `gnome-session` ci mette a comparire sul
 *    bus (`[M]` 3 s sulla macchina di prova, con margine per una macchina
 *    carica), e abbastanza poco perche' un avvio fallito si recuperi mentre chi
 *    guarda e' ancora li'.
 *
 * ⚠ E la briglia resta necessaria: senza, un ri-tentativo ogni secondo
 *   avvierebbe dieci `gnome-session` prima che il primo si faccia vedere.
 */
#define NASCITA_BRIGLIA_MS 12000

/*
 * ⛔⭐⭐ QUANTO SI RIPROVA MENTRE LA SESSIONE STA NASCENDO — e questo numero
 *       e' la cura del difetto che l'utente ha visto quattro volte: *«al quarto
 *       login il desktop ha impiegato molti secondi prima di ricomparire»*.
 *
 * ⛔⛔ LA CAUSA ERA L'ATTESA CHE RADDOPPIA, e il ragionamento che la giustifica
 *     e' giusto per UN caso solo.  `PALCO_RIPROVA_MIN_MS` cresce 1 s → 2 s →
 *     4 s → 8 s, e questo e' quel che serve quando il palco **non c'e' piu'**:
 *     una sessione morta non torna perche' la si chiama piu' spesso, e senza
 *     freno quel ciclo ha gia' scritto 30 GB di registro (14 agosto).
 *
 * ⛔ Ma quando il palco **non c'e' ANCORA** la stessa attesa e' esattamente il
 *    difetto.  `[M]` 16 agosto 2026, venti giri cronometrati: `gnome-session`
 *    si fa vedere sul bus dopo ~2,9 s, e i tentativi cadono a 0, 1, 3, 7 s.
 *    ⇒ Se si fa vedere a 2,9 s lo troviamo a 3 s (100 ms persi, ed e' il caso
 *    buono, mediana 3193 ms); ⛔ **se ci mette 3,2 s il tentativo delle 3 s lo
 *    manca e il successivo e' a SETTE**.  L'utente aspetta quattro secondi di
 *    puro orologio, con la sessione gia' pronta e nessuno che la guarda.
 *
 * ⭐ E si vede nella misura stessa: mediana 2880 ms, p90 **3891 ms**.  Quei due
 *    numeri non sono una distribuzione, sono **due gradini** — il tentativo
 *    delle 3 s e quello dopo.
 *
 * ⇒ I due casi che il commento del ciclo distingueva a parole — «non c'e'
 *   ancora» e «non c'e' piu'» — adesso si distinguono anche nel tempo: finche'
 *   siamo dentro la finestra della nascita si riprova ogni 200 ms, dopo torna
 *   la briglia che raddoppia.  ⚠ Il costo e' sessanta chiamate D-Bus a un nome
 *   che non risponde, in dodici secondi: niente.  Il guadagno e' fino a
 *   quattro secondi di attesa a vuoto, e sono i secondi che l'utente vede.
 */
#define PALCO_NASCITA_RIPROVA_MS 200

/*
 * ⛔⭐ «L'UTENTE E' USCITO»: il terzo stato, e senza di lui il figlio RIFA' la
 *     sessione tre secondi dopo averla lasciata morire.
 *
 * `[M]` 15 agosto 2026, banco del logout: il figlio ha riconosciuto la
 * transizione («c'era e non c'e' piu'»), ha congedato il client con `0x10`, e
 * al ri-tentativo successivo — con l'interruttore gia' riabbassato — ha visto
 * una sessione MORTA come tante e l'ha fatta rinascere.  ⇒ L'utente sarebbe
 * uscito e il desktop sarebbe tornato da solo.
 *
 * ⭐ Gli stati sono TRE, non due: «non c'e' mai stata» (si fa nascere), «c'e'»
 *    (non si tocca), «l'utente l'ha chiusa» (⛔ NON si rifa' finche' non arriva
 *    un attacco NUOVO).  ⚠ Il ritorno al primo stato lo decide l'arrivo di un
 *    client — cioe' `MSG_VIDEO` con un codec — perche' e' quello il gesto con
 *    cui l'utente dice «rivoglio un desktop».
 */
static bool sessione_chiusa_dall_utente;

/* Quando si riprova, e quanto si e' aspettato l'ultima volta. */
static uint64_t palco_riprova_ms;
static uint64_t palco_attesa_ms;

/*
 * ⛔⭐⭐⭐ «LA TELA DEL CLIENTE E' ARRIVATA» — e senza questo il palco nasceva
 *        alla misura sbagliata, sempre.
 *
 * `[M]` 16 agosto 2026, e questa e' la causa comune di TUTTI i sintomi che
 * l'utente ha elencato: bande nere, «desktop rotto», «nessun input», «ci mette
 * molti secondi».  La catena:
 *
 *   1. il figlio nasce con `1920x1080` — il valore della tabella dei figli,
 *      cioe' un RIPIEGO — perche' al `fork` la finestra del cliente non e'
 *      ancora dichiarata;
 *   2. monta subito il palco a quella misura e spedisce una chiave sbagliata;
 *   3. ~650 ms dopo arriva la tela vera (`2544x926`) e servirebbe un
 *      ridimensionamento;
 *   4. ⛔ ma su Wayland il ridimensionamento si compie SOLO quando il
 *      compositore consegna un fotogramma nuovo — e un desktop appena nato non
 *      cambia niente.  `[M]` «1 fotogrammi consegnati, **3538 attese a vuoto**
 *      (scena ferma: Mutter consegna solo quando qualcosa cambia)».
 *
 * ⇒ Si aspettava che qualcosa si muovesse da se': tredici, diciassette, trenta
 *   secondi.  ⭐ Mezzo secondo di attesa qui li toglie tutti.
 *
 * ⚠ E NON si aspetta all'infinito: l'invariante I1 vieta di stare fermi per
 *   prudenza.  Passato `TELA_ATTESA_MS` si parte col ripiego — meglio un
 *   desktop da ridimensionare che nessun desktop.
 */
static bool tela_dal_cliente;

/* ⚠ Quanto si concede alla tela del cliente prima di partire col ripiego.
 *   `[M]` Ne bastano ~650: mezzo secondo di margine e non uno di piu', perche'
 *   oltre si comincia a far aspettare chi ha gia' premuto «Collegati». */
#define TELA_ATTESA_MS 1200

/* ⭐ Quando abbiamo chiesto la NASCITA della sessione grafica, 0 se mai.
 *
 * ⛔ Era una `static` dentro `prendi_il_palco()`, e da li' il ciclo dei
 *    fotogrammi non poteva vederla — quindi non poteva distinguere «il palco
 *    non c'e' ANCORA» da «non c'e' PIU'», e trattava i due casi con la stessa
 *    attesa che raddoppia.  ⇒ Vedi `PALCO_NASCITA_RIPROVA_MS`. */
static uint64_t nascita_chiesta_ms;

/* Siamo dentro la finestra in cui una sessione chiesta puo' ancora farsi
 * vedere?  ⚠ Se si', il palco che manca e' un palco che sta NASCENDO. */
static bool sta_nascendo(uint64_t ora_ms)
{
	return nascita_chiesta_ms != 0 &&
	       ora_ms - nascita_chiesta_ms <= NASCITA_BRIGLIA_MS;
}

#define CODEC_MAX 4
/* ⛔ QUATTRO POSTI PER TRE CODEC, e il conto e' voluto: l'indice E' il numero
 *    di §6.2 (1 = HEVC, 2 = AV1, 3 = H.264) e il posto 0 resta vuoto.  ⚠ Un
 *    array «stretto» con una sottrazione dentro sarebbe la stessa cosa scritta
 *    peggio: il giorno in cui un codec nuovo prendesse il 4, la sottrazione
 *    andrebbe corretta in sei punti e il registro direbbe numeri diversi da
 *    quelli del protocollo. */
static Codificatore *codif[CODEC_MAX];
/* Quale codec il padre ha chiesto: 0 = nessuno, cioe' nessuno sta guardando. */
static uint8_t codec_chiesto;
/* ⛔⭐⭐ E LA PROFONDITA' CHE IL PADRE HA NEGOZIATO (§4.3) — 17 agosto 2026.
 *
 *      Qui c'era un letterale, tre righe piu' in la': `r.profondita = 10`, per
 *      OGNI codec e qualunque cosa fosse stata negoziata.  ⛔ Il flusso usciva
 *      a 10 bit mentre `ECCOMI` ne dichiarava 8 — **due verita' sullo stesso
 *      fatto, in due processi diversi**, e nessun banco poteva vederle insieme.
 *
 * ⚠ `0` = il padre non l'ha ancora detta.  ⛔ E NON vale 8: finche' non si sa,
 *   non si apre nessun codificatore — «non lo so» e «e' otto» sono due fatti
 *   diversi, ed e' proprio la loro confusione che ha prodotto il difetto. */
static uint8_t profondita_chiesta;
/* ⛔⭐⭐ E IL LIVELLO CHE IL CLIENT HA DICHIARATO (§4.3 riga 701) — 23 agosto
 *      2026, e nasce dalla stessa famiglia di difetto della riga qui sopra.
 *
 *      `[M]` tela 3840x2160, H.264: il client dichiara `video.livello=5.1` e il
 *      server produce **5.2**.  Il numero chiesto viveva nel PADRE, il prodotto
 *      nel FIGLIO, e nessuno li metteva vicini — `LEZIONI.md` §7.5.
 *
 * ⚠ In decimi (`5.1` ⇒ 51).  ⛔ `0` = il client non l'ha dichiarato, e §4.3 non
 *   lo obbliga: allora NESSUN TETTO, si apre lo stesso e si SCRIVE che cosa e'
 *   uscito.  ⚠ E qui lo zero non blocca l'apertura come fa la profondita': la
 *   profondita' e' sempre negoziata (§4.3 la impone a tutti e due), il livello
 *   no.  Sono due «zeri» diversi, e trattarli uguali sarebbe inventare un
 *   obbligo che il documento non ha. */
static uint8_t livello_chiesto_x10;
/* ⛔ §5.2 — il debito della chiave, uno per codec: chiederla per l'HEVC non la
 *    produce sull'AV1, e trattarli insieme darebbe una chiave a chi non l'ha
 *    chiesta e un delta a chi si'. */
/* ⛔⛔⭐ QUATTRO POSTI, come `codif[]` — e questa riga e' costata un giro il 20
 *      agosto 2026.  Con `[3]` il codec **3** scriveva FUORI DAI LIMITI, e il
 *      byte che si sporcava era la variabile accanto: il registro diceva
 *      «⭐ §4.3: il padre ha negoziato 8 bit (prima **1**)» a ogni richiesta di
 *      chiave, cioe' un difetto di memoria travestito da difetto di
 *      negoziazione.  ⇒ Zero fotogrammi, e nessuna riga che nominasse la causa.
 * ⚠ L'indice E' il numero di §6.2: chi aggiunge un codec allarga QUESTI array,
 *   e sono CINQUE dal 23 agosto 2026 (`codif_liv[]` e' l'ultimo arrivato).
 *   Cercarli si cerca cosi': `grep "\[CODEC_MAX\]"`. */
static bool debito_chiave[CODEC_MAX];
/* ⛔ Con quale profondita' ciascun codificatore e' stato APERTO.  ⚠ Si tiene qui
 *    e non si chiede a `codificatore.h`: quel modulo non ha un lettore per la
 *    profondita', e aggiungerne uno per una domanda che si puo' ricordare
 *    sarebbe allargare un'interfaccia per pigrizia di chi chiama. */
static uint8_t codif_prof[CODEC_MAX];
/* ⛔ E con quale LIVELLO IMPOSTO (§4.3, in decimi; `0` = nessun tetto).  ⚠ Sta
 *    accanto a `codif_prof[]` e per la stessa ragione: il palco sopravvive al
 *    client (I4), e il secondo che si collega puo' dichiarare un livello
 *    diverso dal primo — senza questa memoria il codificatore resterebbe al
 *    tetto del PRIMO, che e' esattamente il difetto che si sta curando. */
static uint8_t codif_liv[CODEC_MAX];
static uint64_t ciclo_fotogrammi, ciclo_chiavi, ciclo_zero, ciclo_guasti;
/* ⛔ CONTATO A PARTE da `ciclo_guasti`, e non e' pignoleria: quel contatore
 *    entra nel criterio «il ciclo non ha nemmeno provato a catturare» della riga
 *    di riassunto.  Mettere qui i fotogrammi scartati per geometria incoerente
 *    darebbe due fatti diversi sotto la stessa etichetta — la forma E8, dentro
 *    la riga che esiste per smascherarla. */
static uint64_t fotogrammi_incoerenti;
/* ⛔⭐ L'ATTESA CHE CRESCE SULLA RIAPERTURA DEL CODIFICATORE — e la ragione e'
 *     la stessa dei 30,8 GB di registro del 14 agosto: se `codificatore_nuovo()`
 *     fallisce per una causa PERSISTENTE (memoria della GPU, profilo che non
 *     regge quella misura, nodo occupato), `codificatore_di()` ritenterebbe
 *     l'apertura **a ogni fotogramma** — sessanta contesti VAAPI al secondo, e
 *     una riga di registro per ciascuno.  ⚠ Il fondo qui non nasconde niente: la
 *     prima riga si scrive sempre, e la ripresa e' dichiarata. */
static uint64_t codif_riprova_ms[CODEC_MAX];
static uint64_t codif_attesa_ms[CODEC_MAX];
#define CODIF_RIPROVA_MIN_MS 500u
#define CODIF_RIPROVA_MAX_MS 10000u
/* ⭐ Quando si e' riavviato il flusso l'ultima volta per farsi consegnare un
 *    fotogramma su una scena ferma.  ⛔ Il fondo non e' prudenza: ogni riavvio
 *    costa la rinegoziazione, e farne uno a ogni giro toglierebbe i fotogrammi
 *    che si stanno cercando.  ⚠ 400 ms sta sotto ai 4,4 secondi misurati di due
 *    ordini di grandezza e sopra al costo di un riavvio (`[M]` 41,6 ms). */
static uint64_t risveglio_ms;
#define RISVEGLIO_MS 400u
/* ⛔ La cura «A» (21 ago 2026, 🔸 derivata) salta il risveglio quando qualcosa e'
 *    tenuto giu'.  ⚠ Questa bandiera serve solo a NON ripetere la riga di
 *    registro ogni 400 ms mentre l'utente trascina: una diagnostica che annega
 *    quella che conta e' una diagnostica che tace (`LEZIONI.md` §2.7). */
static int risveglio_zitto;
static uint64_t ciclo_detto_ms;
/* ⛔ La misura del punto 7, fatta e NON dedotta: il `pts` che Mutter attacca al
 *    fotogramma e' o non e' il nostro orologio monotono?  Si guarda una volta,
 *    si scrive, e da li' in poi si sa quale istante finisce nei 28 byte. */
static int pts_e_monotono = -1; /* -1 = non ancora guardato */

static uint64_t ora_monotona_us(void)
{
	struct timespec t;
	clock_gettime(CLOCK_MONOTONIC, &t);
	return (uint64_t)t.tv_sec * 1000000u + (uint64_t)(t.tv_nsec / 1000);
}

/* ═══════════════════════════════════════════════════════════════════════════
 * ⭐⭐ FASE 7 — L'AUDIO DENTRO IL FIGLIO
 *
 * ⛔⛔ E LA PRIMA COSA E' UN VINCOLO, NON UN'ARCHITETTURA: il richiamo dei
 *      campioni gira sul **thread di PipeWire, in tempo reale**.
 *
 *      Chi ci scrive dentro una chiamata che aspetta — un lucchetto conteso,
 *      una `send` su un socket, una `malloc` sfortunata — **non ferma soltanto
 *      l'audio: fa saltare il quanto a tutto il grafo PipeWire, cattura del
 *      desktop compresa**.  ⚠ Cioe' l'audio si porterebbe via i fotogrammi, e
 *      il sintomo sarebbe «il video scatta», che non nomina l'audio.
 *      (`v1/remotix-c/src/suono.h`, e `LEZIONI.md` §5.)
 *
 * ⇒ Fra il thread di PipeWire e il ciclo del figlio ci sta un **anello a un
 *   produttore e un consumatore**, senza lucchetti: il produttore muove solo
 *   `testa`, il consumatore solo `coda`, e i due indici sono atomici.  Il
 *   richiamo copia e torna.
 *
 * ⛔ E QUANDO L'ANELLO E' PIENO SI BUTTA IL PIU' VECCHIO, come per i datagram
 *    (`RCP.md` §6.3): il suono in ritardo non serve a nessuno.  ⚠ Ma qui si
 *    butta **contando**, e il conto va nel registro — perche' un anello che
 *    trabocca in silenzio e' un difetto di ritmo che nessuno vedra' mai.
 * ═══════════════════════════════════════════════════════════════════════════ */

/* Un secondo di suono.  ⚠ Non e' un cuscino per la fluidita': e' lo spazio fra
 * due giri del ciclo del figlio, che con il video acceso e' di ~8 ms
 * (`MOVIMENTO_ATTESA_S`).  Un secondo e' due ordini di grandezza di margine, e
 * costa 192 KiB — che e' meno di un fotogramma. */
#define AUDIO_ANELLO_FOTOGRAMMI 48000u

static int16_t audio_anello[AUDIO_ANELLO_FOTOGRAMMI * AUDIO_CANALI];
static _Atomic uint32_t audio_testa; /* lo muove SOLO il thread di PipeWire */
static _Atomic uint32_t audio_coda;  /* lo muove SOLO il ciclo del figlio */
static _Atomic uint64_t audio_traboccati; /* fotogrammi buttati dal produttore */

/* ⛔ L'orologio dell'audio e' il CONTO DEI CAMPIONI, non `CLOCK_MONOTONIC`.
 *
 *    `RCP.md` §6.3 vuole «l'istante del PRIMO campione del blocco», e il primo
 *    campione ha un istante suo che dipende dalla scheda, non dal momento in
 *    cui il nostro ciclo si e' svegliato.  ⚠ Usare l'ora di parete al momento
 *    dell'invio metterebbe nel campo **quando l'abbiamo spedito**, che e' un
 *    numero piu' alto e ballerino: il client lo userebbe per riordinare e
 *    riordinerebbe sul nostro jitter invece che sul suono.
 *
 * ⇒ `audio_base_us` e' l'ora vera del primo campione catturato; da li' in poi
 *   il tempo lo conta la frequenza.  ⛔ E quando l'anello trabocca la base si
 *   SPOSTA dei campioni persi, o l'orologio racconterebbe un suono continuo
 *   dove c'e' stato un buco. */
static uint64_t audio_base_us;
static uint64_t audio_consumati; /* fotogrammi gia' usciti, dalla base */

static void audio_anello_azzera(void)
{
	atomic_store(&audio_testa, 0);
	atomic_store(&audio_coda, 0);
	atomic_store(&audio_traboccati, 0);
	audio_base_us = 0;
	audio_consumati = 0;
}

/*
 * Il richiamo dei campioni.  ⛔ GIRA IN TEMPO REALE: si copia e si torna.
 *
 * ⚠ Nessuna riga di registro qui dentro, ed e' voluto: `registro_dice()` scrive
 *   su un descrittore, e una scrittura che si blocca dentro questo richiamo
 *   costa i fotogrammi del desktop.  Il traboccamento si CONTA qui e si SCRIVE
 *   di la', dal ciclo.
 */
static void audio_campioni(const int16_t *campioni, uint32_t fotogrammi, void *ctx)
{
	uint32_t testa, coda, liberi;
	(void)ctx;

	if (!fotogrammi || !campioni)
		return;

	testa = atomic_load_explicit(&audio_testa, memory_order_relaxed);
	coda = atomic_load_explicit(&audio_coda, memory_order_acquire);

	/* ⛔ Un posto resta sempre vuoto: e' l'unico modo di distinguere «pieno»
	 *    da «vuoto» con due soli indici. */
	liberi = (coda + AUDIO_ANELLO_FOTOGRAMMI - testa - 1u) % AUDIO_ANELLO_FOTOGRAMMI;
	if (fotogrammi > liberi) {
		/* Si tiene la CODA del blocco, cioe' il suono piu' recente. */
		uint32_t buttati = fotogrammi - liberi;
		atomic_fetch_add_explicit(&audio_traboccati, buttati, memory_order_relaxed);
		campioni += (size_t)buttati * AUDIO_CANALI;
		fotogrammi = liberi;
		if (!fotogrammi)
			return;
	}

	for (uint32_t i = 0; i < fotogrammi; i++) {
		uint32_t p = (testa + i) % AUDIO_ANELLO_FOTOGRAMMI;
		audio_anello[p * AUDIO_CANALI] = campioni[i * AUDIO_CANALI];
		audio_anello[p * AUDIO_CANALI + 1] = campioni[i * AUDIO_CANALI + 1];
	}
	atomic_store_explicit(&audio_testa,
	                      (testa + fotogrammi) % AUDIO_ANELLO_FOTOGRAMMI,
	                      memory_order_release);
}

/* Quanti fotogrammi sono pronti da consumare. */
static uint32_t audio_pronti(void)
{
	uint32_t testa = atomic_load_explicit(&audio_testa, memory_order_acquire);
	uint32_t coda = atomic_load_explicit(&audio_coda, memory_order_relaxed);
	return (testa + AUDIO_ANELLO_FOTOGRAMMI - coda) % AUDIO_ANELLO_FOTOGRAMMI;
}

/* ═══ FASE 7 — lo stato dell'audio nel figlio ═══════════════════════════════
 *
 * ⛔ `son` e `acod` hanno DUE VITE DIVERSE, ed e' la stessa divisione del palco
 *    (invariante I4):
 *
 *      `son`   il SINK, e' della **sessione**: nasce col primo ascoltatore e
 *              non muore piu' finche' vive il figlio.  ⚠ Farlo sparire a ogni
 *              distacco interromperebbe il suono a chi ascolta **dentro** la
 *              sessione e lascerebbe le applicazioni gia' aperte su un
 *              dispositivo morto (`v1/remotix-c/src/suono.h`);
 *      `acod`  il CODIFICATORE, e' della **connessione**: dipende dal codec
 *              che quella connessione ha negoziato (§4.3), e si rifa' quando
 *              il codec cambia. */
static suono *son;
static audio_cod *acod;
/* Quale codec audio il padre ha chiesto: 0 = nessuno sta ascoltando. */
static uint8_t audio_codec;
static uint64_t audio_blocchi_spediti, audio_blocchi_persi;
static uint64_t audio_detto_us;

/*
 * Accende, cambia o spegne l'audio.  `codec` 0 = spegni (§6.3: 1 Opus, 2 PCM).
 *
 * ⛔ SPEGNERE FERMA LA CATTURA, NON IL SINK — invariante I4.  Il dispositivo su
 *    cui le applicazioni suonano appartiene alla sessione; il consumo del
 *    monitor appartiene a chi ascolta.
 */
/*
 * ⛔⛔⛔ LA POLITICA DI SCHEDULAZIONE **EFFETTIVA** DEL PERCORSO AUDIO — e non
 *       il permesso di chiederla.  *Riscritta il 21 agosto 2026 su misura di
 *       A8, e la riga di prima era un verde falso.*
 *
 * QUEL CHE C'ERA, e perche' era sbagliato: si leggeva `RLIMIT_RTPRIO` e, se non
 * era zero, si scriveva *«⭐ priorita' di tempo reale concessa dall'unita'»*.
 * ⛔ **Vero del rlimit, falso dell'effetto**: il rlimit dice soltanto «hai il
 * permesso di CHIEDERE», non «l'hai ottenuta».
 *
 * `[M]` A8, 21 agosto 2026, su QUESTA macchina:
 *   · il kernel rifiuta `SCHED_FIFO` a chiunque non stia nel cgroup **radice**
 *     (`CONFIG_RT_GROUP_SCHED` con cgroup v2): `chrt -f 10 /bin/true` fallisce
 *     **da root** dentro una slice e riesce nella radice.  ⇒ Ogni processo
 *     governato da systemd e' escluso, e **`LimitRTPRIO=20` e' inerte**;
 *   · fotografia dei thread del percorso audio nel figlio vivo — `remotix-suono`,
 *     `remotix-cattura`, due `data-loop.0`, due `module-rt`: **tutti a politica
 *     normale, nice 0**;
 *   · `rtkit-daemon` inattivo, gruppo `pipewire` vuoto, e PipeWire chiede
 *     `rt.prio` **88**, non 20.
 *
 * ⛔ E la ragione per cui non basta togliere la riga: senza, «non ho la
 *    priorita'» e «non ho guardato» hanno lo stesso aspetto.  ⇒ Si **guarda**,
 *    e si dichiara quel che si e' visto — `CODER.md` §4.6, *il verde non e'
 *    vero*: una riga che afferma un privilegio che nessuno usa e' peggio del
 *    silenzio, perche' e' un numero che nessuno confronta.
 *
 * ⚠ E LA CURA NON STA QUI, dichiarata per non farla cercare a nessuno: `[M]`
 *   A8, la leva che funziona su questo kernel e' **`nice`** (scoppiettii da
 *   10,4/s a 0,27/s a `nice -20`).  ⛔ Ma un arbitro indipendente — `pw-record`
 *   sullo stesso monitor — vede **gli stessi scoppiettii negli stessi istanti,
 *   e sempre un po' di piu'** ⇒ il difetto nasce **a monte di noi**, nel grafo
 *   audio della sessione, e noi lo trasportiamo fedelmente.  ⇒ La priorita' va
 *   data a **tutto il percorso audio della sessione** (`sessione.c`), non a
 *   questo processo, ed e' una decisione di prodotto.
 */
static void dichiara_priorita_audio(void)
{
	/* ⛔ I nomi dei thread che formano il percorso audio.  ⚠ `data-loop` e
	 *    `module-rt` sono di PipeWire e non nostri: e' proprio per questo che
	 *    vanno guardati — la priorita' che conta e' la LORO. */
	static const char *NOMI[] = { "data-loop", "pw-data", "pw-rt", "module-rt",
		                          "remotix-suono", "remotix-cattura" };
	struct rlimit rl;
	unsigned long tetto = 0;
	DIR *cartella;
	struct dirent *voce;
	int guardati = 0, in_tempo_reale = 0, peggior_nice = -100;
	char elenco[512];
	size_t usato = 0;

	if (getrlimit(RLIMIT_RTPRIO, &rl) == 0)
		tetto = (unsigned long) rl.rlim_cur;

	elenco[0] = '\0';
	cartella = opendir("/proc/self/task");
	while (cartella && (voce = readdir(cartella)) != NULL) {
		char percorso[128], nome[64];
		FILE *f;
		long tid;
		int politica, gentilezza;
		size_t l;

		if (voce->d_name[0] < '0' || voce->d_name[0] > '9')
			continue;
		tid = strtol(voce->d_name, NULL, 10);
		snprintf(percorso, sizeof percorso, "/proc/self/task/%ld/comm", tid);
		f = fopen(percorso, "r");
		if (!f)
			continue;
		if (!fgets(nome, sizeof nome, f)) {
			fclose(f);
			continue;
		}
		fclose(f);
		l = strlen(nome);
		while (l && (nome[l - 1] == '\n' || nome[l - 1] == ' '))
			nome[--l] = '\0';

		{
			int nostro = 0;
			for (size_t i = 0; i < sizeof NOMI / sizeof NOMI[0]; i++)
				if (strstr(nome, NOMI[i])) {
					nostro = 1;
					break;
				}
			if (!nostro)
				continue;
		}

		/* ⛔ `sched_getscheduler(tid)` e non una lettura di `/proc/.../stat`:
		 *    e' la stessa domanda fatta al kernel invece che a un testo da
		 *    scomporre, e non ha un indice di campo da sbagliare. */
		politica = sched_getscheduler((pid_t) tid);
		errno = 0;
		gentilezza = getpriority(PRIO_PROCESS, (id_t) tid);
		if (errno)
			gentilezza = 0;

		guardati++;
		if (politica == SCHED_FIFO || politica == SCHED_RR)
			in_tempo_reale++;
		else if (gentilezza > peggior_nice)
			peggior_nice = gentilezza;

		if (usato < sizeof elenco - 48)
			usato += (size_t) snprintf(elenco + usato, sizeof elenco - usato, "%s%s(%s,nice %d)",
			                           usato ? " " : "", nome,
			                           politica == SCHED_FIFO  ? "FIFO"
			                           : politica == SCHED_RR  ? "RR"
			                           : politica == SCHED_IDLE ? "idle"
			                           : politica == SCHED_BATCH ? "batch"
			                                                     : "normale",
			                           gentilezza);
	}
	if (cartella)
		closedir(cartella);

	/* ⛔ «Non ho trovato nessun thread» NON e' «tutto a posto»: e' uno
	 *    strumento cieco, e si dice con quelle parole (`CODER.md` §3.10). */
	if (guardati == 0) {
		registro_dice(REG_FIGLIO,
		              "⚠ NON HO TROVATO nessun thread del percorso audio "
		              "(cercavo data-loop, pw-data, pw-rt, module-rt, "
		              "remotix-suono, remotix-cattura): ⛔ questa NON e' la "
		              "misura «tutto a posto», e' «non ho guardato».  "
		              "RLIMIT_RTPRIO = %lu",
		              tetto);
		return;
	}

	if (in_tempo_reale == guardati)
		registro_dice(REG_FIGLIO,
		              "⭐ priorita' di tempo reale OTTENUTA: %d thread su %d del "
		              "percorso audio girano FIFO/RR (RLIMIT_RTPRIO = %lu).  %s",
		              in_tempo_reale, guardati, tetto, elenco);
	else
		registro_dice(
		    REG_FIGLIO,
		    "⛔⛔ FIFO **NON** OTTENUTO: %d thread su %d del percorso audio girano a politica "
		    "NORMALE (nice peggiore %d), e RLIMIT_RTPRIO = %lu — ⚠ il rlimit dice «puoi "
		    "CHIEDERLA», non «ce l'hai».  `[M]` 21 ago 2026: su questo kernel "
		    "`CONFIG_RT_GROUP_SCHED` con cgroup v2 rifiuta SCHED_FIFO a chiunque non stia nel "
		    "cgroup RADICE ⇒ ogni processo governato da systemd e' escluso e `LimitRTPRIO=20` "
		    "e' INERTE.  ⇒ L'audio scoppiettera' QUANDO IL DESKTOP LAVORA, e a desktop fermo "
		    "non si riproduce.  ⚠ E la cura non e' qui: l'arbitro indipendente (`pw-record` "
		    "sullo stesso monitor) sente gli stessi scoppiettii negli stessi istanti ⇒ il "
		    "difetto nasce nel grafo audio della SESSIONE, non nel nostro trasporto.  %s",
		    guardati - in_tempo_reale, guardati, peggior_nice == -100 ? 0 : peggior_nice, tetto,
		    elenco);
}

static void audio_regola_figlio(uint8_t codec)
{
	if (codec == audio_codec)
		return;

	/* Si ferma sempre prima: `suono_ascolto_ferma()` ASPETTA il thread di
	 * PipeWire, e chi torna di li' e' autorizzato a toccare quel che il
	 * richiamo usava — l'anello compreso. */
	if (audio_codec) {
		suono_ascolto_ferma(son);
		audio_cod_chiudi(acod);
		acod = NULL;
		registro_dice(REG_FIGLIO,
		              "l'audio si SPEGNE: %llu blocchi spediti, %llu persi, "
		              "%llu fotogrammi traboccati.  ⭐ Il sink resta (I4)",
		              (unsigned long long)audio_blocchi_spediti,
		              (unsigned long long)audio_blocchi_persi,
		              (unsigned long long)atomic_load(&audio_traboccati));
	}
	audio_codec = 0;

	if (!codec)
		return;

	/* ⛔ Il sink si monta UNA VOLTA SOLA per la vita del figlio. */
	if (!son) {
		son = suono_apri();
		if (!son) {
			/* ⚠ RIPIEGO DICHIARATO (`CODER.md` §4.2): il desktop continua a
			 *   funzionare senza audio, e questa riga e' la sola differenza
			 *   fra «degradato» e «rotto in silenzio».  Il registro del
			 *   perche' l'ha gia' scritto `suono_apri()`. */
			registro_dice(REG_FIGLIO,
			              "⛔ il sink dell'audio non si monta: questa sessione "
			              "resta SENZA SUONO.  ⚠ Il desktop continua — e' un "
			              "ripiego dichiarato, non un guasto taciuto");
			return;
		}
	}
	/* ⛔ Invariante I5: chi si collega trova il volume AL MASSIMO.  Si rifa' a
	 *    ogni collegamento e non solo alla creazione, perche' un cursore
	 *    lasciato in basso e' uno stato che il client non puo' vedere ne'
	 *    spiegare. */
	suono_volume_massimo(son);

	acod = audio_cod_apri(codec);
	if (!acod) {
		registro_dice(REG_FIGLIO,
		              "⛔ il codificatore audio per il codec %u non si apre: "
		              "questa sessione resta senza suono", codec);
		return;
	}

	audio_anello_azzera();
	if (!suono_ascolto_avvia(son, audio_campioni, NULL)) {
		registro_dice(REG_FIGLIO,
		              "⛔ la cattura del monitor non parte: senza suono");
		audio_cod_chiudi(acod);
		acod = NULL;
		return;
	}
	/* ⛔⛔ E SI VERIFICA DI AVERE LA PRIORITA' DI TEMPO REALE, invece di
	 *      sperarci — invariante I7: «la protezione di un difetto noto sta nel
	 *      programma, non in una riga di configurazione che si puo' perdere».
	 *
	 *      ⚠ Qui la riga di configurazione serve per forza (un rlimit lo
	 *      concede l'unita', non il codice), ⇒ quel che il programma puo' fare
	 *      e' **accorgersi che manca e dirlo**.
	 *
	 * ⛔ E' R26 di v1, `[M]` 5 agosto 2026 e ritrovata il 17: con
	 *    `RLIMIT_RTPRIO` a zero PipeWire non puo' chiedere `SCHED_FIFO`, e il
	 *    suo anello dei dati raccoglie i campioni a priorita' normale **mentre
	 *    in questo stesso processo il codificatore video si prende un core**.
	 *    Il sintomo non e' un errore: e' audio che scoppietta **quando il
	 *    desktop lavora**, e che a desktop fermo non si riproduce — cioe'
	 *    invisibile a ogni banco che guardi i byte invece del tempo. */
	dichiara_priorita_audio();

	audio_codec = codec;
	audio_blocchi_spediti = audio_blocchi_persi = 0;
	registro_dice(REG_FIGLIO,
	              "⭐ FASE 7: l'audio si ACCENDE — codec %u (%s), blocchi da %u "
	              "fotogrammi, sink nodo %u",
	              codec, codec == 1 ? "Opus" : "PCM", audio_cod_blocco(acod),
	              suono_nodo(son));
}

/*
 * Svuota l'anello, un blocco per volta, e spedisce al padre.
 *
 * ⛔ Si chiama a ogni giro del ciclo, PRIMA della parte video: la parte video
 *    esce con `continue` quando nessuno guarda, e l'audio ci finirebbe dentro
 *    per caso — cioe' una sessione con l'audio acceso e il video spento non
 *    suonerebbe, e nessuna riga direbbe perche'.
 */
static void audio_svuota(void)
{
	uint32_t blocco;
	int16_t campioni[AUDIO_BLOCCO_OPUS * AUDIO_CANALI];
	uint8_t fuori[AUDIO_FUORI_MAX];
	uint64_t traboccati;

	if (!audio_codec || !acod)
		return;
	blocco = audio_cod_blocco(acod);

	/* ⛔ Il traboccamento si legge QUI e non nel richiamo: la' non si puo'
	 *    scrivere nel registro senza rischiare i fotogrammi del desktop. */
	traboccati = atomic_exchange(&audio_traboccati, 0);
	if (traboccati) {
		/* ⭐ E la base dell'orologio si SPOSTA dei campioni persi, o gli
		 *    `istante` racconterebbero un suono continuo dove c'e' stato un
		 *    buco — e il client riordinerebbe su una bugia (§6.3). */
		audio_base_us += traboccati * 1000000u / AUDIO_FREQUENZA;
		registro_dice(REG_FIGLIO,
		              "⚠ l'anello dell'audio ha traboccato di %llu fotogrammi "
		              "(%llu ms): il ciclo non lo svuota abbastanza in fretta.  "
		              "⛔ Non e' la rete: e' qui",
		              (unsigned long long)traboccati,
		              (unsigned long long)(traboccati * 1000u / AUDIO_FREQUENZA));
	}

	while (audio_pronti() >= blocco) {
		uint32_t coda = atomic_load_explicit(&audio_coda, memory_order_relaxed);
		size_t n = 0;
		uint64_t istante;

		for (uint32_t i = 0; i < blocco; i++) {
			uint32_t p = (coda + i) % AUDIO_ANELLO_FOTOGRAMMI;
			campioni[i * AUDIO_CANALI] = audio_anello[p * AUDIO_CANALI];
			campioni[i * AUDIO_CANALI + 1] = audio_anello[p * AUDIO_CANALI + 1];
		}
		atomic_store_explicit(&audio_coda,
		                      (coda + blocco) % AUDIO_ANELLO_FOTOGRAMMI,
		                      memory_order_release);

		if (!audio_base_us)
			audio_base_us = ora_monotona_us();
		istante = audio_base_us + audio_consumati * 1000000u / AUDIO_FREQUENZA;
		audio_consumati += blocco;

		if (audio_cod_passa(acod, campioni, fuori, &n)) {
			struct corpo_blocco c;
			memset(&c, 0, sizeof c);
			c.codec = audio_codec;
			c.byte = (uint32_t)n;
			c.istante_us = istante;
			/* ⛔ Se non parte SI BUTTA e si conta: §6.3 vieta la
			 *    ritrasmissione, e un figlio che aspettasse di poter scrivere
			 *    fermerebbe la cattura del desktop. */
			if (!manda(MSG_BLOCCO, &c, sizeof c, fuori, n))
				audio_blocchi_persi++;
			else
				audio_blocchi_spediti++;
		}
	}

	/* Una riga al secondo, con dentro gli ZERO: «il ciclo non gira», «la
	 * sessione non suona» e «i blocchi non partono» devono avere tre facce
	 * diverse (`CODER.md` §3.10). */
	{
		uint64_t adesso = ora_monotona_us();
		if (adesso - audio_detto_us >= 1000000u) {
			audio_detto_us = adesso;
			registro_dettaglio(REG_FIGLIO,
			                   "audio: %llu blocchi spediti, %llu persi, "
			                   "%llu fotogrammi in attesa nell'anello — codec %u",
			                   (unsigned long long)audio_blocchi_spediti,
			                   (unsigned long long)audio_blocchi_persi,
			                   (unsigned long long)audio_pronti(), audio_codec);
		}
	}
}


static void rilievo_scrivi(const char *dir, const char *nome, const void *dati,
                           size_t byte)
{
	char percorso[512];
	FILE *fp;
	size_t scritti;

	if (!dir || !dir[0] || strcmp(dir, "-") == 0)
		return;
	snprintf(percorso, sizeof percorso, "%s/%s", dir, nome);
	fp = fopen(percorso, "wb");
	if (!fp) {
		/* ⚠ Ci scrive il FIGLIO, cioe' l'utente: una cartella del padre non e'
		 *   sua, e il rilievo non esce.  Si dice, invece di lasciare un file
		 *   che non c'e' con l'aria di un rilievo che nessuno ha chiesto. */
		registro_dice(REG_FIGLIO, "⛔ rilievo %s: %s (ci scrive l'utente, non root)",
		              percorso, strerror(errno));
		return;
	}
	scritti = fwrite(dati, 1, byte, fp);
	if (fclose(fp) != 0 || scritti != byte) {
		registro_dice(REG_FIGLIO, "⛔ rilievo %s: %zu byte su %zu", percorso,
		              scritti, byte);
		return;
	}
	registro_dice(REG_FIGLIO, "rilievo scritto: %s (%zu byte)", percorso, byte);
}

/* ------------------------------------------------------------------ *
 *  ⭐ LO SCATTO A COMANDO — `SIGUSR1` e `SIGUSR2`, 17 agosto 2026
 *
 *  Serve a UNA cosa: separare i tre imputati degli artefatti a blocchi
 *  di 64 px misurati sul video dell'utente (cattura · codificatore ·
 *  browser).  Al `SIGUSR1` il figlio chiede una CHIAVE e poi mette su
 *  disco, dallo stesso istante:
 *
 *    `scatto-ingresso.bgrx`  i pixel che il codificatore HA IN MANO
 *    `scatto-flusso.obu`     i byte che spediamo, dalla chiave in poi
 *    `scatto-uscita.bgrx`    l'ingresso dell'ULTIMO fotogramma accodato
 *
 *  ⇒ Se i blocchi stanno gia' nel BGRX, la colpa e' a MONTE del
 *    codificatore; se compaiono solo decodificando il flusso con un
 *    decodificatore diverso, e' il CODIFICATORE; se nessuno dei due li
 *    ha, resta il BROWSER.
 *
 *  ⛔ Non e' un interruttore di prodotto: scrive solo se `--rilievo` c'e',
 *     si arma una volta per segnale, e `SIGUSR2` lo chiude subito (senza,
 *     su una scena ferma si aspetterebbero i fotogrammi che non arrivano).
 * ------------------------------------------------------------------ */
#define SCATTO_FOTOGRAMMI 300

/* ⛔ E LA CARTELLA SE LA TIENE LUI, invece di leggerla dal parametro.
 *
 * `[M]` 17 agosto 2026, e il primo scatto e' andato perso cosi': nel GIRO
 * principale `codifica_e_manda()` viene chiamata con `dir_rilievo = NULL`
 * (riga del `codec_chiesto`) — la cartella vera arriva solo alla prima
 * codifica, quella dell'accensione.  ⇒ `rilievo_scrivi()` usciva in silenzio,
 * e la riga di registro diceva «ingresso 2560x962, 9850880 byte» di un file
 * che non era stato scritto: la forma peggiore, un verde che non ha guardato
 * niente (`LEZIONI.md` §1.9). */
static const char *scatto_dir = NULL;

static volatile sig_atomic_t scatto_chiesto = 0;
static volatile sig_atomic_t scatto_stop = 0;
static int scatto_stato = 0; /* 0 fermo · 1 aspetto la chiave · 2 accodo */
static int scatto_restano = 0;
static FILE *scatto_fp = NULL;
static unsigned long long scatto_quanti = 0;

static void scatto_segnale(int quale)
{
	if (quale == SIGUSR2)
		scatto_stop = 1;
	else
		scatto_chiesto = 1;
}

/* Chiude il flusso e scrive l'ultimo ingresso.  `perche` finisce nel registro,
 * cosi' un rilievo troncato non si confonde con uno finito. */
static void scatto_chiudi(const char *dir_rilievo, const CatturaFermo *fo,
                          const char *perche)
{
	if (scatto_fp) {
		fclose(scatto_fp);
		scatto_fp = NULL;
	}
	scatto_stato = 0;
	scatto_restano = 0;
	if (fo && fo->pixel)
		rilievo_scrivi(dir_rilievo, "scatto-uscita.bgrx", fo->pixel,
		               (size_t)fo->byte);
	registro_dice(REG_FIGLIO,
	              "⭐ SCATTO FINITO (%s): %llu fotogrammi in "
	              "`scatto-flusso.obu`, e `scatto-uscita.bgrx` e' l'ingresso "
	              "dell'ULTIMO di quelli",
	              perche, scatto_quanti);
}

/* ⛔ La stessa richiesta di codifica di `main.c` prima del 12 agosto 2026 —
 *    CRF 20, 10 bit chiesti su una sorgente a 8 (promozione DICHIARATA dal
 *    codificatore), BGRx, chiavi a richiesta.  ⚠ Non e' stata «riscritta»: e'
 *    stata SPOSTATA, perche' e' il figlio che ha i pixel.
 *
 * ⛔⭐ E `chiavi_ogni = 0` RESTA ZERO, cioe' GOP infinito, ed e' una scelta —
 *     non una dimenticanza.  `RCP.md` §5.2 vuole una chiave in tre casi soli:
 *     il primo dopo `SESSIONE`, il primo alla misura nuova, e quando il client
 *     la chiede.  Chiavi periodiche sarebbero banda spesa per un'assicurazione
 *     che il protocollo compra gia' — e `SPECIFICHE.md` §8.2 dice che la banda
 *     si spende sulla qualita', non sulla prudenza.
 *
 *     ⛔ MA IL PREZZO E' CHE LA CUCITURA DEVE ESISTERE: con GOP infinito e
 *        senza nessuno che chiami `codificatore_chiedi_chiave()`, dopo la prima
 *        chiave non ne arriva **mai piu' una**, e un client che perde un delta
 *        resta con lo schermo sfasciato per sempre.  Il chiamante adesso c'e' —
 *        `MSG_VIDEO` con `chiave = 1`, e la strada intera e' nel riquadro di
 *        `wt_video_gancio()`. */
/* ⛔⭐ IL NODO DI RENDERING E L'ENTRYPOINT — DICHIARATI QUI, NON INDOVINATI E
 *     NON IN UNA RIGA DI CONFIGURAZIONE.
 *
 * `CODER.md` invariante I7: *«la protezione di un difetto noto sta nel
 * programma, non in una riga di configurazione che si puo' perdere»*.  Un nodo
 * preso da una variabile d'ambiente sparirebbe il giorno in cui qualcuno accende
 * il servizio a mano, e il sintomo sarebbe **il codificatore in software con la
 * stessa etichetta**: due ritmi diversi sotto lo stesso nome.
 *
 * ⭐ E i due numeri stanno accanto alla riga perche' questa e' una SCELTA, e una
 *    scelta senza il conto accanto e' una preferenza:
 *
 *   `[M]` 13 agosto 2026, 1920×1080 10 bit, 120 fotogrammi, tutti a 20 Mbit/s,
 *   fotogrammi in uscita CONTATI con `ffprobe`:
 *
 *     /dev/dri/renderD128   Intel iHD 25.2.3    EncSliceLP   ⭐ 3,16-3,24 ms
 *     /dev/dri/renderD129   AMD radeonsi 25.0.7 EncSlice        3,43 ms
 *     libsvtav1 preset 10   (in software)                      22,23 ms
 *
 * ⚠ **E i due nodi NON sono due volti della stessa scheda**: `renderD128` e'
 *   l'iGPU Intel (0000:00:02.0, i915), `renderD129` e' una **AMD Radeon RX
 *   6800** discreta (0000:03:00.0, amdgpu).  Chi leggesse «due nodi» come «due
 *   code della stessa GPU» sceglierebbe a caso fra due macchine diverse.
 *
 * ⛔ **Perche' l'Intel e non l'AMD, che ha l'entrypoint PIENO**: e' piu' veloce
 *    `[M]`, e soprattutto e' **la scheda che compone il desktop** — cioe' quella
 *    su cui i fotogrammi stanno gia' quando la fase 8 togliera' la copia.
 *    ⚠ Il prezzo si dichiara e non si nasconde: `EncSliceLP` e' la codifica **a
 *    bassa potenza**, non e' equivalente alla piena, e il confronto di qualita'
 *    fra le due a parita' di bitrate `[?]` **non e' stato misurato**.
 */
#define NODO_RENDERING "/dev/dri/renderD128"
#define POTENZA_RENDERING CODIFICATORE_POTENZA_BASSA
/* ⛔ Il QP costante, e NON e' «il CRF 20 di prima»: sono due grandezze diverse
 *    (vedi `ModoQualita` in `codificatore.h`).  ⚠ Il valore e' di comodo
 *    dichiarato — il punto di lavoro fra qualita' e banda e' la fase 9, come il
 *    preset di x265. */
#define QP_HARDWARE 26
/* ⛔⭐ E IL CRF DEL RIPIEGO IN SOFTWARE ADESSO HA UN NOME — 23 agosto 2026.
 *
 *     Era il letterale `20` dentro `codificatore_di()`, e finche' nessuno lo
 *     scriveva nel registro non dava fastidio a nessuno.  ⛔ Ma la riga dei
 *     parametri in vigore (alla nascita, piu' giu') lo DEVE dire, e un numero
 *     scritto in due posti e' un numero che prima o poi ne dice due: il
 *     registro direbbe `20` mentre il codificatore chiede altro, ed e' la
 *     forma peggiore — un numero **falso** che sembra misurato.
 * ⚠ E NON e' «il QP con un altro nome»: CRF e QP sono due grandezze diverse
 *   (vedi `ModoQualita`), e i due valori non si confrontano fra loro. */
#define CRF_SOFTWARE 20

/* ⛔ Il nome dell'entrypoint si STAMPA da `POTENZA_RENDERING`, non si scrive a
 *    mano nella riga del registro: e' la stessa forma E2 del difetto del 22
 *    agosto («hevc_vaapi» scritto dentro le virgolette mentre a fallire era
 *    `h264_vaapi») — una riga giusta col nome sbagliato accanto manda la caccia
 *    dalla parte sbagliata.  ⚠ `NON_DICHIARATA` c'e' perche' e' lo zero, cioe'
 *    quel che si ottiene senza scriverlo: se comparisse nel registro sarebbe
 *    gia' la diagnosi. */
static const char *potenza_nome(PotenzaEntrypoint p)
{
	switch (p) {
	case CODIFICATORE_POTENZA_PIENA:
		return "EncSlice (piena)";
	case CODIFICATORE_POTENZA_BASSA:
		return "EncSliceLP (bassa potenza)";
	default:
		return "NON DICHIARATA (⛔ e cosi' non si apre niente)";
	}
}

/* ⛔⭐⭐ `RCP.md` §4.3 (riga 701) — IL LIVELLO PRODOTTO, DETTO NELL'ALFABETO IN
 *      CUI IL CLIENT LO CHIEDE.
 *
 *      §4.3: *«`video.livello`: il livello massimo che sa decodificare, es.
 *      `5.1`.  ⛔ Il server DEVE emettere un flusso di livello non superiore, e
 *      non lo indovina: un livello dichiarato troppo basso non da' un errore di
 *      rete, fa RIFIUTARE LA CONFIGURAZIONE DAL DECODIFICATORE e il sintomo e'
 *      "il browser non apre il flusso" (rilievo O12)»*.
 *
 * ⛔ E IL CONFRONTO NON SI PUO' FARE SUL NUMERO CRUDO, perche' i tre codec lo
 *    scrivono in tre alfabeti diversi — ed e' il modo esatto in cui una riga di
 *    registro puo' essere vera e illeggibile insieme:
 *
 *      H.264   `level_idc`         = maggiore*10 + minore   ⇒ 5.1 e' **51**
 *      HEVC    `general_level_idc` = (maggiore*10+minore)*3 ⇒ 5.1 e' **153**
 *      AV1     `seq_level_idx`     = (maggiore−2)*4+minore  ⇒ 5.1 e' **13**
 *
 *    ⇒ «livello 51» e «livello 153» sono lo STESSO livello, e chi legge il
 *      registro accanto a un `video.livello=5.1` deve poterlo vedere senza una
 *      tabella in mano.  Qui esce in DECIMI, che e' la forma di §4.3 e la
 *      stessa in cui `rcp.c` legge la capacita' del client.
 *
 * ⚠ Restituisce 0 quando non sa tradurre — e lo zero NON e' «basso»: e' «non
 *   lo so», e la riga che lo stampa lo scrive con quelle parole.  ⚠ H.264 ha
 *   anche il livello «1b», che `level_idc` non distingue da 1.1 senza guardare
 *   un altro campo: e' fuori da qualunque tela che questo prodotto serva, e si
 *   dichiara qui invece di far finta che non esista. */
static unsigned livello_in_decimi(CodecVideo codec, int livello_flusso)
{
	if (livello_flusso <= 0)
		return 0;
	switch (codec) {
	case CODIFICATORE_H264:
		return (unsigned)livello_flusso;
	case CODIFICATORE_HEVC:
		return (unsigned)livello_flusso / 3u;
	case CODIFICATORE_AV1:
		return ((unsigned)livello_flusso / 4u + 2u) * 10u
		       + (unsigned)livello_flusso % 4u;
	default:
		return 0;
	}
}

/* ⛔ Il numero di §6.2 e il codec del codificatore sono due alfabeti diversi, e
 *    la traduzione sta in UNA funzione: il giorno in cui divergessero, a
 *    divergere sarebbe una riga sola.  ⚠ Un numero ignoto NON diventa un codec
 *    «per continuare»: si dichiara e non si codifica niente. */
static CodecVideo codec_del_numero(uint8_t numero)
{
	switch (numero) {
	case 1:
		return CODIFICATORE_HEVC;
	case 2:
		return CODIFICATORE_AV1;
	case 3:
		return CODIFICATORE_H264;
	default:
		registro_dice(REG_FIGLIO,
		              "⛔ numero di codec ignoto (%u): §6.2 ne conosce tre, e non "
		              "ne invento un quarto",
		              numero);
		return (CodecVideo) 0;
	}
}

static Codificatore *codificatore_di(CodecVideo codec, uint8_t indice,
                                     uint32_t tela_l, uint32_t tela_a)
{
	CodificatoreRichiesta r;
	char errore[256];
	uint8_t prof = profondita_chiesta;

	if (indice >= CODEC_MAX)
		return NULL;

	/* ⛔⭐ SENZA PROFONDITA' NEGOZIATA NON SI APRE NIENTE, e non e' prudenza:
	 *     aprirne uno «tanto per» vorrebbe dire scegliere noi quel che §4.3 fa
	 *     scegliere al padre — cioe' rimettere il letterale con un altro nome.
	 * ⚠ Non ci si arriva nella pratica: `MSG_VIDEO` porta i due numeri
	 *   insieme, e il ciclo non cattura finche' non e' arrivato.  La riga c'e'
	 *   perche' il giorno in cui ci si arrivasse lo dicesse qualcuno. */
	if (prof != 8 && prof != 10) {
		registro_dice(REG_FIGLIO,
		              "⛔ nessun codificatore: il padre non ha detto quale "
		              "profondita' e' stata negoziata (§4.3, ho «%u»).  ⚠ NON ne "
		              "scelgo una io: sarebbe la bugia del 17 agosto rimessa a "
		              "mano",
		              prof);
		return NULL;
	}

	/* ⛔⭐ E SE LA PROFONDITA' E' CAMBIATA, IL CODIFICATORE SI RIFA'.
	 *
	 *     Il palco sopravvive al client (I4): il secondo che si collega puo'
	 *     aver negoziato 8 dove il primo aveva 10.  ⚠ Tenendo quello vecchio, il
	 *     flusso resterebbe alla profondita' del PRIMO e il secondo vedrebbe
	 *     artefatti — cioe' lo stesso difetto di stasera, con un'altra causa.
	 * ⛔ E il prossimo fotogramma dev'essere una CHIAVE: un codificatore nuovo
	 *    non ha il passato del flusso (§5.2). */
	if (codif[indice] && codif_prof[indice] != prof) {
		registro_dice(REG_FIGLIO,
		              "⭐ la profondita' negoziata e' cambiata (%u → %u): rifaccio "
		              "il codificatore %u, e il prossimo fotogramma sara' una "
		              "CHIAVE (§5.2)",
		              codif_prof[indice], prof, indice);
		codificatore_libera(codif[indice]);
		codif[indice] = NULL;
		codif_prof[indice] = 0;
		debito_chiave[indice] = true;
	}
	/* ⛔⭐ E LO STESSO PER IL LIVELLO (§4.3 riga 701) — 23 agosto 2026.  Il
	 *     livello si imposta all'APERTURA del codificatore e finisce nell'SPS:
	 *     cambiarlo a codificatore aperto non lo cambia nel flusso.  ⇒ Il
	 *     secondo client che dichiara un tetto diverso dal primo si porta
	 *     dietro un codificatore nuovo, o vedrebbe il tetto del PRIMO — e il
	 *     sintomo, di nuovo, sarebbe uno schermo nero senza una riga. */
	if (codif[indice] && codif_liv[indice] != livello_chiesto_x10) {
		registro_dice(REG_FIGLIO,
		              "⭐ §4.3: il tetto di livello e' cambiato (%u.%u → %u.%u, "
		              "0.0 = nessun tetto): rifaccio il codificatore %u, e il "
		              "prossimo fotogramma sara' una CHIAVE (§5.2)",
		              codif_liv[indice] / 10u, codif_liv[indice] % 10u,
		              livello_chiesto_x10 / 10u, livello_chiesto_x10 % 10u,
		              indice);
		codificatore_libera(codif[indice]);
		codif[indice] = NULL;
		codif_prof[indice] = 0;
		codif_liv[indice] = 0;
		debito_chiave[indice] = true;
	}
	if (codif[indice])
		return codif[indice];

	/* ⛔⭐ E NON SI RIPROVA A OGNI FOTOGRAMMA — vedi `codif_riprova_ms`.  ⚠ Il
	 *    silenzio qui e' voluto e limitato: la riga che spiega il fallimento
	 *    l'ha gia' scritta il tentativo precedente, e ripeterla sessanta volte
	 *    al secondo e' il difetto che questa attesa esiste per non avere. */
	if (codif_riprova_ms[indice] && registro_ora_ms() < codif_riprova_ms[indice])
		return NULL;

	memset(&r, 0, sizeof r);
	r.codec = codec;
	r.componente = NULL;
	r.larghezza = tela_l;
	r.altezza = tela_a;
	/* ⛔ La cadenza e' UNA, e la stessa che si chiede alla cattura. */
	r.fotogrammi_al_secondo = MOVIMENTO_FPS;
	r.modo = CODIFICATORE_QUALITA_CRF;
	r.qualita = CRF_SOFTWARE;
	/* ⛔⭐⭐ QUI C'ERA `10`, SCRITTO A MANO — ed e' il difetto misurato il 17
	 *      agosto 2026 su Firefox: si dichiarava 8 in `ECCOMI` (§4.3) e si
	 *      mandavano 10 sul filo.  ⇒ Adesso e' quel che il padre ha negoziato,
	 *      e la riga sopra rifiuta di aprire se non lo sa. */
	r.profondita = prof;
	/* ⛔⭐⭐ IL TETTO DI §4.3, E SI CHIEDE PRIMA INVECE DI SCOPRIRLO DOPO — 23
	 *      agosto 2026.  Fino a stasera nessuno lo chiedeva: il codificatore
	 *      sceglieva il livello da misura e cadenza, e a 3840x2160 a 60/s
	 *      sceglieva **5.2** mentre il client aveva dichiarato 5.1.
	 *
	 * ⛔ LA PREVISIONE FALSIFICABILE, che e' il punto di tutta la cura:
	 *      a 3840x2160 con `video.livello=5.1` imposto, l'SPS DEVE portare
	 *      `level_idc = 51` (H.264) / `general_level_idc = 153` (HEVC), e la
	 *      riga «§4.3 — LIVELLO» qui sotto deve dire **5.1 ≤ 5.1 ✓**.
	 *      ⚠ Se il codificatore NON avesse ubbidito, quella riga direbbe
	 *      **5.2 > 5.1** con un ⛔ davanti — cioe' il difetto di stasera,
	 *      identico, ma nominato da una riga invece che da uno schermo nero.
	 *      ⭐ E' R31 nella sua forma piu' pura: si chiede per nome, e si
	 *      verifica rileggendo i byte prodotti.
	 *
	 * ⚠⚠ E CHE COSA COSTA, detto e non nascosto: un livello e' anche un tetto
	 *     su PIXEL e CADENZA.  H.264 5.1 concede `MaxMBPS = 983 040`; a
	 *     3840x2160 un fotogramma sono 32 400 macroblocchi ⇒ **~30 fot/s** di
	 *     tetto, mentre `MOVIMENTO_FPS` ne chiede 60 (5.2 ne concederebbe 64).
	 *     ⛔ Imporre il livello NON abbassa la cadenza — il codificatore
	 *     stampa 51 nell'SPS e continua a 60 — quindi quel che si vede non
	 *     cambia (e per questo la cura non e' sotto I6).  ⚠ Ma il flusso
	 *     dichiara un livello i cui limiti di cadenza NON rispetta: e'
	 *     esattamente quel che il client ha CHIESTO dichiarando 5.1 a 4K, ed e'
	 *     una cosa da scrivere, non da nascondere.  ⇒ L'alternativa —
	 *     dimezzare la cadenza a 30 — cambierebbe quel che si vede, e quella
	 *     sì sarebbe da interruttore: non si fa qui.
	 *
	 * ⚠ `0` = il client non ha dichiarato niente (§4.3 non lo obbliga): nessun
	 *   tetto, il codificatore sceglie, e il livello scelto si SCRIVE lo
	 *   stesso — chi legge il registro deve sapere che cosa e' uscito. */
	r.livello_x10 = (int) livello_chiesto_x10;
	r.formato = CODIFICATORE_PIXEL_BGRX;
	r.chiavi_ogni = 0;

	/*
	 * ⭐⭐ HEVC SI PROVA PRIMA IN HARDWARE — e AV1 no, e la ragione e' MISURATA.
	 *
	 * `[M]` 13 agosto 2026: `av1_vaapi` **compare** nell'elenco di ffmpeg e
	 * all'uso esce **218**, *«No usable encoding profile found»*, 3 giri su 3;
	 * `vainfo` da' AV1 in **sola decodifica** su tutti e due i nodi.  ⇒ Provarlo
	 * in hardware sarebbe un giro speso per un errore gia' noto.
	 *
	 * ⛔ E il ripiego **si dichiara** (`CODER.md` §4.2): un codificatore in
	 *    software con la stessa etichetta di uno in hardware darebbe due ritmi
	 *    sotto lo stesso nome, che e' la forma E2.  Qui il registro dice quale
	 *    dei due e' vivo, e `codificatore_nome()` porta il nodo dentro il nome.
	 */
	/* ⭐⭐ E DAL 20 AGOSTO ANCHE H.264 SI PROVA IN HARDWARE, per la stessa
	 *     ragione di HEVC e con la stessa misura accanto: `[M]` 13 agosto 2026,
	 *     `h264_vaapi` **3,11-3,16 ms** per fotogramma a 1920x1080 10 bit, 20
	 *     Mbit/s, 120 fotogrammi su 120 — il piu' veloce dei quattro provati.
	 * ⛔ E `libx264` resta il ripiego DICHIARATO, non la strada. */
	if (codec == CODIFICATORE_HEVC || codec == CODIFICATORE_H264) {
		CodificatoreRichiesta hw = r;
		hw.componente = (codec == CODIFICATORE_H264) ? "h264_vaapi" : "hevc_vaapi";
		hw.nodo_rendering = NODO_RENDERING;
		hw.potenza = POTENZA_RENDERING;
		/* ⛔ In hardware non c'e' il CRF: si chiede QP, e si scrive QP. */
		hw.modo = CODIFICATORE_QUALITA_QP;
		hw.qualita = QP_HARDWARE;
		codif[indice] = codificatore_nuovo(&hw, errore, sizeof errore);
		if (!codif[indice])
			/* ⛔⭐ E I DUE NOMI SI STAMPANO, NON SI SCRIVONO A MANO — difetto
			 *     trovato refutando, 22 agosto 2026 (fase 8).  Fino a qui la
			 *     riga diceva **«hevc_vaapi»** e **«libx265»** scritti dentro le
			 *     virgolette: dal 20 agosto questo ramo serve ANCHE H.264, e
			 *     quando a non aprirsi era `h264_vaapi` il registro accusava un
			 *     codificatore che nessuno aveva chiesto e nominava un ripiego
			 *     che non sarebbe stato usato.  ⇒ Una riga col numero giusto e
			 *     **la parola sbagliata accanto**, che e' la forma che manda la
			 *     caccia dalla parte sbagliata (`LEZIONI.md` §1.20). */
			registro_dice(REG_FIGLIO,
			              "⚠ RIPIEGO DICHIARATO: «%s» su %s non si e' "
			              "aperto (%s) ⇒ si scende su «%s» IN SOFTWARE, che sul "
			              "banco costa ~22 ms per fotogramma contro ~3.  ⛔ Non e' "
			              "un dettaglio del registro: e' il tratto piu' grosso "
			              "dei 39 ms della codifica",
			              hw.componente, NODO_RENDERING, errore,
			              codificatore_ripiego_software(codec));
	}

	if (!codif[indice])
		codif[indice] = codificatore_nuovo(&r, errore, sizeof errore);
	if (codif[indice]) {
		codif_prof[indice] = prof;
		codif_liv[indice] = livello_chiesto_x10;
	}
	if (!codif[indice]) {
		/* ⛔ L'attesa cresce, e la riga lo DICE: senza, questo ramo scriveva il
		 *    registro a raffica e bruciava un nucleo — la stessa forma dei 30,8
		 *    GB del 14 agosto, in un altro punto del ciclo. */
		codif_attesa_ms[indice] = codif_attesa_ms[indice]
		                              ? codif_attesa_ms[indice] * 2
		                              : CODIF_RIPROVA_MIN_MS;
		if (codif_attesa_ms[indice] > CODIF_RIPROVA_MAX_MS)
			codif_attesa_ms[indice] = CODIF_RIPROVA_MAX_MS;
		codif_riprova_ms[indice] = registro_ora_ms() + codif_attesa_ms[indice];
		registro_dice(REG_FIGLIO,
		              "⛔ niente video per il codec %d: %s.  ⚠ Riprovo fra %llu "
		              "ms — non a ogni fotogramma, o sarebbero sessanta contesti "
		              "aperti e chiusi al secondo",
		              (int)codec, errore,
		              (unsigned long long)codif_attesa_ms[indice]);
		return NULL;
	}
	/* ⭐ Riuscito: l'attesa si azzera, o la prossima caduta partirebbe dal fondo
	 *    di quella di prima. */
	codif_riprova_ms[indice] = 0;
	codif_attesa_ms[indice] = 0;
	registro_dice(REG_FIGLIO,
	              "⭐ FASE 3: codificatore %d APERTO e TENUTO VIVO fra un "
	              "fotogramma e l'altro, %ux%u a %d/s — senza questo la "
	              "predizione non esisterebbe e ogni fotogramma sarebbe una "
	              "chiave",
	              (int)codec, tela_l, tela_a, MOVIMENTO_FPS);
	return codif[indice];
}

static void codificatori_libera(void)
{
	for (uint8_t i = 0; i < CODEC_MAX; i++) {
		if (!codif[i])
			continue;
		codificatore_libera(codif[i]);
		codif[i] = NULL;
	}
}

/* ⛔⭐ QUALE ISTANTE FINISCE NEI 28 BYTE, E DA DOVE VIENE — il punto 7, deciso
 *     e MISURATO invece che dedotto.
 *
 *     §6.2 dice «microsecondi dell'orologio **monotono del server** alla
 *     cattura».  Le due sorgenti possibili sono:
 *
 *       a) `CLOCK_MONOTONIC` letto da NOI **dopo** che `cattura_prendi()` e'
 *          tornata — quel che faceva la fase 2.  ⚠ Non e' l'istante della
 *          cattura: e' l'istante in cui ce ne siamo accorti, e ci sta dentro
 *          tutta l'attesa nel posto di scambio;
 *       b) il `pts` che PipeWire attacca al fotogramma (`spa_meta_header`), che
 *          e' l'istante vero — se e' lo stesso orologio.
 *
 *     ⛔ «Se» non e' una parola che si scrive in una decisione (`LEZIONI.md`
 *        §2.3-quater): qui si GUARDA.  Alla prima presa si confrontano il `pts`
 *        e il nostro `CLOCK_MONOTONIC`; se distano meno di un secondo sono lo
 *        stesso orologio e si prende il `pts`, altrimenti si prende il nostro e
 *        **si scrive che si e' ripiegato** (`CODER.md` §4.2).
 *
 *     ⚠ L'anello del ritardo dello step 5 si appoggia a questo numero: qui c'e'
 *       la riga che dice quale dei due sta leggendo. */
static uint64_t istante_del_fotogramma(const CatturaFermo *fo, uint64_t nostro_us)
{
	uint64_t pts_us;

	if (!fo->seq_nota || fo->pts <= 0) {
		if (pts_e_monotono != 0) {
			pts_e_monotono = 0;
			registro_dice(REG_FIGLIO,
			              "⚠ il fotogramma non porta un `pts` (seq_nota %d, pts "
			              "%lld): l'istante dei 28 byte e' il NOSTRO "
			              "CLOCK_MONOTONIC letto dopo la presa — ripiego "
			              "dichiarato, e ci sta dentro l'attesa nel posto di "
			              "scambio",
			              (int)fo->seq_nota, (long long)fo->pts);
		}
		return nostro_us;
	}
	pts_us = (uint64_t)fo->pts / 1000u;
	if (pts_e_monotono < 0) {
		uint64_t scarto = pts_us > nostro_us ? pts_us - nostro_us
		                                     : nostro_us - pts_us;
		pts_e_monotono = scarto < 1000000u ? 1 : 0;
		registro_dice(REG_FIGLIO,
		              pts_e_monotono
		                  ? "⭐ MISURATO: il `pts` di Mutter e' lo stesso "
		                    "CLOCK_MONOTONIC nostro (scarto %llu us) ⇒ nei 28 "
		                    "byte di §6.2 finisce l'istante VERO della cattura, "
		                    "non quello in cui ce ne siamo accorti"
		                  : "⚠ MISURATO: il `pts` di Mutter NON e' il nostro "
		                    "CLOCK_MONOTONIC (scarto %llu us, oltre il secondo) "
		                    "⇒ nei 28 byte finisce il NOSTRO orologio letto dopo "
		                    "la presa.  Ripiego dichiarato (CODER.md §4.2): "
		                    "l'anello del ritardo ci legge dentro anche l'attesa "
		                    "nel posto di scambio",
		              (unsigned long long)scarto);
	}
	return pts_e_monotono ? pts_us : nostro_us;
}

/* ═══════════════════════════════════════════════════════════════════════════
 * ⭐⭐ FASE 8 — LA SCOMPOSIZIONE DEL TRATTO `cattura → primo byte`
 *
 * ⛔ IL FATTO CHE LA FA NASCERE, e va detto perche' e' l'unica ragione per cui
 *    questo codice esiste: `[M]` fase 4, quel tratto vale **30,37 ms**, e i tre
 *    tempi che il codificatore gia' dichiarava — conversione **5,6**,
 *    caricamento **2,9**, codifica **5,3** — ne spiegano **13,8**.
 *    ⇒ **~16 ms non avevano un proprietario.**  Un margine senza nome non si
 *    cura: **prima si strumenta, poi si cura**, o la cura nasce senza un «prima».
 *
 * ⛔⛔ E LA SCOMPOSIZIONE NON DEVE AVERE BUCHI, che e' precisamente la
 *      proprieta' per cui quella della fase 4 valeva qualcosa (somma dei tratti
 *      139,08 contro un totale di 139,40: scarto **0,32 ms**).  ⇒ Le voci sono
 *      disgiunte e in fila, e l'ultima e' `resto`: quel che il totale ha in piu'
 *      della somma delle altre.  Un `resto` che cresce e' un pezzo di tratto che
 *      ancora nessuno guarda — e si vede subito, invece di sparire nella media.
 *
 *      pts di Mutter
 *        │  produttore   Mutter+PipeWire fino alla nostra richiamata
 *        │  allocazione  la g_malloc del posto (0 se il buffer si riusa)
 *        │  copia        la memcpy dentro la richiamata di tempo reale
 *      arrivo nel posto
 *        │  nel posto    ⭐ ATTESA: il fotogramma invecchia finche' il ciclo
 *        │               non torna a chiederlo.  ⛔ Non e' lavoro
 *      presa
 *        │  misura       `misura_i_pixel()`: DIAGNOSTICA, ogni pixel, ogni giro
 *        │  conversione  swscale                       (dal codificatore)
 *        │  caricamento  memoria di sistema → GPU      (dal codificatore)
 *        │  codifica     la chiamata al codificatore   (dal codificatore)
 *        │  spedizione   i pezzi verso il padre
 *      primo byte fuori
 *
 * ⚠ E IL CONFINE VA DICHIARATO: qui il tratto finisce **quando i byte sono
 *   partiti verso il padre**, non quando arrivano in pagina.  Il numero della
 *   fase 4 e' misurato dal client; questo e' il pezzo di quello che sta dentro
 *   il figlio, ed e' l'unico che questo processo puo' vedere senza dedurre.
 *
 * ⛔ E SI DICONO LE MEDIANE, non le medie: un fotogramma che prende un guasto di
 *    pagina o una preemption sposta la media e non la mediana, e la fase 4 le
 *    mediane le aveva.  ⚠ Il **massimo** si dice accanto, perche' e' l'unico
 *    posto in cui quei colpi si vedono ancora.
 * ═══════════════════════════════════════════════════════════════════════════ */

#define TRATTI_VOCI 10
#define TRATTI_CAMPIONI 512

/* L'ordine e' quello del riquadro: e' anche l'ordine in cui si stampano. */
static const char *const tratti_nomi[TRATTI_VOCI] = {
	"produttore", "allocazione", "copia",     "nel posto", "misura",
	"conversione", "caricamento", "codifica", "spedizione", "resto"
};
static uint32_t tratti_campione[TRATTI_CAMPIONI][TRATTI_VOCI];
static uint32_t tratti_totale[TRATTI_CAMPIONI];
static unsigned tratti_quanti; /* quanti slot sono pieni (si ferma al tetto) */
static unsigned tratti_prossimo;
static uint64_t tratti_visti;  /* quanti fotogrammi in tutto */
static uint64_t tratti_detto_us;
/* ⛔ Quanti fotogrammi hanno dovuto rinunciare al `pts` di Mutter: senza questo
 *    numero la voce «produttore» sarebbe una media fra due grandezze diverse. */
static uint64_t tratti_senza_pts;

static int tratti_confronta(const void *a, const void *b)
{
	uint32_t x = *(const uint32_t *)a, y = *(const uint32_t *)b;
	return x < y ? -1 : (x > y ? 1 : 0);
}

/* La mediana di una voce sul campione tenuto.  ⚠ Si copia prima di ordinare: il
 * campione e' un anello e ordinarlo sul posto lo distruggerebbe. */
static uint32_t tratti_mediana(int voce, uint32_t *massimo)
{
	uint32_t copia[TRATTI_CAMPIONI];
	unsigned i, n = tratti_quanti;

	if (massimo)
		*massimo = 0;
	if (!n)
		return 0;
	for (i = 0; i < n; i++) {
		copia[i] = voce < 0 ? tratti_totale[i] : tratti_campione[i][voce];
		if (massimo && copia[i] > *massimo)
			*massimo = copia[i];
	}
	qsort(copia, n, sizeof copia[0], tratti_confronta);
	return copia[n / 2];
}

/*
 * Registra un fotogramma nella scomposizione e, una volta al secondo, la dice.
 *
 * ⚠ Una riga per fotogramma renderebbe illeggibile il registro proprio mentre
 *   serve — e' la stessa ragione per cui il resto del ciclo parla una volta al
 *   secondo (`figlio.c`, il conto del ciclo).
 */
static void tratti_conta(const CatturaFermo *fo, const CodificatoreFotogramma *fg,
                         uint64_t us_spedizione, uint64_t us_fine)
{
	uint32_t *v = tratti_campione[tratti_prossimo];
	uint64_t pts_us, inizio, somma = 0;
	uint64_t totale;
	int i;

	/* ⛔ Senza il `pts` di Mutter il tratto non ha un inizio VERO: si parte
	 *    dall'arrivo nel posto e la voce «produttore» resta a zero, che e' un
	 *    vuoto dichiarato e non uno zero misurato. */
	if (pts_e_monotono == 1 && fo->seq_nota && fo->pts > 0) {
		pts_us = (uint64_t)fo->pts / 1000u;
		inizio = pts_us;
	} else {
		tratti_senza_pts++;
		inizio = fo->us_arrivo > (fo->us_copia + fo->us_allocazione)
		             ? fo->us_arrivo - fo->us_copia - fo->us_allocazione
		             : fo->us_arrivo;
	}
	if (us_fine <= inizio)
		return; /* orologi che non si sottraggono: non si inventa un numero */
	totale = us_fine - inizio;

	memset(v, 0, sizeof tratti_campione[0]);
	/* «produttore» = da quando Mutter dice di aver catturato a quando la nostra
	 *  richiamata comincia a copiare.  ⛔ La copia e l'allocazione stanno DENTRO
	 *  l'intervallo pts→arrivo, e si tolgono, o si conterebbero due volte. */
	{
		uint64_t fino_a_copia = fo->us_arrivo > (fo->us_copia + fo->us_allocazione)
		                            ? fo->us_arrivo - fo->us_copia - fo->us_allocazione
		                            : fo->us_arrivo;
		v[0] = fino_a_copia > inizio ? (uint32_t)(fino_a_copia - inizio) : 0u;
	}
	v[1] = (uint32_t)fo->us_allocazione;
	v[2] = (uint32_t)fo->us_copia;
	v[3] = (uint32_t)fo->us_nel_posto;
	v[4] = (uint32_t)fo->us_misura;
	v[5] = (uint32_t)fg->us_conversione;
	v[6] = (uint32_t)fg->us_caricamento;
	v[7] = (uint32_t)fg->us_codifica;
	v[8] = (uint32_t)us_spedizione;
	for (i = 0; i < TRATTI_VOCI - 1; i++)
		somma += v[i];
	v[9] = somma < totale ? (uint32_t)(totale - somma) : 0u;
	tratti_totale[tratti_prossimo] = totale > 0xffffffffu ? 0xffffffffu : (uint32_t)totale;

	tratti_prossimo = (tratti_prossimo + 1) % TRATTI_CAMPIONI;
	if (tratti_quanti < TRATTI_CAMPIONI)
		tratti_quanti++;
	tratti_visti++;

	if (us_fine - tratti_detto_us < 1000000u)
		return;
	tratti_detto_us = us_fine;
	{
		char riga[512];
		size_t off = 0;
		uint32_t massimo_totale = 0;
		uint32_t mediana_totale = tratti_mediana(-1, &massimo_totale);

		for (i = 0; i < TRATTI_VOCI; i++) {
			uint32_t mx = 0, md = tratti_mediana(i, &mx);
			int scritto = snprintf(riga + off, sizeof riga - off, "%s%s %.2f (max %.2f)",
			                       i ? " · " : "", tratti_nomi[i], md / 1000.0,
			                       mx / 1000.0);
			if (scritto < 0 || (size_t)scritto >= sizeof riga - off)
				break;
			off += (size_t)scritto;
		}
		registro_dice(REG_FIGLIO,
		              "⭐ TRATTO cattura → byte fuori: mediana %.2f ms (max %.2f) su %u "
		              "fotogrammi del campione, %llu in tutto — %s%s",
		              mediana_totale / 1000.0, massimo_totale / 1000.0, tratti_quanti,
		              (unsigned long long)tratti_visti, riga,
		              tratti_senza_pts
		                  ? "  ⚠ e qualche fotogramma e' senza `pts` di Mutter: "
		                    "per quelli «produttore» e' un vuoto, non uno zero"
		                  : "");
	}
}

/* Codifica un fotogramma con il codificatore VIVO di quel codec e lo manda al
 * padre.  ⛔ `chiave` non si suppone: e' quel che il codificatore ha letto dal
 * flusso (`fg.chiave`), e §6.2 lo scrive nel campo `tipo`. */
static bool codifica_e_manda(const CatturaFermo *fo, CodecVideo codec,
                             uint8_t numero, const char *dir_rilievo,
                             const char *nome_file, uint64_t istante_us,
                             uint32_t tela_l, uint32_t tela_a, uint32_t input)
{
	CodificatoreFotogramma fg;
	Codificatore *cod;
	const CodificatoreConfessione *c;

	cod = codificatore_di(codec, numero, tela_l, tela_a);
	if (!cod)
		return false;

	/* ⛔ §5.2 — E QUI LA CHIAVE CHIESTA DIVENTA UNA CHIAVE VERA.  ⚠ Si chiede
	 *    PRIMA di comprimere: dopo sarebbe tardi di un fotogramma, e quel
	 *    fotogramma e' proprio quello che il client sta aspettando. */
	if (numero < CODEC_MAX && debito_chiave[numero]) {
		codificatore_chiedi_chiave(cod);
		debito_chiave[numero] = false;
	}

	/* ⛔⛔ E QUI SI GUARDA SE IL CODIFICATORE E' DAVVERO IN HARDWARE — chiesto al
	 *     COMPONENTE (`componente_e_hardware`: accetta un formato di superficie,
	 *     non di pixel), non letto nel nome e non dedotto dall'aver aperto un
	 *     render node (`LEZIONI.md` §1.11).
	 *
	 * ⚠ Il caso esiste: `codificatore_di()` prova prima l'hardware e ripiega in
	 *   software dichiarandolo — per esempio H.264 oltre i 4096 px, che `[M]` il
	 *   driver rifiuta.  ⇒ Su quella strada un descrittore non serve a niente, e
	 *   il palco va rimontato sulla memoria: si segna, e a smontare ci pensa il
	 *   ciclo, che e' l'unico che tiene il palco. */
	if (fo->sulla_scheda && !codificatore_in_hardware(cod)) {
		if (!scheda_da_abbandonare) {
			scheda_da_abbandonare = true;
			scheda_mai_piu = true;
			registro_dice(REG_FIGLIO,
			              "⛔⛔ i pixel sono SULLA SCHEDA e «%s» codifica in "
			              "SOFTWARE: la copia zero non e' percorribile con questo "
			              "codificatore.  ⇒ Rimonto il palco sulla MEMORIA e non "
			              "ci riprovo — ⚠ e questa riga e' la dichiarazione, "
			              "perche' da qui in poi i numeri del tratto sono quelli "
			              "dell'altra strada",
			              codificatore_nome(cod));
		}
		return false;
	}

	/* ⛔⛔⛔ E QUI SI GUARDA IL PASSO **MISURATO**, prima di comprimere — vedi il
	 *      riquadro in `codificatore.h`.
	 *
	 * ⚠ E' l'unico posto in cui il passo vero si conosce: `cattura.h` regola 1
	 *   dice che lo stride si LEGGE dal chunk e non si calcola, quindi prima del
	 *   primo fotogramma non c'era niente da guardare.
	 * ⛔ E il fotogramma NON si spedisce: il difetto che ferma non da' nessun
	 *   errore — da' un desktop inclinato di qualche pixel per riga, che passa
	 *   ogni controllo sui millisecondi e ogni controllo sul colore.  Meglio
	 *   qualche fotogramma non spedito e un rimontaggio, che un'immagine
	 *   sbagliata per tutta la sessione. */
	if (fo->sulla_scheda && !codificatore_stride_importabile(fo->stride)) {
		if (!scheda_da_abbandonare) {
			scheda_da_abbandonare = true;
			scheda_negata_l = fo->larghezza;
			scheda_negata_a = fo->altezza;
			registro_dice(REG_FIGLIO,
			              "⛔⛔ il passo del DMA-BUF e' %u su una tela %ux%u, e "
			              "NON e' multiplo di %u: il driver leggerebbe le righe a "
			              "un passo suo e il desktop uscirebbe INCLINATO, senza "
			              "nessun errore.  `[M]` 22 agosto 2026: a 1552 px la "
			              "marca si legge (contrasto 1,000), a 1544 no — otto "
			              "pixel di differenza e verdetti opposti.  ⇒ Rimonto il "
			              "palco sulla MEMORIA per questa tela, e la copia zero "
			              "tornera' da se' su una tela col passo buono",
			              fo->stride, fo->larghezza, fo->altezza,
			              codificatore_allineamento_scheda());
		}
		return false;
	}

	if (fo->sulla_scheda) {
		CodificatoreSuperficie sup = {
			.fd = fo->fd,
			.offset = fo->offset,
			.stride = fo->stride,
			.larghezza = fo->larghezza,
			.altezza = fo->altezza,
			.formato_drm = fo->formato_drm,
			.modificatore = fo->modificatore,
			.generazione = fo->generazione,
		};
		if (!codificatore_comprimi_scheda(cod, &sup, &fg)) {
			registro_dice(REG_FIGLIO,
			              "⛔ il codec %d non ha consegnato il fotogramma dalla "
			              "SCHEDA: `false` NON e' «un fotogramma vuoto», e' "
			              "«questo non si spedisce»",
			              (int)codec);
			ciclo_guasti++;
			return false;
		}
	} else if (!codificatore_comprimi(cod, fo->pixel, fo->stride, &fg)) {
		registro_dice(REG_FIGLIO,
		              "⛔ il codec %d non ha consegnato il fotogramma: `false` "
		              "NON e' «un fotogramma vuoto», e' «questo non si "
		              "spedisce»",
		              (int)codec);
		ciclo_guasti++;
		return false;
	}
	c = codificatore_confessione(cod);
	/* ⛔ Il primo si dice, i successivi vanno in parlantina: a sessanta al
	 *    secondo questa riga renderebbe illeggibile tutto il resto del registro
	 *    — ed e' precisamente il caso in cui il resto del registro serve. */
	if (ciclo_fotogrammi == 0)
		registro_dice(REG_FIGLIO,
		              "⭐ PRIMO fotogramma codificato: codec %d, %zu byte, %s, "
		              "«%s», profondita' nel flusso %d, livello %d, promozione "
		              "8→10 %s, conversione %llu us, caricamento sulla GPU %llu "
		              "us, codifica %llu us · %s%s",
		              (int)codec, fg.byte, fg.chiave ? "CHIAVE" : "delta",
		              c->stringa_codec, c->profondita_flusso, c->livello_flusso,
		              c->promozione_8_a_10 ? "SI (dichiarata)" : "no",
		              (unsigned long long)fg.us_conversione,
		              (unsigned long long)fg.us_caricamento,
		              (unsigned long long)fg.us_codifica,
		              codificatore_nome(cod),
		              fg.trattenuto ? " — ⚠ TRATTENUTO: il codificatore ha "
		                              "messo un fotogramma di ritardo" : "");
	/* ⛔⭐⭐ E IL LIVELLO SI DICHIARA UNA SECONDA VOLTA, IN CHIARO — §4.3,
	 *      riga 701.  ⚠ Non e' una ripetizione della riga qui sopra: quella
	 *      dice il numero CRUDO dell'SPS, che per HEVC e' il triplo e per AV1
	 *      e' un indice.  Questa lo dice nella forma in cui il client lo chiede
	 *      (`video.livello=5.1`), che e' l'unica in cui i due numeri si possono
	 *      mettere in colonna.
	 *
	 * ⛔⭐⭐ E DAL 23 AGOSTO 2026 IL CONFRONTO LO FA IL PROGRAMMA, perche' il
	 *      numero CHIESTO ha attraversato il confine di processo: il `CIAO`
	 *      (§4.3) → `rcp_livello_negoziato()` → `webtransport.c` → `main.c` →
	 *      `figli_video()` → `struct corpo_video.livello_x10` → qui.  E' la
	 *      stessa catena che la PROFONDITA' negoziata ha percorso il 17 agosto
	 *      2026, per un difetto della stessa famiglia — e prima di stasera
	 *      questo riquadro diceva *«il confronto lo fa chi legge il registro»*,
	 *      che era onesto e non bastava: `[M]` a 3840x2160 il client dichiarava
	 *      5.1 e il server produceva **5.2**, per settimane, e nessuno se ne
	 *      accorgeva.
	 *
	 * ⛔ E IL CONFRONTO NON E' LA CURA: la cura e' **non sforare**, e sta
	 *    all'apertura del codificatore (`codificatore_di()`, `r.livello_x10`).
	 *    Questa riga e' la VERIFICA — R31, *«si chiede per nome e si
	 *    verifica»* — e legge i byte PRODOTTI, non l'opzione passata: un
	 *    componente che ignorasse `level` senza dirlo si vede solo qui.
	 *
	 * ⚠ Un livello prodotto piu' alto del chiesto non da' nessun errore: da'
	 *   uno schermo nero, ed e' la ragione per cui il verdetto si scrive in
	 *   chiaro invece di restare un confronto in testa a chi legge. */
	if (ciclo_fotogrammi == 0) {
		unsigned decimi = livello_in_decimi(codec, c->livello_flusso);
		const char *alfabeto = codec == CODIFICATORE_H264   ? "level_idc"
		                       : codec == CODIFICATORE_HEVC ? "general_level_idc, "
		                                                      "che e' il triplo"
		                                                    : "seq_level_idx";
		if (!decimi)
			registro_dice(REG_FIGLIO,
			              "⚠ §4.3 — LIVELLO PRODOTTO: NON LO SO (nell'SPS c'e' "
			              "%d, e non so tradurlo per questo codec) — ⛔ e «non "
			              "lo so» NON vuol dire «basso»: vuol dire che il tetto "
			              "di `video.livello` oggi non e' verificabile",
			              c->livello_flusso);
		else if (!livello_chiesto_x10)
			registro_dice(REG_FIGLIO,
			              "⭐ §4.3 — LIVELLO: prodotto %u.%u (nell'SPS %d, cioe' "
			              "%s) · stringa per il decodificatore «%s» · CHIESTO: "
			              "niente.  ⚠ §4.3 non obbliga il client a dichiarare "
			              "`video.livello`: nessun tetto da far rispettare — ma "
			              "un livello il server lo produce comunque, ed e' "
			              "questo",
			              decimi / 10u, decimi % 10u, c->livello_flusso,
			              alfabeto, c->stringa_codec);
		else if (decimi <= livello_chiesto_x10)
			registro_dice(REG_FIGLIO,
			              "⭐ §4.3 — LIVELLO: prodotto %u.%u ≤ chiesto %u.%u ✓ "
			              "(nell'SPS %d, cioe' %s) · stringa per il "
			              "decodificatore «%s».  ⭐ Il tetto e' stato IMPOSTO "
			              "all'apertura e RILETTO dai byte: e' R31",
			              decimi / 10u, decimi % 10u,
			              livello_chiesto_x10 / 10u, livello_chiesto_x10 % 10u,
			              c->livello_flusso, alfabeto, c->stringa_codec);
		else
			registro_dice(REG_FIGLIO,
			              "⛔⛔ §4.3 VIOLATA (riga 701) — LIVELLO: prodotto "
			              "%u.%u > chiesto %u.%u (nell'SPS %d, cioe' %s) · "
			              "stringa per il decodificatore «%s».  ⛔ Il "
			              "codificatore NON ha ubbidito al livello imposto: il "
			              "decodificatore del browser puo' RIFIUTARE la "
			              "configurazione, e il sintomo sara' «non si vede "
			              "niente» SENZA nessun altro errore.  ⚠ §4.3 non "
			              "elenca il livello fra i congedi: la sessione resta "
			              "in piedi, e questa riga e' l'unico posto in cui il "
			              "fatto e' scritto",
			              decimi / 10u, decimi % 10u,
			              livello_chiesto_x10 / 10u, livello_chiesto_x10 % 10u,
			              c->livello_flusso, alfabeto, c->stringa_codec);
	}
	if (ciclo_fotogrammi != 0)
		registro_dettaglio(REG_FIGLIO,
		                   "codec %d: %zu byte, %s, caricamento %llu us, "
		                   "codifica %llu us%s",
		                   (int)codec, fg.byte, fg.chiave ? "CHIAVE" : "delta",
		                   (unsigned long long)fg.us_caricamento,
		                   (unsigned long long)fg.us_codifica,
		                   fg.trattenuto ? " — TRATTENUTO" : "");

	ciclo_fotogrammi++;
	if (fg.chiave)
		ciclo_chiavi++;

	{
		uint64_t t_spedizione = ora_monotona_us();
		manda_fotogramma(numero, fg.chiave, tela_l, tela_a, istante_us, fg.dati,
		                 fg.byte, input);
		{
			uint64_t t_fine = ora_monotona_us();
			tratti_conta(fo, &fg, t_fine - t_spedizione, t_fine);
		}
	}
	/* ⛔ Il fotogramma TENUTO e' ancora quello dell'accensione — «rimanda il
	 *    palco» serve a chi rientra prima che il ciclo abbia consegnato il
	 *    primo.  ⚠ E si tiene solo la CHIAVE: rimandare un delta a chi non ha
	 *    il suo passato sarebbe un'immagine sfasciata, cioe' quel che §5.2
	 *    vieta al client di mostrare. */
	if (numero < 3 && fg.chiave) {
		uint8_t *copia = (uint8_t *)malloc(fg.byte);
		if (copia) {
			memcpy(copia, fg.dati, fg.byte);
			free(tenuto[numero]);
			tenuto[numero] = copia;
			tenuto_byte[numero] = fg.byte;
			tenuto_chiave[numero] = true;
			tenuto_l = tela_l;
			tenuto_a = tela_a;
			tenuto_istante = istante_us;
			tenuto_input = input;
		}
	}
	/* ⛔ Il rilievo si scrive solo se qualcuno l'ha chiesto, e solo il primo:
	 *    sessanta file al secondo non sono un rilievo, sono un disco pieno. */
	if (ciclo_fotogrammi <= 2)
		rilievo_scrivi(dir_rilievo, nome_file, fg.dati, fg.byte);

	/* ⭐ LO SCATTO A COMANDO — il riquadro sta sopra `scatto_segnale()`. */
	/* ⛔ E un `SIGUSR2` arrivato quando non c'era niente in corso NON resta
	 *    appeso.  `[M]` 20 agosto 2026: uno scatto chiuso a mano sei minuti
	 *    prima aveva lasciato `scatto_stop` a 1, e lo scatto SEGUENTE si e'
	 *    chiuso al primo fotogramma — «1 fotogrammi in `scatto-flusso.obu`».
	 *    ⚠ Il rilievo c'era e sembrava buono: e' la forma peggiore, un verde
	 *    che ha guardato un fotogramma solo (`LEZIONI.md` §1.9). */
	if (scatto_stop && scatto_stato == 0)
		scatto_stop = 0;
	if (scatto_chiesto) {
		scatto_chiesto = 0;
		if (scatto_stato != 0) {
			registro_dice(REG_FIGLIO,
			              "⚠ SCATTO: ce n'e' gia' uno in corso, il segnale "
			              "non ne apre un secondo");
		} else if (!fo->pixel) {
			/* ⛔ Sulla strada della scheda i pixel non sono qui: si DICE,
			 *    invece di scrivere un file vuoto con l'aria di un rilievo. */
			registro_dice(REG_FIGLIO,
			              "⛔ SCATTO impossibile: i pixel non sono in memoria "
			              "(strada della scheda), non c'e' niente da scrivere");
		} else if (!scatto_dir || !scatto_dir[0] || strcmp(scatto_dir, "-") == 0) {
			registro_dice(REG_FIGLIO,
			              "⛔ SCATTO impossibile: il server non ha una cartella "
			              "di rilievo (`--rilievo`), non c'e' dove scrivere");
		} else {
			codificatore_chiedi_chiave(cod);
			scatto_stato = 1;
			scatto_quanti = 0;
			registro_dice(REG_FIGLIO,
			              "⭐ SCATTO chiesto: ho domandato una CHIAVE, e da "
			              "quella metto su disco ingresso e flusso in «%s»",
			              scatto_dir);
		}
	}
	if (scatto_stato == 1 && fg.chiave && fo->pixel) {
		char percorso[512];

		/* ⛔ `rilievo_scrivi()` dice DA SE' se ha scritto o no: la riga qui
		 *    sotto racconta la geometria, non l'esito — e le due cose non si
		 *    mescolano piu'. */
		rilievo_scrivi(scatto_dir, "scatto-ingresso.bgrx", fo->pixel,
		               (size_t)fo->byte);
		registro_dice(REG_FIGLIO,
		              "⭐ SCATTO: ingresso %ux%u, stride %u, %llu byte — il "
		              "flusso comincia da QUESTA chiave",
		              fo->larghezza, fo->altezza, fo->stride,
		              (unsigned long long)fo->byte);
		snprintf(percorso, sizeof percorso, "%s/scatto-flusso.obu", scatto_dir);
		scatto_fp = fopen(percorso, "wb");
		if (!scatto_fp)
			registro_dice(REG_FIGLIO, "⛔ SCATTO %s: %s", percorso,
			              strerror(errno));
		scatto_stato = scatto_fp ? 2 : 0;
		scatto_restano = SCATTO_FOTOGRAMMI;
	}
	if (scatto_stato == 2 && scatto_fp) {
		if (fwrite(fg.dati, 1, fg.byte, scatto_fp) != fg.byte)
			registro_dice(REG_FIGLIO,
			              "⛔ SCATTO: scrittura corta sul flusso — il file NON "
			              "e' decodificabile fino in fondo");
		scatto_quanti++;
		if (scatto_stop || --scatto_restano <= 0) {
			scatto_chiudi(scatto_dir, fo,
			              scatto_stop ? "chiuso a mano con SIGUSR2"
			                          : "raggiunti i fotogrammi chiesti");
			scatto_stop = 0;
		}
	}

	codificatore_rilascia(cod);
	return true;
}

/* ⛔ Il palco appartiene alla SESSIONE, non alla connessione: `mutter` e
 *    `cattura` restano aperti finche' il figlio vive, perche' il monitor
 *    virtuale esiste finche' qualcuno consuma il flusso.  ⚠ E' l'invariante I4
 *    fatta di processi: chi smonta il palco e' la morte del figlio, non la
 *    caduta di una connessione.
 *
 * ⛔⭐ MA IL PALCO PUO' NON ESSERCI, E SONO DUE CASI CHE SONO LO STESSO —
 *     `[M]` dalla sessione vera dell'utente, 14 agosto 2026:
 *
 *   · **non c'e' ancora**: se alla nascita del figlio la sessione grafica non
 *     esiste, questa funzione falliva e **nessuno ne riprovava un'altra**.  Al
 *     login successivo l'invariante I2 consegnava all'utente **quel figlio
 *     li'** — e l'utente ha visto «niente desktop» due volte di fila;
 *   · **non c'e' piu'**: se la sessione grafica muore sotto un figlio vivo, il
 *     flusso PipeWire va in `connection error`, `cattura_prendi` torna
 *     **subito** con un guasto, e il ciclo girava a vuoto scrivendo il registro
 *     a raffica — ⛔ **30,8 GB e 112 milioni di righe identiche**, cioe' il
 *     disco di una macchina vera.
 *
 * ⇒ ⭐ Sono i due capi della stessa cosa — *il figlio non sa che il suo palco
 *   non c'e' piu', o non c'e' ancora* — e la cura e' una sola: **il palco si
 *   monta, si smonta e si RIMONTA**, con un'attesa che cresce.
 * ⚠ E non si muore: `SPECIFICHE.md` §8.3 vieta di staccare, e una sessione
 *   ferma vale piu' di una sessione chiusa.  ⛔ Ma un figlio **senza palco**
 *   non e' una sessione ferma: e' un figlio che non serve a niente, e per
 *   questo continua a riprovare invece di stare li'.
 *
 * `primo` = e' la nascita: si fa la diagnosi (i due fotogrammi che dimostrano
 * che il palco funziona) e si scrive il rilievo.  ⚠ Su un rimontaggio no: quei
 * due non sono fotogrammi del movimento, e rifarli azzererebbe i conti del
 * ciclo a meta' di una sessione viva. */
static bool prendi_il_palco(uint32_t tela_l, uint32_t tela_a,
                            const char *dir_rilievo, bool primo,
                            MutterSessione **fuori_m, Cattura **fuori_c)
{
	struct corpo_palco p;
	GError *sbaglio = NULL;
	GDBusConnection *bus;
	CatturaFermo fo;
	CatturaPresa presa;
	uint64_t istante_us;
	MutterSessione *mut = NULL;
	Cattura *cat = NULL;
	/* ⏱ il cronometro dei passi — vedi il riquadro qui sotto */
	const char *crono_nome = "";
	uint64_t crono_ms = 0;

	/*
	 * ⭐ E PRIMA DI TUTTO: se qualcuno sta aspettando una tela, glielo si dice.
	 *
	 * ⛔ Montare il palco dura SECONDI — la sessione che nasce, `ScreenCast`,
	 *    la negoziazione di PipeWire — e in tutto quel tempo questa funzione
	 *    non manda niente.  ⚠ Il fondo di §7.1 e' tre secondi: senza questa
	 *    riga scadrebbe **dentro** il montaggio, cioe' proprio mentre la
	 *    risposta si sta preparando.
	 */
	/*
	 * ⛔⭐⭐ E LA PRIMA RIGA LA SCRIVE IL FIGLIO, PRIMA DI PARLARE COL PADRE.
	 *
	 * `[M]` 16 agosto 2026: nel buco dei ventuno secondi l'unica riga al
	 * confine la scriveva **il padre** (quando riceveva l'«attendi»), e da una
	 * riga del padre non si sa quando il FIGLIO l'ha mandata — si sa quando il
	 * padre l'ha letta.  ⛔ E' la forma E6, il mittente dedotto invece che
	 * chiesto, dentro il confine che serviva a delimitare il difetto.
	 *
	 * ⇒ Adesso il figlio dice «sto per parlare» e «ho parlato», e fra le due
	 *   righe c'e' solo `manda()`: se i secondi stanno li', si vedono.
	 */
	registro_dettaglio(REG_FIGLIO,
	                   "entro nel montaggio del palco (tela %ux%u): dico al padre "
	                   "di attendere",
	                   tela_l, tela_a);

	/*
	 * ⛔⭐⭐⭐ NON SI FA NASCERE NIENTE FINCHE' NON SI SA A CHE MISURA.
	 *
	 * ⭐ E' la cura della coda dei tempi di login, e la ragione sta per intero
	 *    nel riquadro di `tela_dal_cliente`: un palco montato al ripiego va
	 *    ridimensionato, e su Wayland il ridimensionamento si compie solo quando
	 *    il compositore consegna un fotogramma — cioe' MAI, su un desktop appena
	 *    nato che non si muove.
	 *
	 * ⚠ Mezzo secondo di attesa qui vale tredici secondi di gara dopo.
	 *
	 * ⛔ E si aspetta con un TETTO, non all'infinito: l'invariante I1 vieta di
	 *    stare fermi per prudenza.  Se il cliente non dichiara la sua finestra
	 *    entro `TELA_ATTESA_MS`, si parte col ripiego e si DICHIARA — meglio un
	 *    desktop da ridimensionare che nessun desktop.
	 */
	if (!tela_dal_cliente) {
		static uint64_t primo_giro_ms;
		uint64_t adesso = registro_ora_ms();

		if (primo_giro_ms == 0)
			primo_giro_ms = adesso;
		if (adesso - primo_giro_ms < TELA_ATTESA_MS) {
			registro_dettaglio(REG_FIGLIO,
			                   "aspetto la tela del cliente prima di far nascere "
			                   "qualcosa (%llu ms su %d): montare al ripiego "
			                   "vorrebbe dire ridimensionare, e il "
			                   "ridimensionamento su una scena ferma non si "
			                   "compie",
			                   (unsigned long long)(adesso - primo_giro_ms),
			                   TELA_ATTESA_MS);
			p.stato_sessione = (uint32_t)SESSIONE_NON_LETTA;
			snprintf(p.guasto, sizeof p.guasto,
			         "aspetto la tela del cliente");
			manda(MSG_PALCO, &p, sizeof p, NULL, 0);
			return false;
		}
		if (!tela_dal_cliente) {
			static bool detto;

			if (!detto) {
				detto = true;
				registro_dice(REG_FIGLIO,
				              "⚠ il cliente non ha dichiarato la sua finestra "
				              "entro %d ms: parto col ripiego %ux%u.  ⛔ Il "
				              "desktop nascera' a una misura che nessuno ha "
				              "chiesto e andra' ridimensionato — ma un desktop "
				              "da ridimensionare batte nessun desktop (I1)",
				              TELA_ATTESA_MS, tela_l, tela_a);
			}
		}
	}
	if (tela_l && tela_a)
		attendi_tela(tela_l, tela_a);
	registro_dettaglio(REG_FIGLIO, "l'«attendi» e' partito: adesso il bus");

	/*
	 * ⛔⭐⭐ IL CRONOMETRO DENTRO I PASSI, e non e' un lusso: e' l'attrezzo che
	 *       ho dovuto costruire dopo TRE diagnosi sbagliate di fila.
	 *
	 * `[M]` 16 agosto 2026.  La misura diceva «mediana 3,2 s, p90 21 s», e il
	 * registro fra le due righe che delimitano il buco non aveva **una sola
	 * riga**.  ⇒ Da fuori si poteva solo DEDURRE quale passo se li mangiava, e
	 * ho dedotto male tre volte: prima l'attesa che raddoppia, poi il gestore
	 * d'utente, poi il sondaggio a Mutter.  Ogni volta la cura era ragionevole
	 * e la misura dopo diceva di no.
	 *
	 * ⭐ Un passo che puo' durare venti secondi e non lascia traccia e' un passo
	 *    su cui si puo' solo tirare a indovinare — ed e' esattamente la forma
	 *    che questo progetto paga da sempre (`LEZIONI.md` §1.9: il silenzio e la
	 *    salute con la stessa faccia).
	 *
	 * ⚠ E si scrive solo quando il passo e' LENTO: un passo veloce non ha
	 *   niente da dire, e riempire il registro di righe normali e' il modo di
	 *   non far leggere quelle che contano.
	 */
#define PASSO_LENTO_MS 250
#define CRONO_INIZIO(nome) \
	do { \
		crono_nome = (nome); \
		crono_ms = registro_ora_ms(); \
	} while (0)
#define CRONO_FINE() \
	do { \
		uint64_t crono_durata = registro_ora_ms() - crono_ms; \
		if (crono_durata >= PASSO_LENTO_MS) \
			registro_dice(REG_FIGLIO, \
			              "⏱ il passo «%s» ha impiegato %llu ms — e' LUI che " \
			              "tiene fermo il figlio, non «la sessione che nasce»", \
			              crono_nome, (unsigned long long)crono_durata); \
	} while (0)

	memset(&p, 0, sizeof p);
	/* ⛔ «Non ho potuto guardare» e' il valore di PARTENZA, non «sana»: con lo
	 *    zero del `memset` una via d'uscita anticipata avrebbe riferito
	 *    `SESSIONE_SANA` senza aver guardato niente — «vuoto» e «proibito» con
	 *    la stessa faccia, la forma d'errore E8, dentro la riga che la deve
	 *    smascherare.  `[M]` visto nel registro del 12 agosto 2026: il palco di
	 *    «prova» diceva «sessione 0» e nessuno l'aveva letta. */
	p.stato_sessione = (uint32_t)SESSIONE_NON_LETTA;

	/* ⛔⭐ IL BUS, ED E' LA MISURA CHE DECIDE TUTTO IL MANDATO.  `[M]` root non
	 *     si collega qui; questo processo e' l'utente, e o si collega o dice
	 *     perche'. */
	CRONO_INIZIO("apri il bus di sessione");
	bus = sessione_bus(&sbaglio);
	CRONO_FINE();
	if (!bus) {
		snprintf(p.guasto, sizeof p.guasto, "bus di sessione: %s",
		         sbaglio ? sbaglio->message : "(nessun dettaglio)");
		registro_dice(REG_FIGLIO,
		              "⛔ NON ho il bus di sessione: %s.  ⚠ Non e' «non c'e' la "
		              "sessione», e' «non ho potuto guardare» — e senza bus non "
		              "c'e' niente da catturare",
		              p.guasto);
		g_clear_error(&sbaglio);
		manda(MSG_PALCO, &p, sizeof p, NULL, 0);
		return false;
	}
	p.bus_aperto = 1;
	g_object_unref(bus);
	registro_dice(REG_FIGLIO,
	              "⭐ IL BUS DI SESSIONE E' MIO: collegato come uid %ld — la "
	              "cosa che il padre root NON puo' fare (P2-6-montaggio.md §5.4)",
	              (long)geteuid());

	/*
	 * ⛔⭐⭐ E ADESSO SI TOCCA — 15 agosto 2026, fase 5.
	 *
	 * ⛔ Qui c'era scritto «si guarda, non si tocca: far NASCERE una sessione e'
	 *    del login vero, non di questo mandato», e per la fase 2 era giusto.
	 *    ⭐ Alla fase 5 quel mandato **e' questo** — `PIANO.md`: «Produce: PAM
	 *    per intero» — e da quando questo processo apre lui la sessione PAM
	 *    (`diventa_ed_esegui`, passo 2-bis) `/run/user/<uid>` c'e' per
	 *    costruzione: l'obiezione che quella riga portava e' caduta.
	 *
	 * ⛔ IL PREZZO DI NON FARLO, misurato la sera del 15 agosto: la macchina si
	 *    riavvia, nessuno rifa' la sessione, e l'utente entra e **non vede
	 *    niente**.  Il registro diceva tre volte «SESSIONE MORTA: guardo e non
	 *    tocco», che e' una diagnosi perfetta di un prodotto che non fa il suo
	 *    mestiere.
	 *
	 * ⚠ E NON SI ASPETTA: `sessione_fai_nascere()` chiede e torna.  L'attesa
	 *   esiste gia' ed e' il nostro ciclo di ri-tentativi (1 s → 30 s); una
	 *   seconda attesa dentro questo processo sarebbe 40 s in cui il padre non
	 *   riceve piu' un fotogramma ne' una risposta (`LEZIONI.md` §6.2-bis).
	 *
	 * ⚠ E si chiede al piu' una volta al minuto: `gnome-session` ci mette
	 *   qualche secondo a farsi vedere sul bus, e senza questa briglia ogni
	 *   ri-tentativo ne avvierebbe un'altra.
	 */
	CRONO_INIZIO("leggi lo stato della sessione (GetCurrentState)");
	p.stato_sessione = (uint32_t)sessione_stato(tela_l, tela_a, NULL);
	CRONO_FINE();
	{
		/*
		 * ⭐⭐ «C'ERA E ADESSO NON C'E' PIU'» — §7.6, il gemello, e la
		 *     distinzione che decide TUTTO il comportamento.
		 *
		 * ⛔ Una sessione MORTA vuol dire due cose opposte:
		 *
		 *   · non c'e' MAI stata (primo attacco, macchina appena riavviata)
		 *     ⇒ la si fa nascere, ed e' quel che l'utente si aspetta;
		 *   · c'era e l'utente e' USCITO dal menu del desktop
		 *     ⇒ ⛔ NON si rifa': rifarla vorrebbe dire **impedirgli di
		 *       uscire**.  Si avvisa chi guarda con `0x10`, e la prossima ne
		 *       nascera' al prossimo attacco (`DECISIONI.md` §4.1-quater: «la
		 *       pagina torna al modulo di accesso»).
		 *
		 * ⚠ E lo stesso vale se il compositore e' MORTO da solo: dal nostro
		 *   lato e' indistinguibile da un logout, e il comportamento giusto e'
		 *   lo stesso — dirlo a chi guarda invece di far ricomparire un
		 *   desktop che l'utente aveva chiuso.
		 */
		static bool vista_viva;

		if (p.stato_sessione != SESSIONE_MORTA &&
		    p.stato_sessione != SESSIONE_NON_LETTA)
			vista_viva = true;
		else if (p.stato_sessione == SESSIONE_MORTA && vista_viva) {
			vista_viva = false;
			sessione_chiusa_dall_utente = true;
			registro_dice(REG_FIGLIO,
			              "⭐ §7.6: la sessione grafica C'ERA e adesso NON "
			              "C'E' PIU' — l'utente e' uscito dal menu del "
			              "desktop.  ⛔ NON la faccio rinascere: rifarla "
			              "vorrebbe dire impedirgli di uscire.  Avviso il "
			              "padre, che congeda chi guarda con 0x10");
			manda(MSG_SESSIONE_FINITA, NULL, 0, NULL, 0);
			manda(MSG_PALCO, &p, sizeof p, NULL, 0);
			return false;
		}
	}
	if (p.stato_sessione == SESSIONE_MORTA && sessione_chiusa_dall_utente) {
		/* ⛔ Il terzo stato: l'utente e' USCITO.  Rifarla adesso vorrebbe dire
		 *    fargli ricomparire il desktop che ha appena chiuso — cioe'
		 *    impedirgli di uscire.  Si aspetta un attacco NUOVO. */
		registro_dettaglio(REG_FIGLIO,
		                   "la sessione grafica di «%s» e' stata CHIUSA "
		                   "dall'utente: non la rifaccio finche' non si "
		                   "riattacca qualcuno",
		                   g_get_user_name());
	} else if (p.stato_sessione == SESSIONE_MORTA) {
		uint64_t adesso_ms = registro_ora_ms();

		if (!sta_nascendo(adesso_ms)) {
			nascita_chiesta_ms = adesso_ms;
			registro_dice(REG_FIGLIO,
			              "⭐ nessuna sessione grafica per «%s»: LA FACCIO "
			              "NASCERE io (tela %ux%u) e torno subito — a "
			              "trovarla ci pensa il prossimo tentativo",
			              g_get_user_name(), tela_l, tela_a);
			if (!sessione_fai_nascere(tela_l, tela_a))
				registro_dice(REG_FIGLIO,
				              "⛔ la sessione grafica di «%s» non e' "
				              "partita: il palco restera' senza niente da "
				              "catturare, e le righe di «sessione» qui "
				              "sopra dicono perche'",
				              g_get_user_name());
		} else {
			registro_dice(REG_FIGLIO,
			              "la sessione grafica di «%s» non c'e' ancora: "
			              "l'ho gia' chiesta %llu ms fa e aspetto che si "
			              "faccia vedere sul bus",
			              g_get_user_name(),
			              (unsigned long long)(adesso_ms - nascita_chiesta_ms));
		}
	} else if (p.stato_sessione != SESSIONE_SANA) {
		registro_dice(REG_FIGLIO,
		              "⚠ la sessione grafica di questo utente e' «%s» (%u): "
		              "non la tocco — gli stati diversi da «morta» li governa "
		              "sessione_assicura(), e buttarne giu' una viva toglierebbe "
		              "il desktop a chi lo guarda (I4)",
		              sessione_marca((SessioneStato)p.stato_sessione),
		              p.stato_sessione);
	}

	/*
	 * ⛔⭐⭐ NON SI MONTA SOPRA UN COMPOSITORE CHE NON HA RISPOSTO — 16 agosto
	 *       2026, ed e' l'altra meta' di `ATTESA_SONDAGGIO_MS`.
	 *
	 * ⛔ `SESSIONE_NON_LETTA` non vuol dire «non c'e'» e non vuol dire «c'e'»:
	 *    vuol dire **«ha il nome sul bus e non mi ha risposto»**, cioe' sta
	 *    ancora nascendo.  ⇒ Andare avanti a montare vorrebbe dire fare a quello
	 *    stesso compositore muto una chiamata piu' cara — `CreateSession` su
	 *    RemoteDesktop, che in `mutter.c` ha un tetto di **quindici secondi**.
	 *
	 * ⚠ Cioe' si sposterebbe il blocco invece di toglierlo: il sondaggio corto
	 *   servirebbe a niente, e il figlio resterebbe muto lo stesso.
	 *
	 * ⭐ La risposta giusta e' quella che il ciclo sa gia' usare: «non adesso».
	 *    Si torna, si dice «ATTENDI» al padre, e si riprova fra 200 ms.
	 */
	if (p.stato_sessione == (uint32_t)SESSIONE_NON_LETTA) {
		snprintf(p.guasto, sizeof p.guasto,
		         "il compositore non ha risposto al sondaggio: sta ancora nascendo");
		registro_dettaglio(REG_FIGLIO,
		                   "il compositore di «%s» ha il nome sul bus ma non ha "
		                   "risposto entro il sondaggio: NON provo a montarci "
		                   "sopra — sarebbe una chiamata da quindici secondi a "
		                   "chi non risponde.  Riprovo fra poco",
		                   g_get_user_name());
		manda(MSG_PALCO, &p, sizeof p, NULL, 0);
		return false;
	}

	CRONO_INIZIO("monta il palco (mutter_apri)");
	mut = mutter_apri(&sbaglio);
	CRONO_FINE();
	if (!mut) {
		snprintf(p.guasto, sizeof p.guasto, "ScreenCast: %s",
		         sbaglio ? sbaglio->message : "(nessun dettaglio)");
		registro_dice(REG_FIGLIO, "⛔ nessun monitor virtuale da catturare: %s",
		              p.guasto);
		g_clear_error(&sbaglio);
		manda(MSG_PALCO, &p, sizeof p, NULL, 0);
		return false;
	}

	/* ⛔ La cadenza si chiede UNA volta e con UN nome: `MOVIMENTO_FPS`.  Qui
	 *    c'era il letterale 60 e la richiesta di codifica ne dichiarava 30 —
	 *    due numeri diversi per la stessa grandezza. */
	/* ⛔ La strada si DICHIARA nel registro al montaggio, perche' e' il fatto
	 *    che spiega tutti i numeri del tratto che verranno dopo: un «conversione
	 *    0,9 ms» sulla scheda e uno sulla memoria non sono la stessa grandezza. */
	registro_dice(REG_FIGLIO,
	              "⭐ il palco si monta sulla strada «%s»%s",
	              strada_del_palco == CATTURA_STRADA_SCHEDA
	                  ? "SCHEDA (DMA-BUF, copia zero)"
	                  : "MEMORIA (i pixel si copiano)",
	              strada_del_palco == CATTURA_STRADA_SCHEDA
	                  ? " — ⚠ vale solo se il codificatore e' in hardware, e se non "
	                    "lo e' questo palco si rimonta sulla memoria dichiarandolo"
	                  : "");
	cat = cattura_avvia(mutter_nodo(mut), tela_l, tela_a, MOVIMENTO_FPS,
	                    strada_del_palco, CATTURA_COLORE_BGRX, NULL, NULL,
	                    NULL, &sbaglio);
	if (!cat) {
		snprintf(p.guasto, sizeof p.guasto, "cattura: %s",
		         sbaglio ? sbaglio->message : "(nessun dettaglio)");
		registro_dice(REG_FIGLIO, "⛔ la cattura non si apre: %s", p.guasto);
		g_clear_error(&sbaglio);
		mutter_chiudi(mut);
		manda(MSG_PALCO, &p, sizeof p, NULL, 0);
		return false;
	}
	*fuori_m = mut;
	*fuori_c = cat;

	memset(&fo, 0, sizeof fo);
	presa = cattura_prendi(cat, 5.0, &fo, &sbaglio);
	istante_us = istante_del_fotogramma(&fo, ora_monotona_us());
	p.presa = (uint32_t)presa;
	/* ⛔ `PIXEL_ALTROVE` E' UN FOTOGRAMMA CONSEGNATO, non un nulla di fatto:
	 *    sulla strada della scheda i pixel non sono in memoria, e il fotogramma
	 *    c'e' lo stesso (`cattura.h`).  ⚠ Trattarlo come guasto qui vorrebbe
	 *    dire smontare il palco a ogni montaggio riuscito. */
	if (presa != CATTURA_PRESA_FATTA && presa != CATTURA_PRESA_PIXEL_ALTROVE) {
		snprintf(p.guasto, sizeof p.guasto, "presa %u: %s", (unsigned)presa,
		         sbaglio ? sbaglio->message : "nessun fotogramma");
		registro_dice(REG_FIGLIO,
		              "⛔ nessun fotogramma in 5 s (%s): e' un RISULTATO se il "
		              "desktop non e' cambiato, un guasto se il flusso non e' "
		              "mai partito — e i due numeri sono diversi apposta",
		              p.guasto);
		g_clear_error(&sbaglio);
		/* ⛔⭐ E QUI SI SMONTA, invece di restare con un palco a meta'.
		 *
		 *     Prima si tornava lasciando `*fuori_c` pieno: il ciclo trovava una
		 *     cattura viva che non consegnava, e non aveva nessun modo di
		 *     distinguerla da una sana.  ⚠ «Il flusso non e' mai partito» e «la
		 *     scena e' ferma» sono due cose diverse (`cattura.h`), e questa e'
		 *     la prima.  ⇒ Si smonta, e chi chiama riprovera'. */
		cattura_fermo_libera(&fo);
		cattura_ferma(cat);
		mutter_chiudi(mut);
		*fuori_c = NULL;
		*fuori_m = NULL;
		manda(MSG_PALCO, &p, sizeof p, NULL, 0);
		return false;
	}

	/* ⛔ Il nome del monitor DOPO il primo fotogramma, non dopo `cattura_avvia`:
	 *    la cucitura corretta il 12 agosto 2026 (`P2-6-montaggio.md` §5.1). */
	if (mutter_monitor_cerca(mut)) {
		guint prima = 0, dopo = 0;
		double scala;

		mutter_monitor_conteggi(mut, &prima, &dopo);
		p.monitor_prima = prima;
		p.monitor_dopo = dopo;
		snprintf(p.monitor, sizeof p.monitor, "%s", mutter_monitor_nostro(mut));

		/* ⛔⭐⭐ LA GUARDIA 2 DI §5.0-sexies, E DA STANOTTE E' UNA CONDIZIONE DI
		 *     SERVIZIO — «leggere la scala e FALLIRE se non e' 1,0».
		 *
		 * ⚠ Fino a ieri si leggeva e si diceva, e bastava: con la tela fissa a
		 *   1920x1080 il danno era teorico.  ⛔ Da stanotte la tela prende la
		 *   misura del client, quindi il layout del monitor logico e i pixel del
		 *   flusso divergono davvero — e quel layout **e' lo spazio delle
		 *   coordinate dell'input**: `[M]` con `scaling-factor = 2` il layout di
		 *   una tela 2133 diventa `1067 x 2 = 2134`, e il puntatore va altrove
		 *   **senza che nessuna riga lo dica**.
		 *
		 * ⛔ E si FALLISCE invece di servire: un desktop che si vede e si comanda
		 *    SBAGLIATO e' peggio di un desktop che non parte, perche' il secondo
		 *    ha una riga che lo spiega e il primo no.  ⚠ E non e' una morte: il
		 *    palco si rimonta con l'attesa che cresce, quindi appena l'utente
		 *    cambia l'impostazione la sessione riparte da se'.
		 *
		 * ⛔ «Non lo so» NON e' «va bene»: se la scala non si e' potuta leggere si
		 *    prosegue dichiarandolo, perche' rifiutare su un'assenza di dato
		 *    spegnerebbe il servizio su una macchina che non ha nessun difetto. */
		scala = mutter_scala_nostra(mut);
		/* ⛔ E IL CASO BUONO SI SCRIVE, non si lascia al silenzio: «la guardia ha
		 *    guardato e la scala e' 1,0» e «la guardia non e' stata percorsa»
		 *    avrebbero la stessa faccia — che e' la forma d'errore che questo
		 *    progetto paga piu' spesso.  ⚠ Una riga per montaggio del palco, non
		 *    per fotogramma. */
		if (scala == 1.0)
			registro_dice(REG_FIGLIO,
			              "⭐ guardia 2 (§5.0-sexies): la scala del nostro monitor "
			              "«%s» e' 1,000 — lo spazio delle coordinate dell'input "
			              "coincide con i pixel del flusso",
			              p.monitor);
		if (scala < 0)
			registro_dice(REG_FIGLIO,
			              "⚠ la scala del nostro monitor logico non si e' potuta "
			              "leggere: PROSEGUO, e non dico 1,0 per abitudine "
			              "(guardia 2 di DECISIONI.md §5.0-sexies)");
		else if (scala != 1.0) {
			registro_dice(REG_FIGLIO,
			              "⛔⛔ SCALA %.3f sul NOSTRO monitor «%s» invece di 1,0: "
			              "lo spazio delle coordinate dell'input non coincide con "
			              "i pixel del flusso, e il puntatore andrebbe altrove "
			              "senza che nulla lo dica.  ⇒ NON prendo il palco "
			              "(guardia 2 di DECISIONI.md §5.0-sexies).  La cura e' "
			              "una riga sola, sulla sessione di questo utente: "
			              "`gsettings set org.gnome.desktop.interface "
			              "scaling-factor 0` — poi la sessione riparte da se', "
			              "senza riavviare niente",
			              scala, p.monitor);
			p.stato_sessione = 0;
			snprintf(p.guasto, sizeof p.guasto,
			         "scala %.3f invece di 1,0 sul monitor «%s»: il puntatore "
			         "andrebbe altrove (guardia 2, DECISIONI.md §5.0-sexies)",
			         scala, p.monitor);
			cattura_fermo_libera(&fo);
			manda(MSG_PALCO, &p, sizeof p, NULL, 0);
			return false;
		}
	} else {
		snprintf(p.monitor, sizeof p.monitor, "(non l'ho saputo dire)");
	}

	p.larghezza = fo.larghezza;
	p.altezza = fo.altezza;
	p.stride = fo.stride;
	p.bit = (uint32_t)fo.consegna.bit_per_canale;
	registro_dice(REG_FIGLIO,
	              "⭐ fotogramma catturato COME «%s»: %ux%u, stride %u LETTO, "
	              "%llu byte, %s a %d bit, %s",
	              getenv("USER") ? getenv("USER") : "?", fo.larghezza,
	              fo.altezza, fo.stride, (unsigned long long)fo.byte,
	              fo.consegna.formato ? fo.consegna.formato : "(ignoto)",
	              fo.consegna.bit_per_canale,
	              /* ⛔ TRE risposte e non due: dal 22 agosto 2026 il giro sui
	               *    pixel si fa a cadenza (`cattura.c`,
	               *    `MISURA_PIXEL_OGNI_MS`), e su un fotogramma non guardato
	               *    `nero == FALSE` vuol dire **«non ho guardato»**, non «non
	               *    e' nero».  ⚠ Qui e' sempre il PRIMO fotogramma — che si
	               *    guarda sempre — ma la riga si scrive giusta lo stesso:
	               *    e' quella che un giorno verra' copiata altrove. */
	              !fo.consegna.pixel_misurati ? "⚠ i pixel non sono stati guardati "
	                                            "(cadenza): NON e' «non e' nero»"
	              : fo.consegna.nero          ? "⛔ NERO"
	                                          : "non nero");

	rilievo_scrivi(dir_rilievo, "cattura.bgrx", fo.pixel, (size_t)fo.byte);

	/* ⛔⭐ E QUESTA PRIMA CODIFICA RESTA, anche se adesso c'e' il ciclo: non
	 *     serve a spedire, serve a DIMOSTRARE che il palco funziona prima che
	 *     qualcuno lo chieda.  `p.flussi` e' il numero che `MSG_PALCO` porta al
	 *     padre, ed e' l'unica riga che distingue «nessuno guarda» da «il
	 *     codificatore non si apre».  ⚠ E i due codificatori restano APERTI:
	 *     sono quelli che il ciclo usera'.
	 * ⛔ §5.2: tutt'e due i primi devono essere una CHIAVE, e si chiede invece
	 *    di sperarlo. */
	debito_chiave[1] = debito_chiave[2] = debito_chiave[3] = true;
	if (primo) {
		/* ⚠ `input = 0` e NON e' un valore di comodo: §6.2 dice «0 se
		 *   nessuno», e qui non c'e' ancora nessuno — il canale di input nasce
		 *   quando il client apre il suo stream, e questi due fotogrammi sono
		 *   la diagnosi dell'accensione, non del movimento. */
		/* ⛔⛔ E LA MISURA E' QUELLA DEL FOTOGRAMMA, non quella che si e'
		 *     chiesta — difetto trovato refutando, la notte del 15 agosto 2026.
		 *
		 *     Qui il codificatore nasceva a `tela_l x tela_a` (il CHIESTO) e
		 *     veniva alimentato con `fo.pixel`/`fo.stride` (l'ARRIVATO), senza la
		 *     riconciliazione e senza la guardia sui byte, che vivono tutt'e due
		 *     nel ciclo piu' sotto.  ⚠ Oggi il caso e' irraggiungibile — la
		 *     proposta dichiara la misura come rettangolo FISSO, quindi o si
		 *     ottiene o la negoziazione fallisce — ⛔ ma il codice nuovo
		 *     RICONOSCE il caso «concesso diverso da chiesto» (§4.5) e lo
		 *     proteggeva in un posto e non nell'altro: un'incoerenza dentro la
		 *     stessa modifica.  ⇒ Qui si usa quel che i pixel sono, e la stessa
		 *     guardia del ciclo decide se si possono toccare. */
		if (fo.stride >= (guint64) fo.larghezza * 4u
		    && fo.byte >= (guint64) fo.stride * fo.altezza) {
			if (codifica_e_manda(&fo, CODIFICATORE_HEVC, 1, dir_rilievo,
			                     "flusso-hevc.265", istante_us, fo.larghezza,
			                     fo.altezza, 0))
				p.flussi++;
			if (codifica_e_manda(&fo, CODIFICATORE_AV1, 2, dir_rilievo,
			                     "flusso-av1.obu", istante_us, fo.larghezza,
			                     fo.altezza, 0))
				p.flussi++;
			/* ⭐ Il terzo, dal 20 agosto: un client che negozia H.264 trova il
			 *    primo fotogramma gia' in deposito come gli altri due, invece di
			 *    aspettare che qualcosa si muova sul desktop. */
			if (codifica_e_manda(&fo, CODIFICATORE_H264, 3, dir_rilievo,
			                     "flusso-h264.264", istante_us, fo.larghezza,
			                     fo.altezza, 0))
				p.flussi++;
			/* ⚠ E la misura del palco NON si scrive qui: `tela_l`/`tela_a` sono
			 *   i PARAMETRI di questa funzione, non le variabili del ciclo —
			 *   scriverci dentro sembrerebbe aggiornare il palco e non
			 *   aggiornerebbe niente.  Ci pensa la riconciliazione al primo giro
			 *   del ciclo, che e' l'unico posto in cui quel numero cambia. */
		} else {
			registro_dice(REG_FIGLIO,
			              "⛔ la diagnosi dell'accensione NON codifica: il "
			              "fotogramma dichiara %ux%u con passo %u e porta %llu "
			              "byte — chi lo comprimesse leggerebbe oltre la copia",
			              fo.larghezza, fo.altezza, fo.stride,
			              (unsigned long long)fo.byte);
		}
		/* ⛔ E i contatori del ciclo ripartono da zero: questi due non sono
		 *    fotogrammi del movimento, sono la diagnosi dell'accensione.
		 *    Sommarli direbbe «due fotogrammi consegnati» a un utente che non
		 *    ne ha visto nemmeno uno. */
		ciclo_fotogrammi = ciclo_chiavi = 0;
	} else {
		/* ⚠ Su un rimontaggio la diagnosi non si rifa': costerebbe ~80 ms di
		 *   codifica a meta' di una sessione viva, e i due fotogrammi
		 *   andrebbero a un client che sta gia' guardando.  ⛔ `p.flussi` resta
		 *   0 e il registro lo dice: e' un rimontaggio, non una nascita. */
		p.flussi = 0;
	}

	cattura_fermo_libera(&fo);
	manda(MSG_PALCO, &p, sizeof p, NULL, 0);

	/* ⭐⭐ E LE DUE CUCITURE DEL PALCO STANNO QUI, non nel chiamante: chi
	 *     rimonta il palco deve rimontarle **tutte**, e lasciarne una fuori
	 *     vorrebbe dire un desktop che si vede e non si comanda — senza nessun
	 *     errore da nessuna parte.
	 *
	 * ⛔ `cursore_apri()` vuole il destinatario **all'apertura**, e l'apertura
	 *    avviene dentro `cattura_avvia()`: percio' la registrazione passa da
	 *    `cattura.h`.  ⚠ Senza questa riga il tubo sarebbe scritto per intero e
	 *    **vuoto**.
	 * ⛔ E `input_apri()` va sulla sessione `RemoteDesktop` che `mutter.c` ha
	 *    appena avviato: su un rimontaggio quella e' **un'altra sessione**, e un
	 *    `Input` agganciato alla vecchia non iniettera' piu' niente. */
	cattura_cursore(cat, cursore_al_padre, NULL);
	if (palco_input) {
		input_chiudi(palco_input);
		palco_input = NULL;
	}
	{
		char *sbaglio_input = NULL;
		palco_input = input_apri(mut, tela_l, tela_a, &sbaglio_input);
		if (palco_input && disposizione_in_attesa[0]) {
			/* ⛔ Prima di dire che il canale e' aperto: la disposizione
			 *    chiesta all'attacco era arrivata a palco chiuso, e se non
			 *    la si applica QUI l'utente batte i primi tasti sulla
			 *    disposizione sbagliata — e `Ctrl+Z` fa «rifai». */
			registro_dice(REG_FIGLIO,
			              "⭐ §5-bis.7: applico adesso la disposizione «%s», "
			              "che era stata chiesta quando il palco non c'era "
			              "ancora",
			              disposizione_in_attesa);
			input_disposizione(palco_input, disposizione_in_attesa);
			disposizione_in_attesa[0] = '\0';
		}
		if (palco_input)
			registro_dice(REG_FIGLIO,
			              "⭐⭐ IL CANALE DI INPUT E' APERTO sulla tela %ux%u: "
			              "da adesso quel che l'utente fa nel browser arriva "
			              "al desktop (§7.3)",
			              tela_l, tela_a);
		else
			/* ⛔ E se non si apre NON si muore: `CODER.md` §4.2 — degradare,
			 *    non fallire.  Un utente che vede il desktop e non lo comanda
			 *    ha meno di quel che gli spetta; un utente a cui la sessione
			 *    cade **non ha niente**.  ⚠ Ma il ripiego si DICHIARA. */
			registro_dice(REG_FIGLIO,
			              "⛔ il canale di input NON si apre (%s): il desktop "
			              "si VEDE ma non si COMANDA.  ⚠ La sessione resta in "
			              "piedi — §8.3 vieta di staccare — e questa riga e' "
			              "il ripiego dichiarato",
			              sbaglio_input ? sbaglio_input : "nessun dettaglio");
		free(sbaglio_input);
	}

	/*
	 * ⭐⭐ E LA TERZA CUCITURA DEL PALCO: GLI APPUNTI — fase 7.
	 *
	 * ⛔ Va rimontata **insieme alle altre due**, e per la stessa ragione: su un
	 *    rimontaggio la sessione `RemoteDesktop` e' **un'altra**, e un `Appunti`
	 *    agganciato alla vecchia non riceverebbe piu' nessun segnale — senza
	 *    nessun errore da nessuna parte.  ⚠ Il sintomo sarebbe «gli appunti
	 *    hanno smesso di funzionare a un certo punto», che non nomina il
	 *    rimontaggio.
	 *
	 * ⛔ E si CHIUDE prima di riaprire, non si lascia il vecchio in piedi:
	 *    `appunti_chiudi()` non chiama mai `DisableClipboard` (trappola 1 di
	 *    `appunti.h`), quindi chiudere qui non brucia la clipboard della
	 *    sessione grafica — chiude solo il nostro thread e le sottoscrizioni.
	 */
	if (palco_appunti) {
		appunti_chiudi(palco_appunti);
		palco_appunti = NULL;
	}
	{
		GError *sbaglio_app = NULL;

		palco_appunti = appunti_apri(mutter_bus(mut),
		                             mutter_percorso_controllo(mut),
		                             &sbaglio_app);
		if (palco_appunti) {
			appunti_ascolta(palco_appunti, appunti_dalla_sessione,
			                appunti_vuole_incollare, NULL);
			registro_dice(REG_FIGLIO,
			              "⭐⭐ GLI APPUNTI SONO APERTI, nei due versi e solo "
			              "testo: da adesso quel che si copia nel desktop si "
			              "puo' incollare sul dispositivo, e viceversa (§7.4)");
			/* ⭐ E PRIMA DI TUTTO: la clipboard che c'era gia' nel desktop
			 *    si CHIEDE, o collegandosi la si perde (vedi il riquadro in
			 *    `appunti.c`).  ⛔ E si chiede PRIMA dell'offerta arretrata:
			 *    offrendo per primi si leggerebbe il nostro testo invece del
			 *    suo. */
			appunti_leggi_adesso(palco_appunti);

			/* ⭐ E l'offerta arrivata mentre non c'erano si rifa' ADESSO. */
			if (appunti_offerta_arretrata) {
				GError *sb = NULL;

				appunti_offerta_arretrata = false;
				if (appunti_offri(palco_appunti, &sb))
					registro_dice(REG_APPUNTI,
					              "⭐ APPUNTI: il client aveva annunciato PRIMA "
					              "che gli appunti si aprissero, e l'offerta e' "
					              "stata RIFATTA adesso: dentro il desktop la "
					              "voce «Incolla» ha di nuovo qualcosa da dare");
				else
					registro_dice(REG_APPUNTI,
					              "⛔ APPUNTI: l'offerta arretrata non e' "
					              "riuscita (%s): dentro il desktop non si "
					              "potra' incollare quel che il client ha "
					              "copiato",
					              sb ? sb->message : "nessun dettaglio");
				g_clear_error(&sb);
			}
		} else {
			/* ⛔ E se non si aprono NON si muore: `CODER.md` §4.2 — degradare,
			 *    non fallire.  Un utente senza appunti ha meno di quel che gli
			 *    spetta; un utente a cui la sessione cade non ha niente.
			 *    ⚠ Ma il ripiego si DICHIARA, o «gli appunti non funzionano» e
			 *    «gli appunti non sono mai partiti» hanno la stessa faccia. */
			registro_dice(REG_FIGLIO,
			              "⛔ gli appunti NON si aprono (%s): il desktop si vede "
			              "e si comanda, ma il copia-incolla fra i due mondi non "
			              "c'e'.  ⚠ La sessione resta in piedi, e questa riga e' "
			              "il ripiego dichiarato",
			              sbaglio_app ? sbaglio_app->message : "nessun dettaglio");
		}
		g_clear_error(&sbaglio_app);
	}

	/*
	 * ⭐⭐ E QUI, UNA VOLTA SOLA PER SESSIONE, LE TRE COSE CHE VANNO FATTE
	 *     QUANDO IL PALCO C'E' — e non prima, perche' prima non c'era una
	 *     sessione a cui dirle.
	 *
	 * ⛔ «Scritto» non e' «in vigore» (`REVIEWER.md` E1): le due verifiche non
	 *    servono a proteggere — proteggono la regola polkit e la sessione senza
	 *    seat — servono a **sapere se quelle protezioni ci sono davvero**.  E le
	 *    fa il figlio perche' e' l'utente: `[M]` root si sente rispondere «yes»
	 *    da logind, che guarda `CAP_SYS_BOOT` prima di polkit.
	 */
	{
		static bool gia_fatto;

		if (!gia_fatto) {
			sentinella *guardia;
			char dettaglio[192];

			gia_fatto = true;

			/* 1. ⛔ La sospensione, e non e' teorica: `[M]` la notifica
			 *    «Automatic Suspend» e' comparsa nel desktop remoto. */
			sessione_inibisci();

			guardia = sentinella_apri();
			if (!guardia) {
				registro_dice(REG_FIGLIO,
				              "⚠ senza bus di sistema non posso VERIFICARE "
				              "ne' l'headless ne' il divieto di spegnere: "
				              "le protezioni possono esserci, ⛔ ma da qui "
				              "non lo so — e «non lo so» non e' «va bene»");
			} else {
				/* 2. L'headless, che dal 15 agosto e' per costruzione. */
				dettaglio[0] = '\0';
				if (sentinella_senza_seat(guardia, dettaglio, sizeof dettaglio))
					registro_dice(REG_FIGLIO,
					              "⭐ VERIFICATO: la mia sessione non ha "
					              "seat (%s) ⇒ Mutter e' headless, e il "
					              "blocca-schermo di GNOME non ci revoca "
					              "cattura e input (§4.3-bis)",
					              dettaglio);
				else
					registro_dice(REG_FIGLIO,
					              "⛔⛔ LA MIA SESSIONE NON E' HEADLESS "
					              "(%s): questa sessione funziona finche' "
					              "nessuno blocca lo schermo, e poi Mutter "
					              "ci CHIUDE cattura e input rifiutando di "
					              "ricrearli.  ⚠ Non esco — I1: una "
					              "sessione con un rischio vale piu' di "
					              "nessuna sessione — ma questa riga e' il "
					              "fallimento dichiarato di §4.3-bis",
					              dettaglio[0] ? dettaglio : "senza dettaglio");

				/* 3. Le tre cinture di §4.7. */
				dettaglio[0] = '\0';
				if (sentinella_spegnimento_vietato(guardia, dettaglio,
				                                   sizeof dettaglio))
					registro_dice(REG_FIGLIO,
					              "⭐ VERIFICATO: da questa sessione NON si "
					              "spegne ne' si sospende la macchina (%s) "
					              "— §4.7, e le tre cinture sono in vigore",
					              dettaglio);
				else
					registro_dice(REG_FIGLIO,
					              "⛔⛔ DA QUESTA SESSIONE SI PUO' SPEGNERE "
					              "O SOSPENDERE LA MACCHINA (%s): §4.7 dice "
					              "che nessuno deve poterlo fare, e la "
					              "macchina e' di piu' persone.  ⇒ Manca la "
					              "regola polkit, o non copre tutte e "
					              "dodici le azioni",
					              dettaglio[0] ? dettaglio : "senza dettaglio");
				sentinella_chiudi(guardia);
			}
		}
	}

	return true;
}

/* ⛔⭐ E IL PALCO SI SMONTA DAVVERO, tutti e tre i pezzi e in quest'ordine.
 *
 *     Prima l'input (che parla con la sessione `RemoteDesktop` di `mut`), poi
 *     la cattura (che ha un filo suo e delle richiamate che girano di la'), poi
 *     `mut`.  ⚠ All'incontrario si distruggerebbe la sessione mentre qualcuno
 *     la sta usando.
 *
 * ⛔ E prima di tutto si RILASCIA quel che era rimasto giu' (`RCP.md` §11): il
 *    palco che se ne va non porta via un Ctrl premuto, e al rimontaggio
 *    l'utente si troverebbe un desktop inservibile senza collegare le due cose.
 */
static void smonta_il_palco(MutterSessione **m, Cattura **c)
{
	if (palco_input) {
		int quanti = input_rilascia_tutto(palco_input);
		if (quanti > 0)
			registro_dice(REG_FIGLIO,
			              "⭐ §7.3: il palco si smonta e %d fra tasti e "
			              "pulsanti erano rimasti giu': rilasciati",
			              quanti);
		input_chiudi(palco_input);
		palco_input = NULL;
	}
	/* ⛔⭐ E GLI APPUNTI SI CHIUDONO PRIMA DELLA SESSIONE, non dopo: le due
	 *     sottoscrizioni e il thread vivono su `mutter_bus()`, che e' della
	 *     `MutterSessione` chiusa tre righe piu' giu'.  ⚠ Chiudere al contrario
	 *     lascerebbe un thread che parla su un bus gia' andato.
	 * ⛔ E NON si chiama `DisableClipboard` (trappola 1 di `appunti.h`): chi la
	 *    chiamasse allo smontaggio si ritroverebbe, al rimontaggio, appunti
	 *    morti **per il resto della sessione grafica**. */
	if (palco_appunti) {
		appunti_chiudi(palco_appunti);
		palco_appunti = NULL;
		appunti_montaggio_libera();
	}
	if (*c) {
		cattura_ferma(*c);
		*c = NULL;
	}
	if (*m) {
		mutter_chiudi(*m);
		*m = NULL;
	}
}

/* ⛔ L'ingresso del figlio.  `main.c` ci arriva PRIMA di qualunque altra cosa,
 *    e non torna mai. */
void figlio_vive(int argc, char **argv)
{
	struct corpo_sono s;
	struct stat st;
	uint32_t tela_l, tela_a;
	const char *utente, *dir_rilievo;
	uid_t atteso;
	gid_t atteso_g;
	MutterSessione *mut = NULL;
	Cattura *cat = NULL;
	int uno = 1;
	uid_t r, e, sv;
	gid_t rg, eg, sg;
	/* ⭐ FASE 9 — quel che il padre ha scritto nella riga di comando, e che
	 *    questo processo deve ripetere a se stesso: vedi sotto. */
	bool f9_risale = false;
	uint32_t f9_tetto = 0;
	/* ⛔ `true`, e non `false` come le due qui sopra: questa cura nasce ACCESA
	 *    (24 agosto 2026), quindi l'assenza della parola in coda vuol dire
	 *    «accesa».  ⚠ E il figlio NON puo' chiedere il predefinito ad `audio.c`
	 *    e basta: deve poter dichiarare che cosa gli e' ARRIVATO, o «l'opzione
	 *    e' caduta nel passaggio» e «la cura non funziona» hanno la stessa
	 *    faccia (forma D5). */
	bool f9_audio_silenzio = true;

	/* `--figlio-interno <utente> <uid> <gid> <l> <a> <matricola> <rilievo>` */
	if (argc < 9)
		_exit(40);
	utente = argv[2];
	atteso = (uid_t)strtoul(argv[3], NULL, 10);
	atteso_g = (gid_t)strtoul(argv[4], NULL, 10);
	tela_l = (uint32_t)strtoul(argv[5], NULL, 10);
	tela_a = (uint32_t)strtoul(argv[6], NULL, 10);
	/* ⛔ La tela VOLUTA nasce uguale a quella di partenza e diverge al primo
	 *    `ADATTA_TELA`: e' quella che si richiede al RIMONTAGGIO del palco.
	 *    ⚠ Senza, un palco che cade dopo un ridimensionamento rinasceva alla
	 *    misura della riga di comando, e le bande tornavano senza che nessuna
	 *    riga collegasse le due cose. */
	tela_voluta_l = tela_l;
	tela_voluta_a = tela_a;
	mia_matricola = strtoull(argv[7], NULL, 10);
	dir_rilievo = argv[8];
	/* ⭐ Lo scatto se la tiene: vedi il riquadro sopra `scatto_dir`. */
	scatto_dir = dir_rilievo;
	/* ⭐ La parlantina, se il padre ce l'ha passata: vedi il riquadro in
	 *    `figli_esegui()`.  ⛔ Senza, ogni `registro_dettaglio` di questo file
	 *    e' scritto e non arriva a nessuno. */
	/* ⛔⭐⭐ E LE **TRE** CURE DELLA FASE 9 SI ACCENDONO QUI, DENTRO IL FIGLIO.
	 *
	 *      Il riquadro che spiega perche' non possono venire da nessun'altra
	 *      parte sta in `figlio.h`, sopra `figli_fase9()`: sono statiche del
	 *      processo, e il processo che apre i codificatori e' questo.
	 *
	 * ⚠ PRIMA di `prendi_il_palco()`, che apre gia' il primo codificatore: due
	 *   righe piu' in basso e la prima sessione nascerebbe senza la cura, con
	 *   la riga d'avvio a dire «spento» — cioe' il difetto travestito da
	 *   misura che tutta questa fase cerca di evitare.
	 * ⚠ Si scorre per NOME e non per posizione, come la parlantina: le prime
	 *   nove sono fisse, queste sono facoltative e possono mancare tutt'e due.
	 */
	for (int i = 9; i < argc; i++) {
		if (strcmp(argv[i], "--parlantina") == 0)
			registro_parlantina(true);
		else if (strcmp(argv[i], "--qualita-risale") == 0)
			f9_risale = true;
		else if (strcmp(argv[i], "--tetto-banda-mbit") == 0 && i + 1 < argc)
			f9_tetto = (uint32_t)strtoul(argv[++i], NULL, 10);
		/* ⛔⭐ E QUESTA SI LEGGE NEGATA, perche' nasce ACCESA (24 ago 2026): la
		 *     parola in coda e' l'ECCEZIONE al predefinito.  ⚠ Un'assenza qui
		 *     vuol dire «acceso», che e' il contrario delle due righe sopra —
		 *     ed e' il motivo per cui `f9_audio_silenzio` parte da `true`. */
		else if (strcmp(argv[i], "--niente-audio-silenzio") == 0)
			f9_audio_silenzio = false;
	}
	codificatore_qualita_risale(f9_risale);
	codificatore_tetto_banda(f9_tetto);
	/* ⛔ E il codificatore audio sta in QUESTO processo, come quello video: la
	 *    riga del valore IN VIGORE la scrive `audio.c` all'apertura di ogni
	 *    codificatore, ed e' la terza della terna (padre PASSERA' · figlio
	 *    RICEVUTO · in vigore). */
	audio_silenzio_taci(f9_audio_silenzio);

	signal(SIGTERM, SIG_DFL);
	signal(SIGINT, SIG_DFL);
	signal(SIGPIPE, SIG_IGN);
	/* ⭐ Lo scatto a comando: il riquadro sta sopra `scatto_segnale()`. */
	signal(SIGUSR1, scatto_segnale);
	signal(SIGUSR2, scatto_segnale);

	/* ⛔ Se il server muore, questo processo muore con lui: nessun orfano
	 *    attaccato al monitor virtuale di un utente.  ⚠ E si arma DOPO il calo
	 *    di privilegio, perche' un cambio di credenziali puo' azzerarlo — ⭐ e
	 *    per questo NON e' l'unica strada: l'EOF sul socket (il ciclo qui
	 *    sotto) chiude comunque, e due reti indipendenti sono due apposta. */
	prctl(PR_SET_PDEATHSIG, SIGTERM);

	/* ⛔⭐ E SI RICONTROLLA DI ESSERE CHI SI DEVE ESSERE, DOPO L'`exec`.
	 *     `diventa_ed_esegui()` l'ha gia' verificato, ma quello era un altro
	 *     programma: quel che vale qui e' quel che il NUCLEO dice adesso di
	 *     questo processo.  Un'immagine nuova che si fidasse del proprio
	 *     `argv` sarebbe un figlio che si dichiara da se'. */
	if (getresuid(&r, &e, &sv) != 0 || getresgid(&rg, &eg, &sg) != 0)
		_exit(41);
	if (r != atteso || e != atteso || sv != atteso || rg != atteso_g
	    || eg != atteso_g || sg != atteso_g) {
		registro_dice(REG_FIGLIO,
		              "⛔⛔ NON SONO CHI DOVREI ESSERE: mi volevano uid %ld gid "
		              "%ld e il nucleo dice uid %ld/%ld/%ld gid %ld/%ld/%ld.  "
		              "ESCO senza toccare niente: un figlio che gira come "
		              "l'utente sbagliato e' I3 violata in modo invisibile",
		              (long)atteso, (long)atteso_g, (long)r, (long)e, (long)sv,
		              (long)rg, (long)eg, (long)sg);
		_exit(42);
	}
	mio_uid = e;

	/* ⛔ Anche il figlio vuole il timbro del nucleo sui messaggi del padre: il
	 *    legame si verifica **ai due capi**.  ⚠ `SO_PEERCRED` qui direbbe la
	 *    verita' (il socketpair l'ha creato root), ma dev'essere la stessa
	 *    prova che fa il padre — e la sua e' per messaggio. */
	setsockopt(fd_figlio, SOL_SOCKET, SO_PASSCRED, &uno, sizeof uno);

	memset(&s, 0, sizeof s);
	s.uid = r;
	s.euid = e;
	s.suid = sv;
	s.gid = rg;
	s.egid = eg;
	s.sgid = sg;
	s.pid = (uint32_t)getpid();
	s.ppid = (uint32_t)getppid();
	s.descrittori = quanti_descrittori();
	snprintf(s.utente, sizeof s.utente, "%s", utente);
	snprintf(s.runtime, sizeof s.runtime, "%s",
	         getenv("XDG_RUNTIME_DIR") ? getenv("XDG_RUNTIME_DIR") : "(nessuna)");
	/* ⛔ «C'e'» e «e' sua» sono due fatti diversi: una cartella di runtime di
	 *    qualcun altro sarebbe un permesso negato molto piu' tardi. */
	if (s.runtime[0] != '(' && stat(s.runtime, &st) == 0 && st.st_uid == e)
		s.runtime_c_e = 1;
	{
		char percorso[224];
		snprintf(percorso, sizeof percorso, "%s/bus", s.runtime);
		if (s.runtime_c_e && stat(percorso, &st) == 0)
			s.socket_bus_c_e = 1;
	}

	registro_dice(REG_FIGLIO,
	              "⭐ sono il figlio di «%s»: pid %u, uid %u (chiesto al nucleo, "
	              "non dedotto), %u descrittori aperti — la porta del server NON "
	              "e' fra questi",
	              utente, s.pid, s.euid, s.descrittori);

	/* ⛔⭐⭐ I PARAMETRI DELLA FASE 9 SI SCRIVONO ALLA NASCITA — 23 agosto 2026.
	 *
	 *      La regola e' gia' scritta, e sta in `src/riavvia-7700.sh`: *«il
	 *      valore IN VIGORE il server lo scrive all'avvio, cosi' non si prova
	 *      un tetto credendo di provarne un altro»*.  ⛔ Valeva per i tre
	 *      orologi di §5.3 e NON per quel che governa immagine e ritmo — cioe'
	 *      proprio le due grandezze che la fase 9 va a tarare.
	 *
	 * ⛔ E LA TARATURA SENZA QUESTE RIGHE NON E' UNA MISURA.  «Ho provato QP
	 *    26» e' una frase che vale solo se qualcuno ha scritto che era 26: un
	 *    numero cambiato in un `#define` e dimenticato produce un banco intero
	 *    di numeri veri attribuiti al valore sbagliato — e nessuno se ne
	 *    accorge, perche' i fotogrammi escono lo stesso.
	 *
	 * ⚠ E QUI SI SCRIVE QUEL CHE IL FIGLIO **CHIEDE**, non quel che il
	 *   codificatore **fa**: sono due cose diverse e vivono in due file.  Il QP
	 *   accettato davvero, i tetti e la conferma dell'entrypoint li scrive
	 *   `codificatore.c` quando apre — «scritto» non e' «in vigore»
	 *   (`REVIEWER.md` E1), e queste righe sono la meta' «chiesto» del
	 *   confronto, non il verdetto.
	 *
	 * ⚠ La tela e' quella della NASCITA: §4.5 la puo' cambiare a sessione
	 *   aperta, e il valore nuovo lo scrive la riga «codificatore APERTO».
	 * ⚠ La profondita' NON c'e' apposta: alla nascita non e' negoziata, e
	 *   scriverne una qui sarebbe rimettere a mano la bugia del 17 agosto. */
	registro_dice(REG_FIGLIO,
	              "⭐⛔ PARAMETRI IN VIGORE (fase 9), quel che il figlio CHIEDE: "
	              "cadenza %d/s · tela alla nascita %ux%u · GOP INFINITO "
	              "(chiavi_ogni = 0: chiavi solo a richiesta, §5.2 — e' una "
	              "scelta, non una dimenticanza)",
	              MOVIMENTO_FPS, tela_l, tela_a);
	registro_dice(REG_FIGLIO,
	              "⭐⛔ PARAMETRI IN VIGORE (fase 9), qualita' e codificatore "
	              "CHIESTI: QP %d in hardware · CRF %d sul ripiego in software "
	              "(due grandezze diverse, non si confrontano) · nodo %s · "
	              "entrypoint %s",
	              QP_HARDWARE, CRF_SOFTWARE, NODO_RENDERING,
	              potenza_nome(POTENZA_RENDERING));

	/* ⛔⭐⭐ E QUESTA E' LA RIGA CHE FA CADERE LA FORMA D5 — «un binario stantio
	 *      resta verde».
	 *
	 * ⛔ Un'opzione accettata dal padre e caduta nel passaggio padre → figlio
	 *    ha ESATTAMENTE la stessa faccia di una cura che non funziona: il
	 *    banco misura, non vede differenza, e il rosso finisce sull'imputato
	 *    sbagliato.  ⇒ Chi dichiara di averla ricevuta e' il figlio, che l'ha
	 *    letta dal proprio `argv` — non il padre, che l'ha solo scritta.
	 *
	 * ⚠ E' la meta' «ricevuto» di tre righe che si leggono in fila:
	 *      1. `figli_fase9()` nel padre — «che cosa PASSERO'»;
	 *      2. questa — «che cosa mi e' ARRIVATO»;
	 *      3. `codificatore.c` all'apertura — «che cosa e' IN VIGORE».
	 *    Se le tre non concordano, il punto in cui si perde e' fra le due che
	 *    divergono, e non c'e' da indovinare. */
	registro_dice(REG_FIGLIO,
	              "⭐⛔ PARAMETRI IN VIGORE (fase 9), quel che il figlio ha "
	              "RICEVUTO nella sua riga di comando: risalita della qualita' "
	              "%s · tetto di banda %s (pavimento %u Mbit/s) · ⭐ silenzio "
	              "dell'audio %s — ⚠ chiesti al "
	              "codificatore adesso, prima del primo palco.  Che li abbia "
	              "presi lo dice la riga «codificatore APERTO» (video) e la riga "
	              "«cura del silenzio digitale» (audio)",
	              f9_risale ? "ACCESA" : "spenta (I6)",
	              f9_tetto ? "ACCESO" : "spento (I6)", f9_tetto,
	              f9_audio_silenzio
	                  ? "ACCESO (predefinito dal 24 ago 2026)"
	                  : "SPENTO a mano (--niente-audio-silenzio)");

	if (!manda(MSG_SONO, &s, sizeof s, NULL, 0)) {
		registro_dice(REG_FIGLIO, "⛔ non riesco a presentarmi al padre (%s)",
		              strerror(errno));
		_exit(43);
	}

	/* ⛔⭐ E SI PRENDE IL PALCO SUBITO, senza aspettare che qualcuno lo chieda.
	 *
	 *     La ragione e' un numero: §4.4-bis impone al server un secondo fisso
	 *     prima di rispondere a `CREDENZIALI`, e la sessione RCP non puo'
	 *     arrivare a `SESSIONE` prima.  ⇒ Fra «PAM ha detto si'» e «serve un
	 *     fotogramma» c'e' **almeno un secondo garantito dal protocollo**, ed e'
	 *     tutto il tempo che questo figlio ha per nascere, collegarsi al bus,
	 *     catturare e codificare.  Aspettare una richiesta lo butterebbe via. */
	if (!prendi_il_palco(tela_l, tela_a, dir_rilievo, true, &mut, &cat)) {
		/* ⛔⭐ E SE ALLA NASCITA IL PALCO NON C'E', NON SI RESTA COSI' — e' il
		 *     secondo difetto gemello, `[M]` dalla sessione vera dell'utente:
		 *     un figlio nato senza sessione grafica non ne riprovava **mai**
		 *     un'altra, e al login successivo l'invariante I2 gli consegnava
		 *     quel figlio li'.  L'utente ha visto «niente desktop» due volte
		 *     di fila per questa ragione. */
		registro_dice(REG_FIGLIO,
		              "⛔ SENZA PALCO alla nascita: la sessione grafica di "
		              "«%s» non c'e' (ancora).  ⚠ NON esco — §8.3 vieta di "
		              "staccare — e NON resto fermo: riprovo, la prima volta "
		              "fra %d ms",
		              utente, PALCO_RIPROVA_MIN_MS);
		palco_riprova_ms = registro_ora_ms() + PALCO_RIPROVA_MIN_MS;
		palco_attesa_ms = PALCO_RIPROVA_MIN_MS;
	}

	/* ═══════════════════════════════════════════════════════════════════ */
	/* ⭐⭐ IL CICLO DELLA FASE 3 — cattura, codifica, manda; e ascolta.    */
	/*                                                                     */
	/* ⛔ DUE COSE DA FARE E UN PROCESSO SOLO, e l'ordine conta.  Il ciclo  */
	/*    guarda PRIMA se il padre ha detto qualcosa (che non aspetta:     */
	/*    `poll` con zero) e POI cattura (che aspetta).  Al contrario, un   */
	/*    `MSG_SPEGNITI` o una chiave chiesta resterebbero fermi per tutta  */
	/*    l'attesa della cattura — cioe' fino a un quarto di secondo, che   */
	/*    sul ritardo di `SPECIFICHE.md` §3.2 e' cinque volte il tetto.     */
	/*                                                                     */
	/* ⛔ E QUANDO NESSUNO GUARDA NON SI CATTURA: `codec_chiesto` a zero    */
	/*    vuol dire che l'ultima sessione se n'e' andata.  ⚠ NON e'        */
	/*    l'invariante I1 al contrario — I1 vieta di calare il ritmo per    */
	/*    prudenza **mentre qualcuno guarda**; qui non guarda nessuno, e il */
	/*    palco (I4) resta in piedi: si ferma solo il ciclo.  Allora si     */
	/*    aspetta sul socket, e il processo costa zero.                     */
	for (;;) {
		uint8_t busta[BUSTA_MAX];
		struct testa t;
		struct ucred chi;
		bool c_e = false;
		ssize_t letti;
		struct pollfd pf;
		int pronto;
		bool fine = false;

		/*
		 * ⛔⭐⭐ IL BATTITO DEL CICLO, e serve perche' senza di lui ho passato
		 *       una giornata a leggere il sorgente invece che i fatti.
		 *
		 * `[M]` 16 agosto 2026: nei giri lenti passavano DICIOTTO SECONDI fra
		 * due righe che nel codice sono a poche istruzioni di distanza, e in
		 * mezzo il figlio non scriveva niente.  Da fuori i casi possibili erano
		 * tre — bloccato in una chiamata, fermo ad aspettare, o il ciclo che non
		 * gira — ⛔ e i primi due li avevo gia' strumentati e tacevano.  ⇒ Resta
		 * il terzo, e per vederlo serve una riga che si scrive **comunque**.
		 *
		 * ⚠ Una al secondo, e solo finche' non c'e' palco: quando il desktop va,
		 *   questa riga non compare mai.
		 */
		if (!cat) {
			static uint64_t battito_ms;
			uint64_t adesso = registro_ora_ms();

			if (adesso - battito_ms >= 1000) {
				battito_ms = adesso;
				registro_dice(REG_FIGLIO,
				              "♥ ciclo VIVO senza palco: codec %u, tela voluta "
				              "%ux%u, prossimo tentativo fra %lld ms",
				              (unsigned)codec_chiesto, tela_voluta_l, tela_voluta_a,
				              (long long)((int64_t)palco_riprova_ms - (int64_t)adesso));
			}
		}

		/* ── 1. quel che il padre ha da dire, senza aspettare ────────── */
		for (;;) {
			struct pollfd due[2];
			int quanti = 1;
			int fd_ei;

			pf.fd = fd_figlio;
			pf.events = POLLIN;
			pf.revents = 0;
			due[0] = pf;
			/* ⭐⭐ E IL DESCRITTORE DI `libei` STA NELLO STESSO `poll`, non in
			 *     un sondaggio a intervalli.  ⛔ Non e' una comodita': un
			 *     sondaggio ogni N millisecondi REGALA fino a N millisecondi
			 *     all'utente **su ogni gesto**, e il tetto di `CODER.md`
			 *     §1-bis e' 50 ms in tutto.  ⚠ Quando non si cattura questo
			 *     `poll` aspetta un secondo intero: senza questa riga, un
			 *     click su un desktop fermo arriverebbe **fino a un secondo
			 *     dopo**. */
			fd_ei = palco_input ? input_descrittore(palco_input) : -1;
			if (fd_ei >= 0) {
				due[1].fd = fd_ei;
				due[1].events = POLLIN;
				due[1].revents = 0;
				quanti = 2;
			}
			/* ⛔ Zero quando si sta catturando, il tetto quando non si
			 *    cattura: cosi' il processo fermo non gira a vuoto e quello
			 *    che lavora non perde tempo.
			 * ⛔⭐ E «si sta catturando» vuole DUE cose: che qualcuno guardi
			 *     **e** che il palco ci sia.  Con il solo `codec_chiesto`, un
			 *     figlio che ha perso il palco mentre un client guardava
			 *     girava con `poll` a zero — cioe' bruciava un nucleo intero
			 *     senza catturare niente.  `[M]` e' la meta' silenziosa del
			 *     difetto del 14 agosto: il registro si cura togliendo una
			 *     riga, questo no. */
			/* ⛔⭐⭐ E L'ATTESA DEL `poll` SI ACCORCIA QUANDO C'E' UN
			 *       TENTATIVO DOVUTO — 16 agosto 2026, e senza questa riga
			 *       la cura di `PALCO_NASCITA_RIPROVA_MS` non arrivava a
			 *       terra.
			 *
			 * ⛔ Il ciclo, senza palco, dormiva **un secondo fisso**.  ⇒ Un
			 *    ri-tentativo fissato fra 200 ms non poteva scattare a 200
			 *    ms: scattava al risveglio dopo, cioe' a mille.  Il numero
			 *    piccolo sarebbe rimasto scritto nel sorgente e falso nei
			 *    fatti — ed e' la forma «scritto non e' in vigore» che
			 *    `REVIEWER.md` chiama E1, dentro la cura di un difetto di
			 *    tempo.
			 *
			 * ⭐ Adesso ci si sveglia QUANDO il tentativo e' dovuto, non a
			 *    cadenza fissa: il secondo resta come tetto (il padre deve
			 *    poter parlare comunque), ma non e' piu' un pavimento. */
			{
				int attesa_ms = (codec_chiesto && cat) ? 0 : 1000;

				/*
				 * ⛔⭐⭐ E LO ZERO VUOL DIRE «ADESSO», NON «NON ARMATO» — 16
				 *       agosto 2026, ed e' la SECONDA volta che questo numero
				 *       inganna in questo file.
				 *
				 * `[M]` La tela del cliente arriva, il gestore mette
				 * `palco_riprova_ms = 0` per dire «riprova subito», e questo
				 * `poll` — che leggeva lo zero come «nessun tentativo in
				 * agenda» — si metteva a dormire.  ⇒ Fra «la tela e' arrivata»
				 * e «entro nel montaggio» passavano **2000 ms tondi**, cioe'
				 * due dormite intere, e si buttava via meta' del guadagno della
				 * cura della tela.
				 *
				 * ⚠ Lo zero come «non armato» aveva gia' fatto danni qui il 15
				 *   agosto.  ⇒ Adesso ha UN significato solo: «il tentativo e'
				 *   dovuto», e l'attesa e' sempre «quanto manca», zero
				 *   compreso.
				 *
				 * ⛔ E non si gira a vuoto: il tentativo che segue rimette
				 *    subito `palco_riprova_ms` nel futuro, quindi lo zero vale
				 *    per un giro solo.
				 */
				if (!cat) {
					uint64_t adesso = registro_ora_ms();

					attesa_ms = palco_riprova_ms > adesso
					                ? (int)(palco_riprova_ms - adesso)
					                : 0;
					if (attesa_ms > 1000)
						attesa_ms = 1000;
				}
				/* ⛔⭐ E CON L'AUDIO ACCESO IL CICLO NON PUO' DORMIRE UN
				 *     SECONDO.  L'anello si riempie a 48 000 fotogrammi al
				 *     secondo qualunque cosa faccia il video: un'attesa da
				 *     1000 ms lo farebbe traboccare **mentre il desktop e'
				 *     fermo**, cioe' proprio quando l'utente sta ascoltando
				 *     musica senza toccare niente.
				 * ⚠ 5 ms e' un blocco di PCM (§5.3): il ciclo si sveglia in
				 *   tempo per portarne via uno per volta, invece di
				 *   accumularne e poi buttarli. */
				if (audio_codec && attesa_ms > 5)
					attesa_ms = 5;
				pronto = poll(due, (nfds_t)quanti, attesa_ms);
			}
			pf.revents = due[0].revents;
			/* ⛔⛔ E QUI SI PAGA IL DEBITO VERSO CHI STA INCOLLANDO, a ogni
			 *      risveglio del ciclo — anche quando il `poll` e' scaduto a
			 *      vuoto.
			 *
			 *      ⚠ E' l'unico posto in cui il fondo di `APPUNTI_ATTESA_MS`
			 *        puo' scattare: il thread degli appunti non ha un orologio
			 *        (aspetta segnali di D-Bus, e se non ne arrivano dorme per
			 *        sempre), quindi una richiesta senza risposta resterebbe
			 *        appesa finche' qualcuno non copia qualcos'altro.
			 *      ⛔ Cioe' senza questa riga il fondo esisterebbe scritto e non
			 *        scatterebbe mai — la forma peggiore di una protezione:
			 *        quella che si legge nel codice e non c'e'. */
			appunti_scadi(registro_ora_ms());
			/* ⭐ Se ha parlato `libei`, lo si serve SUBITO — prima ancora di
			 *    leggere il padre: e' il percorso su cui si misura il
			 *    ritardo. */
			if (pronto > 0 && quanti == 2 && due[1].revents)
				input_gira(palco_input);
			if (pronto < 0) {
				if (errno == EINTR)
					continue;
				fine = true;
				break;
			}
			if (pronto == 0)
				break;
			/* ⛔⛔⛔ E QUI STAVANO I QUATTRO SECONDI CHE L'UTENTE ASPETTAVA.
			 *
			 * `[M]` 14 agosto 2026, pila letta con `gdb` a 2,6 s dal login:
			 * il figlio era fermo in `recvmsg` a `figlio.c:336`, cioe' in
			 * questa riga, su **fd 3** — il socket del padre.
			 *
			 * ⛔ La riga sopra calcolava `pf.revents` e **nessuno lo
			 *    guardava**.  Quando il `poll` si sveglia perche' ha parlato
			 *    `libei` (due[1]) e il padre NON ha detto niente, `pronto` e'
			 *    comunque > 0: si arrivava qui e si leggeva lo stesso — e il
			 *    capo del FIGLIO e' **bloccante di proposito** (il padre mette
			 *    `O_NONBLOCK` solo sul suo, e `socketpair` fa due descrizioni
			 *    di file distinte).  ⇒ Il figlio restava dentro `recvmsg`
			 *    finche' il padre non gli scriveva qualcosa, e **il ciclo dei
			 *    fotogrammi non girava affatto**: il registro lo diceva, e
			 *    nessuno l'aveva letto — *«0 fotogrammi consegnati, **0 attese
			 *    a vuoto**»* per quattro secondi.
			 *
			 * ⚠ Ed e' la ragione per cui la tesi *«il ritardo non e' nostro,
			 *   e' Mutter che non consegna su un desktop fermo»* era **falsa**:
			 *   Mutter aveva i fotogrammi, e noi non eravamo li' a prenderli.
			 *   ⭐ La riga di registro che avrebbe dovuto smascherarlo diceva
			 *   *«scena ferma: Mutter consegna solo quando qualcosa cambia»* —
			 *   cioe' accusava il compositore di un difetto nostro. */
			if (!pf.revents)
				break;

			letti = ricevi_con_credenziali(fd_figlio, busta, sizeof busta, &chi,
			                               &c_e);
			if (letti == 0) {
				registro_dice(REG_FIGLIO,
				              "il padre ha chiuso il socket: smonto il palco ed "
				              "esco.  ⚠ E' la SECONDA rete di sicurezza, quella "
				              "che non dipende da PR_SET_PDEATHSIG");
				fine = true;
				break;
			}
			if (letti < 0) {
				if (errno == EINTR)
					continue;
				if (errno == EAGAIN || errno == EWOULDBLOCK)
					break;
				fine = true;
				break;
			}
			if ((size_t)letti < sizeof t)
				continue;
			memcpy(&t, busta, sizeof t);
			if (!magia_giusta(&t))
				continue;
			/* ⛔ Il padre dev'essere root E dev'essere il mio processo padre.
			 *    Un messaggio senza timbro del nucleo non e' un messaggio del
			 *    padre. */
			if (!c_e || chi.uid != 0) {
				registro_dice(REG_FIGLIO,
				              "⛔ un messaggio che dice di venire dal padre e "
				              "non porta il timbro di root (uid %ld): SCARTATO",
				              c_e ? (long)chi.uid : -1L);
				continue;
			}
			if (t.uid_dichiarato != (uint32_t)mio_uid) {
				registro_dice(REG_FIGLIO,
				              "⛔ il padre crede che io sia uid %lu e il nucleo "
				              "dice %ld: NON rispondo",
				              (unsigned long)t.uid_dichiarato, (long)mio_uid);
				continue;
			}
			if (t.tipo == MSG_SPEGNITI) {
				fine = true;
				break;
			}
			if (t.tipo == MSG_VIDEO) {
				struct corpo_video cv;
				if ((size_t)letti < sizeof t + sizeof cv)
					continue;
				memcpy(&cv, busta + sizeof t, sizeof cv);
				/* ⛔⭐ IL TETTO E' 3 DAL 20 AGOSTO 2026 (H.264, §1.13-ter), e
				 *     questa riga e' costata un giro: il padre negoziava gia'
				 *     il codec 3 e il figlio lo RIFIUTAVA qui — «il padre
				 *     chiede il codec 3, che §6.2 non definisce» — con la
				 *     sessione viva, zero fotogrammi e la pagina che non
				 *     sapeva perche'.
				 * ⚠ Il numero massimo sta in UN posto solo: qui.  Un secondo
				 *   controllo altrove con un numero suo e' esattamente il
				 *   difetto appena pagato. */
				if (cv.codec > CODIFICATORE_H264) {
					registro_dice(REG_FIGLIO,
					              "⛔ il padre chiede il codec %u, che §6.2 non "
					              "definisce: NON cambio niente",
					              cv.codec);
					continue;
				}
				/* ⭐ Il ritorno dal terzo stato al primo: qualcuno vuole di
				 *    nuovo un desktop.  ⛔ E' QUI e non altrove perche'
				 *    questo e' l'unico messaggio che dice «c'e' un client
				 *    che guarda»: la nascita della sessione deve seguire
				 *    una VOLONTA', non un orologio. */
				if (cv.codec != 0 && sessione_chiusa_dall_utente) {
					sessione_chiusa_dall_utente = false;
					registro_dice(REG_FIGLIO,
					              "⭐ §7.6: si riattacca qualcuno dopo un'uscita "
					              "— da adesso la sessione grafica si puo' far "
					              "rinascere, e sara' NUOVA");
				}
				if (cv.codec != codec_chiesto)
					registro_dice(REG_FIGLIO,
					              cv.codec
					                  ? "⭐ FASE 3: il ciclo dei fotogrammi si "
					                    "ACCENDE, codec %u, %d/s chiesti alla "
					                    "cattura"
					                  : "il ciclo dei fotogrammi si SPEGNE "
					                    "(codec %u): non guarda piu' nessuno, e "
					                    "il palco resta in piedi (I4).  %d/s",
					              cv.codec, MOVIMENTO_FPS);
				/* ⛔ E la profondita' con lui: sono lo stesso fatto, e
				 *    separarli e' esattamente quel che si e' appena curato. */
				if (cv.profondita && cv.profondita != profondita_chiesta) {
					registro_dice(REG_FIGLIO,
					              "⭐ §4.3: il padre ha negoziato %u bit "
					              "(prima %u)",
					              cv.profondita, profondita_chiesta);
					profondita_chiesta = cv.profondita;
				}
				/* ⛔⭐ E IL LIVELLO CON LORO — §4.3 riga 701, 23 agosto 2026.
				 *
				 * ⚠ La condizione NON e' `cv.livello_x10 && ...` come per la
				 *   profondita': qui lo ZERO E' UN VALORE — vuol dire «questo
				 *   client non dichiara nessun livello», e passare da 5.1 a
				 *   «nessun tetto» e' un cambiamento vero che va registrato e
				 *   ubbidito.  ⛔ Trattarlo come «non me l'ha detto» terrebbe
				 *   in vigore il tetto del client precedente, cioe' l'errore
				 *   che I4 (il palco sopravvive al client) rende possibile.
				 * ⚠ `cv.codec &&` c'e' perche' «spegni» (codec 0) porta zeri in
				 *   tutti i campi: non e' un client che dichiara «nessun
				 *   livello», e' nessun client. */
				if (cv.codec && cv.livello_x10 != livello_chiesto_x10) {
					if (cv.livello_x10)
						registro_dice(REG_FIGLIO,
						              "⭐ §4.3: il client dichiara "
						              "video.livello=%u.%u (prima %s) — lo "
						              "IMPORRO' al codificatore, e poi lo "
						              "rileggo dall'SPS",
						              cv.livello_x10 / 10u,
						              cv.livello_x10 % 10u,
						              livello_chiesto_x10 ? "un altro" : "nessuno");
					else
						registro_dice(REG_FIGLIO,
						              "⚠ §4.3: nessun video.livello dichiarato "
						              "(prima %u.%u) — NESSUN TETTO, e non ne "
						              "invento uno: il livello prodotto si "
						              "scrive lo stesso",
						              livello_chiesto_x10 / 10u,
						              livello_chiesto_x10 % 10u);
					livello_chiesto_x10 = cv.livello_x10;
				}
				codec_chiesto = cv.codec;
				/* ⛔ §5.2: il debito si segna sul codec CHIESTO, non su tutti.
				 *    Chiedere una chiave per l'HEVC non ne produce una
				 *    sull'AV1, e segnarli insieme darebbe una chiave a chi non
				 *    l'ha chiesta. */
				if (cv.chiave && cv.codec)
					debito_chiave[cv.codec] = true;
				continue;
			}
			if (t.tipo == MSG_AUDIO) {
				struct corpo_audio ca;

				if ((size_t)letti < sizeof t + sizeof ca)
					continue;
				memcpy(&ca, busta + sizeof t, sizeof ca);
				if (ca.codec > 2) {
					registro_dice(REG_FIGLIO,
					              "⛔ il padre chiede il codec audio %u, che "
					              "§6.3 non definisce: NON cambio niente",
					              ca.codec);
					continue;
				}
				/* ⛔ Il codec INVARIATO non e' un messaggio inutile: e'
				 *    qualcuno che si e' appena collegato, e l'invariante I5
				 *    gli deve il volume al massimo.  ⚠ Rimettere in piedi
				 *    cattura e codificatore invece no: quello
				 *    interromperebbe il suono a chi sta gia' ascoltando. */
				if (ca.codec && ca.codec == audio_codec) {
					suono_volume_massimo(son);
					registro_dettaglio(REG_FIGLIO,
					                   "si collega qualcun altro: volume al "
					                   "massimo (I5), cattura invariata");
					continue;
				}
				audio_regola_figlio(ca.codec);
				continue;
			}
			/* ⭐⭐ FASE 7 — «IL CLIENT HA COPIATO DEL TESTO»: si offre alla
			 *     sessione, e da li' in poi qualcuno potra' incollarlo.
			 * ⛔ Non porta il testo, ed e' il «si annuncia e poi si tira» di
			 *    §7.4: il testo si chiede quando qualcuno incolla davvero. */
			if (t.tipo == MSG_APPUNTI_OFFERTA) {
				GError *sb = NULL;

				if (!palco_appunti) {
					/* ⚠ Non e' un guasto: e' il palco che non c'e' ancora, o
					 *   gli appunti che non si sono aperti (il ripiego
					 *   dichiarato piu' su).  Si dice, e si va avanti. */
					appunti_offerta_arretrata = true;
					registro_dettaglio(REG_APPUNTI,
					                   "il client ha copiato del testo e gli "
					                   "appunti della sessione non ci sono "
					                   "ANCORA: l'offerta si RIFA' appena si "
					                   "aprono, invece di cadere");
					continue;
				}
				if (!appunti_offri(palco_appunti, &sb))
					registro_dice(REG_APPUNTI,
					              "⛔ l'offerta alla sessione non e' riuscita "
					              "(%s): dentro il desktop non si potra' "
					              "incollare quel che il client ha copiato",
					              sb ? sb->message : "nessun dettaglio");
				g_clear_error(&sb);
				continue;
			}
			/* ⭐⭐ E LA RISPOSTA A CHI STA INCOLLANDO, che arriva **a pezzi**. */
			if (t.tipo == MSG_APPUNTI_DAL_CLIENT) {
				struct corpo_appunti ca;

				if ((size_t)letti < sizeof t + sizeof ca)
					continue;
				memcpy(&ca, busta + sizeof t, sizeof ca);
				if ((size_t)letti < sizeof t + sizeof ca + ca.pezzo)
					continue;
				appunti_dal_client(&ca, busta + sizeof t + sizeof ca);
				continue;
			}
			if (t.tipo == MSG_DISPOSIZIONE) {
				struct corpo_disposizione cd;

				if ((size_t)letti < sizeof t + sizeof cd)
					continue;
				memcpy(&cd, busta + sizeof t, sizeof cd);
				/* ⛔ Il NUL si impone NOI: la busta arriva da un socket, e
				 *    una stringa non terminata letta come tale e' un difetto
				 *    di memoria, non di tastiera. */
				cd.nome[sizeof cd.nome - 1] = '\0';
				/* ⚠ E se il palco non c'e' ancora, si DICHIARA: «non l'ho
				 *   applicata» e «non c'era niente da applicare» sono due
				 *   fatti diversi (`LEZIONI.md` §1.9 regola 1). */
				if (!palco_input) {
					/* ⛔ NON si butta: si TIENE.  `rcp.c` la chiede quando
					 *    `SESSIONE` e' partita, e `libei` si apre qualche
					 *    centesimo dopo — buttarla qui vorrebbe dire che la
					 *    cura funziona su ogni attacco tranne il PRIMO. */
					snprintf(disposizione_in_attesa,
					         sizeof disposizione_in_attesa, "%s", cd.nome);
					registro_dice(REG_FIGLIO,
					              "⚠ disposizione «%s» chiesta ma il canale "
					              "di input non c'e' ancora: TENUTA, si "
					              "applica all'apertura del palco",
					              cd.nome);
				}
				else
					input_disposizione(palco_input, cd.nome);
				continue;
			}
			if (t.tipo == MSG_INPUT) {
				struct corpo_input ci;
				int e;

				if ((size_t)letti < sizeof t + sizeof ci)
					continue;
				memcpy(&ci, busta + sizeof t, sizeof ci);
				/* ⛔⭐ LA TELA NON E' UN INPUT, e passa PRIMA della guardia qui
				 *     sotto.  ⚠ Difetto trovato rileggendo, il 15 agosto 2026:
				 *     `FIGLI_INPUT_RITELA` viaggia dentro `MSG_INPUT` per non
				 *     avere due buste sul filo fra padre e figlio — ⛔ ma la
				 *     guardia «non ho un canale verso il compositore» e' dei
				 *     GESTI, e applicata alla tela avrebbe legato il
				 *     ridimensionamento del monitor all'apertura di `libei`.
				 *     ⇒ Il sintomo sarebbe stato: una sessione in cui l'input
				 *     non si e' aperto (un `libei` che non risponde) resta anche
				 *     con le bande nere e il testo interpolato, **e nessuna riga
				 *     collega le due cose**. */
				/*
				 * ⭐⭐ §7.6 — «TERMINA LA SESSIONE», e sta QUI, prima della
				 *     guardia dei gesti, per la stessa ragione della tela:
				 *     uscire non e' un gesto, e legarlo all'apertura di
				 *     `libei` vorrebbe dire che in una sessione dove l'input
				 *     non si e' aperto **non si puo' nemmeno uscire**.
				 *
				 * ⛔ E il congedo `0x10` e' GIA' PARTITO quando questa riga
				 *    gira: lo manda `rcp.c` prima di chiamare il gancio,
				 *    perche' quando il compositore cade il palco cade con lui
				 *    e il canale non serve piu' (`RCP.md` §7.6).
				 */
				if (ci.azione == FIGLI_INPUT_TERMINA) {
					/* ⛔ Si dice la causa VERA, non quella di sempre: questa
					 *    riga per un giorno ha detto «l'utente ha chiesto»
					 *    anche quando a chiedere era un orologio. */
					registro_dice(REG_FIGLIO,
					              ci.a == FIGLI_USCITA_ABBANDONO
					                  ? "⭐ §5.3: la sessione e' ABBANDONATA — "
					                    "chiudo la sessione grafica e con lei i "
					                    "suoi programmi.  ⚠ Non l'ha chiesto "
					                    "nessuno: e' scaduto il tetto, e il "
					                    "numero sta nella riga del padre"
					                  : "⭐ §7.6: l'utente ha chiesto di USCIRE — "
					                    "chiudo la sessione grafica e con lei i "
					                    "suoi programmi.  Al prossimo attacco ne "
					                    "nascera' una NUOVA");
					if (!sessione_termina())
						registro_dice(REG_FIGLIO,
						              "⛔ la sessione grafica NON e' "
						              "finita: l'utente ha chiesto di "
						              "uscire e il desktop e' ancora "
						              "li'.  ⚠ Il client e' gia' stato "
						              "congedato con 0x10, quindi "
						              "adesso le due verita' non "
						              "combaciano — e questa riga e' "
						              "l'unico posto in cui si vede");
					continue;
				}

				if (ci.azione == FIGLI_INPUT_RITELA) {
					CatturaRitela r;
					uint32_t ora_l = 0, ora_a = 0;

					/* ⛔ La tela VOLUTA si ricorda PRIMA di provarci, e non e'
					 *    la stessa cosa di `tela_l`/`tela_a` (che sono quel che
					 *    il palco DA'): serve al rimontaggio.  ⚠ Senza, un palco
					 *    che cade dopo un ridimensionamento rinasce alla misura
					 *    di prima e le bande tornano — e nessuna riga collega le
					 *    due cose. */
					tela_voluta_l = (uint32_t)ci.a;
					tela_voluta_a = (uint32_t)ci.b;
					/* ⭐ Da adesso la tela e' QUELLA DEL CLIENTE, non il ripiego
					 *    della riga di comando: vedi `tela_dal_cliente`. */
					if (!tela_dal_cliente) {
						tela_dal_cliente = true;
						/* ⭐ E si riprova SUBITO: aspettare il prossimo
						 *    ri-tentativo vorrebbe dire buttare via il mezzo
						 *    secondo che si e' appena aspettato apposta. */
						palco_riprova_ms = 0;
						registro_dice(REG_FIGLIO,
						              "⭐ la tela del CLIENTE e' arrivata (%ux%u): "
						              "da adesso si puo' far nascere la sessione "
						              "alla misura giusta, senza ridimensionarla "
						              "dopo",
						              tela_voluta_l, tela_voluta_a);
					}

					if (!cat) {
						/*
						 * ⛔⛔ E QUI SI TACE, DI PROPOSITO — e fino al 16 agosto
						 *     2026 si rispondeva «non ce l'ho fatta» subito.
						 *
						 * ⭐ Quella risposta sembrava una gentilezza — «lo dico
						 *    subito invece di farlo aspettare» — ⛔ ed era la
						 *    causa delle BANDE NERE viste dall'utente il 16
						 *    agosto, per una catena in quattro passi:
						 *
						 *      1. il client chiede 2544x926 mentre il palco non
						 *         c'e' ancora (server appena riavviato);
						 *      2. rispondiamo `NON_ORA`, e `rcp.c` CHIUDE la
						 *         richiesta: `tela_volo = false`;
						 *      3. `[M]` 2,2 s dopo il palco monta — e monta alla
						 *         misura VOLUTA, che ci siamo ricordati qui
						 *         sopra: 2544x926, giusta;
						 *      4. ⛔ ma per `rcp.c` non c'e' piu' nessuna
						 *         richiesta in volo: vede un fotogramma di
						 *         misura diversa dalla tela in vigore e
						 *         **riporta il palco a 1920x1080**.  Bande.
						 *
						 * ⇒ «Non ce l'ho fatta» e «non ancora» sono due fatti
						 *   diversi (`CODER.md` §3.10, e la stessa forma per cui
						 *   lo zero non e' il fallimento).  Qui il palco non ha
						 *   fallito: NON C'E'.  E §7.1 ha gia' la risposta
						 *   giusta per questo caso — il fondo di tre secondi —
						 *   ⭐ e la risposta vera arriva col FOTOGRAMMA, che e'
						 *   esattamente quel che succede quando il palco monta
						 *   alla misura voluta.
						 *
						 * ⚠ Il prezzo, dichiarato: se il palco NON monta entro i
						 *   tre secondi, il client aspetta il fondo invece di
						 *   saperlo subito.  ⛔ Tre secondi di attesa valgono
						 *   meno delle bande nere per tutta la sessione.
						 */
						registro_dice(REG_FIGLIO,
						              "§7.1: il padre chiede la tela %ux%u ma il "
						              "palco non c'e' ANCORA: gli dico «ATTENDI», "
						              "e riprovo SUBITO invece di finire l'attesa "
						              "— c'e' qualcuno che aspetta",
						              (unsigned)ci.a, (unsigned)ci.b);
						attendi_tela(tela_voluta_l, tela_voluta_a);
						/*
						 * ⛔⭐ E L'ATTESA SI AZZERA — 16 agosto 2026, e senza
						 *     questa riga l'«attendi» non serviva a niente.
						 *
						 * `[M]` Il fondo di §7.1 veniva rimandato di tre
						 * secondi UNA VOLTA, e poi il figlio taceva: fra un
						 * tentativo e l'altro l'attesa raddoppia (1, 2, 4, 8
						 * s…), e in quel silenzio il fondo scadeva lo stesso.
						 *
						 * ⇒ Una richiesta di tela e' la notizia che **qualcuno
						 *   sta aspettando**: l'attesa che cresce serve a non
						 *   bruciare un nucleo quando non guarda nessuno, non
						 *   a far aspettare chi guarda.  ⚠ E cosi' il prossimo
						 *   giro manda un altro «attendi», e il fondo si
						 *   rimanda finche' il palco non c'e' davvero.
						 */
						palco_attesa_ms = PALCO_RIPROVA_MIN_MS;
						palco_riprova_ms = 0;
						continue;
					}
					/*
					 * ⛔⛔⭐ SI RILASCIA TUTTO **PRIMA** DI RIDIMENSIONARE — e
					 *       questa riga vale «su Android il mouse non prende
					 *       piu' i click».
					 *
					 * `[R]` La catena e' tutta dentro Mutter, e nessun anello e'
					 * nostro (misurata dalla sottofase 6.1, 16 agosto 2026):
					 *
					 *   1. `meta-eis-client.c:197-206` — al cambio di geometria
					 *      `remove_viewport_devices()` chiama `eis_device_remove()`
					 *      e ⛔ **non passa da `drop_device()`**, che e' l'unico
					 *      posto in cui Mutter rilascia quel che era premuto;
					 *   2. `meta-eis-client.c:612-621` — `handle_button()` **ingoia
					 *      in silenzio** il rilascio di un pulsante non premuto *su
					 *      quel* dispositivo, e dopo il ricambio il dispositivo e'
					 *      un altro;
					 *   3. `meta-seat-impl.c:899-908` — `update_button_count()` e'
					 *      **del posto**, condiviso: il press del dispositivo morto
					 *      lo tiene a 1, ogni press dopo lo porta a 2 (scartato) e
					 *      ogni release lo riporta a 1 (scartato).  ⛔ **Non scende
					 *      mai a zero**, e da li' in poi il desktop non prende piu'
					 *      un clic — senza un errore da nessuna parte.
					 *
					 * ⇒ `[M]` Da `input.c` NON si recupera: press+release sul
					 *   dispositivo nuovo fa 1→2→1 e non consegna niente.  ⭐ L'unico
					 *   istante in cui il rilascio arriva a qualcuno e' **adesso**,
					 *   finche' i dispositivi vecchi sono ancora vivi.
					 *
					 * ⚠ E il costo, dichiarato: chi tiene giu' un pulsante mentre la
					 *   tela cambia se lo vede rilasciare.  ⛔ Vale infinitamente
					 *   meno di un desktop che non prende piu' nessun clic per tutta
					 *   la sessione — ed e' esattamente il rapporto danno/costo che
					 *   `RCP.md` §11 dichiara il piu' alto del documento.
					 *
					 * ⚠ `!palco_input` non e' un guasto: e' una sessione senza
					 *   input, e la riga l'ha gia' scritta chi non l'ha aperto.
					 */
					if (palco_input) {
						int giu = input_rilascia_tutto(palco_input);
						if (giu > 0)
							registro_dice(REG_FIGLIO,
							              "⭐ §7.1: RILASCIATI %d fra tasti e "
							              "pulsanti PRIMA di ridimensionare — il "
							              "cambio di tela fa ricreare i dispositivi "
							              "di libei, e un pulsante premuto durante "
							              "il ricambio resta giu' NEL POSTO per "
							              "sempre (Mutter, `meta-seat-impl.c` "
							              "`update_button_count()`): da li' in poi "
							              "il desktop non prende piu' un clic",
							              giu);
						else
							registro_dettaglio(REG_FIGLIO,
							                   "§7.1: niente da rilasciare prima "
							                   "del ridimensionamento (%d)", giu);
					}
					r = cattura_ridimensiona(cat, tela_voluta_l, tela_voluta_a);
					if (r == CATTURA_RITELA_CHIESTA) {
						/*
						 * ⛔ «CHIESTA» NON E' «IL FLUSSO E' ANCORA VIVO» — `[M]`
						 *    22 agosto 2026, banco
						 *    `banchi/06-b5-esiti-cattura.c` caso 2: se il
						 *    produttore non regge la misura, la rinegoziazione
						 *    non lascia il flusso dov'era, lo **uccide** 2 ms
						 *    dopo questo ritorno.
						 *
						 * ⭐ E qui non serve un esito nuovo, perche' la strada
						 *    per saperlo e' gia' quella che questo ciclo
						 *    percorre: `cattura_prendi()` guarda lo stato PRIMA
						 *    di aspettare ⇒ `[M]` **8,1 ms**, un giro solo, e il
						 *    messaggio nomina «error, no more input formats».
						 *    Da li' si passa da `IL PALCO SE N'E' ANDATO SOTTO I
						 *    PIEDI` e si rimonta.
						 *
						 * ⏳⛔ E IL DIFETTO CHE RESTA APERTO, dichiarato invece
						 *     che taciuto: il rimontaggio chiede
						 *     `prendi_il_palco(tela_voluta_*)`, cioe' **la stessa
						 *     misura che ha appena ucciso il palco**, e con
						 *     `codec_chiesto && tela_voluta_l` sceglie l'attesa
						 *     CORTA.  `[M]` (banco 06-b5 caso 3) `cattura_avvia()`
						 *     a quella misura **RIESCE 3 volte su 3** e il palco
						 *     e' morto 300 ms dopo, 3 su 3 ⇒ il ciclo non ne esce
						 *     da solo, e `attendi_tela()` a ogni giro impedisce
						 *     anche al padre di scadere.  ⚠ Sul prodotto vero e'
						 *     `[?]`: Mutter ha concesso 30 misure su 30 fino a
						 *     7680x4320 e `rcp_misura_ammessa()` taglia li'.  La
						 *     cura sta nella politica di rimontaggio, non qui.
						 */
						registro_dice(REG_FIGLIO,
						              "⭐ §7.1: tela %ux%u CHIESTA al compositore.  "
						              "La risposta al client parte quando arriva un "
						              "fotogramma, non da questa riga",
						              (unsigned)ci.a, (unsigned)ci.b);
						continue;
					}
					if (r == CATTURA_RITELA_GIA_COSI) {
						/* ⭐ Il flusso ha GIA' quella misura: non arrivera'
						 *    nessun fotogramma «nuovo», perche' quelli che
						 *    arrivano sono gia' della misura giusta.  ⇒ Si
						 *    risponde subito, o il padre aspetterebbe il fondo
						 *    dei tre secondi per una cosa gia' fatta. */
						/*
						 * ⛔⛔ E IL «NON LO SO» NON SI SPEDISCE COME «NON CE
						 *     L'HO FATTA» — difetto trovato **rileggendo** la
						 *     notte del 16 agosto 2026, sottofase 6.3.
						 *
						 * `cattura_misura_negoziata()` torna `FALSE` quando il
						 * formato **non e' stato ancora negoziato**, e in quel
						 * caso ⛔ NON scrive niente nei due parametri: `ora_l` e
						 * `ora_a` restano gli zeri con cui nascono.  ⚠ E per
						 * `rispondi_tela()` lo zero non e' «non lo so»: e'
						 * **«non ce l'ho fatta»** (`figlio.h`, `corpo_tela`), che
						 * `rcp.c` gira al client come
						 * `TELA(RIFIUTATA, NON_ORA)`.
						 *
						 * ⇒ Su una sessione **sana** il client si sentiva
						 *   rispondere di no per una tela che il palco ha gia',
						 *   e la pagina mostrava «adatta» come fallita.  ⛔ E' la
						 *   forma di `CODER.md` §3.10 — *una lettura negata non
						 *   e' una lettura che dice zero* — dentro il messaggio
						 *   che esiste apposta per togliere una deduzione al
						 *   padre (`LEZIONI.md` §7.5).
						 *
						 * ⚠ La finestra e' stretta e va detta: fra
						 *   `cattura_avvia()` e la prima richiamata del formato.
						 *   `[M]` 16 agosto 2026, 38 passaggi da questo ramo su
						 *   banco 06-b35: **zero** con il formato ignoto — cioe'
						 *   il difetto e' REALE e non l'ho visto scattare.  ⇒ La
						 *   cura si scrive lo stesso, perche' il caso e' nominato
						 *   dal codice e il prezzo di sbagliarlo e' un «no» a chi
						 *   non ha sbagliato niente.
						 *
						 * ⭐ E la risposta giusta e' la misura CHIESTA: in questo
						 *   ramo `cattura_ridimensiona()` ha risposto `GIA_COSI`
						 *   proprio **perche'** la misura chiesta e' quella che
						 *   il flusso ha (`cattura.c`, la guardia di §kde
						 *   §8.2-bis: col formato ignoto confronta il chiesto).
						 *   ⇒ Dirla non e' un'invenzione: e' l'unico numero che
						 *   in quel ramo si sa per certo.
						 */
						if (!cattura_misura_negoziata(cat, &ora_l, &ora_a)) {
							ora_l = tela_voluta_l;
							ora_a = tela_voluta_a;
							registro_dice(REG_FIGLIO,
							              "⚠ §7.1: la tela %ux%u il palco ce l'ha "
							              "gia', ma il formato NON e' ancora "
							              "negoziato: rispondo con la misura "
							              "CHIESTA.  ⛔ Uno zero qui vorrebbe dire "
							              "«non ce l'ho fatta» a un client che non "
							              "ha sbagliato niente (CODER.md §3.10)",
							              (unsigned)ci.a, (unsigned)ci.b);
						} else
							registro_dice(REG_FIGLIO,
							              "§7.1: la tela %ux%u il palco ce l'ha gia' "
							              "(negoziata %ux%u): rispondo subito",
							              (unsigned)ci.a, (unsigned)ci.b, ora_l,
							              ora_a);
						rispondi_tela(tela_voluta_l, tela_voluta_a, ora_l, ora_a);
						continue;
					}
					registro_dice(REG_FIGLIO,
					              "⛔ §7.1: tela %ux%u NON chiesta — il flusso non e' "
					              "in grado adesso.  Lo dico subito: il client avra' "
					              "`TELA(NON_ORA)` invece di tre secondi di attesa",
					              (unsigned)ci.a, (unsigned)ci.b);
					rispondi_tela(tela_voluta_l, tela_voluta_a, 0, 0);
					continue;
				}
				if (!palco_input) {
					/* ⛔ «Non ho un canale di input» NON e' «il client ha
					 *    sbagliato»: si DICHIARA e si tira avanti, e la
					 *    sessione resta in piedi.  ⚠ In parlantina: a
					 *    sessanta messaggi al secondo una riga per ciascuno
					 *    seppellirebbe il registro. */
					registro_dettaglio(REG_FIGLIO,
					                   "input %u (azione %u) e nessun canale "
					                   "verso il compositore: NON iniettato",
					                   (unsigned)ci.id, (unsigned)ci.azione);
					input_rifiutati++;
					continue;
				}
				switch (ci.azione) {
				case FIGLI_INPUT_PUNTATORE:
					e = input_puntatore(palco_input, (uint32_t)ci.a,
					                    (uint32_t)ci.b);
					break;
				case FIGLI_INPUT_PULSANTE:
					e = input_pulsante(palco_input, ci.codice, ci.premuto);
					break;
				case FIGLI_INPUT_ROTELLA:
					/* ⛔ Il segno lo inverte `input_rotella()`, una volta
					 *    sola: qui passa intero, mezzi scatti compresi. */
					e = input_rotella(palco_input, ci.a, ci.b);
					break;
				case FIGLI_INPUT_LETTERA:
					e = input_lettera(palco_input, (uint32_t)ci.a);
					break;
				case FIGLI_INPUT_POSIZIONE:
					e = input_posizione(palco_input, ci.codice, ci.premuto);
					break;
				case FIGLI_INPUT_RILASCIA_TUTTO: {
					int quanti = input_rilascia_tutto(palco_input);
					registro_dice(REG_FIGLIO,
					              "⭐ §7.3: rilasciati %d fra tasti e pulsanti "
					              "che erano rimasti giu'.  ⚠ Zero NON e' un "
					              "guasto: vuol dire che non c'era niente di "
					              "premuto",
					              quanti);
					continue;
				}
				/* ⛔ `FIGLI_INPUT_RITELA` non compare qui: e' servito PRIMA della
				 *    guardia del canale di input, qualche riga piu' su, e la
				 *    ragione sta li'.  ⚠ Se ricomparisse in questo `switch`
				 *    sarebbero due strade per lo stesso messaggio, e la seconda
				 *    non verrebbe mai percorsa — cioe' codice che sembra vivo. */
				default:
					registro_dice(REG_FIGLIO,
					              "⛔ azione di input %u sconosciuta: NON "
					              "iniettata",
					              (unsigned)ci.azione);
					input_rifiutati++;
					continue;
				}

				/* ⛔⭐ E QUI STA IL PUNTO DI TUTTA LA CUCITURA: il contatore
				 *     avanza SOLO se il compositore ha preso.  §6.2 promette
				 *     che «l'effetto di quell'input e' gia' nella scena», e
				 *     di un input rifiutato non c'e' nessun effetto da
				 *     vedere.  ⚠ Farlo avanzare comunque renderebbe il campo
				 *     `input` una promessa che il fotogramma non mantiene —
				 *     e l'anello del ritardo la crederebbe. */
				if (e == 0) {
					input_iniettato = ci.id;
				} else if (e == 1) {
					/* ⛔ Solo `input_lettera`: «non producibile con questa
					 *    disposizione».  La riga nel registro l'ha gia'
					 *    scritta `tastiera.c`, con dentro QUALE disposizione:
					 *    qui si conta e basta, o la stessa cosa finirebbe due
					 *    volte con due parole diverse. */
					input_non_producibili++;
				} else {
					input_rifiutati++;
					registro_dettaglio(REG_FIGLIO,
					                   "input %u (azione %u): il compositore "
					                   "non l'ha preso",
					                   (unsigned)ci.id, (unsigned)ci.azione);
				}
				continue;
			}
			if (t.tipo == MSG_RIMANDA_PALCO) {
				int quanti = 0;
				for (uint8_t c = 1; c < 3; c++) {
					if (!tenuto[c])
						continue;
					manda_fotogramma(c, tenuto_chiave[c], tenuto_l, tenuto_a,
					                 tenuto_istante, tenuto[c], tenuto_byte[c],
					                 tenuto_input);
					quanti++;
				}
				registro_dice(REG_FIGLIO,
				              quanti
				                  ? "il padre ha chiesto il palco: rimando %d "
				                    "flussi (l'ultima CHIAVE tenuta — un delta "
				                    "senza il suo passato sarebbe un'immagine "
				                    "sfasciata, §5.2)"
				                  : "il padre ha chiesto il palco e non ho "
				                    "niente da rimandare (%d): il perche' e' "
				                    "nelle righe qui sopra",
				              quanti);
				/* ⛔ E si segna il debito: chi rientra ha bisogno di una chiave
				 *    NUOVA, non di quella di prima — quella la sta gia'
				 *    ricevendo, ma il suo decodificatore riparte da li' e i
				 *    delta che seguono sono figli di un'altra catena. */
				if (codec_chiesto)
					debito_chiave[codec_chiesto] = true;

				/* ⛔⛔⭐ E SI RIMANDA ANCHE LA CLIPBOARD — 21 agosto 2026.
				 *
				 * ⚠ Questo messaggio vuol dire «un client si e' RIATTACCATO a
				 *   un figlio che c'era gia'» (`main.c`, il ramo `c_era`).  Il
				 *   figlio sopravvive fra un collegamento e l'altro, quindi la
				 *   lettura fatta all'accensione degli appunti e' avvenuta UNA
				 *   volta sola: il client nuovo non sa che cosa c'e' nella
				 *   clipboard del desktop.
				 * ⛔ E allora, appena si annuncia per farsi trovare, si
				 *   prendeva la selezione a mani vuote e **cancellava** quel
				 *   che l'utente aveva copiato di la'.  `[M]` misurato il 21
				 *   agosto: `wl-paste` diceva «TESTO-CHE-ERA-GIA-NEL-DESKTOP»
				 *   prima e «» dopo il collegamento.
				 * ⇒ Chi rientra riceve la clipboard del desktop come riceve
				 *   l'ultimo fotogramma: e' la stessa idea, applicata all'altra
				 *   cosa che il palco ha da dare. */
				if (palco_appunti)
					appunti_leggi_adesso(palco_appunti);
				continue;
			}
			if (t.tipo == MSG_CHI_SEI) {
				/* ⛔ Si RILEGGE dal nucleo, non si ristampa la copia di
				 *    prima. */
				getresuid(&r, &e, &sv);
				getresgid(&rg, &eg, &sg);
				s.uid = r;
				s.euid = e;
				s.suid = sv;
				s.gid = rg;
				s.egid = eg;
				s.sgid = sg;
				s.ppid = (uint32_t)getppid();
				s.descrittori = quanti_descrittori();
				manda(MSG_SONO, &s, sizeof s, NULL, 0);
				continue;
			}
		}
		if (fine)
			break;

		/* ── 1-bis. il canale di input, che ha una voce sua ──────────── */
		/* ⛔⭐ `libei` NON e' una libreria che si chiama e basta: e' un pari
		 *     che PARLA, e fra le cose che dice ci sono i due ricambi
		 *     silenziosi di `STUDI.md` §gnome §9 — un cambio di keymap distrugge e
		 *     ricrea il dispositivo tastiera, un cambio di geometria tutti i
		 *     dispositivi assoluti.  ⚠ E il puntatore agganciato al
		 *     dispositivo vecchio smette di funzionare **senza errore**: chi
		 *     non gira questo ciclo non vede nessun guasto, vede solo un
		 *     desktop che a un certo punto non risponde piu'.
		 * ⚠ Sta QUI, fra i messaggi del padre e la cattura, per la stessa
		 *   ragione dell'ordine di sopra: non aspetta, e rimandarlo dopo la
		 *   cattura gli farebbe pagare fino a un quarto di secondo. */
		/* ⚠ E questa resta come rete di sicurezza, non come strada principale:
		 *   la strada principale e' il `poll` qui sopra.  ⛔ Serve perche'
		 *   `libei` puo' avere lavoro da fare senza che il descrittore sia
		 *   leggibile (le scadenze sue), e un ciclo che si fidasse solo del
		 *   descrittore le mancherebbe **senza nessun errore**. */
		if (palco_input)
			input_gira(palco_input);

		/* ── 1-ter. il palco che non c'e': si RIMONTA ─────────────────── */
		/* ⛔⭐ I DUE DIFETTI GEMELLI SI CURANO QUI, ED E' LO STESSO POSTO
		 *     PERCHE' SONO LO STESSO FATTO: *il figlio non sa che il suo palco
		 *     non c'e' piu', o non c'e' ancora.*
		 *
		 *   · non c'e' ANCORA — la sessione grafica non esisteva alla nascita;
		 *   · non c'e' PIU' — la sessione e' morta sotto un figlio vivo, e
		 *     `cattura_prendi` ha dichiarato il guasto qui sotto.
		 *
		 * ⚠ E non si stacca (§8.3): la sessione RCP resta in piedi, il client
		 *   resta collegato, e quando il palco torna il desktop ricompare da
		 *   se'.  ⛔ Ma non si sta nemmeno fermi: un figlio senza palco non e'
		 *   una sessione ferma, e' un figlio che non serve a niente. */
		if (!cat) {
			uint64_t ora = registro_ora_ms();
			/*
			 * ⛔⭐ E SE SI STA SOLO ASPETTANDO, LO SI DICE — una volta al
			 *     secondo, e non di piu'.
			 *
			 * `[M]` 16 agosto 2026: un giro su cinque metteva TRENTA secondi a
			 * far comparire il desktop, e in quei trenta secondi il figlio non
			 * scriveva **una riga**.  ⛔ Da fuori i due casi hanno la stessa
			 * faccia — «sta provando e non ci riesce» e «non sta provando
			 * affatto» — e la differenza e' tutta la diagnosi.  ⇒ Ho tirato a
			 * indovinare tre volte, e tre volte la misura dopo ha detto di no.
			 *
			 * ⭐ Un'attesa che non si dichiara e' un'attesa che non si puo'
			 *    curare.  Questa riga costa una riga al secondo e vale le tre
			 *    diagnosi che mi ha risparmiato.
			 */
			if (ora < palco_riprova_ms) {
				static uint64_t detto_ms;

				if (ora - detto_ms >= 1000) {
					detto_ms = ora;
					registro_dice(REG_FIGLIO,
					              "⏳ senza palco e ASPETTO: mancano %llu ms al "
					              "prossimo tentativo (attesa in corso %llu ms, "
					              "nascita chiesta %llu ms fa) — ⚠ non sto "
					              "provando e fallendo: non sto provando",
					              (unsigned long long)(palco_riprova_ms - ora),
					              (unsigned long long)palco_attesa_ms,
					              nascita_chiesta_ms
					                  ? (unsigned long long)(ora - nascita_chiesta_ms)
					                  : 0ULL);
				}
			}
			if (ora >= palco_riprova_ms) {
				/* ⛔⭐ E SI CRONOMETRA L'INTERO TENTATIVO, non i suoi tre passi
				 *     principali.
				 *
				 * `[M]` 16 agosto 2026: i tre cronometri dentro
				 * `prendi_il_palco` tacevano — nessun passo sopra 250 ms — e
				 * pero' in diciannove secondi i tentativi erano DIECI, cioe'
				 * quasi due secondi l'uno.  ⇒ Il tempo stava in un pezzo che
				 * nessun cronometro copriva, e il candidato e' lo SMONTAGGIO di
				 * un tentativo fallito a meta': chiude oggetti su un
				 * compositore che non risponde, e `mutter.c` li' aspetta fino a
				 * QUINDICI secondi.
				 *
				 * ⚠ Lezione, e vale oltre questo difetto: **un cronometro sui
				 *   passi che sospetti misura i tuoi sospetti.**  Quello che
				 *   serve sta attorno al giro intero. */
				uint64_t tentativo_ms = registro_ora_ms();
				bool preso;

				/* ⛔ Si rimonta alla tela VOLUTA, non a quella che il palco
				 *    caduto aveva: quel che il client ha chiesto non muore con la
				 *    sessione grafica.  ⚠ Se il compositore concedera' altro, la
				 *    riconciliazione del punto 2 lo dira' e il padre lo sapra'. */
				preso = prendi_il_palco(tela_voluta_l, tela_voluta_a, dir_rilievo,
				                        false, &mut, &cat);
				if (registro_ora_ms() - tentativo_ms >= 250)
					registro_dice(REG_FIGLIO,
					              "⏱ il TENTATIVO INTERO (%s) ha impiegato "
					              "%llu ms — e i cronometri dei singoli passi "
					              "tacciono: il tempo sta fuori da loro",
					              preso ? "riuscito" : "fallito",
					              (unsigned long long)(registro_ora_ms() - tentativo_ms));
				if (preso) {
					registro_dice(REG_FIGLIO,
					              "⭐⭐ RIAVVIO LA CATTURA: il palco e' tornato "
					              "dopo %llu ms di attesa — e il prossimo "
					              "fotogramma sara' una CHIAVE (§5.2), perche' "
					              "chi guarda ha perso il passato del flusso",
					              (unsigned long long)palco_attesa_ms);
					palco_attesa_ms = PALCO_RIPROVA_MIN_MS;
					palco_riprova_ms = 0;
					/* ⛔ §5.2: dopo un buco il client NON puo' decodificare un
					 *    delta — il suo decodificatore non ha piu' il passato
					 *    di questa catena.  Il debito si segna sul codec
					 *    CHIESTO, non su tutti. */
					if (codec_chiesto)
						debito_chiave[codec_chiesto] = true;
				} else {
					/* ⛔ Si smonta quel che il tentativo ha lasciato a meta':
					 *    un `mut` aperto senza cattura terrebbe un monitor
					 *    virtuale che nessuno consuma. */
					smonta_il_palco(&mut, &cat);
					/* ⛔⭐ QUI SI DISTINGUONO I DUE CASI CHE IL COMMENTO QUI
					 *     SOPRA NOMINAVA GIA', e fino al 16 agosto 2026 li
					 *     trattava tutt'e due con la stessa attesa.
					 *
					 *   · non c'e' ANCORA — la sessione e' stata chiesta e
					 *     `gnome-session` si sta alzando: ⭐ si riprova FITTO,
					 *     perche' l'unica cosa che ci separa dal desktop e'
					 *     accorgersene, e accorgersene costa una chiamata
					 *     D-Bus a un nome che non c'e'.
					 *   · non c'e' PIU' — o non arriva: ⚠ l'attesa raddoppia,
					 *     ed e' la briglia dei 30 GB di registro.
					 *
					 * ⇒ Vedi `PALCO_NASCITA_RIPROVA_MS`: e' la cura del «al
					 *   quarto login il desktop ha impiegato molti secondi».
					 *
					 * ⛔⭐⭐⭐ E LA REGOLA VERA E' LA SECONDA CONDIZIONE, che
					 *        e' costata quattro diagnosi sbagliate:
					 *        **l'attesa che raddoppia e' per quando NON C'E'
					 *        NESSUNO CHE GUARDA.**
					 *
					 * `[M]` 16 agosto 2026.  Appena il figlio ha avuto una riga
					 * per dirlo, ha dato tutt'e due i pezzi insieme:
					 *
					 *   «⏳ senza palco e ASPETTO: mancano 4962 ms al prossimo
					 *    tentativo (attesa in corso **30000 ms**, nascita
					 *    chiesta **0 ms** fa)»
					 *
					 *   · `attesa in corso 30000` ⇒ l'attesa raddoppiava
					 *     davvero, fino al tetto: 2, 4, 8, 16, 30 secondi;
					 *   · `nascita chiesta 0 ms fa` ⇒ ⛔ e la guardia qui sopra
					 *     non poteva scattare, perche' `nascita_chiesta_ms` si
					 *     scrive SOLO quando la sessione risulta MORTA.
					 *
					 * ⭐ E i giri lenti sono ESATTAMENTE quelli in cui la
					 *    sessione non e' morta: e' la precedente che sta ancora
					 *    chiudendo (B7 di `SPECIFICHE.md` §5.9; `[M]` `loginctl` dice
					 *    `State=closing`).  Il figlio, giustamente, non la
					 *    tocca — buttarne giu' una viva toglierebbe il desktop a
					 *    chi lo guarda (I4) — ⛔ ma poi si metteva ad aspettare
					 *    TRENTA SECONDI un palco che arrivava in tre.
					 *
					 * ⇒ ⚠ La briglia dei 30 GB resta necessaria, ma il caso che
					 *   curava era un altro: un figlio SENZA CLIENTE che
					 *   rimontava all'infinito.  ⭐ Quando invece un cliente e'
					 *   attaccato e sta chiedendo una tela, dall'altra parte c'e'
					 *   una persona davanti a uno schermo fermo, e l'unica
					 *   attesa difendibile e' la piu' corta.
					 *
					 * ⛔ E non costa niente: la riga di registro si scrive al
					 *    massimo una volta al secondo comunque. */
					/* ⛔⭐ E «sto aspettando la tela del cliente» e' un «non
				 *     ancora», non un fallimento: `[M]` 16 agosto 2026, senza
				 *     questa terza condizione il rifiuto della guardia finiva
				 *     nell'attesa che raddoppia, e la sessione nasceva a 3,2 s
				 *     invece che a 1,1 — cioe' la cura si mangiava meta' del
				 *     suo guadagno. */
				if (sta_nascendo(ora) || !tela_dal_cliente ||
				    (codec_chiesto && tela_voluta_l)) {
						palco_attesa_ms = PALCO_NASCITA_RIPROVA_MS;
						palco_riprova_ms = ora + palco_attesa_ms;
						registro_dettaglio(REG_FIGLIO,
						                   "senza palco e QUALCUNO GUARDA (o la "
						                   "sessione sta nascendo, chiesta %llu "
						                   "ms fa): riprovo fra %llu ms — fitto "
						                   "apposta, l'attesa che raddoppia e' "
						                   "per il palco che non c'e' PIU', "
						                   "non per quello che non c'e' ANCORA",
						                   nascita_chiesta_ms
						                       ? (unsigned long long)(ora - nascita_chiesta_ms)
						                       : 0ULL,
						                   (unsigned long long)palco_attesa_ms);
						if (tela_voluta_l && tela_voluta_a)
							attendi_tela(tela_voluta_l, tela_voluta_a);
						continue;
					}
					if (palco_attesa_ms < PALCO_RIPROVA_MIN_MS)
						palco_attesa_ms = PALCO_RIPROVA_MIN_MS;
					else
						palco_attesa_ms *= 2;
					if (palco_attesa_ms > PALCO_RIPROVA_MAX_MS)
						palco_attesa_ms = PALCO_RIPROVA_MAX_MS;
					palco_riprova_ms = ora + palco_attesa_ms;
					registro_dice(REG_FIGLIO,
					              "⛔ SENZA PALCO: il tentativo non e' riuscito "
					              "— riprovo fra %llu ms.  ⚠ L'attesa cresce "
					              "apposta: senza, questo ciclo scrive gigabyte "
					              "di registro e brucia un nucleo",
					              (unsigned long long)palco_attesa_ms);
					/*
					 * ⭐⭐ E SI CONTINUA A DIRE «ATTENDI» — 16 agosto 2026, e
					 *     senza questa riga la cura di prima non serviva a
					 *     niente: dirlo UNA VOLTA sposta il fondo di §7.1 di
					 *     tre secondi da adesso, e `[M]` il palco ci ha messo
					 *     CINQUE secondi a montare dopo un logout.
					 *
					 * ⇒ Finche' c'e' una misura voluta e un palco che non c'e',
					 *   il padre deve sapere a ogni giro che qualcuno ci sta
					 *   ancora provando.  ⚠ E' l'opposto del silenzio: chi tace
					 *   fa dedurre, e la deduzione era il difetto.
					 */
					if (tela_voluta_l && tela_voluta_a)
						attendi_tela(tela_voluta_l, tela_voluta_a);
				}
			}
		}

		/* ── 1-bis. l'audio ──────────────────────────────────────────── */
		/* ⛔ PRIMA del `continue` della parte video, e non e' un dettaglio di
		 *    ordine: quel `continue` scatta ogni volta che nessuno guarda, e
		 *    l'audio ci finirebbe dentro per caso.  ⇒ Una sessione con l'audio
		 *    acceso e il video spento **non suonerebbe**, e nessuna riga direbbe
		 *    perche'.  ⚠ Il caso non e' teorico: e' quel che succede a chi
		 *    ascolta musica con la scheda del browser in secondo piano. */
		audio_svuota();

		/* ── 2. il fotogramma ────────────────────────────────────────── */
		if (!codec_chiesto || !cat)
			continue;
		{
			CatturaFermo fo;
			GError *sbaglio = NULL;
			CatturaPresa presa;
			uint64_t istante_us, adesso;

			memset(&fo, 0, sizeof fo);
			presa = cattura_prendi(cat, MOVIMENTO_ATTESA_S, &fo, &sbaglio);
			/* ⛔⭐ IL CONTO SI SCRIVE PRIMA DI GUARDARE L'ESITO, ED E' UNA
			 *     CURA TROVATA DAL PRIMO GIRO DAL VIVO (13 agosto 2026).
			 *
			 *     La prima stesura scriveva questa riga solo DOPO un fotogramma
			 *     consegnato: su un desktop fermo — cioe' su ogni macchina
			 *     senza una scena dichiarata — il ciclo girava e il registro
			 *     non diceva NIENTE.  ⛔ «Il ciclo non parte», «la cattura non
			 *     consegna» e «la scena e' ferma» avevano tutt'e tre la stessa
			 *     faccia: il silenzio.  E' esattamente `LEZIONI.md` §1.9 —
			 *     «vuoto» e «proibito» con lo stesso aspetto — dentro la riga
			 *     che dovrebbe smascherarlo.
			 *
			 *     ⇒ Adesso si scrive comunque, una volta al secondo, con dentro
			 *     gli ZERO: chi legge distingue le tre cose senza dedurre. */
			adesso = ora_monotona_us();
			if (adesso - ciclo_detto_ms >= 1000000u) {
				ciclo_detto_ms = adesso;
				registro_dice(REG_FIGLIO,
				              "ciclo: %llu fotogrammi consegnati (%llu chiavi), "
				              "%llu attese a vuoto (scena ferma: Mutter consegna "
				              "solo quando qualcosa cambia), %llu guasti — codec "
				              "%u, %d/s chiesti, attesa %.2f s%s",
				              (unsigned long long)ciclo_fotogrammi,
				              (unsigned long long)ciclo_chiavi,
				              (unsigned long long)ciclo_zero,
				              (unsigned long long)ciclo_guasti, codec_chiesto,
				              MOVIMENTO_FPS, MOVIMENTO_ATTESA_S,
				              /* ⛔⭐ E QUESTA CODA VALE QUANTO LA RIGA.
				               *
				               * `[M]` 14 agosto 2026: per quattro secondi il
				               * registro diceva *«0 fotogrammi consegnati, 0
				               * attese a vuoto (scena ferma: Mutter consegna
				               * solo quando qualcosa cambia)»* — e chi lo
				               * leggeva concludeva che il ritardo fosse di
				               * Mutter.  ⛔ Era il contrario: **zero attese a
				               * vuoto vuol dire che nessuno ha nemmeno provato
				               * a catturare**, cioe' che il ciclo era fermo
				               * altrove.  La riga aveva il numero giusto e la
				               * parola sbagliata accanto. */
				              (ciclo_fotogrammi == 0 && ciclo_zero == 0
				               && ciclo_guasti == 0)
				                  ? "  ⛔⛔ e ZERO attese a vuoto vuol dire che "
				                    "il ciclo NON HA NEMMENO PROVATO a catturare: "
				                    "NON e' «la scena e' ferma», e' questo "
				                    "processo che sta da un'altra parte"
				                  : "");
			}

			/* ⭐⭐ IL QUARTO SINTOMO — i 4 secondi fra il login e il desktop, e
			 *     si curano QUI perche' qui stanno tutt'e due i fatti che
			 *     servono: «qualcuno aspetta un fotogramma» e «non ne arriva
			 *     nessuno».
			 *
			 * `[M]` 14 agosto 2026, registro delle 21:32:55: una richiesta di
			 * chiave ogni 200 ms per **4,4 secondi** e **659 attese a vuoto**,
			 * perche' un compositore Wayland consegna solo quando la scena
			 * cambia — e un desktop appena acceso e' fermo.  ⇒ Il client chiede
			 * l'immagine, il palco non ha niente da dare, e nessuno dei due
			 * sbaglia.
			 *
			 * ⛔ Xpra ordina «ridipingi adesso» (`buffer_refresh`) e su Wayland
			 *    non si puo'.  ⭐ La sola leva e' riavviare il flusso, che e'
			 *    quel che fa `cattura_risveglia()`.
			 *
			 * ⚠ E si fa SOLO quando una chiave e' dovuta — cioe' quando c'e'
			 *   davvero qualcuno che non puo' dipingere niente — e non piu' di
			 *   una volta ogni `RISVEGLIO_MS`: ogni riavvio costa la
			 *   rinegoziazione, e farne sessanta al secondo toglierebbe proprio
			 *   i fotogrammi che si stanno cercando. */
			/* ⚠ `codec_chiesto` sta dentro l'array, e il limite e' UNO: chi
			 *   aggiunge un codec non deve trovarne un secondo scritto a mano
			 *   qui (era `< 3`, ed e' rimasto indietro il 20 agosto). */
			if (presa == CATTURA_PRESA_ZERO && codec_chiesto < CODEC_MAX
			    && debito_chiave[codec_chiesto]) {
				uint64_t adesso_ms = registro_ora_ms();
				if (adesso_ms - risveglio_ms >= RISVEGLIO_MS) {
					/*
					 * ⛔⛔⛔ LA CURA «A» — 21 agosto 2026.  🔸 DERIVATA dal
					 *       coordinatore, e il prezzo qui sotto e' VISIBILE
					 *       all'utente: quando lo vedra', il giudizio e' suo.
					 *
					 * IL FATTO, `[M]` (banco `banchi/06-b33-risveglio.*`):
					 * `cattura_risveglia()` fa ricreare a Mutter i dispositivi
					 * assoluti — **3 risvegli, 3 ricambi, con ZERO cambi di
					 * tela** — e se in quel momento un pulsante e' premuto,
					 * quel pulsante resta giu' **nel posto** e ⛔ **il desktop
					 * non prende piu' un clic per tutta la sessione**.  E'
					 * `fasi/06-la-tela-e-la-vista.md` §4.6, per la seconda
					 * porta che §7.1 ha trovato.
					 *
					 * ⛔ E questa riga sta nel posto peggiore possibile: ci si
					 *    arriva quando **la scena e' ferma**, cioe' esattamente
					 *    quando l'utente puo' tenere premuto il mouse su un
					 *    desktop immobile.
					 *
					 * ⛔ La cura ovvia — rilasciare prima, come si fa a `:3964`
					 *    prima di `cattura_ridimensiona()` — QUI E' VIETATA:
					 *    li' e' il client che ha chiesto il cambio di tela, qui
					 *    non ha chiesto niente nessuno, e rilasciare
					 *    distruggerebbe **ogni trascinamento**.
					 *
					 * ⇒ Non ci si risveglia: si aspetta che l'utente molli.
					 *
					 * 🔸 IL PREZZO, e l'utente lo vedra': su un desktop fermo,
					 *    con un tasto o un pulsante tenuto giu', la chiave non
					 *    parte — e un client appena attaccato puo' restare con
					 *    la **pagina bianca** finche' non si rilascia.
					 *    ⚠ E' limitato e si sana da se': `risveglio_ms` NON si
					 *      tocca, quindi al primo rilascio il fondo e' gia'
					 *      scaduto e il giro dopo risveglia.
					 *    ⚠ E la scena e' rara: un trascinamento **muove** il
					 *      desktop, e allora la presa non e' ZERO e qui non ci
					 *      si arriva nemmeno.
					 *
					 * ⚠ Quel che questa guardia NON copre lo ripara la cura «C»
					 *   in `input.c` (`guarisci()`): le porte che non
					 *   controlliamo — `monitors-changed`, il cambio di keymap,
					 *   e quelle che GNOME aggiungera'.
					 */
					unsigned giu = palco_input ? input_premuti(palco_input) : 0;

					if (giu) {
						/* ⛔ E si dice UNA VOLTA per attesa, non a ogni giro: a
						 *    400 ms l'una queste righe annegherebbero il
						 *    registro proprio mentre l'utente trascina. */
						if (!risveglio_zitto) {
							risveglio_zitto = 1;
							registro_dice(
							    REG_FIGLIO,
							    "⛔ una CHIAVE e' dovuta e la scena e' ferma, ma %u "
							    "fra tasti e pulsanti sono TENUTI GIU': NON risveglio "
							    "il flusso.  ⭐ Il risveglio fa ricreare i dispositivi "
							    "di libei (`[M]` §7.1) e un pulsante premuto durante "
							    "il ricambio resta giu' NEL POSTO per sempre.  🔸 Il "
							    "prezzo, dichiarato: chi si e' appena attaccato puo' "
							    "vedere la pagina bianca finche' l'utente non molla",
							    giu);
						}
					} else {
						risveglio_zitto = 0;
						risveglio_ms = adesso_ms;
						registro_dice(REG_FIGLIO,
						              "⭐ una CHIAVE e' dovuta e la scena e' ferma da "
						              "%u ms: riavvio il flusso per farmi consegnare "
						              "un fotogramma.  ⚠ Senza, l'utente guarda una "
						              "pagina bianca finche' qualcosa non si muove sul "
						              "desktop (`[M]` 4,4 s il 14 agosto 2026)",
						              (unsigned)RISVEGLIO_MS);
						cattura_risveglia(cat);
					}
				}
			}

			if (presa == CATTURA_PRESA_ZERO) {
				/* ⛔ ZERO E FALLIMENTO SONO DUE COSE DIVERSE, e questo e' lo
				 *    zero: il flusso e' stato attivo per tutta l'attesa e non
				 *    e' arrivato niente.  Su Mutter e' il DESKTOP FERMO, ed e'
				 *    un risultato — `LEZIONI.md` §1.1: «un compositore Wayland
				 *    consegna un fotogramma solo quando qualcosa cambia».
				 *    ⚠ Non si codifica niente e non si spedisce niente: I1
				 *    vieta di calare il ritmo per prudenza, non di stare fermi
				 *    quando la scena non si muove. */
				ciclo_zero++;
				g_clear_error(&sbaglio);
				continue;
			}
			if (presa != CATTURA_PRESA_FATTA
			    && presa != CATTURA_PRESA_PIXEL_ALTROVE) {
				/* ⛔⛔ E QUI STAVANO I 30,8 GB DI REGISTRO.
				 *
				 * `[M]` 14 agosto 2026, sessione vera dell'utente: la
				 * sessione grafica e' morta sotto un figlio vivo, il flusso
				 * PipeWire e' andato in `connection error`, e
				 * `cattura_prendi` da quel momento torna **subito** —
				 * l'attesa di 0,25 s non si spende nemmeno, perche' lo
				 * stato del flusso si guarda prima di aspettare
				 * (`cattura.c`).  ⇒ Questo `continue` rimetteva il ciclo
				 * in cima **milioni di volte al secondo**, e ogni giro
				 * scriveva questa riga: 112 milioni di righe identiche,
				 * tutte nello stesso millisecondo, e il disco pieno.
				 *
				 * ⇒ ⭐ Adesso il palco si SMONTA: `cat` diventa NULL, il
				 *   ciclo non ci ripassa, e il rimontaggio con l'attesa
				 *   che cresce sta al punto 1-ter.  ⚠ La riga si scrive
				 *   **una volta per perdita**, non una per giro. */
				ciclo_guasti++;
				registro_dice(REG_FIGLIO,
				              "⛔⛔ IL PALCO SE N'E' ANDATO SOTTO I PIEDI "
				              "(presa %u: %s).  ⚠ NON e' «la scena e' ferma»: "
				              "e' la sessione grafica che non c'e' piu'.  Smonto "
				              "il palco e lo rimonto quando torna — la sessione "
				              "RCP resta in piedi (§8.3), e chi guarda vedra' "
				              "l'ultima immagine finche' il desktop non ricompare",
				              (unsigned)presa,
				              sbaglio ? sbaglio->message : "nessun dettaglio");
				g_clear_error(&sbaglio);
				cattura_fermo_libera(&fo);
				smonta_il_palco(&mut, &cat);
				palco_attesa_ms = PALCO_RIPROVA_MIN_MS;
				palco_riprova_ms = registro_ora_ms() + palco_attesa_ms;
				continue;
			}
			g_clear_error(&sbaglio);

			/* ══ ⭐⭐ LA MISURA NUOVA E' ARRIVATA — e la dice IL FOTOGRAMMA ══
			 *
			 * ⛔ E' il punto in cui il ridimensionamento diventa un fatto, ed e'
			 *    UNO SOLO apposta: la richiesta parte da `FIGLI_INPUT_RITELA`, ma
			 *    fra la richiesta e i pixel c'e' un compositore che puo'
			 *    concedere altro (`RCP.md` §4.5), rispondere «riuscito» senza
			 *    fare niente (`[M]` labwc), o non farcela.  ⇒ Qui non si guarda
			 *    che cosa si e' CHIESTO: si guarda che cosa e' ARRIVATO.
			 *
			 * ⛔⛔ E LE TRE COSE VANNO FATTE TUTT'E TRE, o il difetto e' peggiore
			 *     di quello che si stava curando:
			 *
			 *   1. il CODIFICATORE si riapre alla misura nuova.  ⚠
			 *      `codificatore_comprimi()` riceve i pixel e il passo, **non**
			 *      larghezza e altezza (`codificatore.h`): alimentato con
			 *      un'immagine piu' grande di quella per cui e' aperto non
			 *      protesta — taglia o riempie, e il difetto si vede solo
			 *      nell'immagine.  ⭐ E la riapertura porta con se' la chiave che
			 *      §5.2 pretende («su HEVC in Chrome un delta alla misura nuova
			 *      non solleva niente: il decodificatore continua a emettere
			 *      fotogrammi alla misura VECCHIA»);
			 *   2. la REGIONE DEL PUNTATORE si rimappa.  Senza, il puntatore
			 *      resta nello spazio di prima e va altrove — il difetto misurato
			 *      per due giorni sul DeX;
			 *   3. `tela_l`/`tela_a` diventano quelli veri, perche' sono i numeri
			 *      che finiscono nei 28 byte di §6.2 e che il padre confronta con
			 *      la tela in vigore.  ⛔ Finche' non lo erano, quei due campi
			 *      dicevano quel che il figlio aveva CHIESTO alla nascita: una
			 *      misura DICHIARATA e mai verificata, cioe' la guardia 3 di
			 *      §5.0-sexies aperta all'ultimo anello.
			 *
			 * ⚠ E il fotogramma di questo giro si spedisce LO STESSO, alla misura
			 *   sua: e' il primo alla misura nuova, ed e' quello che al padre fa
			 *   spedire `TELA(ADATTATA)` (§7.1).  Buttarlo vorrebbe dire
			 *   rimandare di un giro la cosa che tutti stanno aspettando. */
			/* ⛔⛔ E PRIMA DI TUTTO: IL FOTOGRAMMA DEVE CONTENERE QUEL CHE
			 *     DICHIARA — la guardia nata refutando, la notte del 15 agosto
			 *     2026, e la prima stesura la metteva DOPO la riconciliazione.
			 *
			 * `codificatore_comprimi()` riceve **i pixel e il passo**, non
			 * larghezza e altezza: legge fino a `(altezza-1) x passo +
			 * larghezza x 4` byte, e la geometria la conosce dalla sua apertura.
			 * ⇒ Servono DUE controlli e non uno:
			 *
			 *   · `passo >= larghezza x 4`  — il verso «la tela si ALLARGA», che
			 *     il solo controllo sui byte NON copre: con passo vecchio e
			 *     larghezza nuova i conti tornano e la lettura esce lo stesso;
			 *   · `byte >= passo x altezza` — il verso «la tela si ALZA».
			 *
			 * ⛔ E sta PRIMA della riconciliazione perche' un fotogramma che poi
			 *    si scarta non deve aver gia' fatto riaprire i codificatori (un
			 *    contesto VAAPI), rimappare il puntatore e spostare
			 *    `tela_l`/`tela_a` su una misura che quei pixel non avevano.
			 *
			 * ⚠ `larghezza`/`altezza` a zero rendevano la vecchia guardia VUOTA
			 *   (`byte < 0` e' sempre falso): si nominano, invece di fidarsi che
			 *   i numeri tornino. */
			/* ⚠ E vale su tutt'e due le strade, con la stessa aritmetica: sulla
			 *   scheda `byte` non e' una copia da leggere ma `passo x altezza`
			 *   letto dal chunk, e chi importa il DMA-BUF descrive esattamente
			 *   quella regione.  ⛔ Un passo piu' corto della larghezza
			 *   dichiarata farebbe leggere alla GPU oltre l'oggetto, che e' lo
			 *   stesso difetto di prima con un altro lettore. */
			if (!fo.larghezza || !fo.altezza || !fo.stride
			    || fo.stride < (guint64) fo.larghezza * 4u
			    || fo.byte < (guint64) fo.stride * fo.altezza) {
				fotogrammi_incoerenti++;
				if (fotogrammi_incoerenti == 1)
					registro_dice(REG_FIGLIO,
					              "⛔ fotogramma SCARTATO: dichiara %ux%u con passo %u "
					              "e porta %llu byte — chi lo comprime leggerebbe "
					              "oltre la copia (servono passo >= %llu e byte >= "
					              "%llu).  ⚠ E' la finestra fra una rinegoziazione e "
					              "i buffer nuovi",
					              fo.larghezza, fo.altezza, fo.stride,
					              (unsigned long long)fo.byte,
					              (unsigned long long)((guint64)fo.larghezza * 4u),
					              (unsigned long long)((guint64)fo.stride * fo.altezza));
				cattura_fermo_libera(&fo);
				continue;
			}

			if (fo.larghezza != tela_l || fo.altezza != tela_a) {
				uint32_t chiesta_l = 0, chiesta_a = 0;
				char errore[256];

				/* ⭐ E QUESTO E' IL POSTO IN CUI LA DIVERGENZA SI LEGGE DAVVERO,
				 *    ed e' l'unico: `cattura.c` la vede sul FORMATO — dove non
				 *    puo' sapere se quel `Format` risponde alla richiesta di
				 *    adesso o a una superata — mentre qui la si vede sui PIXEL,
				 *    che sono arrivati e non si disdicono.  E' la regola di
				 *    §5.0-sexies: *«la verita' la dice il fotogramma»*.
				 *
				 * ⚠ `[M]` 22 agosto 2026, banco `banchi/06-b5-esiti-cattura.c`
				 *   caso 4: anche qui i due numeri possono divergere per un
				 *   motivo INNOCENTE — due `ADATTA_TELA` incatenate (l'utente che
				 *   trascina il bordo), dove questo fotogramma risponde alla
				 *   richiesta di prima e quello della nuova sta arrivando.  ⇒ La
				 *   riga NOMINA tutt'e due i moventi invece di accusarne uno:
				 *   un registro che attribuisce la causa sbagliata costa piu' di
				 *   un registro muto.  ⛔ E in nessuno dei due casi si cambia
				 *   condotta: la riconciliazione qui sotto guarda il fotogramma,
				 *   che e' giusto in tutt'e due. */
				cattura_misura_chiesta(cat, &chiesta_l, &chiesta_a);
				registro_dice(REG_FIGLIO,
				              "⭐⭐ TELA NUOVA DAL PALCO: %ux%u → %ux%u (chiesti al "
				              "produttore %ux%u)%s.  Riapro il codificatore, "
				              "rimappo il puntatore, e da qui i 28 byte di §6.2 "
				              "portano la misura nuova",
				              tela_l, tela_a, fo.larghezza, fo.altezza, chiesta_l,
				              chiesta_a,
				              (chiesta_l == fo.larghezza && chiesta_a == fo.altezza)
				                  ? ""
				                  : " — ⛔ CONCESSO DIVERSO DA CHIESTO: o il "
				                    "compositore ha concesso altro (§4.5 lo "
				                    "permette), o questo fotogramma risponde a una "
				                    "richiesta SUPERATA (`[M]` due ADATTA_TELA "
				                    "incatenate, banco 06-b5 caso 4).  ⚠ Riconcilio "
				                    "sul FOTOGRAMMA, che e' giusto in tutt'e due");

				/* 1. il codificatore, ⛔ TUTTI quelli vivi: il debito della
				 *    chiave e' per codec, e un codificatore aperto e non
				 *    ridimensionato consegnerebbe immagini tagliate al primo
				 *    fotogramma dopo un cambio di codec. */
				for (uint8_t c = 1; c < CODEC_MAX; c++) {
					if (!codif[c])
						continue;
					if (!codificatore_ridimensiona(codif[c], fo.larghezza,
					                               fo.altezza, errore,
					                               sizeof errore)) {
						registro_dice(REG_FIGLIO,
						              "⛔⛔ il codificatore %u NON si e' riaperto a "
						              "%ux%u (%s): lo BUTTO invece di alimentarlo "
						              "con un'immagine che non e' la sua — meglio "
						              "nessun fotogramma che uno tagliato",
						              c, fo.larghezza, fo.altezza, errore);
						codificatore_libera(codif[c]);
						codif[c] = NULL;
					}
					/* ⛔ §5.2: il primo alla misura nuova DEVE essere una chiave.
					 *    `codificatore_ridimensiona()` lo impone gia' da se'; il
					 *    debito si segna lo stesso, perche' un codificatore
					 *    BUTTATO qui sopra rinascera' dal `codificatore_di()` piu'
					 *    sotto e quello non sa niente di questo cambio. */
					debito_chiave[c] = true;
				}

				/* 2. la regione del puntatore.  ⚠ Se non c'e' canale di input non
				 *    e' un guasto: e' una sessione senza input, e si tace qui
				 *    perche' la riga l'ha gia' scritta chi non l'ha aperto. */
				if (palco_input
				    && input_ritela(palco_input, fo.larghezza, fo.altezza) != 0)
					registro_dice(REG_FIGLIO,
					              "⛔ la regione del puntatore NON si e' rimappata "
					              "su %ux%u: da qui in poi il puntatore andrebbe "
					              "dove non deve",
					              fo.larghezza, fo.altezza);

				/* 3. ⛔ E LE CHIAVI TENUTE SI BUTTANO — difetto trovato
				 *    refutando: `tenuto[]` e' per CODEC, ma `tenuto_l`/`tenuto_a`
				 *    sono una coppia sola.  ⇒ Dopo un ridimensionamento il codec
				 *    non attivo conservava una chiave della misura VECCHIA che
				 *    `MSG_RIMANDA_PALCO` avrebbe spedito dichiarando la misura
				 *    NUOVA: il client avrebbe dimensionato la tela su un numero e
				 *    ricevuto pixel di un altro — cioe' l'immagine stirata e il
				 *    puntatore fuori posto, il difetto che questa catena esiste
				 *    per chiudere. */
				for (uint8_t c = 0; c < 3; c++) {
					if (!tenuto[c])
						continue;
					free(tenuto[c]);
					tenuto[c] = NULL;
					tenuto_byte[c] = 0;
					tenuto_chiave[c] = false;
				}

				/* 4. e la misura vera diventa la nostra. */
				tela_l = fo.larghezza;
				tela_a = fo.altezza;

				/* ⭐ 4-bis.  E LA COPIA ZERO SI RIPROVA, perche' la tela e'
				 *    cambiata: era stata negata per la tela di PRIMA, e su
				 *    questa il passo puo' essere buono.  ⛔ Senza questa riga
				 *    una sola tela storta spegnerebbe la copia zero per tutta
				 *    la sessione, comprese le tele che andrebbero benissimo —
				 *    cioe' una cura permanente per un difetto temporaneo.
				 * ⚠ Qui non si rimonta niente: si segna, e il palco lo rimonta
				 *   il ciclo poco piu' sotto.  ⛔ E il verdetto lo dara' di
				 *   nuovo il passo MISURATO, non un conto sulla larghezza. */
				if (COPIA_ZERO && !scheda_mai_piu && scheda_negata_l != 0
				    && strada_del_palco == CATTURA_STRADA_MEMORIA
				    && (fo.larghezza != scheda_negata_l
				        || fo.altezza != scheda_negata_a)) {
					scheda_negata_l = 0;
					scheda_negata_a = 0;
					scheda_da_riprovare = true;
					registro_dice(REG_FIGLIO,
					              "⭐ tela nuova %ux%u: la copia zero era stata "
					              "negata per la tela di prima, e su questa si "
					              "riprova",
					              fo.larghezza, fo.altezza);
				}

				/* 5. ⭐⭐ E SI RISPONDE AL PADRE, che sta aspettando questo
				 *    numero: senza, lui dovrebbe INDOVINARE dai fotogrammi a
				 *    quale richiesta risponde questa misura — e con due richieste
				 *    incatenate indovinerebbe male.  ⚠ Si manda anche quando
				 *    nessuno aveva chiesto niente (il palco che deriva da solo):
				 *    e' un fatto, e chi lo riceve decide che farne. */
				rispondi_tela(tela_voluta_l, tela_voluta_a, tela_l, tela_a);
			}

			istante_us = istante_del_fotogramma(&fo, ora_monotona_us());
			/* ⭐⭐ §6.2 — IL TIMBRO SI PRENDE QUI, nell'istante della cattura,
			 *     e da nessun'altra parte.  ⛔ Leggerlo dopo la codifica
			 *     direbbe «l'ultimo input iniettato prima della SPEDIZIONE»,
			 *     che e' un numero piu' alto: l'anello del ritardo misurerebbe
			 *     un ritardo piu' corto del vero — **in nostro favore**, cioe'
			 *     la direzione in cui nessuno sbaglia per caso
			 *     (`CODER.md` §1-bis, «il confine si sposta nella direzione
			 *     scomoda»). */
			/* ⛔ La mappa numero → codec sta QUI e in nessun altro posto: con
			 *    due codec un `? :` bastava, col terzo un `? :` annidato
			 *    direbbe «AV1» di ogni numero che non conosce — e il sintomo
			 *    sarebbe un flusso AV1 spedito con l'etichetta 3. */
			codifica_e_manda(&fo, codec_del_numero(codec_chiesto),
			                 codec_chiesto, NULL, NULL, istante_us, tela_l,
			                 tela_a, input_iniettato);
			/* ⛔⭐ IL RILASCIO — e sulla strada della scheda questa riga NON e'
			 *     una pulizia: e' la cura di `LEZIONI.md` §8.  Finche' non si
			 *     chiama, il buffer di Mutter e' nostro; e si chiama DOPO la
			 *     codifica, cioe' dopo che la GPU ha finito di leggerlo
			 *     (`codificatore_comprimi_scheda` aspetta davvero prima di
			 *     tornare).  ⚠ Spostarla di due righe piu' in su rimetterebbe in
			 *     piedi le due schermate che si alternano. */
			cattura_fermo_libera(&fo);

			/* ⛔ E se la scheda si e' rivelata impercorribile — codificatore in
			 *    software — il palco si rimonta sulla memoria.  ⚠ Si fa QUI e non
			 *    dentro `codifica_e_manda`: il fermo e' gia' rilasciato, e
			 *    smontare con un buffer ancora in mano renderebbe un `pw_buffer`
			 *    a una cattura che non c'e' piu'. */
			if (scheda_da_abbandonare || scheda_da_riprovare) {
				strada_del_palco = scheda_da_riprovare
				                       ? CATTURA_STRADA_SCHEDA
				                       : CATTURA_STRADA_MEMORIA;
				scheda_da_abbandonare = false;
				scheda_da_riprovare = false;
				smonta_il_palco(&mut, &cat);
				palco_attesa_ms = PALCO_RIPROVA_MIN_MS;
				palco_riprova_ms = registro_ora_ms() + palco_attesa_ms;
				continue;
			}
		}
	}

	codificatori_libera();
	for (uint8_t c = 0; c < 3; c++) {
		free(tenuto[c]);
		tenuto[c] = NULL;
	}
	registro_dice(REG_FIGLIO,
	              "il ciclo si ferma: %llu fotogrammi consegnati (%llu chiavi), "
	              "%llu attese a vuoto, %llu guasti",
	              (unsigned long long)ciclo_fotogrammi,
	              (unsigned long long)ciclo_chiavi,
	              (unsigned long long)ciclo_zero,
	              (unsigned long long)ciclo_guasti);

	/* ⛔⭐ E PRIMA DI TUTTO IL RESTO SI RILASCIA QUEL CHE E' RIMASTO GIU'.
	 *
	 *     `RCP.md` §11 la chiama «la regola col rapporto danno/costo piu' alto
	 *     del documento», e qui morde nel modo peggiore: il palco sopravvive al
	 *     client (I4), quindi un Ctrl rimasto premuto **non se ne va con la
	 *     connessione** — resta sul desktop dell'utente, che al riattacco lo
	 *     trova inservibile e non collega le due cose.
	 * ⚠ E si fa anche qui, non solo alla fine di ogni connessione: questo e'
	 *   l'ultimo istante in cui qualcuno puo' ancora farlo. */
	registro_dice(REG_FIGLIO,
	              "il canale di input si chiude: %u iniettati, %u rifiutati "
	              "dal compositore, %u non producibili con la disposizione (§7.3)",
	              (unsigned)input_iniettato, (unsigned)input_rifiutati,
	              (unsigned)input_non_producibili);
	/* ⚠ E il rilascio lo fa `smonta_il_palco`, che e' lo STESSO smontaggio del
	 *   rimontaggio: due strade per smontare il palco vorrebbero dire che una
	 *   delle due, un giorno, dimentichera' un pezzo. */
	smonta_il_palco(&mut, &cat);
	/* ⛔ E l'audio si spegne PRIMA di uscire, nell'ordine giusto:
	 *    `audio_regola_figlio(0)` ferma la cattura e ASPETTA il thread di
	 *    PipeWire.  ⚠ Uscire con quel thread ancora vivo vorrebbe dire lasciarlo
	 *    scrivere nell'anello di un processo che sta morendo — e il difetto si
	 *    presenterebbe una volta ogni tanto, all'uscita, che e' il posto in cui
	 *    nessuno guarda. */
	audio_regola_figlio(0);
	if (son) {
		suono_chiudi(son);
		son = NULL;
	}
	registro_dice(REG_FIGLIO, "il figlio di «%s» ha smontato il palco ed esce",
	              utente);
	_exit(0);
}
