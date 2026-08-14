/*
 * 04-b31-tela.c — IL BANCO DELLA TELA CHE CAMBIA, `RCP.md` §7.1 e §6.2.
 *
 *   04-b31-tela            gira tutti i casi
 *   04-b31-tela <n>        gira solo il caso n
 *
 * ---------------------------------------------------------------------------
 * ⛔ PERCHE' ESISTE, E PERCHE' NON E' UN BANCO DI RETE
 *
 * `CODER.md` §3.6: *«quando la catena e' gia' ristretta, non fare un altro giro
 * di banco: scrivi il programma minimo che chiama la sola funzione sospetta su
 * un ingresso noto.  Costa meno e chiude prima.»*
 *
 * La catena nuova del 15 agosto 2026 — `ADATTA_TELA` → `figli_ritela()` →
 * `cattura_ridimensiona()` → il fotogramma che torna — attraversa **due
 * processi, un compositore e una scheda video**.  ⛔ Provarla tutta vuole la
 * macchina di prova con la sessione grafica viva; ⭐ ma la META' che decide —
 * la macchina a stati di `rcp.c` — non ha bisogno di niente di tutto questo:
 * riceve byte, restituisce byte, e chiede a chi la ospita di fare.
 *
 * ⇒ Qui `rcp.c` e' montato NUDO, con ganci di prova al posto del palco.  Il
 *   «palco» e' una variabile di questo file: si puo' far rispondere in ritardo,
 *   concedere una misura diversa da quella chiesta, o non rispondere affatto.
 *
 * ⛔ E QUEL CHE QUESTO BANCO NON PROVA, dichiarato invece che scoperto:
 *   · **non prova che il compositore ridimensioni**: quello e' `[M]` di
 *     `banchi/04-in8-misura.c` (Mutter 41,6 ms, labwc 5,1 ms);
 *   · **non prova che i pixel siano giusti**: qui non c'e' un pixel;
 *   · **non prova la pagina**: `src/pagina.html` ha i suoi contatori (§6.2), e
 *     quelli si guardano dal browser.
 *   ⇒ Prova la sola cosa che sta in mezzo, ed e' quella che nessun banco
 *     guardava: **che a ogni `ADATTA_TELA` risponda esattamente un `TELA`, e che
 *     la tela in vigore non prenda mai un valore che nessuno ha concesso.**
 *
 * ---------------------------------------------------------------------------
 * ⛔ L'ATTESO SI DICHIARA PRIMA (regola B0.4 di `LEZIONI.md`): ogni caso qui
 *    sotto porta la sua riga «atteso», e il banco confronta con quella.  Un
 *    banco che stampa quel che e' successo e lo chiama risultato non misura
 *    niente.
 */
#include "../src/rcp.h"

#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* ------------------------------------------------------------------ *
 *  Il filo, in byte — §6.0/§6.1: rete (big-endian), niente riempimento
 * ------------------------------------------------------------------ */

static uint8_t fuori[4096];
static size_t fuori_n;

static void mette(uint8_t **p, uint8_t v) { *(*p)++ = v; }
static void mette16(uint8_t **p, uint16_t v)
{
	mette(p, (uint8_t)(v >> 8));
	mette(p, (uint8_t)v);
}
static void mette32(uint8_t **p, uint32_t v)
{
	mette16(p, (uint16_t)(v >> 16));
	mette16(p, (uint16_t)v);
}
static void mettestr(uint8_t **p, const char *s)
{
	size_t n = strlen(s);
	mette16(p, (uint16_t)n);
	memcpy(*p, s, n);
	*p += n;
}

/* Un messaggio del CLIENT: intestazione (u16 tipo, u32 lunghezza) + corpo. */
static size_t incornicia(uint8_t *buf, uint16_t tipo, const uint8_t *corpo,
                         size_t len)
{
	uint8_t *p = buf;
	mette16(&p, tipo);
	mette32(&p, (uint32_t)len);
	memcpy(p, corpo, len);
	return 6 + len;
}

/* ------------------------------------------------------------------ *
 *  Il palco finto — e i suoi tre modi di comportarsi
 * ------------------------------------------------------------------ */

static struct {
	/* che cosa gli e' stato chiesto */
	uint32_t chiesta_l, chiesta_a;
	int quante_richieste;
	/* come risponde */
	bool accetta;        /* il gancio `ritela` restituisce true?            */
	bool concede_altro;  /* concede una misura DIVERSA da quella chiesta    */
	uint32_t altro_l, altro_a;
	/* che misura ha adesso, per il gancio `tela_del_palco` */
	bool misura_nota;
	uint32_t misura_l, misura_a;
} palco;

