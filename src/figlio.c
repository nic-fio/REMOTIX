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

#include "registro.h"

#include <errno.h>
#include <fcntl.h>
#include <grp.h>
#include <poll.h>
#include <pwd.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/prctl.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

/* Solo il figlio ha bisogno del palco.  Il padre non include niente di tutto
 * questo, e non e' pulizia: e' la dichiarazione che root non ci parla. */
#include "cattura.h"
#include "codificatore.h"
#include "mutter.h"
#include "sessione.h"

/* ⛔ Lo stesso tetto delle sessioni di `rcp.c` (`DECISIONI.md` §1.11: 16, fisso
 * in compilazione fino alla fase 3).  Un utente per figlio, quindi il numero e'
 * lo stesso — e quando quello diventera' un budget di pixel, questo lo seguira'
 * dallo stesso posto. */
#define MAX_FIGLI 16

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
	MSG_SONO = 10,      /* figlio → padre */
	MSG_PALCO = 11,     /* figlio → padre */
	MSG_FOTOGRAMMA = 12 /* figlio → padre */
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

/* ⛔ Che cosa il padre chiede al palco.  ⚠ `codec` a **0** vuol dire «smetti di
 *    catturare»: non e' un sentinella implicito, e' il valore che §4.3/§6.2
 *    riservano a «nessun codec negoziato», e qui vuol dire la stessa cosa —
 *    nessuno sta guardando. */
struct corpo_video {
	uint8_t codec;  /* 1 = HEVC, 2 = AV1, 0 = spegni */
	uint8_t chiave; /* ⛔ §5.2: il prossimo DEVE essere una chiave */
	uint16_t riempi;
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
};

/* Il messaggio piu' lungo che passa di qui. */
#define BUSTA_MAX (sizeof(struct testa) + sizeof(struct corpo_fotogramma) + PEZZO_MAX)

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
	/* ⛔ Il conto dei fotogrammi arrivati da questo figlio.  ⚠ Sta qui e non
	 *    in una variabile di modulo perche' e' PER FIGLIO: sommato fra due
	 *    utenti direbbe che il palco funziona anche quando ne funziona uno
	 *    solo — due misure sotto la stessa etichetta. */
	uint64_t fotogrammi_avuti, byte_avuti, chiavi_avute;
	uint64_t detto_conto_ms;
	/* ⛔ Che cosa il padre ha gia' chiesto a questo palco: si tiene per non
	 *    ripetere lo stesso comando a ogni giro di `poll`. */
	uint8_t video_codec_chiesto;
};

struct figli {
	struct figlio v[MAX_FIGLI];
	uint64_t prossima_matricola;
	uint32_t tela_l, tela_a;
	char dir_rilievo[256];
	bool c_e_rilievo;
	char percorso_mio[512]; /* /proc/self/exe risolto, per l'`exec` */
	FiglioDeposito deposita;
	FiglioCongedo congeda;
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

figli *figli_accendi(uint32_t tela_l, uint32_t tela_a, const char *dir_rilievo,
                     FiglioDeposito deposita, FiglioCongedo congeda, void *ctx)
{
	figli *f = (figli *)calloc(1, sizeof *f);
	ssize_t n;

	if (!f)
		return NULL;
	for (int i = 0; i < MAX_FIGLI; i++)
		f->v[i].fd = -1;
	f->prossima_matricola = 1;
	f->tela_l = tela_l;
	f->tela_a = tela_a;
	f->deposita = deposita;
	f->congeda = congeda;
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
	char e_home[512], e_user[96], e_log[96], e_path[128], e_runtime[160],
		e_bus[224], e_shell[16];
	char *argv[10];
	char *envp[9];
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
		            g->monta_a, g->monta_istante);
	free(g->monta);
	g->monta = NULL;
	g->monta_totale = g->monta_avuti = 0;
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
bool figli_video(figli *f, const char *utente, uint8_t codec, bool chiave)
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
	if (codec == g->video_codec_chiesto && !chiave)
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
		memset(g, 0, sizeof *g);
		g->fd = -1;
	}
	free(f);
}

/* ========================================================================== */
/* ⭐ IL FIGLIO — da qui in giu' si gira come l'utente, e non si torna indietro */

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

static void manda_fotogramma(uint8_t codec, bool chiave, uint32_t l, uint32_t a,
                             uint64_t istante_us, const uint8_t *dati, size_t byte)
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

