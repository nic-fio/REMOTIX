/*
 * 04-b23-filo-input.c — ⛔ B23: il canale di input di `RCP.md` §7.3, provato
 *                       violandolo, e con la TRACCIA in JSON.
 *
 *     cc -std=gnu11 -D_GNU_SOURCE -O1 -o 04-b23-filo-input 04-b23-filo-input.c
 *     ./04-b23-filo-input > 04-b23-traccia.jsonl
 *
 * ===========================================================================
 * ⛔ CHE COSA E' E CHE COSA NON E'
 *
 * ⭐ **Non giudica niente.**  Manda byte guasti sullo stream di input di
 *    `banchi/rcp/rcp.c` e **scrive quel che e' uscito dal lato che riceve**: i
 *    byte del `CONGEDO`, il codice della chiusura, e ⛔ **su quale byte il
 *    server ha accusato**.  A giudicare e' `04-b23-filo-input.py`, che e' un
 *    altro programma in un altro linguaggio, che tiene le PREVISIONI, e che
 *    `RCP.md` §7.3 lo ha letto per conto suo.
 *
 * ⛔ E il divieto vale nei due versi: questo file non conosce le previsioni,
 *    quel file non conosce i byte.  Se i due lettori tornassero a essere uno,
 *    la fase 4 comprerebbe un arbitro per poi buttarlo (`RCP.md` §0).
 *
 * ===========================================================================
 * ⛔⭐ SU QUALE BYTE, E PERCHE' E' LA MISURA CHE CONTA
 *
 * «La violazione e' stata accusata» e' una misura debole: un server che
 * accumula un megabyte e POI si accorge che la lunghezza non torna la accusa
 * anche lui — e ha gia' regalato il megabyte che §6.1 gli vieta di regalare.
 *
 * ⇒ Qui i byte si consegnano **UNO ALLA VOLTA**, e si registra l'indice del
 *   byte dopo il quale `rcp_ricevi_input()` ha detto «sessione finita».
 *   L'indice e' dichiarato in anticipo, nel file del giudice, e vale come
 *   verdetto quanto il motivo.
 *
 * ⭐ Che cosa distingue, in concreto:
 *
 *   · una lunghezza di 1 MiB annunciata per un `PUNTATORE` DEVE essere accusata
 *     al **byte 5** — i sei byte dell'intestazione, e non uno di piu'.  Un
 *     server che aspettasse il corpo la accuserebbe al byte 1 048 581, e nessun
 *     conteggio di violazioni lo vedrebbe;
 *   · un `id` fuori regola non si puo' accusare prima dell'ultimo byte del
 *     corpo, e accusarlo prima vorrebbe dire averlo indovinato.
 *
 * ⚠ E la consegna a byte singoli e' anche una prova di suo: un ricevente che
 *   desse per scontato di trovare il messaggio intero nel primo pezzo qui non
 *   arriverebbe in fondo a nessun caso.
 *
 * ===========================================================================
 * ⛔ E I CASI CHE DEVONO PASSARE VALGONO QUANTO LE VIOLAZIONI
 *
 * Senza di loro «il server chiude su tutto» darebbe verde su tutto.  Qui sono
 * contati a parte, hanno il loro denominatore, e su ciascuno si guarda **che
 * cosa e' stato iniettato** — non solo che la sessione regga: un server che
 * accettasse ogni messaggio e non iniettasse mai niente passerebbe un banco che
 * guarda la sola sopravvivenza.
 *
 * ⛔ Il caso di bordo che ha gia' un rilievo scritto contro di se' (R1.16):
 *    **1919 su una tela 1920 PASSA**, 1920 no.  Non e' un dettaglio — chiudere
 *    la sessione per un arrotondamento e' quel che `SPECIFICHE.md` §8.3 vieta.
 *
 * ===========================================================================
 * ⛔ E DOPO OGNI VIOLAZIONE, UNA CONNESSIONE NUOVA
 *
 * Un server che resta rotto dopo un rifiuto e' un difetto che il conteggio
 * delle violazioni non vede.  Dopo ogni caso si apre una sessione nuova e la si
 * porta fino a `ECCOMI`, ⛔ verificando che i byte dell'`ECCOMI` siano usciti —
 * non che nessuno abbia protestato.
 *
 * ===========================================================================
 * ⚠ QUEL CHE QUESTO BANCO **NON** PROVA, E VA DETTO
 *
 *  1. ⛔ **Non gira sul filo vero.**  I byte entrano da `rcp_ricevi_input()`
 *     chiamata in processo, non da uno stream WebTransport: `src/webtransport.c`
 *     oggi i byte del canale di input li **scarta** (`G_UNI_OK`), e quel file
 *     non e' di questo anello.  ⇒ La cucitura si chiede al coordinatore, e sta
 *     scritta nel rapporto `fasi/rapporti/F4-A3-filo-input.md`.
 *     ⭐ Quel che si perde e' l'inquadratura di WebTransport (il preambolo
 *       `40 54` + numero di sessione, rilievo P18) e la vera capsula di
 *       chiusura; quel che si prova per intero e' §7.3, §6.1 e §3.1 su
 *       **lo stesso sorgente** che il prodotto compila.
 *  2. ⛔ **Non tocca `libei`.**  I cinque ganci sono finti e registrano quel che
 *     e' stato chiesto loro: qui si prova che `rcp.c` chiede la cosa giusta, non
 *     che il desktop si muova.  Quella meta' e' di A4 (`04-b24-iniezione`).
 *  3. ⚠ **Il segno della rotella non si giudica qui**, e apposta: §7.3 dice che
 *     il server DEVE invertire l'asse verticale **dentro `input_rotella()`**.
 *     Questo banco verifica il contrario — che `rcp.c` NON lo inverta — perche'
 *     due inversioni si annullano.
 */
#include "rcp/rcp.c"

/* ⛔ Lo stream su cui viaggia l'input.  §2.5 dice «uno solo»: il numero e' un
 * nome, e il canale NON si riconosce dal numero (rilievo R11.9). */
#define STREAM_INPUT 6
#define STREAM_ALTRO 10

#define TELA_L 1920u
#define TELA_A 1080u

/* ------------------------------------------------------------------------ */
/* L'OSPITE FINTO — i tre ganci della fase 1, i quattro del video, i sei      */
/* dell'input.                                                               */

#define MAX_INJ 32