static void raccogli(void); /* legge quel che il server ha spedito, e svuota */

static bool g_ritela(void *ctx, uint32_t l, uint32_t a)
{
	(void)ctx;
	palco.quante_richieste++;
	palco.chiesta_l = l;
	palco.chiesta_a = a;
	return palco.accetta;
}

static bool g_tela_del_palco(void *ctx, uint32_t *l, uint32_t *a)
{
	(void)ctx;
	if (!palco.misura_nota)
		return false;
	*l = palco.misura_l;
	*a = palco.misura_a;
	return true;
}

/* ⭐⭐ IL PALCO RISPONDE — ed e' la strada che la prima stesura NON aveva: li' il
 *     padre indovinava dai fotogrammi «se ne arriva uno di misura diversa allora
 *     il palco ha obbedito», e con due richieste incatenate indovinava male.
 *
 * `voluta_*` = a quale richiesta risponde.  ⛔ E' quel che rende il
 * riconoscimento un FATTO invece di una deduzione. */
static void palco_risponde(rcp_sessione *s, uint32_t voluta_l, uint32_t voluta_a,
                           uint64_t ora)
{
	uint32_t l = voluta_l, a = voluta_a;
	if (palco.concede_altro) {
		l = palco.altro_l;
		a = palco.altro_a;
	}
	palco.misura_nota = true;
	palco.misura_l = l;
	palco.misura_a = a;
	rcp_tela_dal_palco(s, voluta_l, voluta_a, l, a, ora);
	raccogli();
}

/* Il palco risponde all'ULTIMA richiesta che ha ricevuto. */
static void palco_consegna(rcp_sessione *s, uint64_t ora)
{
	palco_risponde(s, palco.chiesta_l, palco.chiesta_a, ora);
}

/* ⛔ «Non ce l'ho fatta»: `0x0`, che NON e' una misura. */
static void palco_rinuncia(rcp_sessione *s, uint64_t ora)
{
	rcp_tela_dal_palco(s, palco.chiesta_l, palco.chiesta_a, 0, 0, ora);
	raccogli();
}

/* ------------------------------------------------------------------ *
 *  I ganci
 * ------------------------------------------------------------------ */

static bool chiuso;
static uint8_t motivo_chiusura;
static bool parlantina;

static void g_manda(void *ctx, const uint8_t *dati, size_t len)
{
	(void)ctx;
	if (fuori_n + len > sizeof fuori)
		return;
	memcpy(fuori + fuori_n, dati, len);
	fuori_n += len;
}
static void g_chiudi(void *ctx, uint8_t motivo)
{
	(void)ctx;
	chiuso = true;
	motivo_chiusura = motivo;
}
static void g_registra(void *ctx, const char *riga)
{
	(void)ctx;
	if (parlantina)
		printf("      | %s\n", riga);
}
static bool g_verifica(void *ctx, const char *utente, const char *parola)
{
	(void)ctx;
	return strcmp(utente, "prova") == 0 && strcmp(parola, "prova2026") == 0;
}

/* ------------------------------------------------------------------ *
 *  La lettura di quel che il server ha spedito
 * ------------------------------------------------------------------ */

#define T_SESSIONE 0x0007u
#define T_TELA 0x000Eu
#define T_ADATTA_TELA 0x000Bu
#define T_CIAO 0x0001u
#define T_CREDENZIALI 0x0003u
#define T_ATTACCA 0x0006u

struct tela_vista {
	uint8_t esito, motivo;
	uint32_t l, a;
};

static int quanti_tela;
static struct tela_vista ultima_tela;
static uint32_t sessione_l, sessione_a;

/* Legge tutti i messaggi accumulati e conta i `TELA`.  ⛔ Si SVUOTA: il conto
 * che interessa e' «quanti ne sono usciti da quando ho guardato l'ultima
 * volta», non il totale. */
