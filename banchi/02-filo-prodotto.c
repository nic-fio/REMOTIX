/*
 * 02-filo-prodotto.c — ⛔ F2.4: quel che il PRODOTTO mette sul filo, in JSON.
 *
 *     cc -std=gnu11 -D_GNU_SOURCE -O1 -o 02-filo-prodotto 02-filo-prodotto.c
 *     ./02-filo-prodotto > tracce.jsonl
 *
 * ---------------------------------------------------------------------------
 * ⛔ CHE COSA E' E CHE COSA NON E'
 *
 * ⭐ **Non giudica niente.**  Fa una cosa sola: monta il canale video di
 *    `banchi/rcp/rcp.c` su un ospite finto, gli fa spedire un fotogramma per
 *    scena, e **scrive i byte che sono usciti**.  A giudicarli e'
 *    `02-filo-fotogramma.py`, che e' un altro programma in un altro linguaggio
 *    e che `RCP.md` lo ha letto da solo.
 *
 * ⛔ **E non importa il giudice, e non lo puo' importare**: e' un programma in
 *    C che non sa niente di Python.  ⚠ Il divieto vale nell'altro verso ed e'
 *    il punto: se il prodotto conoscesse il giudice, i due lettori
 *    tornerebbero a essere uno, e la fase 2 comprerebbe un arbitro per poi
 *    buttarlo.
 *
 * ---------------------------------------------------------------------------
 * ⛔ PERCHE' `#include` DEL SORGENTE, E NON UN COLLEGAMENTO
 *
 * Due regole si vedono **solo** in punti che l'interfaccia pubblica non
 * raggiunge, e senza questo `#include` resterebbero raccontate:
 *
 *   · il giro del contatore (§6.2, «da `0xFFFFFFFF` si passa a 1»): per
 *     provarlo sul FILO bisogna portare il contatore a `0xFFFFFFFF`, e nessuna
 *     funzione pubblica ci arriva — a 60 fotogrammi al secondo ci vogliono due
 *     anni e due mesi.  ⛔ Un banco che non lo prova certifica una riga che
 *     nessuno ha mai percorso, ed e' la riga che sarebbe scattata **una volta
 *     sola nella vita di una sessione**;
 *
 *   · la rottura a meta' dell'intestazione (§6.2, P4): serve un ospite che
 *     rifiuti la scrittura dei 28 byte, e questo file e' l'ospite.
 *
 * ⚠ Il prezzo si dichiara: qui si compila **il sorgente**, non l'oggetto che
 *   il `Makefile` produce.  E' lo stesso file — `src/rcp.c` e `banchi/rcp/rcp.c`
 *   sono confrontati byte per byte a ogni costruzione — ma «lo stesso sorgente»
 *   e «lo stesso binario» sono due fatti diversi, e questo banco prova il primo.
 *
 * ---------------------------------------------------------------------------
 * ⛔ LA SCENA, DICHIARATA — `CODER.md` §3.2
 *
 * ⚠ **La scena e' FERMA, ed e' il soggetto**: la fase 2 consegna un'immagine
 *   ferma (`PIANO.md` «Fase 2»), e questo banco misura i BYTE del protocollo,
 *   non il ritmo.  I «dati» del fotogramma sono un riempimento che nessuno
 *   guarda: chi giudica i pixel e' F2.6, e il metro e' l'utente (I8).
 *   Dalla fase 3 la regola torna a valere senza sconti.
 */
#include "rcp/rcp.c"

/* ------------------------------------------------------------------------ */
/* L'OSPITE FINTO — i quattro ganci del video, piu' i tre della fase 1        */

#define MAX_STREAM 8
#define TESTA_VISIBILE 28 /* §6.2: i 28 byte dell'intestazione, e basta */

typedef struct {
	int64_t id;
	uint8_t testa[TESTA_VISIBILE];
	size_t testa_n;
	size_t byte;       /* quanti byte in tutto sono usciti su questo stream */
	const char *fine;  /* "aperto" | "fin" | "reset" */
} traccia;

typedef struct {
	traccia s[MAX_STREAM];
	int n;
	int64_t prossimo_id;
	/* ⛔ L'iniezione del guasto dell'OSPITE, non del prodotto: «la scrittura
	 * non entra».  Serve a P4, e si dichiara nella traccia. */
	bool scrittura_fallisce;
	/* i byte del canale di CONTROLLO, per poter dire che il video NON ci e'
	 * finito sopra (§2.5, P3) */
	size_t byte_controllo;
	char ultimo_registro[512];
	int righe_registro;
	char tolleranza[512]; /* §3: l'ultima tolleranza dichiarata */
} ospite;