typedef struct {
	/* I byte usciti sul canale di CONTROLLO: e' da qui che si legge il
	 * `CONGEDO`, cioe' **dal lato che riceve** (§8.1). */
	/* ⛔ 512 KiB e non 8: un `CURSORE_FORMA` di 256x256 — il massimo che §5.5
	 * concede — pesa **262 158 byte** sul filo.  ⚠ Con un buffer piccolo il
	 * giudice leggerebbe un messaggio troncato DAL BANCO e darebbe rosso al
	 * server: il rosso all'imputato sbagliato, `LEZIONI.md` §1.9. */
	uint8_t ctrl[512u * 1024u];
	size_t ctrl_n;
	/* §3.1 punto 3: il motivo dentro la chiusura della sessione. */
	bool chiuso;
	uint8_t codice_chiusura;
	/* Che cosa e' stato chiesto ai cinque ganci, in ordine. */
	struct {
		const char *quale;
		long a, b;
	} inj[MAX_INJ];
	int inj_n;
	/* §7.3: quante volte e' stato chiesto il rilascio al distacco, e quanti
	 * ne ha dichiarati.  ⛔ Due numeri: «chiamato zero volte» e «chiamato e non
	 * c'era niente» sono due fatti diversi. */
	int rilasci_chiesti, rilasci_dichiarati;
	/* Quel che i cinque ganci rispondono: 0 consegnato, -1 no, 1 «non
	 * producibile» (solo la lettera).  E' l'iniezione del guasto DELL'OSPITE,
	 * dichiarata nella traccia. */
	int esito_ganci;
	/* Il video, per il campo `input` di §6.2. */
	uint8_t testa[28];
	size_t testa_n;
	bool testa_c_e;
	int64_t prossimo_stream;
} ospite;

static ospite O;

static void o_manda(void *c, const uint8_t *d, size_t n)
{
	(void)c;
	for (size_t i = 0; i < n && O.ctrl_n < sizeof O.ctrl; i++)
		O.ctrl[O.ctrl_n++] = d[i];
}
static void o_chiudi(void *c, uint8_t motivo)
{
	(void)c;
	/* ⚠ Il PRIMO codice, non l'ultimo: §3.1 vuole «il codice del motivo», e un
	 *   secondo motivo per lo stesso fatto direbbe due verita' sulla stessa
	 *   cosa.  Se ne arrivassero due, il giudice deve vedere il primo. */
	if (!O.chiuso) {
		O.chiuso = true;
		O.codice_chiusura = motivo;
	}
}
static void o_registra(void *c, const char *riga)
{
	(void)c;
	(void)riga;
	/* ⛔ IL REGISTRO DEL SERVER NON ENTRA NEL GIUDIZIO — `CODER.md` §3.8: «il
	 * registro di chi manda dice che ha chiamato una funzione, non che il byte
	 * e' arrivato».  Qui si butta apposta: quel che conta esce da `o_manda` e
	 * da `o_chiudi`. */
}
static bool o_verifica(void *c, const char *u, const char *p)
{
	(void)c;
	(void)u;
	(void)p;
	return true;
}

static bool o_video_apri(void *c, int64_t *stream, uint64_t *restano)
{
	(void)c;
	*stream = O.prossimo_stream;
	O.prossimo_stream += 4;
	*restano = 16;
	return true;
}
static bool o_video_scrivi(void *c, int64_t id, const uint8_t *d, size_t n)
{
	(void)c;
	(void)id;
	for (size_t i = 0; i < n && O.testa_n < sizeof O.testa; i++)
		O.testa[O.testa_n++] = d[i];
	O.testa_c_e = true;
	return true;
}
static void o_video_fin(void *c, int64_t id)
{
	(void)c;
	(void)id;
}
static void o_video_azzera(void *c, int64_t id)
{
	(void)c;
	(void)id;
}

static void segna(const char *quale, long a, long b)
{
	if (O.inj_n < MAX_INJ) {
		O.inj[O.inj_n].quale = quale;
		O.inj[O.inj_n].a = a;
		O.inj[O.inj_n].b = b;
		O.inj_n++;
	}
}
static int o_puntatore(void *c, uint32_t x, uint32_t y)
{
	(void)c;
	segna("puntatore", (long)x, (long)y);
	return O.esito_ganci;
}
static int o_pulsante(void *c, uint16_t k, int premuto)
{
	(void)c;
	segna("pulsante", (long)k, (long)premuto);
	return O.esito_ganci;
}
static int o_rotella(void *c, int32_t ax, int32_t ay)
{
	(void)c;
	/* ⛔ Si registra IL VALORE COSI' COM'E' ARRIVATO.  §7.3 vuole che il segno
	 * dell'asse verticale sia invertito **dentro `input_rotella()`**, cioe' in
	 * `src/input.c`: se `rcp.c` lo invertisse anche lui, le due inversioni si
	 * annullerebbero e la rotella andrebbe al contrario per ogni utente (forma
	 * d'errore E11).  ⇒ Il giudice pretende +120 quando il client ha mandato
	 * +120. */
	segna("rotella", (long)ax, (long)ay);
	return O.esito_ganci;
}
static int o_lettera(void *c, uint32_t car)
{
	(void)c;
	segna("lettera", (long)car, 0);
	return O.esito_ganci;
}
static int o_posizione(void *c, uint16_t k, int premuto)
{
	(void)c;
	segna("posizione", (long)k, (long)premuto);
	return O.esito_ganci;
}
static int o_rilascia(void *c)
{
	(void)c;
	O.rilasci_chiesti++;
	O.rilasci_dichiarati += 2; /* due tasti finti giu': il giudice li conta */
	return 2;
}

/* ------------------------------------------------------------------------ */
/* LA STRETTA DI MANO, IN PROCESSO — §4.3, §4.4, §4.5                        */

static void sc_msg(scrittore *w, uint16_t tipo, const uint8_t *corpo, size_t n)
{
	sc_u16(w, tipo);
	sc_u32(w, (uint32_t)n);
	for (size_t i = 0; i < n; i++)
		sc_byte(w, corpo[i]);
}

static void ganci_di_base(rcp_ganci *g, bool con_input, bool con_video)
{
	memset(g, 0, sizeof *g);
	g->manda = o_manda;
	g->chiudi = o_chiudi;
	g->registra = o_registra;
	g->verifica = o_verifica;
	if (con_video) {
		g->video_apri = o_video_apri;
		g->video_scrivi = o_video_scrivi;
		g->video_fin = o_video_fin;
		g->video_azzera = o_video_azzera;
	}
	/* ⛔ I cinque insieme o per niente: `rcp.c` guarda tutti e cinque. */
	if (con_input) {
		g->input_puntatore = o_puntatore;
		g->input_pulsante = o_pulsante;
		g->input_rotella = o_rotella;
		g->input_lettera = o_lettera;
		g->input_posizione = o_posizione;
		g->input_rilascia_tutto = o_rilascia;
	}
}

/* Manda `CIAO` e basta: serve alla ripresa, che si ferma a `ECCOMI`. */
static void manda_ciao(rcp_sessione *s, uint64_t ora)
{
	uint8_t buf[512], corpo[256];
	scrittore c = {corpo, sizeof corpo, 0, false};
	sc_u16(&c, RCP_VERSIONE);
	sc_u16(&c, 3);
	sc_str(&c, "video.codec");
	sc_str(&c, "hevc,av1");
	sc_str(&c, "video.profondita");
	sc_str(&c, "8,10");
	sc_str(&c, "audio.codec");
	sc_str(&c, "opus,pcm");
	scrittore w = {buf, sizeof buf, 0, false};
	sc_msg(&w, T_CIAO, corpo, c.len);
	rcp_ricevi(s, buf, w.len, ora);
}