static void raccogli(void)
{
	size_t i = 0;
	quanti_tela = 0;
	while (i + 6 <= fuori_n) {
		uint16_t tipo = (uint16_t)((fuori[i] << 8) | fuori[i + 1]);
		uint32_t len = ((uint32_t)fuori[i + 2] << 24)
		             | ((uint32_t)fuori[i + 3] << 16)
		             | ((uint32_t)fuori[i + 4] << 8) | fuori[i + 5];
		const uint8_t *c = fuori + i + 6;
		if (i + 6 + len > fuori_n)
			break;
		if (tipo == T_TELA && len >= 10) {
			quanti_tela++;
			ultima_tela.esito = c[0];
			ultima_tela.motivo = c[1];
			ultima_tela.l = ((uint32_t)c[2] << 24) | ((uint32_t)c[3] << 16)
			              | ((uint32_t)c[4] << 8) | c[5];
			ultima_tela.a = ((uint32_t)c[6] << 24) | ((uint32_t)c[7] << 16)
			              | ((uint32_t)c[8] << 8) | c[9];
		}
		if (tipo == T_SESSIONE && len >= 9) {
			sessione_l = ((uint32_t)c[1] << 24) | ((uint32_t)c[2] << 16)
			           | ((uint32_t)c[3] << 8) | c[4];
			sessione_a = ((uint32_t)c[5] << 24) | ((uint32_t)c[6] << 16)
			           | ((uint32_t)c[7] << 8) | c[8];
		}
		i += 6 + len;
	}
	fuori_n = 0;
}

/* ------------------------------------------------------------------ *
 *  La stretta di mano, fino a `SESSIONE`
 * ------------------------------------------------------------------ */

static uint64_t orologio;

static rcp_sessione *apri_sessione(uint32_t tela_l, uint32_t tela_a,
                                   const char *max_misura, bool con_ganci)
{
	rcp_ganci g;
	rcp_sessione *s;
	uint8_t corpo[512], busta[600];
	uint8_t *p;
	size_t n;

	memset(&g, 0, sizeof g);
	g.manda = g_manda;
	g.chiudi = g_chiudi;
	g.registra = g_registra;
	g.verifica = g_verifica;
	if (con_ganci) {
		g.ritela = g_ritela;
		g.tela_del_palco = g_tela_del_palco;
	}

	chiuso = false;
	fuori_n = 0;
	orologio = 1000;
	s = rcp_apri(&g, "10.0.0.9:5000", orologio);
	if (!s)
		return NULL;

	/* CIAO: versione + capacita' (§4.3).
	 * ⛔ `audio.codec=pcm` NON e' decorazione: §4.3 lo pretende, e senza il
	 *    server congeda con `NIENTE_IN_COMUNE` — cosa che questo banco ha
	 *    scoperto al primo giro, con tutti i casi rossi e zero `SESSIONE`.
	 *    E' `CODER.md` §3.3: il banco si certifica PRIMA di puntarlo
	 *    sull'incognita, o un rosso non distingue «non funziona l'incognita» da
	 *    «non funzionava il banco». */
	p = corpo;
	mette16(&p, 1);                      /* versione */
	mette16(&p, max_misura ? 4 : 3);     /* quante capacita' */
	mettestr(&p, "video.codec");
	mettestr(&p, "hevc");
	mettestr(&p, "video.profondita");
	mettestr(&p, "8,10");
	mettestr(&p, "audio.codec");
	mettestr(&p, "pcm");
	if (max_misura) {
		mettestr(&p, "video.misura_massima");
		mettestr(&p, max_misura);
	}
	n = incornicia(busta, T_CIAO, corpo, (size_t)(p - corpo));
	rcp_ricevi(s, busta, n, orologio);

	/* CREDENZIALI */
	p = corpo;
	mettestr(&p, "prova");
	mettestr(&p, "prova2026");
	n = incornicia(busta, T_CREDENZIALI, corpo, (size_t)(p - corpo));
	rcp_ricevi(s, busta, n, orologio);
	/* ⛔ §4.4-bis: il secondo fisso.  Si fa scorrere il tempo, che e' quel che
	 *    farebbe il ciclo `poll` del server. */
	orologio += 1500;
	rcp_tempo(s, orologio);

	/* ATTACCA */
	p = corpo;
	mette32(&p, tela_l);
	mette32(&p, tela_a);
	mette32(&p, tela_l); /* vista: qui non conta */
	mette32(&p, tela_a);
	mettestr(&p, "it");
	n = incornicia(busta, T_ATTACCA, corpo, (size_t)(p - corpo));
	rcp_ricevi(s, busta, n, orologio);
	raccogli();
	return s;
}

static void manda_adatta(rcp_sessione *s, uint32_t l, uint32_t a)
{
	uint8_t corpo[8], busta[32];
	uint8_t *p = corpo;
	size_t n;
	mette32(&p, l);
	mette32(&p, a);
	n = incornicia(busta, T_ADATTA_TELA, corpo, 8);
	rcp_ricevi(s, busta, n, orologio);
	raccogli();
}

