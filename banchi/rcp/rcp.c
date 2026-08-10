/*
 * rcp.c — la stretta di mano di RCP/1, lato server.
 *
 * Le regole che seguono hanno tutte un numero di paragrafo accanto: chi le
 * cambia deve cambiare `RCP.md` per primo, o i due si separano in silenzio.
 */
#include "rcp.h"

#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

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
#define TETTO_ATTACCA 60000
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

#define MAX_MESSAGGIO (1024u * 1024u) /* §6.1 */
#define MAX_ACCUMULO (64u * 1024u)    /* quanto si tiene in attesa di un corpo */

enum stato {
	S_ATTESA_CIAO,
	S_ATTESA_CREDENZIALI,
	S_ATTESA_VERDETTO, /* CREDENZIALI ricevute, il ritardo fisso scorre */
	S_ATTESA_ATTACCA,
	S_ATTIVA,
	S_FINITA,
};

static const char *NOMI_STATO[] = {"attesa-ciao", "attesa-credenziali",
                                   "attesa-verdetto", "attesa-attacca",
                                   "attiva", "finita"};

struct rcp_sessione {
	rcp_ganci g;
	enum stato stato;
	char provenienza[64];
	/* ⛔ L'INDIRIZZO SENZA LA PORTA, e non e' un dettaglio: vedi il riquadro
	 * sopra `solo_indirizzo()`. */
	char indirizzo[64];
	char utente[257];
	uint64_t da_quando;   /* quando e' cominciato lo stato corrente */
	uint64_t ultimo_byte; /* l'ultimo byte arrivato DAL CLIENT (§5.3) */
	uint64_t cred_arrivo; /* quando e' arrivato CREDENZIALI */
	bool cred_buone;      /* il verdetto, gia' calcolato ma non ancora detto */
	uint8_t cred_motivo;  /* se non buone */
	bool attaccata;       /* occupa un posto nel registro delle sessioni */
	uint8_t acc[MAX_ACCUMULO];
	size_t acc_len;
	/* le capacita' negoziate, per il registro (§4.3: la scelta si scrive) */
	char codec[32];
	char profondita[32];
	char audio[32];
};

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