/* Porta la sessione fino ad `attiva`, cioe' fino a `SESSIONE` spedita. */
static rcp_sessione *apri_attiva(bool con_input, bool con_video)
{
	rcp_ganci g;
	ganci_di_base(&g, con_input, con_video);
	rcp_sessione *s = rcp_apri(&g, "127.0.0.1:1", 1000);
	if (!s)
		return NULL;
	manda_ciao(s, 1000);

	uint8_t buf[512], corpo[256];
	scrittore c = {corpo, sizeof corpo, 0, false};
	sc_str(&c, "prova");
	sc_str(&c, "parola-di-prova");
	scrittore w = {buf, sizeof buf, 0, false};
	sc_msg(&w, T_CREDENZIALI, corpo, c.len);
	rcp_ricevi(s, buf, w.len, 1000);
	rcp_tempo(s, 3000); /* §4.4-bis: il secondo fisso */

	c = (scrittore){corpo, sizeof corpo, 0, false};
	sc_u32(&c, TELA_L);
	sc_u32(&c, TELA_A);
	sc_u32(&c, 1280);
	sc_u32(&c, 800);
	sc_str(&c, "it");
	w = (scrittore){buf, sizeof buf, 0, false};
	sc_msg(&w, T_ATTACCA, corpo, c.len);
	rcp_ricevi(s, buf, w.len, 3000);
	return s;
}

/* ------------------------------------------------------------------------ */
/* LA LETTURA DAL LATO CHE RICEVE — i byte del `CONGEDO`, non il registro     */

typedef struct {
	bool trovato;
	uint8_t motivo;
	char dettaglio[400];
	uint16_t primo_tipo;
	int quanti_messaggi;
	bool eccomi;
	/* ⭐ §7.2 — LA `CURSORE_FORMA` RILETTA COME LA LEGGEREBBE LA PAGINA.
	 *
	 * ⛔ Non si guarda il valore di ritorno di `rcp_cursore_forma()`: quello e'
	 *    il registro di chi manda, e `CODER.md` §3.8 dice che «il registro di chi
	 *    manda dice che ha chiamato una funzione, non che il byte e' arrivato».
	 *    Qui si riaprono i byte usciti sul canale di controllo e si rifa' il
	 *    conto di §7.2: `lunghezza == 8 + larghezza x altezza x 4`. */
	int cursori;              /* quanti CURSORE_FORMA sono usciti */
	uint32_t cur_lunghezza;   /* la lunghezza DICHIARATA nell'inquadratura */
	uint16_t cur_l, cur_a;
	int16_t cur_ax, cur_ay;
	bool cur_lunghezza_torna; /* §7.2: 8 + l*a*4 */
	bool cur_immagine_intatta;/* i byte dell'immagine sono quelli dati? */
} letto;

/* ⛔ L'immagine di prova e' un DISEGNO NOTO, non zeri: `i & 0xFF`.  ⚠ Con un
 *    riempimento di zeri, «memoria altrui» e «l'immagine giusta» avrebbero lo
 *    stesso aspetto — ed e' precisamente il difetto che §7.2 nomina.  Con un
 *    disegno, il giudice puo' dire che sono arrivati QUEI byte. */
static uint8_t IMMAGINE[256u * 256u * 4u];
static void immagine_prepara(void)
{
	for (size_t i = 0; i < sizeof IMMAGINE; i++)
		IMMAGINE[i] = (uint8_t)(i & 0xFF);
}

static void leggi_controllo(letto *L)
{
	memset(L, 0, sizeof *L);
	size_t off = 0;
	while (off + 6 <= O.ctrl_n) {
		uint16_t tipo = (uint16_t)((O.ctrl[off] << 8) | O.ctrl[off + 1]);
		uint32_t lung = ((uint32_t)O.ctrl[off + 2] << 24) |
		                ((uint32_t)O.ctrl[off + 3] << 16) |
		                ((uint32_t)O.ctrl[off + 4] << 8) | O.ctrl[off + 5];
		if (off + 6 + lung > O.ctrl_n)
			break;
		if (L->quanti_messaggi == 0)
			L->primo_tipo = tipo;
		L->quanti_messaggi++;
		if (tipo == T_ECCOMI)
			L->eccomi = true;
		if (tipo == T_CURSORE_FORMA) {
			L->cursori++;
			L->cur_lunghezza = lung;
			if (lung >= 8) {
				const uint8_t *c = O.ctrl + off + 6;
				L->cur_l = (uint16_t)((c[0] << 8) | c[1]);
				L->cur_a = (uint16_t)((c[2] << 8) | c[3]);
				L->cur_ax = (int16_t)((c[4] << 8) | c[5]);
				L->cur_ay = (int16_t)((c[6] << 8) | c[7]);
				/* ⛔ §7.2: «la lunghezza del messaggio DEVE valere esattamente
				 * 8 + larghezza x altezza x 4».  Il conto si rifa' QUI, dai
				 * campi che sono arrivati — non da quelli che sono stati
				 * passati alla funzione. */
				size_t attesa = 8u + (size_t)L->cur_l * L->cur_a * 4u;
				L->cur_lunghezza_torna = (attesa == lung);
				L->cur_immagine_intatta =
				    L->cur_lunghezza_torna &&
				    (lung == 8 ||
				     memcmp(c + 8, IMMAGINE, lung - 8) == 0);
			}
		}
		if (tipo == T_CONGEDO && lung >= 1 && !L->trovato) {
			L->trovato = true;
			L->motivo = O.ctrl[off + 6];
			if (lung >= 3) {
				uint32_t n = (uint32_t)((O.ctrl[off + 7] << 8) | O.ctrl[off + 8]);
				if (n > sizeof L->dettaglio - 1)
					n = sizeof L->dettaglio - 1;
				if (off + 9 + n <= O.ctrl_n) {
					memcpy(L->dettaglio, O.ctrl + off + 9, n);
					L->dettaglio[n] = 0;
				}
			}
		}
		off += 6 + lung;
	}
}

/* ------------------------------------------------------------------------ */
/* LA SCENA DI UN CASO — tutto quel che lo distingue, dichiarato              */