/* ------------------------------------------------------------------ *
 *  I casi
 * ------------------------------------------------------------------ */

static int falliti, passati;

static void esito(const char *caso, bool bene, const char *atteso,
                  const char *visto)
{
	if (bene) {
		passati++;
		printf("  \033[1;32mOK\033[0m  %-34s %s\n", caso, visto);
	} else {
		falliti++;
		printf("  \033[1;31mNO\033[0m  %-34s\n        atteso: %s\n        visto:  %s\n",
		       caso, atteso, visto);
	}
}

static char detto[256];
static const char *dillo(void)
{
	snprintf(detto, sizeof detto,
	         "TELA usciti %d (esito %u motivo %u -> %ux%u), richieste al palco "
	         "%d, tela in vigore %ux%u",
	         quanti_tela, ultima_tela.esito, ultima_tela.motivo, ultima_tela.l,
	         ultima_tela.a, palco.quante_richieste, ultima_tela.l,
	         ultima_tela.a);
	return detto;
}

static void azzera_palco(void)
{
	memset(&palco, 0, sizeof palco);
	palco.accetta = true;
	memset(&ultima_tela, 0, sizeof ultima_tela);
	quanti_tela = 0;
}

/* 1 — la strada buona: si chiede, il palco consegna, esce UN `TELA`. */
static void caso1(void)
{
	rcp_sessione *s;
	uint32_t l = 0, a = 0;
	bool bene;

	rcp_azzera_registro_sessioni();
	azzera_palco();
	s = apri_sessione(1920, 1080, NULL, true);
	manda_adatta(s, 1600, 900);
	/* ⛔ ATTESO: nessun `TELA` ancora — la risposta e' il fotogramma. */
	bene = quanti_tela == 0 && palco.quante_richieste == 1
	    && palco.chiesta_l == 1600 && palco.chiesta_a == 900;
	if (bene) {
		palco_consegna(s, orologio);
		rcp_tela_in_vigore(s, &l, &a);
		bene = quanti_tela == 1 && ultima_tela.esito == 1
		    && ultima_tela.l == 1600 && ultima_tela.a == 900 && l == 1600
		    && a == 900 && !chiuso;
	}
	esito("1 la strada buona", bene,
	      "nessun TELA prima del fotogramma, poi UNO solo con 1600x900",
	      dillo());
	rcp_libera(s);
}

/* 2 — la misura che c'e' gia': si risponde SUBITO e non si tocca il palco. */
static void caso2(void)
{
	rcp_sessione *s;
	bool bene;

	rcp_azzera_registro_sessioni();
	azzera_palco();
	s = apri_sessione(1920, 1080, NULL, true);
	manda_adatta(s, 1920, 1080);
	bene = quanti_tela == 1 && ultima_tela.esito == 1 && ultima_tela.motivo == 0
	    && ultima_tela.l == 1920 && ultima_tela.a == 1080
	    && palco.quante_richieste == 0 && !chiuso;
	esito("2 la misura che c'e' gia'", bene,
	      "UN TELA(ADATTATA 1920x1080) subito, ZERO richieste al palco",
	      dillo());
	rcp_libera(s);
}

/* 3 — due `ADATTA_TELA` di fila: DUE `TELA`, o il conto del client non torna
 *     piu' a zero e la pagina trattiene fotogrammi per sempre (§6.2). */
static void caso3(void)
{
	rcp_sessione *s;
	int primi, secondi;
	bool bene;

	rcp_azzera_registro_sessioni();
	azzera_palco();
	s = apri_sessione(1920, 1080, NULL, true);
	manda_adatta(s, 1600, 900);
	primi = quanti_tela;
	manda_adatta(s, 1280, 720);
	secondi = quanti_tela;
	/* ⛔ ATTESO: la seconda richiesta fa uscire il `TELA` che risponde alla
	 *    PRIMA (NON_ORA), e poi il fotogramma fa uscire quello della seconda. */
	bene = primi == 0 && secondi == 1 && ultima_tela.esito == 2
	    && ultima_tela.motivo == 3;
	if (bene) {
		palco_consegna(s, orologio);
		bene = quanti_tela == 1 && ultima_tela.esito == 1
		    && ultima_tela.l == 1280 && ultima_tela.a == 720 && !chiuso;
	}
	esito("3 due ADATTA_TELA di fila", bene,
	      "due TELA in tutto: NON_ORA alla prima, ADATTATA 1280x720 alla seconda",
	      dillo());
	rcp_libera(s);
}