/* ⛔⭐ IL FIGLIO SI TIENE QUEL CHE HA CODIFICATO, e la ragione non e' la
 *     velocita': e' che il PADRE ha un deposito solo (`webtransport.c`), quindi
 *     quando entra un altro utente il padre lo SVUOTA — e il primo utente, che
 *     ha ancora il suo figlio vivo, dovrebbe poterselo far rimandare senza
 *     ricatturare.
 *
 * ⚠ E si rimanda **lo stesso fotogramma**, non uno nuovo: la fase 2 e'
 *   un'immagine ferma, quella dell'accensione del palco
 *   (`fasi/02-primo-fotogramma.md`), e ricatturare qui vorrebbe dire consegnare
 *   due immagini diverse sotto la stessa etichetta.  ⛔ Il ciclo dei fotogrammi
 *   e' della fase 3. */
static uint8_t *tenuto[3];
static size_t tenuto_byte[3];
static bool tenuto_chiave[3];
static uint32_t tenuto_l, tenuto_a;
static uint64_t tenuto_istante;

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

/* ⛔ Quanto si aspetta un fotogramma dalla cattura dentro un giro del ciclo.
 *
 * ⚠ Non e' un tetto di cadenza: e' quanto si resta fermi PRIMA di tornare a
 *   guardare se il padre ha detto qualcosa.  ⭐ Qui si PUO' aspettare — questo
 *   e' un altro processo, e `CODER.md` §4.4 vieta l'attesa dentro il ciclo
 *   asincrono del server, non qui.  Ma non troppo: un `MSG_SPEGNITI` che
 *   arrivasse durante l'attesa resterebbe fermo tutto quel tempo.
 * ⛔ E su un desktop FERMO Mutter non consegna niente: questa attesa scade
 *    tutta, e il giro dopo ricomincia.  Zero fotogrammi su una scena ferma e'
 *    un RISULTATO (`CatturaPresa` lo distingue dal guasto), non un difetto. */
#define MOVIMENTO_ATTESA_S 0.25

static Codificatore *codif[3];
/* Quale codec il padre ha chiesto: 0 = nessuno, cioe' nessuno sta guardando. */
static uint8_t codec_chiesto;
/* ⛔ §5.2 — il debito della chiave, uno per codec: chiederla per l'HEVC non la
 *    produce sull'AV1, e trattarli insieme darebbe una chiave a chi non l'ha
 *    chiesta e un delta a chi si'. */