static bool posto_prendi(const char *utente)
{
	if (posto_occupato(utente))
		return false;
	for (int i = 0; i < MAX_ATTACCATE; i++) {
		if (!attaccate[i].usato) {
			attaccate[i].usato = true;
			snprintf(attaccate[i].utente, sizeof attaccate[i].utente, "%s",
			         utente);
			return true;
		}
	}
	return false;
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
/* ⛔ LA LIMITAZIONE DEI TENTATIVI — §4.4-bis
 *
 * Due contatori, uno per nome utente e uno per indirizzo, e si applica il piu'
 * severo.  ⚠ Il contatore per indirizzo non protegge da tutto — dietro un NAT
 * gli indirizzi si condividono — ed e' il motivo per cui quello per nome
 * esiste e si azzera con un successo.                                       */
#define SOGLIA 5
#define FINESTRA_CONTEGGIO 300000u /* 5 minuti */
#define BLOCCO_INIZIALE 30000u
#define BLOCCO_TETTO 900000u /* 15 minuti */
#define MAX_TENTATIVI 64

static struct {
	char chiave[257];
	bool usato;
	int falliti;
	uint64_t primo_fallito;
	uint64_t bloccato_fino;
	uint64_t blocco_corrente;
} tentativi[MAX_TENTATIVI];

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
 *    per **nome** copriva il buco, e il banco sarebbe stato verde.
 *
 * ⚠ Si taglia agli ULTIMI due punti, non ai primi: un indirizzo IPv6 e'
 *   `[fe80::1]:44661`, e tagliare al primo produrrebbe `[fe80`. */
static void solo_indirizzo(const char *da, char *fuori, size_t cap)
{
	const char *due = strrchr(da, ':');
	size_t n = due ? (size_t)(due - da) : strlen(da);
	if (n >= cap)
		n = cap - 1;
	memcpy(fuori, da, n);
	fuori[n] = 0;
}

static int trova_o_crea(const char *chiave)
{
	int libero = -1;
	for (int i = 0; i < MAX_TENTATIVI; i++) {
		if (tentativi[i].usato && strcmp(tentativi[i].chiave, chiave) == 0)
			return i;
		if (!tentativi[i].usato && libero < 0)
			libero = i;
	}
	if (libero < 0)
		return -1;
	memset(&tentativi[libero], 0, sizeof tentativi[libero]);
	tentativi[libero].usato = true;
	snprintf(tentativi[libero].chiave, sizeof tentativi[libero].chiave, "%s",
	         chiave);
	return libero;
}

static bool bloccato(const char *chiave, uint64_t ora)
{
	int i = trova_o_crea(chiave);
	return i >= 0 && ora < tentativi[i].bloccato_fino;
}

static void segna_fallito(const char *chiave, uint64_t ora)
{
	int i = trova_o_crea(chiave);
	if (i < 0)
		return;
	if (tentativi[i].falliti == 0 ||
	    ora - tentativi[i].primo_fallito > FINESTRA_CONTEGGIO) {
		tentativi[i].falliti = 0;
		tentativi[i].primo_fallito = ora;
	}
	tentativi[i].falliti++;
	if (tentativi[i].falliti >= SOGLIA) {
		/* ⛔ La finestra RADDOPPIA a ogni tentativo oltre la soglia, e non
		 * riparte da capo: chi insiste aspetta sempre di piu'. */
		uint64_t b = tentativi[i].blocco_corrente ? tentativi[i].blocco_corrente * 2
		                                          : BLOCCO_INIZIALE;
		if (b > BLOCCO_TETTO)
			b = BLOCCO_TETTO;
		tentativi[i].blocco_corrente = b;
		tentativi[i].bloccato_fino = ora + b;
	}
}

static void azzera_tentativi(const char *chiave)
{
	int i = trova_o_crea(chiave);
	if (i >= 0)
		memset(&tentativi[i], 0, sizeof tentativi[i]);
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

/* ------------------------------------------------------------------------ */
static void reg(rcp_sessione *s, const char *fmt, ...)
    __attribute__((format(printf, 2, 3)));

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
 *    di «va piano e non si capisce perche'». */
static const char *prima_comune(const char *elenco_client, const char *nostro,
                                char *fuori, size_t cap, char *scarti,
                                size_t cap_scarti)
{
	if (scarti && cap_scarti)
		scarti[0] = 0;
	const char *scelta = NULL;
	const char *p = elenco_client;
	while (*p) {
		const char *virgola = strchr(p, ',');
		size_t n = virgola ? (size_t)(virgola - p) : strlen(p);
		char voce[64];
		if (n && n < sizeof voce && n + 1 < cap) {
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
					/* ⚠ `%.*s` e non `%s`: al compilatore la lunghezza di
					 *   `voce` e' ignota, e con `%s` avverte di una
					 *   troncatura che la guardia qui sopra ha gia' escluso.
					 *   Un avviso che si sa innocuo e' un avviso che il
					 *   giorno dopo si smette di leggere. */
					snprintf(fuori, cap, "%.*s", (int)n, voce);
					scelta = fuori;
				}
			} else if (scarti && cap_scarti) {
				size_t g = strlen(scarti);
				if (g + n + 2 < cap_scarti)
					snprintf(scarti + g, cap_scarti - g, "%s%s",
					         g ? "," : "", voce);
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
	 * avvio.  Qui vale `no`, e la riga non serve. */
	sc_str(&w, "banco.marca");
	sc_str(&w, "no");
	if (!w.pieno)
		manda_messaggio(s, T_ECCOMI, corpo, w.len);
}

/* ------------------------------------------------------------------------ */
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
	char visti[32][65];
	int n_visti = 0;
	char c_codec[257] = "", c_prof[257] = "", c_audio[257] = "";
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
		if (lv > 256 || !utf8_valido(valore, lv)) {
			congeda(s, RCP_ERRORE_PROTOCOLLO, "valore di capacita' non valido");
			return false;
		}
		/* ⛔ Un nome ripetuto e' ERRORE_PROTOCOLLO: «vince l'ultimo» e «vince
		 * il primo» sono due implementazioni dello stesso documento. */
		for (int i = 0; i < n_visti; i++)
			if (strcmp(visti[i], nome) == 0) {
				congeda(s, RCP_ERRORE_PROTOCOLLO, "capacita' ripetuta");
				return false;
			}
		if (n_visti < 32)
			snprintf(visti[n_visti++], 65, "%s", nome);
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
	if (!prima_comune(c_codec, NOSTRO_CODEC, s->codec, sizeof s->codec,
	                  sc_codec, sizeof sc_codec) ||
	    !prima_comune(c_prof, NOSTRA_PROFONDITA, s->profondita,
	                  sizeof s->profondita, sc_prof, sizeof sc_prof) ||
	    !prima_comune(c_audio, NOSTRO_AUDIO, s->audio, sizeof s->audio,
	                  sc_audio, sizeof sc_audio)) {
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
	if (sc_codec[0] || sc_prof[0] || sc_audio[0])
		reg(s, "scartate voci sconosciute: video.codec=[%s] "
		       "video.profondita=[%s] audio.codec=[%s]",
		    sc_codec, sc_prof, sc_audio);
	manda_eccomi(s);
	s->stato = S_ATTESA_CREDENZIALI;
	return true;
}

static bool tratta_credenziali(rcp_sessione *s, lettore *l, uint64_t ora)
{
	char utente[257], parola[1025];
	size_t lu = le_str(l, utente, sizeof utente);
	size_t lp = le_str(l, parola, sizeof parola);
	if (l->corto) {
		congeda(s, RCP_ERRORE_PROTOCOLLO, "CREDENZIALI troncate");
		return false;
	}
	/* §4.4: gli intervalli.  Una stringa vuota e' legale per §6.0, e senza
	 * questi limiti `CREDENZIALI` con due stringhe di zero byte sarebbe
	 * conforme — e un attaccante non incrementerebbe nessun contatore. */
	if (lu < 1 || lu > 256 || lp < 1 || lp > 1024) {
		congeda(s, RCP_ERRORE_PROTOCOLLO, "utente o parola fuori intervallo");
		return false;
	}
	if (!utf8_valido(utente, lu)) {
		congeda(s, RCP_ERRORE_PROTOCOLLO, "utente non e' UTF-8 valido");
		return false;
	}
	snprintf(s->utente, sizeof s->utente, "%s", utente);
	/* ⛔ Tre righe di strumentazione, e non sono di passaggio: il 10 agosto
	 * 2026 la stretta di mano si fermava qui e «CREDENZIALI non e' arrivato»
	 * e «PAM non risponde» avevano lo stesso aspetto — cioe' nessuno.
	 * ⚠ La parola NON compare, a nessun livello (§4.4). */
	reg(s, "CREDENZIALI ricevute utente=%s (parola di %zu byte)", s->utente, lp);

	/* ⛔ Il limitatore PRIMA di PAM, e il rifiuto e' subito: §4.4-bis dice che
	 * l'attesa e' una FINESTRA in cui si rifiuta, non un ritardo — con un solo
	 * tentativo per connessione, un server che ritardasse di quindici minuti
	 * non consegnerebbe mai il rifiuto. */
	if (bloccato(s->utente, ora) || bloccato(s->indirizzo, ora)) {
		s->cred_buone = false;
		s->cred_motivo = RCP_TROPPI_TENTATIVI;
	} else {
		bool ok = s->g.verifica && s->g.verifica(s->g.ctx, utente, parola);
		reg(s, "PAM ha risposto: %s", ok ? "ammesso" : "respinto");
		s->cred_buone = ok;
		s->cred_motivo = RCP_CREDENZIALI_ERRATE;
		if (ok) {
			azzera_tentativi(s->utente);
		} else {
			segna_fallito(s->utente, ora);
			segna_fallito(s->indirizzo, ora);
		}
	}
	/* ⛔ La parola si azzera appena PAM ha risposto, e non compare in nessun
	 * registro a nessun livello (§4.4). */
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
	if (!posto_prendi(s->utente)) {
		reg(s, "posto NEGATO a %s da %s (occupati: %d)", s->utente,
		    s->provenienza, posti_occupati());
		congeda(s, RCP_GIA_ATTIVA_REMOTA,
		        "c'e' gia' un client attaccato a questa sessione");
		return false;
	}
	s->attaccata = true;
	reg(s, "posto PRESO da %s via %s (occupati adesso: %d)", s->utente,
	    s->provenienza, posti_occupati());

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
	solo_indirizzo(s->provenienza, s->indirizzo, sizeof s->indirizzo);
	reg(s, "canale di controllo aperto da %s (indirizzo per §4.4-bis: %s)",
	    s->provenienza, s->indirizzo);
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
	free(s);
}

const char *rcp_stato_nome(const rcp_sessione *s)
{
	return s ? NOMI_STATO[s->stato] : "?";
}

const char *rcp_utente(const rcp_sessione *s) { return s ? s->utente : ""; }

bool rcp_ricevi(rcp_sessione *s, const uint8_t *dati, size_t len, uint64_t ora)
{
	if (s->stato == S_FINITA) {
		/* ⛔ E si SCRIVE.  §4.4 dice che dopo `RESPINTO` il client non deve
		 * riprovare sulla stessa connessione, e §4.2 che dopo la fine della
		 * sessione non si spedisce piu' niente: sono due DEVE del CLIENT, e
		 * l'unico posto da cui si possono osservare e' qui.  ⚠ Senza questa
		 * riga un client che riprova e' indistinguibile da uno che si e'
		 * fermato — B11 misurerebbe il silenzio del server invece del
		 * comportamento della pagina. */
		reg(s, "⛔ %zu byte arrivati DOPO la fine della sessione da %s", len,
		    s->provenienza);
		return false;
	}
	/* ⭐ L'orologio del silenzio si azzera QUI, sui byte di RCP. */
	s->ultimo_byte = ora;
	if (s->acc_len + len > MAX_ACCUMULO) {
		congeda(s, RCP_ERRORE_PROTOCOLLO, "troppi byte in attesa di un corpo");
		return false;
	}
	memcpy(s->acc + s->acc_len, dati, len);
	s->acc_len += len;

	for (;;) {
		if (s->acc_len < 6)
			return true;
		lettore intest = {s->acc, s->acc_len, 0, false};
		uint16_t tipo = le_u16(&intest);
		uint32_t lung = le_u32(&intest);
		/* ⛔ La lunghezza si controlla PRIMA di allocare: chi alloca e poi
		 * verifica ha gia' regalato un megabyte a chi sa scrivere sei byte. */
		if (lung > MAX_MESSAGGIO) {
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
			uint8_t motivo = le_u8(&l);
			reg(s, "il client si congeda, motivo=%#04x", motivo);
			s->stato = S_FINITA;
			if (s->attaccata) {
				posto_lascia(s->utente);
				s->attaccata = false;
			}
			s->g.chiudi(s->g.ctx, motivo ? motivo : RCP_CHIUSO_DALL_UTENTE);
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
			 * inventa un tipo, e il registro deve distinguerli. */
			bool del_server = tipo == T_ECCOMI || tipo == T_AMMESSO ||
			                  tipo == T_RESPINTO || tipo == T_SESSIONE ||
			                  tipo == 0x000A /* CURSORE_FORMA */ ||
			                  tipo == 0x000E /* TELA */ ||
			                  tipo == T_BANCO_ESITO;
			char d[96];
			snprintf(d, sizeof d,
			         del_server ? "tipo %#06x: e' del server, non del client"
			                    : "tipo %#06x sconosciuto sul controllo",
			         tipo);
			congeda(s, RCP_ERRORE_PROTOCOLLO, d);
			return false;
		}
		}
		if (!avanti)
			return false;
		/* ⛔ §6.0: si avanza della lunghezza DICHIARATA, non di quanto si e'
		 * letto.  Se il corpo aveva byte in piu' — un riempimento — se ne
		 * accorge il controllo qui sotto, non il messaggio successivo. */
		if (l.i != lung) {
			congeda(s, RCP_ERRORE_PROTOCOLLO,
			        "il corpo ha byte in piu' dei campi previsti");
			return false;
		}
		memmove(s->acc, s->acc + 6 + lung, s->acc_len - 6 - lung);
		s->acc_len -= 6 + lung;
		s->da_quando = ora;
	}
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
 *   rosso sul codice giusto il giorno in cui non lo fosse (rilievo R3.3). */
void rcp_violazione(rcp_sessione *s, const char *dettaglio)
{
	if (!s)
		return;
	congeda(s, RCP_ERRORE_PROTOCOLLO, dettaglio);
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
	 * ⚠ La connessione resta aperta — vedi il riquadro in cima. */
	if (s->stato == S_ATTIVA && s->attaccata &&
	    ora - s->ultimo_byte > SILENZIO) {
		posto_lascia(s->utente);
		s->attaccata = false;
		reg(s, "STACCATO per silenzio: %llu ms senza un byte da %s "
		       "(posti occupati adesso: %d)",
		    (unsigned long long)(ora - s->ultimo_byte), s->provenienza,
		    posti_occupati());
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