/* 4 — il palco non consegna: dopo il fondo si risponde `NON_ORA` (§7.1: «un
 *     silenzio lascia il client ad aspettare per sempre»). */
static void caso4(void)
{
	rcp_sessione *s;
	uint32_t l = 0, a = 0;
	bool bene;

	rcp_azzera_registro_sessioni();
	azzera_palco();
	s = apri_sessione(1920, 1080, NULL, true);
	manda_adatta(s, 1600, 900);
	/* un giro di orologio PRIMA del fondo: non deve uscire niente */
	orologio += RCP_TELA_ATTESA_MS - 1;
	rcp_tempo(s, orologio);
	raccogli();
	bene = quanti_tela == 0;
	if (bene) {
		orologio += 2;
		rcp_tempo(s, orologio);
		raccogli();
		rcp_tela_in_vigore(s, &l, &a);
		bene = quanti_tela == 1 && ultima_tela.esito == 2
		    && ultima_tela.motivo == 3 && l == 1920 && a == 1080 && !chiuso;
	}
	esito("4 il palco non consegna", bene,
	      "niente prima del fondo, poi UN TELA(RIFIUTATA, NON_ORA), tela 1920x1080",
	      dillo());
	rcp_libera(s);
}

/* 5 — la misura fuori dai limiti: si rifiuta SENZA chiudere la sessione
 *     (`RCP.md:483` punto 4: «l'utente che trascina male una finestra non deve
 *     perdere la sessione»). */
static void caso5(void)
{
	rcp_sessione *s;
	bool bene;

	rcp_azzera_registro_sessioni();
	azzera_palco();
	s = apri_sessione(1920, 1080, NULL, true);
	manda_adatta(s, 100000, 100000);
	bene = quanti_tela == 1 && ultima_tela.esito == 2 && ultima_tela.motivo == 2
	    && ultima_tela.l == 1920 && ultima_tela.a == 1080
	    && palco.quante_richieste == 0 && !chiuso;
	esito("5 misura fuori dai limiti", bene,
	      "UN TELA(RIFIUTATA, MISURA_FUORI_LIMITI), sessione VIVA, palco intatto",
	      dillo());
	rcp_libera(s);
}

/* 6 — la misura dispari si tronca in giu' e SI DICE (§5.0-sexies: «un pixel
 *     detto vale piu' di un pixel nascosto in una scala»). */
static void caso6(void)
{
	rcp_sessione *s;
	bool bene;

	rcp_azzera_registro_sessioni();
	azzera_palco();
	s = apri_sessione(1920, 1080, NULL, true);
	manda_adatta(s, 2133, 1201);
	bene = palco.quante_richieste == 1 && palco.chiesta_l == 2132
	    && palco.chiesta_a == 1200;
	if (bene) {
		palco_consegna(s, orologio);
		bene = quanti_tela == 1 && ultima_tela.l == 2132
		    && ultima_tela.a == 1200;
	}
	esito("6 la misura dispari, troncata", bene,
	      "al palco 2132x1200 (troncata al pari), e il TELA porta quella",
	      dillo());
	rcp_libera(s);
}

/* 7 — §4.5: il palco concede una misura DIVERSA da quella chiesta.  Il `TELA`
 *     deve portare quella VERA, non quella chiesta. */
static void caso7(void)
{
	rcp_sessione *s;
	uint32_t l = 0, a = 0;
	bool bene;

	rcp_azzera_registro_sessioni();
	azzera_palco();
	palco.concede_altro = true;
	palco.altro_l = 1366;
	palco.altro_a = 768;
	s = apri_sessione(1920, 1080, NULL, true);
	manda_adatta(s, 1600, 900);
	palco_consegna(s, orologio);
	rcp_tela_in_vigore(s, &l, &a);
	bene = quanti_tela == 1 && ultima_tela.esito == 1 && ultima_tela.l == 1366
	    && ultima_tela.a == 768 && l == 1366 && a == 768 && !chiuso;
	esito("7 il palco concede altro (§4.5)", bene,
	      "UN TELA(ADATTATA 1366x768), e la tela in vigore e' quella VERA",
	      dillo());
	rcp_libera(s);
}

/* 8 — ⭐ IL RI-ATTACCO: il palco ha gia' 1912x1044, la pagina chiede 1920x1080.
 *     `SESSIONE` deve concedere quella del PALCO, o non arriva un pixel. */