static bool debito_chiave[3];
static uint64_t ciclo_fotogrammi, ciclo_chiavi, ciclo_zero, ciclo_guasti;
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
static Codificatore *codificatore_di(CodecVideo codec, uint8_t indice,
                                     uint32_t tela_l, uint32_t tela_a)
{
	CodificatoreRichiesta r;
	char errore[256];

	if (indice > 2)
		return NULL;
	if (codif[indice])
		return codif[indice];

	memset(&r, 0, sizeof r);
	r.codec = codec;
	r.componente = NULL;
	r.larghezza = tela_l;
	r.altezza = tela_a;
	/* ⛔ La cadenza e' UNA, e la stessa che si chiede alla cattura. */
	r.fotogrammi_al_secondo = MOVIMENTO_FPS;
	r.modo = CODIFICATORE_QUALITA_CRF;
	r.qualita = 20;
	r.profondita = 10;
	r.formato = CODIFICATORE_PIXEL_BGRX;
	r.chiavi_ogni = 0;

	codif[indice] = codificatore_nuovo(&r, errore, sizeof errore);
	if (!codif[indice]) {
		registro_dice(REG_FIGLIO, "⛔ niente video per il codec %d: %s",
		              (int)codec, errore);
		return NULL;
	}
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
	for (uint8_t i = 0; i < 3; i++) {
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

/* Codifica un fotogramma con il codificatore VIVO di quel codec e lo manda al
 * padre.  ⛔ `chiave` non si suppone: e' quel che il codificatore ha letto dal
 * flusso (`fg.chiave`), e §6.2 lo scrive nel campo `tipo`. */
static bool codifica_e_manda(const CatturaFermo *fo, CodecVideo codec,
                             uint8_t numero, const char *dir_rilievo,
                             const char *nome_file, uint64_t istante_us,
                             uint32_t tela_l, uint32_t tela_a)
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
	if (numero < 3 && debito_chiave[numero]) {
		codificatore_chiedi_chiave(cod);
		debito_chiave[numero] = false;
	}

	if (!codificatore_comprimi(cod, fo->pixel, fo->stride, &fg)) {
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
		              "8→10 %s, conversione %llu us, codifica %llu us%s",
		              (int)codec, fg.byte, fg.chiave ? "CHIAVE" : "delta",
		              c->stringa_codec, c->profondita_flusso, c->livello_flusso,
		              c->promozione_8_a_10 ? "SI (dichiarata)" : "no",
		              (unsigned long long)fg.us_conversione,
		              (unsigned long long)fg.us_codifica,
		              fg.trattenuto ? " — ⚠ TRATTENUTO: il codificatore ha "
		                              "messo un fotogramma di ritardo" : "");
	else
		registro_dettaglio(REG_FIGLIO,
		                   "codec %d: %zu byte, %s, codifica %llu us%s",
		                   (int)codec, fg.byte, fg.chiave ? "CHIAVE" : "delta",
		                   (unsigned long long)fg.us_codifica,
		                   fg.trattenuto ? " — TRATTENUTO" : "");

	ciclo_fotogrammi++;
	if (fg.chiave)
		ciclo_chiavi++;

	manda_fotogramma(numero, fg.chiave, tela_l, tela_a, istante_us, fg.dati,
	                 fg.byte);
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
		}
	}
	/* ⛔ Il rilievo si scrive solo se qualcuno l'ha chiesto, e solo il primo:
	 *    sessanta file al secondo non sono un rilievo, sono un disco pieno. */
	if (ciclo_fotogrammi <= 2)
		rilievo_scrivi(dir_rilievo, nome_file, fg.dati, fg.byte);

	codificatore_rilascia(cod);
	return true;
}

/* ⛔ Il palco, preso una volta e TENUTO: `mutter` e `cattura` restano aperti
 *    finche' il figlio vive, perche' il monitor virtuale esiste finche' qualcuno
 *    consuma il flusso.  ⚠ E' l'invariante I4 fatta di processi: chi smonta il
 *    palco e' la morte del figlio, non la caduta di una connessione. */