typedef struct {
	const char *nome;
	/* i byte VALIDI mandati prima, in blocco, e NON contati */
	uint8_t prima[512];
	size_t prima_n;
	/* i byte del caso: si consegnano UNO ALLA VOLTA, e l'indice e' su questi */
	uint8_t byte[4096];
	size_t byte_n;
	int64_t stream;       /* su quale stream vanno i byte del caso */
	int64_t stream_prima; /* su quale stream vanno quelli di prima */
	bool prima_di_sessione; /* non si arriva a `SESSIONE`: §2.5 */
	bool ganci;           /* i cinque ganci d'iniezione collegati? */
	int esito_ganci;      /* 0 · -1 · 1 (solo la lettera) */
	bool adatta;          /* §7.1: si cambia la tela prima del caso */
	uint32_t adatta_l, adatta_a;
	uint64_t ora_tela;    /* quando */
	uint64_t ora;         /* l'ora dei byte del caso */
	bool fotogramma;      /* §6.2: si spedisce un fotogramma alla fine */
	bool congeda_alla_fine; /* §7.3: si chiude, per guardare il rilascio */
	/* ⭐ §7.2 — la forma del cursore, spedita dal server verso il client.
	 * ⛔ `cur_bugia` e' l'iniezione del guasto DI CHI CHIAMA, non del prodotto:
	 *    dichiara una misura e ne porta un'altra, che e' il caso in cui «leggo
	 *    quel che c'e' e vado avanti» confeziona un cursore fatto di memoria
	 *    altrui.  Si dichiara qui perche' il giudice lo possa distinguere da un
	 *    difetto di `rcp.c`. */
	bool cursore;
	uint16_t cur_l, cur_a;
	int16_t cur_ax, cur_ay;
	long cur_bugia;       /* byte in piu'/in meno DICHIARATI a `immagine_n` */
	bool cur_niente_immagine; /* si passa NULL */
	bool cur_prima_di_sessione;
} scena;

static void scena_nuova(scena *sc, const char *nome)
{
	memset(sc, 0, sizeof *sc);
	sc->nome = nome;
	sc->stream = STREAM_INPUT;
	sc->stream_prima = STREAM_INPUT;
	sc->ganci = true;
	sc->esito_ganci = 0;
	sc->ora = 5000;
	sc->ora_tela = 4000;
}

/* I costruttori dei cinque messaggi di §7.3. */
static void msg(uint8_t *out, size_t *n, uint16_t tipo, uint32_t lung_dichiarata,
                const uint8_t *corpo, size_t corpo_n)
{
	scrittore w = {out + *n, 4096, 0, false};
	sc_u16(&w, tipo);
	sc_u32(&w, lung_dichiarata);
	for (size_t i = 0; i < corpo_n; i++)
		sc_byte(&w, corpo[i]);
	*n += w.len;
}

static size_t comuni(uint8_t *c, uint32_t id, uint64_t istante)
{
	scrittore w = {c, 64, 0, false};
	sc_u32(&w, id);
	sc_u64(&w, istante);
	return w.len;
}

static void m_puntatore(uint8_t *out, size_t *n, uint32_t id, uint32_t x,
                        uint32_t y)
{
	uint8_t c[64];
	scrittore w = {c, sizeof c, 0, false};
	w.len = comuni(c, id, 1234000ull);
	sc_u32(&w, x);
	sc_u32(&w, y);
	msg(out, n, T_PUNTATORE, (uint32_t)w.len, c, w.len);
}
static void m_pulsante(uint8_t *out, size_t *n, uint32_t id, uint16_t k,
                       uint8_t premuto)
{
	uint8_t c[64];
	scrittore w = {c, sizeof c, 0, false};
	w.len = comuni(c, id, 1234000ull);
	sc_u16(&w, k);
	sc_byte(&w, premuto);
	msg(out, n, T_PULSANTE, (uint32_t)w.len, c, w.len);
}
static void m_posizione(uint8_t *out, size_t *n, uint32_t id, uint16_t k,
                        uint8_t premuto)
{
	uint8_t c[64];
	scrittore w = {c, sizeof c, 0, false};
	w.len = comuni(c, id, 1234000ull);
	sc_u16(&w, k);
	sc_byte(&w, premuto);
	msg(out, n, T_POSIZIONE_TASTO, (uint32_t)w.len, c, w.len);
}
static void m_rotella(uint8_t *out, size_t *n, uint32_t id, int32_t ax,
                      int32_t ay)
{
	uint8_t c[64];
	scrittore w = {c, sizeof c, 0, false};
	w.len = comuni(c, id, 1234000ull);
	sc_u32(&w, (uint32_t)ax);
	sc_u32(&w, (uint32_t)ay);
	msg(out, n, T_ROTELLA, (uint32_t)w.len, c, w.len);
}
static void m_lettera(uint8_t *out, size_t *n, uint32_t id, uint32_t car)
{
	uint8_t c[64];
	scrittore w = {c, sizeof c, 0, false};
	w.len = comuni(c, id, 1234000ull);
	sc_u32(&w, car);
	msg(out, n, T_LETTERA, (uint32_t)w.len, c, w.len);
}

/* ------------------------------------------------------------------------ */
/* LA TRACCIA — una riga JSON per caso                                       */

static void virgolette(const char *t)
{
	putchar('"');
	for (const unsigned char *p = (const unsigned char *)t; *p; p++) {
		if (*p == '"' || *p == '\\')
			printf("\\%c", *p);
		else if (*p < 0x20)
			printf("\\u%04x", *p);
		else
			putchar(*p);
	}
	putchar('"');
}

/* ------------------------------------------------------------------------ */
/* L'ESECUZIONE DI UN CASO                                                    */