static void caso8(void)
{
	rcp_sessione *s;
	bool bene;

	rcp_azzera_registro_sessioni();
	azzera_palco();
	palco.misura_nota = true;
	palco.misura_l = 1912;
	palco.misura_a = 1044;
	s = apri_sessione(1920, 1080, NULL, true);
	bene = sessione_l == 1912 && sessione_a == 1044 && !chiuso;
	snprintf(detto, sizeof detto, "SESSIONE concede %ux%u", sessione_l,
	         sessione_a);
	esito("8 il ri-attacco", bene,
	      "SESSIONE concede 1912x1044 (quella del palco, §4.5), non 1920x1080",
	      detto);
	rcp_libera(s);
}

/* 9 — ⭐⭐ IL PALCO FA DI TESTA SUA — e qui la prima stesura sbagliava di
 *      GRAVITA': adottava la misura del palco e mandava un `TELA` che nessuno
 *      aveva chiesto.  ⛔ §6.2 dice che il client trattiene una misura mai
 *      annunciata **solo finche' ha una `ADATTA_TELA` senza risposta**: senza,
 *      e' `ERRORE_PROTOCOLLO` — e il fotogramma, che viaggia su uno stream suo,
 *      arriva prima del `TELA` la meta' delle volte.  ⇒ Il server avrebbe fatto
 *      chiudere una sessione in cui nessuno aveva sbagliato.
 *
 *      ⇒ ATTESO ADESSO: **nessun `TELA`, mai**, e il palco RICHIAMATO alla tela
 *      in vigore con un'attesa che cresce. */
static void caso9(void)
{
	rcp_sessione *s;
	uint32_t l = 0, a = 0;
	int primi;
	bool bene;

	rcp_azzera_registro_sessioni();
	azzera_palco();
	s = apri_sessione(1920, 1080, NULL, true);
	/* il palco dice di essere a 1280x720 senza che nessuno abbia chiesto */
	rcp_tela_dal_palco(s, 0, 0, 1280, 720, orologio);
	raccogli();
	primi = palco.quante_richieste;
	bene = quanti_tela == 0 && primi == 1 && palco.chiesta_l == 1920
	    && palco.chiesta_a == 1080;
	if (bene) {
		/* insiste: e il richiamo si ripete, ma non a ogni messaggio */
		rcp_tela_dal_palco(s, 0, 0, 1280, 720, orologio);
		raccogli();
		bene = quanti_tela == 0 && palco.quante_richieste == 1;
	}
	if (bene) {
		orologio += RCP_TELA_RICHIAMO_MS + 1;
		rcp_tela_dal_palco(s, 0, 0, 1280, 720, orologio);
		raccogli();
		rcp_tela_in_vigore(s, &l, &a);
		bene = quanti_tela == 0 && palco.quante_richieste == 2 && l == 1920
		    && a == 1080 && !chiuso;
	}
	esito("9 il palco fa di testa sua", bene,
	      "ZERO TELA (uno non richiesto farebbe chiudere il client), il palco "
	      "richiamato a 1920x1080 con l'attesa che cresce",
	      dillo());
	rcp_libera(s);
}

/* 10 — il tetto del decodificatore del client (§4.5): `ADATTA_TELA` oltre
 *      `video.misura_massima` si RIDUCE in proporzione, come in `ATTACCA`. */
static void caso10(void)
{
	rcp_sessione *s;
	uint32_t l = 0, a = 0;
	bool bene;

	rcp_azzera_registro_sessioni();
	azzera_palco();
	/* ⚠ Il tetto e' 2560x1440 e non 1920x1080 apposta: con quest'ultimo la
	 *   riduzione darebbe **esattamente la tela in vigore**, e il caso finirebbe
	 *   nel ramo «la misura che c'e' gia'» — che e' giusto, ma non prova la
	 *   riduzione.  (La prima stesura di questo caso ci era cascata: l'atteso
	 *   era sbagliato, non il codice.) */
	s = apri_sessione(1920, 1080, "2560x1440", true);
	/* il client hi-dpi chiede la misura della sua finestra in pixel FISICI */
	manda_adatta(s, 3840, 2160);
	bene = palco.quante_richieste == 1 && palco.chiesta_l == 2560
	    && palco.chiesta_a == 1440;
	if (bene) {
		palco_consegna(s, orologio);
		rcp_tela_in_vigore(s, &l, &a);
		bene = quanti_tela == 1 && ultima_tela.esito == 1 && l == 2560
		    && a == 1440 && !chiuso;
	}
	esito("10 oltre il tetto del client", bene,
	      "ridotta a 2560x1440 (proporzioni tenute) e concessa, MAI 3840x2160",
	      dillo());
	rcp_libera(s);
}