static void prendi_il_palco(uint32_t tela_l, uint32_t tela_a,
                            const char *dir_rilievo, MutterSessione **fuori_m,
                            Cattura **fuori_c)
{
	struct corpo_palco p;
	GError *sbaglio = NULL;
	GDBusConnection *bus;
	CatturaFermo fo;
	CatturaPresa presa;
	uint64_t istante_us;
	MutterSessione *mut = NULL;
	Cattura *cat = NULL;

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
	bus = sessione_bus(&sbaglio);
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
		return;
	}
	p.bus_aperto = 1;
	g_object_unref(bus);
	registro_dice(REG_FIGLIO,
	              "⭐ IL BUS DI SESSIONE E' MIO: collegato come uid %ld — la "
	              "cosa che il padre root NON puo' fare (P2-6-montaggio.md §5.4)",
	              (long)geteuid());

	/* ⛔ SI GUARDA, NON SI TOCCA.  `sessione_assicura()` farebbe NASCERE una
	 *    sessione, e per un utente che non ha mai fatto login su questa
	 *    macchina non c'e' nemmeno `/run/user/<uid>` a cui appoggiarla: quella
	 *    e' la strada del login vero (`pam_open_session` → `pam_systemd`), e
	 *    non e' di questo mandato.  ⚠ Dichiarato invece che scoperto. */
	p.stato_sessione = (uint32_t)sessione_stato(tela_l, tela_a, NULL);
	if (p.stato_sessione != SESSIONE_SANA)
		registro_dice(REG_FIGLIO,
		              "⚠ la sessione grafica di questo utente e' «%s» (%u): "
		              "guardo e non tocco — far NASCERE una sessione e' del "
		              "login vero, non di qui",
		              sessione_marca((SessioneStato)p.stato_sessione),
		              p.stato_sessione);

	mut = mutter_apri(&sbaglio);
	if (!mut) {
		snprintf(p.guasto, sizeof p.guasto, "ScreenCast: %s",
		         sbaglio ? sbaglio->message : "(nessun dettaglio)");
		registro_dice(REG_FIGLIO, "⛔ nessun monitor virtuale da catturare: %s",
		              p.guasto);
		g_clear_error(&sbaglio);
		manda(MSG_PALCO, &p, sizeof p, NULL, 0);
		return;
	}

	/* ⛔ La cadenza si chiede UNA volta e con UN nome: `MOVIMENTO_FPS`.  Qui
	 *    c'era il letterale 60 e la richiesta di codifica ne dichiarava 30 —
	 *    due numeri diversi per la stessa grandezza. */
	cat = cattura_avvia(mutter_nodo(mut), tela_l, tela_a, MOVIMENTO_FPS,
	                    CATTURA_STRADA_MEMORIA, CATTURA_COLORE_BGRX, NULL, NULL,
	                    NULL, &sbaglio);
	if (!cat) {
		snprintf(p.guasto, sizeof p.guasto, "cattura: %s",
		         sbaglio ? sbaglio->message : "(nessun dettaglio)");
		registro_dice(REG_FIGLIO, "⛔ la cattura non si apre: %s", p.guasto);
		g_clear_error(&sbaglio);
		mutter_chiudi(mut);
		manda(MSG_PALCO, &p, sizeof p, NULL, 0);
		return;
	}
	*fuori_m = mut;
	*fuori_c = cat;

	memset(&fo, 0, sizeof fo);
	presa = cattura_prendi(cat, 5.0, &fo, &sbaglio);
	istante_us = istante_del_fotogramma(&fo, ora_monotona_us());
	p.presa = (uint32_t)presa;
	if (presa != CATTURA_PRESA_FATTA) {
		snprintf(p.guasto, sizeof p.guasto, "presa %u: %s", (unsigned)presa,
		         sbaglio ? sbaglio->message : "nessun fotogramma");
		registro_dice(REG_FIGLIO,
		              "⛔ nessun fotogramma in 5 s (%s): e' un RISULTATO se il "
		              "desktop non e' cambiato, un guasto se il flusso non e' "
		              "mai partito — e i due numeri sono diversi apposta",
		              p.guasto);
		g_clear_error(&sbaglio);
		manda(MSG_PALCO, &p, sizeof p, NULL, 0);
		return;
	}

	/* ⛔ Il nome del monitor DOPO il primo fotogramma, non dopo `cattura_avvia`:
	 *    la cucitura corretta il 12 agosto 2026 (`P2-6-montaggio.md` §5.1). */
	if (mutter_monitor_cerca(mut)) {
		guint prima = 0, dopo = 0;
		mutter_monitor_conteggi(mut, &prima, &dopo);
		p.monitor_prima = prima;
		p.monitor_dopo = dopo;
		snprintf(p.monitor, sizeof p.monitor, "%s", mutter_monitor_nostro(mut));
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
	              fo.consegna.nero ? "⛔ NERO" : "non nero");

	rilievo_scrivi(dir_rilievo, "cattura.bgrx", fo.pixel, (size_t)fo.byte);

	/* ⛔⭐ E QUESTA PRIMA CODIFICA RESTA, anche se adesso c'e' il ciclo: non
	 *     serve a spedire, serve a DIMOSTRARE che il palco funziona prima che
	 *     qualcuno lo chieda.  `p.flussi` e' il numero che `MSG_PALCO` porta al
	 *     padre, ed e' l'unica riga che distingue «nessuno guarda» da «il
	 *     codificatore non si apre».  ⚠ E i due codificatori restano APERTI:
	 *     sono quelli che il ciclo usera'.
	 * ⛔ §5.2: tutt'e due i primi devono essere una CHIAVE, e si chiede invece
	 *    di sperarlo. */
	debito_chiave[1] = debito_chiave[2] = true;
	if (codifica_e_manda(&fo, CODIFICATORE_HEVC, 1, dir_rilievo,
	                     "flusso-hevc.265", istante_us, tela_l, tela_a))
		p.flussi++;
	if (codifica_e_manda(&fo, CODIFICATORE_AV1, 2, dir_rilievo,
	                     "flusso-av1.obu", istante_us, tela_l, tela_a))
		p.flussi++;
	/* ⛔ E i contatori del ciclo ripartono da zero: questi due non sono
	 *    fotogrammi del movimento, sono la diagnosi dell'accensione.  Sommarli
	 *    direbbe «due fotogrammi consegnati» a un utente che non ne ha visto
	 *    nemmeno uno. */
	ciclo_fotogrammi = ciclo_chiavi = 0;

	cattura_fermo_libera(&fo);
	manda(MSG_PALCO, &p, sizeof p, NULL, 0);
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

	/* `--figlio-interno <utente> <uid> <gid> <l> <a> <matricola> <rilievo>` */
	if (argc < 9)
		_exit(40);
	utente = argv[2];
	atteso = (uid_t)strtoul(argv[3], NULL, 10);
	atteso_g = (gid_t)strtoul(argv[4], NULL, 10);
	tela_l = (uint32_t)strtoul(argv[5], NULL, 10);
	tela_a = (uint32_t)strtoul(argv[6], NULL, 10);
	mia_matricola = strtoull(argv[7], NULL, 10);
	dir_rilievo = argv[8];

	signal(SIGTERM, SIG_DFL);
	signal(SIGINT, SIG_DFL);
	signal(SIGPIPE, SIG_IGN);

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
	prendi_il_palco(tela_l, tela_a, dir_rilievo, &mut, &cat);

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

		/* ── 1. quel che il padre ha da dire, senza aspettare ────────── */
		for (;;) {
			pf.fd = fd_figlio;
			pf.events = POLLIN;
			pf.revents = 0;
			/* ⛔ Zero quando si sta catturando, il tetto quando non si
			 *    cattura: cosi' il processo fermo non gira a vuoto e quello
			 *    che lavora non perde tempo. */
			pronto = poll(&pf, 1, codec_chiesto ? 0 : 1000);
			if (pronto < 0) {
				if (errno == EINTR)
					continue;
				fine = true;
				break;
			}
			if (pronto == 0)
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
				if (cv.codec > 2) {
					registro_dice(REG_FIGLIO,
					              "⛔ il padre chiede il codec %u, che §6.2 non "
					              "definisce: NON cambio niente",
					              cv.codec);
					continue;
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
				codec_chiesto = cv.codec;
				/* ⛔ §5.2: il debito si segna sul codec CHIESTO, non su tutti.
				 *    Chiedere una chiave per l'HEVC non ne produce una
				 *    sull'AV1, e segnarli insieme darebbe una chiave a chi non
				 *    l'ha chiesta. */
				if (cv.chiave && cv.codec)
					debito_chiave[cv.codec] = true;
				continue;
			}
			if (t.tipo == MSG_RIMANDA_PALCO) {
				int quanti = 0;
				for (uint8_t c = 1; c < 3; c++) {
					if (!tenuto[c])
						continue;
					manda_fotogramma(c, tenuto_chiave[c], tenuto_l, tenuto_a,
					                 tenuto_istante, tenuto[c], tenuto_byte[c]);
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
				              "%u, %d/s chiesti, attesa %.2f s",
				              (unsigned long long)ciclo_fotogrammi,
				              (unsigned long long)ciclo_chiavi,
				              (unsigned long long)ciclo_zero,
				              (unsigned long long)ciclo_guasti, codec_chiesto,
				              MOVIMENTO_FPS, MOVIMENTO_ATTESA_S);
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
			if (presa != CATTURA_PRESA_FATTA) {
				ciclo_guasti++;
				registro_dice(REG_FIGLIO,
				              "⛔ la cattura non consegna piu' (presa %u: %s): "
				              "il ciclo continua, e questa riga dice che non e' "
				              "«la scena e' ferma»",
				              (unsigned)presa,
				              sbaglio ? sbaglio->message : "nessun dettaglio");
				g_clear_error(&sbaglio);
				cattura_fermo_libera(&fo);
				continue;
			}
			g_clear_error(&sbaglio);

			istante_us = istante_del_fotogramma(&fo, ora_monotona_us());
			codifica_e_manda(&fo, codec_chiesto == 1 ? CODIFICATORE_HEVC
			                                         : CODIFICATORE_AV1,
			                 codec_chiesto, NULL, NULL, istante_us, tela_l,
			                 tela_a);
			cattura_fermo_libera(&fo);
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

	if (cat)
		cattura_ferma(cat);
	if (mut)
		mutter_chiudi(mut);
	registro_dice(REG_FIGLIO, "il figlio di «%s» ha smontato il palco ed esce",
	              utente);
	_exit(0);
}