static void gira(const scena *sc)
{
	memset(&O, 0, sizeof O);
	O.prossimo_stream = 3;
	O.esito_ganci = sc->esito_ganci;

	rcp_sessione *s;
	if (sc->prima_di_sessione || sc->cur_prima_di_sessione) {
		/* ⛔ §2.5: lo stream di input si apre DOPO `SESSIONE`.  Qui la stretta
		 * di mano si ferma prima, e i byte arrivano lo stesso. */
		rcp_ganci g;
		ganci_di_base(&g, sc->ganci, sc->fotogramma);
		s = rcp_apri(&g, "127.0.0.1:1", 1000);
		manda_ciao(s, 1000);
	} else {
		s = apri_attiva(sc->ganci, sc->fotogramma);
	}
	if (!s) {
		fprintf(stderr, "⛔ sessione non aperta per «%s»\n", sc->nome);
		return;
	}

	/* §7.1: il cambio di tela, quando il caso lo chiede.  ⛔ Con l'ora, o il
	 * secondo di grazia non si apre — ed e' il ripiego dichiarato di
	 * `rcp_tela_adattata()`. */
	if (sc->adatta)
		rcp_tela_adattata_ora(s, sc->adatta_l, sc->adatta_a, sc->ora_tela);

	/* ⛔ I byte «di prima» sono VALIDI e vanno in blocco: non sono il caso, e
	 * contarli sposterebbe l'indice dichiarato. */
	bool viva = true;
	if (sc->prima_n)
		viva = rcp_ricevi_input(s, sc->stream_prima, sc->prima, sc->prima_n,
		                        sc->ora);

	/* ⛔⭐ UNO ALLA VOLTA: e' questa riga che rende misurabile «su quale byte». */
	int accusato = -1;
	if (viva) {
		for (size_t i = 0; i < sc->byte_n; i++) {
			if (!rcp_ricevi_input(s, sc->stream, sc->byte + i, 1, sc->ora)) {
				accusato = (int)i;
				break;
			}
		}
	}

	uint32_t ultimo_iniettato = rcp_input_ultimo_iniettato(s);
	uint32_t ultimo_id = rcp_input_ultimo_id(s);

	/* §6.2: il campo `input` torna indietro nei 28 byte del fotogramma.  ⛔ Il
	 * numero lo legge CHI CATTURA nell'istante della cattura — qui, adesso — e
	 * lo passa: non se lo prende `rcp_video_apri()`. */
	if (sc->fotogramma && !rcp_e_finita(s)) {
		static const uint8_t dati[16] = {0};
		rcp_video_spedisci(s, true, dati, sizeof dati, 999000ull,
		                   ultimo_iniettato, sc->ora);
	}

	/* ⭐ §7.2: la forma del cursore.  ⛔ L'esito si REGISTRA ma non si giudica:
	 * a giudicare sono i byte usciti sul canale di controllo (§8.1, `CODER.md`
	 * §3.8). */
	int esito_cursore = 2; /* 2 = non chiamata */
	if (sc->cursore) {
		size_t veri = (size_t)sc->cur_l * sc->cur_a * 4u;
		long dichiarati = (long)veri + sc->cur_bugia;
		if (dichiarati < 0)
			dichiarati = 0;
		esito_cursore = rcp_cursore_forma(
		    s, sc->cur_l, sc->cur_a, sc->cur_ax, sc->cur_ay,
		    sc->cur_niente_immagine ? NULL : IMMAGINE, (size_t)dichiarati);
	}

	if (sc->congeda_alla_fine)
		rcp_congeda(s, RCP_CHIUSO_DALL_UTENTE, "fine del caso");

	bool finita = rcp_e_finita(s);
	const char *stato = rcp_stato_nome(s);

	letto L;
	leggi_controllo(&L);

	/* ⛔ Il rilascio di §7.3 si guarda PRIMA di `rcp_libera()` per i casi che
	 * chiudono da se', e DOPO per gli altri: `rcp_libera()` e' l'ultima rete e
	 * scatta comunque.  Qui si stampano tutt'e due i numeri. */
	int rilasci_prima = O.rilasci_chiesti;
	rcp_libera(s);
	int rilasci_dopo = O.rilasci_chiesti;
	rcp_azzera_registro_sessioni();

	/* ------------------------------------------------------------------ */
	/* ⛔ LA RIPRESA: dopo il caso, una connessione NUOVA deve arrivare a
	 *    `ECCOMI`.  Un server che resta rotto dopo un rifiuto e' un difetto che
	 *    il conteggio delle violazioni non vede. */
	size_t ctrl_del_caso = O.ctrl_n;
	uint8_t chiuso_del_caso = O.chiuso;
	uint8_t codice_del_caso = O.codice_chiusura;
	O.ctrl_n = 0;
	O.chiuso = false;
	rcp_ganci g2;
	ganci_di_base(&g2, true, false);
	rcp_sessione *r = rcp_apri(&g2, "127.0.0.2:1", 20000);
	bool ripresa = false;
	if (r) {
		manda_ciao(r, 20000);
		letto L2;
		leggi_controllo(&L2);
		ripresa = L2.eccomi;
		rcp_libera(r);
		rcp_azzera_registro_sessioni();
	}
	(void)ctrl_del_caso;

	/* ------------------------------------------------------------------ */
	printf("{\"caso\":");
	virgolette(sc->nome);
	printf(",\"byte_mandati\":%zu", sc->byte_n);
	printf(",\"accusato_al_byte\":%d", accusato);
	printf(",\"congedo\":%s", L.trovato ? "true" : "false");
	if (L.trovato)
		printf(",\"motivo\":%u", L.motivo);
	else
		printf(",\"motivo\":null");
	printf(",\"dettaglio\":");
	virgolette(L.dettaglio);
	if (chiuso_del_caso)
		printf(",\"codice_chiusura\":%u", codice_del_caso);
	else
		printf(",\"codice_chiusura\":null");
	printf(",\"finita\":%s", finita ? "true" : "false");
	printf(",\"stato\":");
	virgolette(stato);
	printf(",\"ultimo_id\":%u,\"ultimo_iniettato\":%u", ultimo_id,
	       ultimo_iniettato);
	printf(",\"ganci\":%s,\"esito_ganci\":%d", sc->ganci ? "true" : "false",
	       sc->esito_ganci);
	printf(",\"rilasci_prima_di_liberare\":%d,\"rilasci_dopo\":%d",
	       rilasci_prima, rilasci_dopo);
	printf(",\"iniezioni\":[");
	for (int i = 0; i < O.inj_n; i++)
		printf("%s{\"quale\":\"%s\",\"a\":%ld,\"b\":%ld}", i ? "," : "",
		       O.inj[i].quale, O.inj[i].a, O.inj[i].b);
	printf("]");
	printf(",\"testa_video\":");
	if (O.testa_c_e) {
		putchar('"');
		for (size_t i = 0; i < O.testa_n; i++)
			printf("%02x", O.testa[i]);
		putchar('"');
	} else {
		printf("null");
	}
	printf(",\"cursori_sul_filo\":%d,\"cursore_esito\":%d", L.cursori,
	       esito_cursore);
	printf(",\"cursore_lunghezza\":%u,\"cursore_l\":%u,\"cursore_a\":%u",
	       L.cur_lunghezza, L.cur_l, L.cur_a);
	printf(",\"cursore_ax\":%d,\"cursore_ay\":%d", L.cur_ax, L.cur_ay);
	printf(",\"cursore_lunghezza_torna\":%s,\"cursore_immagine_intatta\":%s",
	       L.cur_lunghezza_torna ? "true" : "false",
	       L.cur_immagine_intatta ? "true" : "false");
	printf(",\"ripresa_fino_a_eccomi\":%s", ripresa ? "true" : "false");
	printf("}\n");
	fflush(stdout);
}

/* ========================================================================= */
/* I CASI.  ⛔ Qui ci sono i BYTE; le previsioni — su quale byte, con quale   */
/*          motivo — stanno in `04-b23-filo-input.py`, che e' un altro        */
/*          programma e non conosce questo file.                             */
/* ========================================================================= */