/* 11 — nessun gancio (l'ospite non ha un palco): `COMPOSITORE_INCAPACE`, che e'
 *      la risposta vera e non chiude la sessione (§7.1). */
static void caso11(void)
{
	rcp_sessione *s;
	bool bene;

	rcp_azzera_registro_sessioni();
	azzera_palco();
	s = apri_sessione(1920, 1080, NULL, false);
	manda_adatta(s, 1600, 900);
	bene = quanti_tela == 1 && ultima_tela.esito == 2 && ultima_tela.motivo == 1
	    && ultima_tela.l == 1920 && ultima_tela.a == 1080 && !chiuso;
	esito("11 ospite senza palco", bene,
	      "UN TELA(RIFIUTATA, COMPOSITORE_INCAPACE), sessione viva", dillo());
	rcp_libera(s);
}

/* 12 — la richiesta che non parte: `NON_ORA` subito, e non si resta appesi. */
static void caso12(void)
{
	rcp_sessione *s;
	bool bene;

	rcp_azzera_registro_sessioni();
	azzera_palco();
	palco.accetta = false;
	s = apri_sessione(1920, 1080, NULL, true);
	manda_adatta(s, 1600, 900);
	bene = quanti_tela == 1 && ultima_tela.esito == 2 && ultima_tela.motivo == 3
	    && ultima_tela.l == 1920 && ultima_tela.a == 1080 && !chiuso;
	esito("12 la richiesta non parte", bene,
	      "UN TELA(RIFIUTATA, NON_ORA) subito", dillo());
	rcp_libera(s);
}

/* 13 — ⛔ IL FOTOGRAMMA VECCHIO che arriva mentre una richiesta e' in volo: il
 *      palco sta ancora consegnando la misura di prima.  NON deve chiudere la
 *      richiesta, o il client riceverebbe `TELA(ADATTATA, la misura vecchia)`
 *      come risposta a una richiesta che stava per riuscire. */
static void caso13(void)
{
	rcp_sessione *s;
	uint32_t l = 0, a = 0;
	bool bene;

	rcp_azzera_registro_sessioni();
	azzera_palco();
	s = apri_sessione(1920, 1080, NULL, true);
	manda_adatta(s, 1600, 900);
	/* il palco dice ancora la misura di prima: sta rinegoziando */
	rcp_tela_dal_palco(s, 0, 0, 1920, 1080, orologio);
	raccogli();
	bene = quanti_tela == 0;
	if (bene) {
		palco_consegna(s, orologio);
		rcp_tela_in_vigore(s, &l, &a);
		bene = quanti_tela == 1 && ultima_tela.l == 1600
		    && ultima_tela.a == 900 && l == 1600 && a == 900;
	}
	esito("13 il fotogramma vecchio in volo", bene,
	      "la misura VECCHIA non chiude la richiesta; poi TELA(1600x900)",
	      dillo());
	rcp_libera(s);
}

/* 14 — ⭐⭐ DUE RICHIESTE INCATENATE, e la risposta della PRIMA che arriva dopo:
 *      e' il gesto di chi trascina il bordo della finestra.  ⛔ La prima stesura
 *      prendeva il fotogramma della prima richiesta per la risposta della
 *      seconda — e il desktop si assestava sulla misura sbagliata **con i conti
 *      dei messaggi in ordine**, cioe' senza che niente lo dicesse. */
static void caso14(void)
{
	rcp_sessione *s;
	uint32_t l = 0, a = 0;
	bool bene;

	rcp_azzera_registro_sessioni();
	azzera_palco();
	s = apri_sessione(1920, 1080, NULL, true);
	manda_adatta(s, 1600, 900);      /* prima */
	manda_adatta(s, 1280, 720);      /* seconda: NON_ORA alla prima */
	bene = quanti_tela == 1 && ultima_tela.esito == 2 && ultima_tela.motivo == 3;
	if (bene) {
		/* ⛔ arriva la risposta della PRIMA richiesta, in ritardo */
		palco_risponde(s, 1600, 900, orologio);
		rcp_tela_in_vigore(s, &l, &a);
		bene = quanti_tela == 0 && l == 1920 && a == 1080;
	}
	if (bene) {
		/* e poi quella della seconda, che e' la sola che conta */
		palco_risponde(s, 1280, 720, orologio);
		rcp_tela_in_vigore(s, &l, &a);
		bene = quanti_tela == 1 && ultima_tela.esito == 1
		    && ultima_tela.l == 1280 && ultima_tela.a == 720 && l == 1280
		    && a == 720 && !chiuso;
	}
	esito("14 due richieste incatenate", bene,
	      "la risposta della PRIMA non chiude la SECONDA: la tela finisce a "
	      "1280x720, quella che l'utente ha chiesto per ultima",
	      dillo());
	rcp_libera(s);
}