static ospite O;

static void o_manda(void *c, const uint8_t *d, size_t n)
{
	(void)c;
	(void)d;
	O.byte_controllo += n;
}
static void o_chiudi(void *c, uint8_t motivo)
{
	(void)c;
	(void)motivo;
}
static void o_registra(void *c, const char *riga)
{
	(void)c;
	O.righe_registro++;
	snprintf(O.ultimo_registro, sizeof O.ultimo_registro, "%s", riga);
	if (strstr(riga, "TOLLERANZA DICHIARATA"))
		snprintf(O.tolleranza, sizeof O.tolleranza, "%s", riga);
}
static bool o_verifica(void *c, const char *u, const char *p)
{
	(void)c;
	(void)u;
	(void)p;
	return true;
}

static bool o_video_apri(void *c, int64_t *stream)
{
	(void)c;
	if (O.n >= MAX_STREAM)
		return false;
	traccia *t = &O.s[O.n++];
	memset(t, 0, sizeof *t);
	/* ⛔ Uno stream unidirezionale del SERVER: i numeri di QUIC vanno di
	 * quattro in quattro e quelli del server uni cominciano da 3.  ⚠ Il canale
	 * NON si riconosce dal numero (rilievo R11.9): questo e' solo un nome. */
	t->id = O.prossimo_id;
	O.prossimo_id += 4;
	t->fine = "aperto";
	*stream = t->id;
	return true;
}
static traccia *o_trova(int64_t id)
{
	for (int i = 0; i < O.n; i++)
		if (O.s[i].id == id)
			return &O.s[i];
	return NULL;
}
static bool o_video_scrivi(void *c, int64_t id, const uint8_t *d, size_t n)
{
	(void)c;
	if (O.scrittura_fallisce)
		return false;
	traccia *t = o_trova(id);
	if (!t)
		return false;
	for (size_t i = 0; i < n && t->testa_n < TESTA_VISIBILE; i++)
		t->testa[t->testa_n++] = d[i];
	t->byte += n;
	return true;
}
static void o_video_fin(void *c, int64_t id)
{
	(void)c;
	traccia *t = o_trova(id);
	if (t)
		t->fine = "fin";
}
static void o_video_azzera(void *c, int64_t id)
{
	(void)c;
	traccia *t = o_trova(id);
	if (t)
		t->fine = "reset";
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

static rcp_sessione *apri_sessione(const char *codec, uint32_t tela_l,
                                   uint32_t tela_a, bool col_video)
{
	memset(&O, 0, sizeof O);
	O.prossimo_id = 3;
	rcp_ganci g;
	memset(&g, 0, sizeof g);
	g.manda = o_manda;
	g.chiudi = o_chiudi;
	g.registra = o_registra;
	g.verifica = o_verifica;
	/* ⛔ I quattro ganci si collegano insieme o per niente: vedi `rcp.h`. */
	if (col_video) {
		g.video_apri = o_video_apri;
		g.video_scrivi = o_video_scrivi;
		g.video_fin = o_video_fin;
		g.video_azzera = o_video_azzera;
	}
	rcp_sessione *s = rcp_apri(&g, "127.0.0.1:1", 1000);

	uint8_t buf[512], corpo[256];
	scrittore w;

	/* CIAO — §4.3 */
	scrittore c = {corpo, sizeof corpo, 0, false};
	sc_u16(&c, RCP_VERSIONE);
	sc_u16(&c, 3);
	sc_str(&c, "video.codec");
	sc_str(&c, codec);
	/* ⛔ §4.3: `pcm` e `8` sono i CONTROLLI POSITIVI del documento — un client
	 * che non li dichiara non ha niente in comune col server e si prende un
	 * `RESPINTO(NIENTE_IN_COMUNE)`.  ⚠ Trovato girando: la prima stesura di
	 * questo banco dichiarava solo `opus` e `hevc`, e TUTTE le scene uscivano
	 * «prima di SESSIONE» — un rosso puntato sul canale video mentre a non
	 * essere partita era la stretta di mano. */
	sc_str(&c, "video.profondita");
	sc_str(&c, "8,10");
	sc_str(&c, "audio.codec");
	sc_str(&c, "opus,pcm");
	w = (scrittore){buf, sizeof buf, 0, false};
	sc_msg(&w, T_CIAO, corpo, c.len);
	rcp_ricevi(s, buf, w.len, 1000);

	/* CREDENZIALI — §4.4 */
	c = (scrittore){corpo, sizeof corpo, 0, false};
	sc_str(&c, "prova");
	sc_str(&c, "parola-di-prova");
	w = (scrittore){buf, sizeof buf, 0, false};
	sc_msg(&w, T_CREDENZIALI, corpo, c.len);
	rcp_ricevi(s, buf, w.len, 1000);
	/* §4.4-bis: il ritardo fisso di un secondo, e il verdetto esce da qui. */
	rcp_tempo(s, 3000);

	/* ATTACCA — §4.5 */
	c = (scrittore){corpo, sizeof corpo, 0, false};
	sc_u32(&c, tela_l);
	sc_u32(&c, tela_a);
	sc_u32(&c, 1280);
	sc_u32(&c, 800);
	sc_str(&c, "it");
	w = (scrittore){buf, sizeof buf, 0, false};
	sc_msg(&w, T_ATTACCA, corpo, c.len);
	rcp_ricevi(s, buf, w.len, 3000);
	return s;
}

static void manda_richiedi_chiave(rcp_sessione *s, uint32_t ultimo, uint64_t ora)
{
	uint8_t buf[64], corpo[8];
	scrittore c = {corpo, sizeof corpo, 0, false};
	sc_u32(&c, ultimo);
	scrittore w = {buf, sizeof buf, 0, false};
	sc_msg(&w, T_RICHIEDI_CHIAVE, corpo, c.len);
	rcp_ricevi(s, buf, w.len, ora);
}

/* ------------------------------------------------------------------------ */
/* LA TRACCIA IN JSON — una riga per scena                                   */

static void stampa(const char *scena, const char *regola, int esito,
                   rcp_sessione *s)
{
	printf("{\"scena\":\"%s\",\"regola\":\"%s\",\"esito\":%d,"
	       "\"byte_sul_controllo\":%zu,\"serve_chiave\":%s,"
	       "\"ultimo_numero\":%u,\"stream\":[",
	       scena, regola, esito, O.byte_controllo,
	       rcp_video_serve_chiave(s) ? "true" : "false",
	       rcp_video_ultimo_numero(s));
	for (int i = 0; i < O.n; i++) {
		traccia *t = &O.s[i];
		printf("%s{\"id\":%lld,\"lunghezza\":%zu,\"fine\":\"%s\",\"testa\":\"",
		       i ? "," : "", (long long)t->id, t->byte, t->fine);
		for (size_t k = 0; k < t->testa_n; k++)
			printf("%02x", t->testa[k]);
		printf("\"}");
	}
	printf("],\"tolleranza\":\"%s\"}\n", O.tolleranza[0] ? "si" : "no");
	fflush(stdout);
}

/* Un fotogramma finto: i byte non li guarda nessuno qui (vedi il riquadro
 * della scena).  Si riusa un blocco solo, per non allocare 16 MiB due volte. */
static uint8_t *RIEMPIMENTO;
#define RIEMP_N (64u * 1024u)

static int spedisci_lungo(rcp_sessione *s, bool chiave, size_t len,
                          uint64_t ora)
{
	int e = rcp_video_apri(s, chiave, len, 123456789ull, 0, ora);
	if (e != RCP_VIDEO_SPEDITO)
		return e;
	size_t fatti = 0;
	while (fatti < len) {
		size_t q = len - fatti;
		if (q > RIEMP_N)
			q = RIEMP_N;
		e = rcp_video_pezzo(s, RIEMPIMENTO, q);
		if (e != RCP_VIDEO_SPEDITO)
			return e;
		fatti += q;
	}
	return rcp_video_finisci(s);
}

int main(void)
{
	RIEMPIMENTO = (uint8_t *)calloc(RIEMP_N, 1);
	if (!RIEMPIMENTO)
		return 2;
	rcp_sessione *s;
	int e;

	/* --- 1. P1: PRIMA di `SESSIONE` non esce un byte -------------------- */
	/* ⛔ Si apre la sessione a mano e ci si ferma dopo `CIAO`: `SESSIONE` non
	 *    e' partita, e §2.5 vieta di aprire uno stream video. */
	{
		memset(&O, 0, sizeof O);
		O.prossimo_id = 3;
		rcp_ganci g;
		memset(&g, 0, sizeof g);
		g.manda = o_manda;
		g.chiudi = o_chiudi;
		g.registra = o_registra;
		g.verifica = o_verifica;
		g.video_apri = o_video_apri;
		g.video_scrivi = o_video_scrivi;
		g.video_fin = o_video_fin;
		g.video_azzera = o_video_azzera;
		s = rcp_apri(&g, "127.0.0.1:1", 1000);
		e = rcp_video_spedisci(s, true, RIEMPIMENTO, 100, 1ull, 0, 1000);
		stampa("prima-di-sessione", "RCP.md §2.5", e, s);
		rcp_libera(s);
	}

	/* --- 2. P6 + P2 + P5 + codec: la CHIAVE che la fase 2 consegna ------ */
	s = apri_sessione("hevc", 1920, 1080, true);
	e = rcp_video_spedisci(s, true, RIEMPIMENTO, 4096, 123456789ull, 7, 4000);
	stampa("chiave-dopo-sessione", "RCP.md §6.2", e, s);
	rcp_libera(s);

	/* --- 3. P6: un DELTA in apertura non parte -------------------------- */
	s = apri_sessione("hevc", 1920, 1080, true);
	e = rcp_video_spedisci(s, false, RIEMPIMENTO, 4096, 1ull, 0, 4000);
	stampa("delta-in-apertura", "RCP.md §5.2", e, s);
	rcp_libera(s);

	/* --- 4. un delta DOPO la chiave: passa (e la regola non e' «niente
	 *        delta») ------------------------------------------------------ */
	s = apri_sessione("hevc", 1920, 1080, true);
	rcp_video_spedisci(s, true, RIEMPIMENTO, 4096, 1ull, 0, 4000);
	memset(&O.s, 0, sizeof O.s);
	O.n = 0;
	e = rcp_video_spedisci(s, false, RIEMPIMENTO, 2048, 2ull, 0, 4100);
	stampa("delta-dopo-la-chiave", "RCP.md §6.2", e, s);
	rcp_libera(s);

	/* --- 5. il codec e' quello NEGOZIATO (§4.3) ------------------------- */
	s = apri_sessione("av1", 1280, 720, true);
	e = rcp_video_spedisci(s, true, RIEMPIMENTO, 1024, 5ull, 0, 4000);
	stampa("codec-negoziato-av1", "RCP.md §6.2, §4.3", e, s);
	rcp_libera(s);

	/* --- 6. il tetto: 16 MiB + 1 non parte ------------------------------ */
	s = apri_sessione("hevc", 1920, 1080, true);
	e = spedisci_lungo(s, true, (16u * 1024u * 1024u) - 28u + 1u, 4000);
	stampa("oltre-16-mib", "RCP.md §6.2", e, s);
	rcp_libera(s);

	/* --- 7. e 16 MiB ESATTI passano: il tetto e' un massimo ------------- */
	s = apri_sessione("hevc", 1920, 1080, true);
	e = spedisci_lungo(s, true, (16u * 1024u * 1024u) - 28u, 4000);
	stampa("16-mib-esatti", "RCP.md §6.2", e, s);
	rcp_libera(s);

	/* --- 8. P2 dall'altra parte: IL GIRO DEL CONTATORE ------------------ */
	/* ⛔ Il contatore si porta a `0xFFFFFFFF` da dentro — nessuna funzione
	 *    pubblica ci arriva — e si guarda che il fotogramma dopo porti **1**.
	 *    ⚠ E' l'unico punto in cui questo banco tocca lo stato del prodotto,
	 *      ed e' dichiarato: senza, la riga di §6.2 resterebbe non percorsa. */
	s = apri_sessione("hevc", 1920, 1080, true);
	rcp_video_spedisci(s, true, RIEMPIMENTO, 512, 1ull, 0, 4000);
	s->video_numero = 0xFFFFFFFFu;
	memset(&O.s, 0, sizeof O.s);
	O.n = 0;
	e = rcp_video_spedisci(s, false, RIEMPIMENTO, 512, 2ull, 0, 4100);
	stampa("giro-del-contatore", "RCP.md §6.2", e, s);
	rcp_libera(s);

	/* --- 9. P9: dopo un `TELA(ADATTATA)` che CAMBIA, ci vuole una chiave - */
	s = apri_sessione("hevc", 1920, 1080, true);
	rcp_video_spedisci(s, true, RIEMPIMENTO, 512, 1ull, 0, 4000);
	rcp_tela_adattata(s, 1280, 720);
	memset(&O.s, 0, sizeof O.s);
	O.n = 0;
	e = rcp_video_spedisci(s, false, RIEMPIMENTO, 512, 2ull, 0, 4100);
	stampa("delta-alla-misura-nuova", "RCP.md §5.2", e, s);
	/* e la chiave alla misura nuova porta la misura NUOVA (P5) */
	memset(&O.s, 0, sizeof O.s);
	O.n = 0;
	e = rcp_video_spedisci(s, true, RIEMPIMENTO, 512, 3ull, 0, 4200);
	stampa("chiave-alla-misura-nuova", "RCP.md §6.2", e, s);
	rcp_libera(s);

	/* --- 10. un `TELA` che NON cambia la misura non apre nessun debito -- */
	s = apri_sessione("hevc", 1920, 1080, true);
	rcp_video_spedisci(s, true, RIEMPIMENTO, 512, 1ull, 0, 4000);
	rcp_tela_adattata(s, 1920, 1080);
	memset(&O.s, 0, sizeof O.s);
	O.n = 0;
	e = rcp_video_spedisci(s, false, RIEMPIMENTO, 512, 2ull, 0, 4100);
	stampa("tela-che-non-cambia", "RCP.md §6.2", e, s);
	rcp_libera(s);

	/* --- 11. §5.1: un delta si ABBANDONA, e si azzera (non FIN) --------- */
	s = apri_sessione("hevc", 1920, 1080, true);
	rcp_video_spedisci(s, true, RIEMPIMENTO, 512, 1ull, 0, 4000);
	memset(&O.s, 0, sizeof O.s);
	O.n = 0;
	rcp_video_apri(s, false, 10240, 2ull, 0, 4100);
	rcp_video_pezzo(s, RIEMPIMENTO, 4000);
	bool ab = rcp_video_abbandona(s, "ne' e' partito uno piu' recente");
	stampa("abbandono-di-un-delta", "RCP.md §5.1, §6.2", ab ? 0 : 99, s);
	rcp_libera(s);

	/* --- 12. §5.2: una CHIAVE non si abbandona ------------------------- */
	s = apri_sessione("hevc", 1920, 1080, true);
	memset(&O.s, 0, sizeof O.s);
	O.n = 0;
	rcp_video_apri(s, true, 10240, 1ull, 0, 4000);
	rcp_video_pezzo(s, RIEMPIMENTO, 4000);
	ab = rcp_video_abbandona(s, "la linea non porta");
	stampa("abbandono-di-una-chiave", "RCP.md §5.2", ab ? 0 : 99, s);
	rcp_libera(s);

	/* --- 13. P4: se i 28 byte non escono si AZZERA, mai FIN ------------- */
	s = apri_sessione("hevc", 1920, 1080, true);
	O.scrittura_fallisce = true;
	e = rcp_video_spedisci(s, true, RIEMPIMENTO, 4096, 1ull, 0, 4000);
	stampa("intestazione-che-non-esce", "RCP.md §6.2", e, s);
	rcp_libera(s);

	/* --- 14. §5.2: `RICHIEDI_CHIAVE` accolta ---------------------------- */
	s = apri_sessione("hevc", 1920, 1080, true);
	rcp_video_spedisci(s, true, RIEMPIMENTO, 512, 1ull, 0, 4000);
	memset(&O.s, 0, sizeof O.s);
	O.n = 0;
	manda_richiedi_chiave(s, 1, 5000); /* 1000 ms dopo la chiave: si serve */
	stampa("richiedi-chiave-accolta", "RCP.md §5.2", 0, s);
	rcp_libera(s);

	/* --- 15. §3 eccezione 5: entro 200 ms si PUO' ignorare, e si SCRIVE - */
	s = apri_sessione("hevc", 1920, 1080, true);
	rcp_video_spedisci(s, true, RIEMPIMENTO, 512, 1ull, 0, 4000);
	memset(&O.s, 0, sizeof O.s);
	O.n = 0;
	manda_richiedi_chiave(s, 1, 4100); /* 100 ms dopo: dentro i 200 */
	stampa("richiedi-chiave-nei-200-ms", "RCP.md §5.2, §3 ecc. 5", 0, s);
	rcp_libera(s);

	/* --- 16. senza i ganci non c'e' un canale video, e si DICE ---------- */
	s = apri_sessione("hevc", 1920, 1080, false);
	e = rcp_video_spedisci(s, true, RIEMPIMENTO, 512, 1ull, 0, 4000);
	stampa("senza-i-ganci", "RCP.md §2.5", e, s);
	rcp_libera(s);

	free(RIEMPIMENTO);
	return 0;
}