int main(void)
{
	scena sc;

	immagine_prepara();

	/* ── §2.5: il canale, e il verso ──────────────────────────────────── */
	static const struct {
		const char *nome;
		uint16_t tipo;
	} CANALI[] = {
	    {"canale-controllo-su-input", 0x0001},
	    {"canale-appunti-su-input", 0x0201},
	    {"canale-video-su-input", 0x0301},
	    {"canale-audio-su-input", 0x0401},
	    {"canale-sconosciuto", 0x0701},
	};
	for (size_t i = 0; i < sizeof CANALI / sizeof CANALI[0]; i++) {
		scena_nuova(&sc, CANALI[i].nome);
		uint8_t c[20] = {0};
		msg(sc.byte, &sc.byte_n, CANALI[i].tipo, 20, c, 20);
		gira(&sc);
	}

	/* ── §7.3: i tipi che non esistono ────────────────────────────────── */
	scena_nuova(&sc, "tipo-0x0100");
	{
		uint8_t c[20] = {0};
		msg(sc.byte, &sc.byte_n, 0x0100, 20, c, 20);
	}
	gira(&sc);

	scena_nuova(&sc, "tipo-0x0106");
	{
		uint8_t c[20] = {0};
		msg(sc.byte, &sc.byte_n, 0x0106, 20, c, 20);
	}
	gira(&sc);

	/* ── §6.1: la lunghezza che non torna ─────────────────────────────── */
	scena_nuova(&sc, "lunghezza-in-piu");
	{
		uint8_t c[21] = {0};
		msg(sc.byte, &sc.byte_n, T_PUNTATORE, 21, c, 21);
	}
	gira(&sc);

	scena_nuova(&sc, "lunghezza-in-meno");
	{
		uint8_t c[19] = {0};
		msg(sc.byte, &sc.byte_n, T_PUNTATORE, 19, c, 19);
	}
	gira(&sc);

	/* ⛔ §6.0: «un byte in piu' che fa tornare i conti in una struttura C».
	 *    Il `PULSANTE` occupa QUINDICI byte, non sedici. */
	scena_nuova(&sc, "pulsante-allineato-a-16");
	{
		uint8_t c[16] = {0};
		msg(sc.byte, &sc.byte_n, T_PULSANTE, 16, c, 16);
	}
	gira(&sc);

	/* ⛔ §6.1: «la lunghezza si controlla PRIMA di allocare».  Qui il corpo non
	 *    si manda affatto: se il server aspettasse i byte, non accuserebbe mai. */
	scena_nuova(&sc, "lunghezza-1mib");
	{
		msg(sc.byte, &sc.byte_n, T_PUNTATORE, 2u * 1024u * 1024u, NULL, 0);
	}
	gira(&sc);

	scena_nuova(&sc, "lunghezza-4gib");
	{
		msg(sc.byte, &sc.byte_n, T_PUNTATORE, 0xFFFFFFFFu, NULL, 0);
	}
	gira(&sc);

	/* ── §7.3: l'identificatore ───────────────────────────────────────── */
	scena_nuova(&sc, "id-zero");
	m_puntatore(sc.byte, &sc.byte_n, 0, 10, 10);
	gira(&sc);

	scena_nuova(&sc, "id-ripetuto");
	m_puntatore(sc.prima, &sc.prima_n, 5, 10, 10);
	m_puntatore(sc.byte, &sc.byte_n, 5, 11, 11);
	gira(&sc);

	scena_nuova(&sc, "id-indietro");
	m_puntatore(sc.prima, &sc.prima_n, 9, 10, 10);
	m_puntatore(sc.byte, &sc.byte_n, 4, 11, 11);
	gira(&sc);

	/* ⛔⭐ IL CASO CHE SEPARA UN CONTATORE DA CINQUE.  §7.3: «cresce di almeno
	 *     uno SU TUTTO IL CANALE, non uno per tipo».  Con cinque contatori per
	 *     tipo, questo `PUNTATORE(4)` dopo un `PULSANTE(9)` e' un legittimo
	 *     «primo PUNTATORE» e passa. */
	scena_nuova(&sc, "id-per-tipo-invece-che-per-canale");
	m_pulsante(sc.prima, &sc.prima_n, 9, 0x110, 1);
	m_puntatore(sc.byte, &sc.byte_n, 4, 11, 11);
	gira(&sc);

	/* ── §7.3: le coordinate ──────────────────────────────────────────── */
	scena_nuova(&sc, "x-1920-su-tela-1920");
	m_puntatore(sc.byte, &sc.byte_n, 1, 1920, 500);
	gira(&sc);

	scena_nuova(&sc, "y-1080-su-tela-1080");
	m_puntatore(sc.byte, &sc.byte_n, 1, 500, 1080);
	gira(&sc);

	scena_nuova(&sc, "x-enorme");
	m_puntatore(sc.byte, &sc.byte_n, 1, 0xFFFFFFFFu, 0);
	gira(&sc);

	/* §7.1: la grazia scaduta — un secondo e mezzo dopo il cambio di tela. */
	scena_nuova(&sc, "grazia-scaduta");
	sc.adatta = true;
	sc.adatta_l = 1280;
	sc.adatta_a = 720;
	sc.ora_tela = 4000;
	sc.ora = 5501; /* 1501 ms dopo */
	m_puntatore(sc.byte, &sc.byte_n, 1, 1900, 1000);
	gira(&sc);

	/* §7.1: dentro il secondo, ma la coordinata non era valida NEMMENO sulla
	 * tela vecchia — la grazia copre le coordinate vecchie, non quelle
	 * sbagliate. */
	scena_nuova(&sc, "grazia-non-copre-le-coordinate-sbagliate");
	sc.adatta = true;
	sc.adatta_l = 1280;
	sc.adatta_a = 720;
	sc.ora_tela = 4000;
	sc.ora = 4500;
	m_puntatore(sc.byte, &sc.byte_n, 1, 5000, 5000);
	gira(&sc);

	/* ── §7.3: premuto ────────────────────────────────────────────────── */
	scena_nuova(&sc, "pulsante-premuto-2");
	m_pulsante(sc.byte, &sc.byte_n, 1, 0x110, 2);
	gira(&sc);

	scena_nuova(&sc, "posizione-premuto-255");
	m_posizione(sc.byte, &sc.byte_n, 1, 30, 255);
	gira(&sc);

	/* ── §7.3: il carattere ───────────────────────────────────────────── */
	scena_nuova(&sc, "lettera-oltre-10ffff");
	m_lettera(sc.byte, &sc.byte_n, 1, 0x110000);
	gira(&sc);

	scena_nuova(&sc, "lettera-surrogato-d800");
	m_lettera(sc.byte, &sc.byte_n, 1, 0xD800);
	gira(&sc);

	scena_nuova(&sc, "lettera-surrogato-dfff");
	m_lettera(sc.byte, &sc.byte_n, 1, 0xDFFF);
	gira(&sc);

	scena_nuova(&sc, "lettera-ffffffff");
	m_lettera(sc.byte, &sc.byte_n, 1, 0xFFFFFFFFu);
	gira(&sc);

	/* ── §2.5: lo stato e lo stream ───────────────────────────────────── */
	scena_nuova(&sc, "input-prima-di-sessione");
	sc.prima_di_sessione = true;
	m_puntatore(sc.byte, &sc.byte_n, 1, 10, 10);
	gira(&sc);

	scena_nuova(&sc, "secondo-stream-di-input");
	m_puntatore(sc.prima, &sc.prima_n, 1, 10, 10);
	sc.stream = STREAM_ALTRO;
	m_puntatore(sc.byte, &sc.byte_n, 2, 11, 11);
	gira(&sc);

	/* ===================================================================== */
	/* ⭐ I CASI CHE DEVONO PASSARE                                          */
	/* ===================================================================== */

	scena_nuova(&sc, "ok-puntatore-0-0");
	m_puntatore(sc.byte, &sc.byte_n, 1, 0, 0);
	gira(&sc);

	/* ⛔⭐ IL BORDO — rilievo R1.16.  Su una tela 1920×1080 l'angolo in basso a
	 *     destra e' (1919, 1079), e DEVE passare. */
	scena_nuova(&sc, "ok-puntatore-al-bordo-1919-1079");
	m_puntatore(sc.byte, &sc.byte_n, 1, 1919, 1079);
	gira(&sc);

	scena_nuova(&sc, "ok-pulsante-premuto");
	m_pulsante(sc.byte, &sc.byte_n, 1, 0x110, 1);
	gira(&sc);

	scena_nuova(&sc, "ok-pulsante-rilasciato");
	m_pulsante(sc.byte, &sc.byte_n, 1, 0x110, 0);
	gira(&sc);

	scena_nuova(&sc, "ok-posizione-key-a");
	m_posizione(sc.byte, &sc.byte_n, 1, 30, 1);
	gira(&sc);

	/* ⛔ Il segno: +120 DEVE arrivare al gancio come +120.  L'inversione la fa
	 *    `input_rotella()`, e farla anche qui l'annullerebbe. */
	scena_nuova(&sc, "ok-rotella-uno-scatto-su");
	m_rotella(sc.byte, &sc.byte_n, 1, 0, 120);
	gira(&sc);

	scena_nuova(&sc, "ok-rotella-uno-scatto-giu");
	m_rotella(sc.byte, &sc.byte_n, 1, 0, -120);
	gira(&sc);

	/* ⚠ 60 e' MEZZO scatto, e non si arrotonda a zero (§7.3). */
	scena_nuova(&sc, "ok-rotella-mezzo-scatto");
	m_rotella(sc.byte, &sc.byte_n, 1, 0, 60);
	gira(&sc);

	scena_nuova(&sc, "ok-rotella-orizzontale");
	m_rotella(sc.byte, &sc.byte_n, 1, -120, 0);
	gira(&sc);

	scena_nuova(&sc, "ok-rotella-zero");
	m_rotella(sc.byte, &sc.byte_n, 1, 0, 0);
	gira(&sc);

	scena_nuova(&sc, "ok-lettera-a");
	m_lettera(sc.byte, &sc.byte_n, 1, 0x61);
	gira(&sc);

	scena_nuova(&sc, "ok-lettera-accentata");
	m_lettera(sc.byte, &sc.byte_n, 1, 0xE8); /* è */
	gira(&sc);

	scena_nuova(&sc, "ok-lettera-fuori-dal-bmp");
	m_lettera(sc.byte, &sc.byte_n, 1, 0x1F600); /* 😀 */
	gira(&sc);

	/* ⚠ U+0000 e' un valore scalare Unicode valido, e §7.3 dice «da 0».  ⛔ Non
	 *   e' la regola dell'`id`, dove lo zero e' riservato: due campi, due
	 *   regole. */
	scena_nuova(&sc, "ok-lettera-zero");
	m_lettera(sc.byte, &sc.byte_n, 1, 0);
	gira(&sc);

	/* Il limite superiore ESATTO: 0x10FFFF passa, 0x110000 no. */
	scena_nuova(&sc, "ok-lettera-10ffff");
	m_lettera(sc.byte, &sc.byte_n, 1, 0x10FFFF);
	gira(&sc);

	/* §7.3: «cresce di ALMENO uno» — i salti sono leciti. */
	scena_nuova(&sc, "ok-id-che-salta");
	m_puntatore(sc.prima, &sc.prima_n, 1, 10, 10);
	m_puntatore(sc.byte, &sc.byte_n, 100, 11, 11);
	gira(&sc);

	/* Tre messaggi di tre tipi diversi in un pezzo solo, con l'id che cresce
	 * sul CANALE. */
	scena_nuova(&sc, "ok-tre-messaggi-in-un-pezzo");
	m_puntatore(sc.byte, &sc.byte_n, 1, 10, 10);
	m_pulsante(sc.byte, &sc.byte_n, 2, 0x110, 1);
	m_lettera(sc.byte, &sc.byte_n, 3, 0x61);
	gira(&sc);

	/* ⭐ §7.1, terza eccezione di §3: dentro il secondo, una coordinata valida
	 *    sulla tela PRECEDENTE si SATURA invece di chiudere. */
	scena_nuova(&sc, "ok-grazia-satura");
	sc.adatta = true;
	sc.adatta_l = 1280;
	sc.adatta_a = 720;
	sc.ora_tela = 4000;
	sc.ora = 4500;
	m_puntatore(sc.byte, &sc.byte_n, 1, 1900, 1000);
	gira(&sc);

	/* Al millesimo esatto: «per un secondo» comprende il 1000. */
	scena_nuova(&sc, "ok-grazia-al-millesimo-1000");
	sc.adatta = true;
	sc.adatta_l = 1280;
	sc.adatta_a = 720;
	sc.ora_tela = 4000;
	sc.ora = 5000;
	m_puntatore(sc.byte, &sc.byte_n, 1, 1900, 1000);
	gira(&sc);

	/* ⭐ §6.2: il campo `input` torna indietro nei 28 byte del fotogramma. */
	scena_nuova(&sc, "ok-campo-input-torna-indietro");
	sc.fotogramma = true;
	m_puntatore(sc.byte, &sc.byte_n, 1, 10, 10);
	m_pulsante(sc.byte, &sc.byte_n, 2, 0x110, 1);
	m_lettera(sc.byte, &sc.byte_n, 5, 0x61);
	m_posizione(sc.byte, &sc.byte_n, 9, 30, 1);
	gira(&sc);

	/* §6.2: «0 se nessuno», ed e' il significato dichiarato dello zero. */
	scena_nuova(&sc, "ok-campo-input-zero-senza-input");
	sc.fotogramma = true;
	gira(&sc);

	/* ⛔ «Iniettato», non «ricevuto»: se il compositore rifiuta, il campo NON
	 *    avanza — e la sessione REGGE, perche' il client non ha sbagliato. */
	scena_nuova(&sc, "ok-campo-input-non-avanza-se-non-iniettato");
	sc.fotogramma = true;
	sc.esito_ganci = -1;
	m_puntatore(sc.byte, &sc.byte_n, 7, 10, 10);
	gira(&sc);

	/* §7.3: una `LETTERA` non producibile si scrive nel registro, non si
	 * sostituisce e non si tace — e la sessione REGGE. */
	scena_nuova(&sc, "ok-lettera-non-producibile");
	sc.fotogramma = true;
	sc.esito_ganci = 1;
	m_lettera(sc.byte, &sc.byte_n, 3, 0x1E9);
	gira(&sc);

	/* ⛔ «Non ho un canale di input» non e' «il client ha sbagliato». */
	scena_nuova(&sc, "ok-senza-ganci-la-sessione-regge");
	sc.ganci = false;
	m_puntatore(sc.byte, &sc.byte_n, 1, 10, 10);
	gira(&sc);

	/* ⭐ §7.3: il rilascio al distacco, e UNA VOLTA SOLA anche se il congedo e
	 *    la liberazione si susseguono. */
	scena_nuova(&sc, "ok-rilascio-al-distacco-una-volta-sola");
	sc.congeda_alla_fine = true;
	m_pulsante(sc.byte, &sc.byte_n, 1, 0x110, 1);
	gira(&sc);

	/* ===================================================================== */
	/* ⭐ §7.2 — `CURSORE_FORMA`, E LA LUNGHEZZA CHE IL SERVER NON DEVE       */
	/*    SBAGLIARE.                                                         */
	/*                                                                       */
	/* ⛔ Questi non sono ne' violazioni del client ne' verdi del client: sono */
	/*    prove di AUTOCONTROLLO DEL SERVER, e stanno in un conto loro.       */
	/*    §7.2 fa rilevare la lunghezza sbagliata a CHI RICEVE — cioe' un     */
	/*    messaggio storto spedito da qui fa cadere la sessione ALLA PAGINA,  */
	/*    e il registro del server non ne saprebbe niente.                    */
	/*                                                                       */
	/* ⚠ I limiti di §5.5 (256 per lato, il punto attivo dentro l'immagine)   */
	/*   NON si provano qui: li fa rispettare `src/cursore.c`, ed e' A6 a     */
	/*   provarli in `04-b26-cursore`.  Provarli anche qui vorrebbe dire      */
	/*   pretendere due volte la stessa regola, e il giorno in cui una delle  */
	/*   due cambiasse diventerebbero due regole.                            */
	/* ===================================================================== */

	scena_nuova(&sc, "ok-cursore-16x16-sul-filo");
	sc.cursore = true;
	sc.cur_l = 16;
	sc.cur_a = 16;
	sc.cur_ax = 3;
	sc.cur_ay = 4;
	gira(&sc);

	/* ⛔ Il massimo che §5.5 concede: 256x256 = 262 152 byte di corpo, 262 158
	 *    sul filo.  ⭐ DEVE passare: un tetto di §6.1 messo male qui
	 *    ucciderebbe il cursore piu' grande che l'arbitro ammette. */
	scena_nuova(&sc, "ok-cursore-256x256-il-massimo-di-5.5");
	sc.cursore = true;
	sc.cur_l = 256;
	sc.cur_a = 256;
	sc.cur_ax = 0;
	sc.cur_ay = 0;
	gira(&sc);

	/* ⛔⭐ LA COPPIA CHE SI DISTINGUE SOLO SE CI SONO TUTT'E DUE — §5.5.
	 *
	 *     `0x0` e' il cursore NASCOSTO e **deve passare**; `0x5` e `5x0` no.
	 *     ⚠ Col solo `0x0` un controllo che rifiutasse **tutti** gli zeri
	 *       sarebbe verde — e farebbe sparire per sempre il cursore nascosto,
	 *       cioe' il sintomo «il puntatore resta fermo quando entro in un campo
	 *       di testo».  Coi soli `0x5`/`5x0` non si vedrebbe il contrario.
	 *
	 * ⛔ E questo e' l'unico posto in cui il controllo di LUNGHEZZA non basta:
	 *    `0x5` da' zero byte d'immagine, cioe' un messaggio di otto byte la cui
	 *    lunghezza **TORNA**.  Il valore malformato passa proprio il controllo
	 *    che dovrebbe fermarlo. */
	scena_nuova(&sc, "ok-cursore-nascosto-otto-byte");
	sc.cursore = true;
	sc.cur_l = 0;
	sc.cur_a = 0;
	sc.cur_niente_immagine = true;
	gira(&sc);

	scena_nuova(&sc, "cursore-una-sola-a-zero-0x5");
	sc.cursore = true;
	sc.cur_l = 0;
	sc.cur_a = 5;
	gira(&sc);

	scena_nuova(&sc, "cursore-una-sola-a-zero-5x0");
	sc.cursore = true;
	sc.cur_l = 5;
	sc.cur_a = 0;
	gira(&sc);

	/* ⛔⭐ IL CASO CHE IL COORDINATORE HA CHIESTO: si dichiara 16x16 e si
	 *     portano meno byte.  «Leggo quel che c'e' e vado avanti» qui
	 *     confezionerebbe **un cursore fatto di memoria altrui**, e lo
	 *     spedirebbe. */
	scena_nuova(&sc, "cursore-lunghezza-non-torna-in-meno");
	sc.cursore = true;
	sc.cur_l = 16;
	sc.cur_a = 16;
	sc.cur_bugia = -100;
	gira(&sc);

	/* L'altro lato dello stesso confine: piu' byte di quelli che la misura
	 * dichiara.  ⚠ Meno pericoloso e ugualmente sbagliato: il client
	 * chiuderebbe lo stesso, perche' §7.2 vuole la lunghezza ESATTA. */
	scena_nuova(&sc, "cursore-lunghezza-non-torna-in-piu");
	sc.cursore = true;
	sc.cur_l = 16;
	sc.cur_a = 16;
	sc.cur_bugia = +4;
	gira(&sc);

	/* ⛔ Una misura addosso e nessuna immagine: leggerla sarebbe la fine del
	 *    processo, non un messaggio storto. */
	scena_nuova(&sc, "cursore-immagine-nulla-con-misura");
	sc.cursore = true;
	sc.cur_l = 16;
	sc.cur_a = 16;
	sc.cur_niente_immagine = true;
	gira(&sc);

	/* ⛔ §6.1 — oltre 1 MiB.  ⚠ 512 e' gia' oltre §5.5, quindi `cursore.c` non
	 *    lo farebbe mai passare: quel che si prova qui NON e' il limite di §5.5,
	 *    e' che il tetto del MESSAGGIO — che e' di questo modulo — esiste e
	 *    tiene anche se quello di §5.5 fosse spento. */
	scena_nuova(&sc, "cursore-oltre-1mib");
	sc.cursore = true;
	sc.cur_l = 512;
	sc.cur_a = 512;
	gira(&sc);

	/* §5: il cursore vive sul canale di controllo, e prima di `SESSIONE` non
	 * c'e' nessuno che lo disegni.  ⚠ Non e' l'errore di nessuno: la cattura
	 * comincia prima che il client si attacchi. */
	scena_nuova(&sc, "cursore-prima-di-sessione");
	sc.cursore = true;
	sc.cur_prima_di_sessione = true;
	sc.cur_l = 16;
	sc.cur_a = 16;
	gira(&sc);

	return 0;
}