/* 15 — ⭐ il palco dice «non ce l'ho fatta»: `NON_ORA` SUBITO, senza aspettare i
 *      tre secondi del fondo per una notizia che c'e' gia'. */
static void caso15(void)
{
	rcp_sessione *s;
	bool bene;

	rcp_azzera_registro_sessioni();
	azzera_palco();
	s = apri_sessione(1920, 1080, NULL, true);
	manda_adatta(s, 1600, 900);
	bene = quanti_tela == 0;
	if (bene) {
		palco_rinuncia(s, orologio);
		bene = quanti_tela == 1 && ultima_tela.esito == 2
		    && ultima_tela.motivo == 3 && ultima_tela.l == 1920
		    && ultima_tela.a == 1080 && !chiuso;
	}
	esito("15 il palco rinuncia", bene,
	      "UN TELA(RIFIUTATA, NON_ORA) subito, non dopo il fondo", dillo());
	rcp_libera(s);
}

/* 16 — ⭐ il palco risponde «quella misura ce l'ho gia'»: si chiude la richiesta
 *      con `TELA(ADATTATA)` senza aspettare un fotogramma che non arrivera',
 *      perche' i fotogrammi di quella misura chi guarda li ha gia' davanti. */
static void caso16(void)
{
	rcp_sessione *s;
	bool bene;

	rcp_azzera_registro_sessioni();
	azzera_palco();
	s = apri_sessione(1920, 1080, NULL, true);
	manda_adatta(s, 1600, 900);
	/* il palco cambia davvero */
	palco_consegna(s, orologio);
	bene = quanti_tela == 1 && ultima_tela.l == 1600;
	if (bene) {
		/* adesso il client richiede una misura che il palco HA GIA': il figlio
		 * risponde subito, senza nessun fotogramma nuovo */
		manda_adatta(s, 1280, 720);
		bene = quanti_tela == 0;
	}
	if (bene) {
		rcp_tela_dal_palco(s, 1280, 720, 1280, 720, orologio);
		raccogli();
		bene = quanti_tela == 1 && ultima_tela.esito == 1
		    && ultima_tela.l == 1280 && ultima_tela.a == 720 && !chiuso;
	}
	esito("16 il palco ce l'aveva gia'", bene,
	      "TELA(ADATTATA 1280x720) alla risposta del palco, senza fondo",
	      dillo());
	rcp_libera(s);
}

/* 17 — ⛔ i limiti di §4.5 PER LATO: 1600x230 e' fuori (l'altezza), e va
 *      rifiutata — o al ri-attacco `ATTACCA` rifiuterebbe una tela che questo
 *      stesso server aveva concesso. */
static void caso17(void)
{
	rcp_sessione *s;
	bool bene;

	rcp_azzera_registro_sessioni();
	azzera_palco();
	s = apri_sessione(1920, 1080, NULL, true);
	manda_adatta(s, 1600, 230);
	bene = quanti_tela == 1 && ultima_tela.esito == 2 && ultima_tela.motivo == 2
	    && ultima_tela.l == 1920 && ultima_tela.a == 1080
	    && palco.quante_richieste == 0 && !chiuso;
	esito("17 sotto il minimo di §4.5", bene,
	      "UN TELA(RIFIUTATA, MISURA_FUORI_LIMITI): 230 < 240", dillo());
	rcp_libera(s);
}

int main(int argc, char **argv)
{
	int solo = argc > 1 ? atoi(argv[1]) : 0;
	void (*casi[])(void) = { caso1,  caso2,  caso3,  caso4,  caso5,  caso6,
		                     caso7,  caso8,  caso9,  caso10, caso11, caso12,
		                     caso13, caso14, caso15, caso16, caso17 };
	const int quanti = (int)(sizeof casi / sizeof casi[0]);

	parlantina = getenv("PARLANTINA") != NULL;
	printf("\n== 04-b31: la tela che cambia (RCP.md §7.1, §6.2) ==\n\n");
	for (int i = 0; i < quanti; i++) {
		if (solo && solo != i + 1)
			continue;
		casi[i]();
	}
	printf("\n  passati %d, falliti %d\n\n", passati, falliti);
	return falliti ? 1 : 0;
}
