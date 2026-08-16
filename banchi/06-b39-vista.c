/*
 * 06-b39-vista.c — LA VISTA CHE NON COMBACIA, `RCP.md` §7.1.
 *
 *   06-b39-vista            gira tutti i casi
 *   06-b39-vista -v         con la parlantina del registro di `rcp.c`
 *
 * ---------------------------------------------------------------------------
 * ⛔ PERCHE' ESISTE
 *
 * `SPECIFICHE.md` §6.5 promette che l'implementazione resta **parametrica su
 * N**, e `RCP.md` §7.1 dice tre cose sulla vista che nessun banco ha mai
 * provato:
 *
 *   1. ⛔ «**La vista non ha i vincoli della tela**: qualunque misura da **1x1**
 *      in su e' legale, **dispari compresa**» — rilievo **R1.17**, e la riga
 *      vecchia (che dava alla vista i limiti della tela) e' costata la sessione
 *      chiusa a chi stringeva la finestra del browser a 300 pixel;
 *   2. «la vista non ha **nessun vincolo di proporzione** con la tela: se le
 *      proporzioni non combaciano si impagina con le bande»;
 *   3. ⚠ «`VISTA` serve **a scegliere quanti bit spendere**» — ed e' la riga
 *      che questo banco tratta come **un'ipotesi da refutare**, non come un
 *      fatto: si conta se il valore ricevuto muova QUALCOSA.
 *
 * ⭐ E il caso «la tela e' piu' grande della vista» — che e' la forma del
 *   multi-monitor di §6.5 — **esiste gia' oggi**: e' la condizione normale con
 *   `?adatta=no`, o al riattacco da uno schermo piu' piccolo.  Qui si prova la
 *   meta' che sta nel server: che le coordinate dell'input restino **sulla
 *   tela** e non si facciano contagiare dalla vista.
 *
 * ---------------------------------------------------------------------------
 * ⛔ QUEL CHE QUESTO BANCO NON PROVA, dichiarato invece che scoperto:
 *   · **non prova che la pagina impagini**: qui non c'e' un pixel.  Quello lo
 *     misura `06-b39-sonda.html` sotto `xvfb-run`;
 *   · **non prova che il compositore accetti la coordinata**: `libei` non c'e';
 *   · **non prova il multi-monitor**: nessun compositore, nessuna regione.
 *   ⇒ Prova la sola cosa che sta in mezzo: **che una vista legale non chiuda la
 *     sessione, che non tocchi la tela, e che l'input resti in coordinate di
 *     tela anche quando la vista e' molto piu' piccola.**
 *
 * ---------------------------------------------------------------------------
 * ⛔ L'ATTESO SI DICHIARA PRIMA (regola B0.4 di `LEZIONI.md`): ogni caso porta
 *    la sua riga «atteso», scritta prima di aver girato il banco.
 *
 * ⛔ E IL CONTROLLO POSITIVO NON E' UN ORNAMENTO (`LEZIONI.md` §1.9): il caso 0
 *    prova che questa strumentazione **sa vedere un gancio scattare**, prima
 *    che il caso 9 concluda che per la vista non ne scatta nessuno.  Senza,
 *    «nessun gancio» non si distingue da «non sto guardando i ganci».
 */
#include "../src/rcp.h"

#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* ------------------------------------------------------------------ *
 *  Il filo, in byte — §6.0/§6.1: rete (big-endian), niente riempimento
 * ------------------------------------------------------------------ */

static uint8_t fuori[8192];
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
static void mette64(uint8_t **p, uint64_t v)
{
	mette32(p, (uint32_t)(v >> 32));
	mette32(p, (uint32_t)v);
}
static void mettestr(uint8_t **p, const char *s)
{
	size_t n = strlen(s);
	mette16(p, (uint16_t)n);
	memcpy(*p, s, n);
	*p += n;
}

static size_t incornicia(uint8_t *buf, uint16_t tipo, const uint8_t *corpo,
                         size_t len)
{
	uint8_t *p = buf;
	mette16(&p, tipo);
	mette32(&p, (uint32_t)len);
	memcpy(p, corpo, len);
	return 6 + len;
}

#define T_CIAO 0x0001u
#define T_CREDENZIALI 0x0003u
#define T_ATTACCA 0x0006u
#define T_SESSIONE 0x0007u
#define T_VISTA 0x0008u
#define T_ADATTA_TELA 0x000Bu
#define T_CONGEDO 0x000Cu
#define T_TELA 0x000Eu

#define T_PUNTATORE 0x0101u

/* §8.2 — ⛔ e NON si scrivono a mano: la prima stesura di questo banco aveva
 *   `M_ERRORE_PROTOCOLLO 0x02`, che in §8.2 e' `INATTIVITA`.  Il caso 11 sarebbe
 *   stato rosso su un codice giusto (`LEZIONI.md` §2.3) e il caso 6 verde per la
 *   ragione sbagliata.  ⇒ Si prendono dall'enum di `rcp.h`, che e' l'unica
 *   copia. */
#define M_ERRORE_PROTOCOLLO ((uint8_t)RCP_ERRORE_PROTOCOLLO)
#define M_GIA_ATTIVA_REMOTA ((uint8_t)RCP_GIA_ATTIVA_REMOTA)

/* ------------------------------------------------------------------ *
 *  Il palco finto, e IL CONTATORE DI OGNI GANCIO
 * ------------------------------------------------------------------ *
 *
 * ⛔ Si contano TUTTI i ganci, non solo quelli che ci si aspetta scattino: la
 *    domanda del caso 9 e' «la vista muove qualcosa?», e una domanda cosi' si
 *    risponde solo guardando **tutto** quel che si puo' muovere.  Guardarne uno
 *    solo sarebbe la forma E7 di `REVIEWER.md` — verificare dal lato sbagliato.
 */
static struct {
	int ritela, tela_del_palco;
	int puntatore, pulsante, rotella, lettera, posizione, rilascia;
	int video_apri, video_scrivi, video_fin, video_azzera;
	int sessione_locale, termina;
	int manda, registra;
	/* l'ultima coordinata consegnata al desktop */
	uint32_t px, py;
	/* che misura ha il palco, e che cosa gli e' stato chiesto */
	bool misura_nota;
	uint32_t misura_l, misura_a;
	uint32_t chiesta_l, chiesta_a;
} g;

static int ganci_totali(void)
{
	/* ⚠ `manda` e `registra` restano FUORI dal totale: scattano per ragioni
	 *   che non c'entrano con la vista (un `TELA`, una riga di diagnosi), e
	 *   dentro il totale renderebbero il conto insensibile.  Si guardano
	 *   separatamente. */
	return g.ritela + g.tela_del_palco + g.puntatore + g.pulsante + g.rotella
	     + g.lettera + g.posizione + g.rilascia + g.video_apri + g.video_scrivi
	     + g.video_fin + g.video_azzera + g.sessione_locale + g.termina;
}

static bool chiuso;
static uint8_t motivo_chiusura;
static bool parlantina;

static void raccogli(void);

static void gc_manda(void *ctx, const uint8_t *dati, size_t len)
{
	(void)ctx;
	g.manda++;
	if (fuori_n + len > sizeof fuori)
		return;
	memcpy(fuori + fuori_n, dati, len);
	fuori_n += len;
}
static void gc_chiudi(void *ctx, uint8_t motivo)
{
	(void)ctx;
	chiuso = true;
	motivo_chiusura = motivo;
}
static void gc_registra(void *ctx, const char *riga)
{
	(void)ctx;
	g.registra++;
	if (parlantina)
		printf("      | %s\n", riga);
}
static bool gc_verifica(void *ctx, const char *utente, const char *parola)
{
	(void)ctx;
	return strcmp(utente, "prova") == 0 && strcmp(parola, "prova2026") == 0;
}
static bool gc_ritela(void *ctx, uint32_t l, uint32_t a)
{
	(void)ctx;
	g.ritela++;
	g.chiesta_l = l;
	g.chiesta_a = a;
	return true;
}
static bool gc_tela_del_palco(void *ctx, uint32_t *l, uint32_t *a)
{
	(void)ctx;
	g.tela_del_palco++;
	if (!g.misura_nota)
		return false;
	*l = g.misura_l;
	*a = g.misura_a;
	return true;
}
static int gc_puntatore(void *ctx, uint32_t x, uint32_t y)
{
	(void)ctx;
	g.puntatore++;
	g.px = x;
	g.py = y;
	return 0;
}
static int gc_pulsante(void *ctx, uint16_t c, int p)
{
	(void)ctx; (void)c; (void)p;
	g.pulsante++;
	return 0;
}
static int gc_rotella(void *ctx, int32_t x, int32_t y)
{
	(void)ctx; (void)x; (void)y;
	g.rotella++;
	return 0;
}
static int gc_lettera(void *ctx, uint32_t c)
{
	(void)ctx; (void)c;
	g.lettera++;
	return 0;
}
static int gc_posizione(void *ctx, uint16_t c, int p)
{
	(void)ctx; (void)c; (void)p;
	g.posizione++;
	return 0;
}
static int gc_rilascia(void *ctx)
{
	(void)ctx;
	g.rilascia++;
	return 0;
}

/* ------------------------------------------------------------------ *
 *  La lettura di quel che il server ha spedito
 * ------------------------------------------------------------------ */

static int quanti_tela, quanti_sessione, quanti_congedo;
static uint32_t sessione_l, sessione_a;
static uint32_t tela_l_msg, tela_a_msg;
static uint8_t congedo_motivo;

static void raccogli(void)
{
	size_t i = 0;
	quanti_tela = quanti_sessione = quanti_congedo = 0;
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
			tela_l_msg = ((uint32_t)c[2] << 24) | ((uint32_t)c[3] << 16)
			           | ((uint32_t)c[4] << 8) | c[5];
			tela_a_msg = ((uint32_t)c[6] << 24) | ((uint32_t)c[7] << 16)
			           | ((uint32_t)c[8] << 8) | c[9];
		}
		if (tipo == T_SESSIONE && len >= 9) {
			quanti_sessione++;
			sessione_l = ((uint32_t)c[1] << 24) | ((uint32_t)c[2] << 16)
			           | ((uint32_t)c[3] << 8) | c[4];
			sessione_a = ((uint32_t)c[5] << 24) | ((uint32_t)c[6] << 16)
			           | ((uint32_t)c[7] << 8) | c[8];
		}
		if (tipo == T_CONGEDO && len >= 1) {
			quanti_congedo++;
			congedo_motivo = c[0];
		}
		i += 6 + len;
	}
	fuori_n = 0;
}

/* ------------------------------------------------------------------ *
 *  La stretta di mano, fino a `SESSIONE` — con la VISTA che si sceglie
 * ------------------------------------------------------------------ */

static uint64_t orologio;
static const char *prossima_provenienza = "10.0.0.9:5000";

static void azzera(void)
{
	memset(&g, 0, sizeof g);
	chiuso = false;
	motivo_chiusura = 0;
	fuori_n = 0;
	quanti_tela = quanti_sessione = quanti_congedo = 0;
	sessione_l = sessione_a = 0;
	rcp_azzera_registro_sessioni();
}

static rcp_sessione *apri(uint32_t tela_l, uint32_t tela_a, uint32_t vista_l,
                          uint32_t vista_a)
{
	rcp_ganci ganci;
	rcp_sessione *s;
	uint8_t corpo[512], busta[600];
	uint8_t *p;
	size_t n;

	memset(&ganci, 0, sizeof ganci);
	ganci.manda = gc_manda;
	ganci.chiudi = gc_chiudi;
	ganci.registra = gc_registra;
	ganci.verifica = gc_verifica;
	ganci.ritela = gc_ritela;
	ganci.tela_del_palco = gc_tela_del_palco;
	ganci.input_puntatore = gc_puntatore;
	ganci.input_pulsante = gc_pulsante;
	ganci.input_rotella = gc_rotella;
	ganci.input_lettera = gc_lettera;
	ganci.input_posizione = gc_posizione;
	ganci.input_rilascia_tutto = gc_rilascia;

	orologio = 1000;
	s = rcp_apri(&ganci, prossima_provenienza, orologio);
	if (!s)
		return NULL;

	/* CIAO — ⛔ `audio.codec=pcm` non e' decorazione: senza, §4.3 congeda con
	 *   `NIENTE_IN_COMUNE` e ogni caso diventa rosso per la ragione sbagliata
	 *   (`CODER.md` §3.3). */
	p = corpo;
	mette16(&p, 1);
	mette16(&p, 3);
	mettestr(&p, "video.codec");
	mettestr(&p, "hevc");
	mettestr(&p, "video.profondita");
	mettestr(&p, "8,10");
	mettestr(&p, "audio.codec");
	mettestr(&p, "pcm");
	n = incornicia(busta, T_CIAO, corpo, (size_t)(p - corpo));
	rcp_ricevi(s, busta, n, orologio);

	/* CREDENZIALI */
	p = corpo;
	mettestr(&p, "prova");
	mettestr(&p, "prova2026");
	n = incornicia(busta, T_CREDENZIALI, corpo, (size_t)(p - corpo));
	rcp_ricevi(s, busta, n, orologio);
	orologio += 1500; /* §4.4-bis: il secondo fisso */
	rcp_tempo(s, orologio);

	/* ATTACCA — e qui la vista e' quel che il caso vuole provare */
	p = corpo;
	mette32(&p, tela_l);
	mette32(&p, tela_a);
	mette32(&p, vista_l);
	mette32(&p, vista_a);
	mettestr(&p, "it");
	n = incornicia(busta, T_ATTACCA, corpo, (size_t)(p - corpo));
	rcp_ricevi(s, busta, n, orologio);
	/* Il palco nasce della misura chiesta: e' quel che fa il prodotto dal 15
	 * agosto (§4.5, «dico al palco a che misura nascere»). */
	if (g.ritela > 0) {
		g.misura_nota = true;
		g.misura_l = g.chiesta_l;
		g.misura_a = g.chiesta_a;
		rcp_tela_dal_palco(s, g.chiesta_l, g.chiesta_a, g.chiesta_l,
		                   g.chiesta_a, orologio);
	}
	raccogli();
	return s;
}

static void manda_vista(rcp_sessione *s, uint32_t l, uint32_t a)
{
	uint8_t corpo[8], busta[32];
	uint8_t *p = corpo;
	size_t n;
	mette32(&p, l);
	mette32(&p, a);
	n = incornicia(busta, T_VISTA, corpo, 8);
	rcp_ricevi(s, busta, n, orologio);
	raccogli();
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

static uint32_t id_input = 1;

static void manda_puntatore(rcp_sessione *s, uint32_t x, uint32_t y)
{
	uint8_t corpo[32], busta[64];
	uint8_t *p = corpo;
	size_t n;
	mette32(&p, id_input++);
	mette64(&p, (uint64_t)orologio * 1000);
	mette32(&p, x);
	mette32(&p, y);
	n = incornicia(busta, T_PUNTATORE, corpo, (size_t)(p - corpo));
	rcp_ricevi_input(s, 4, busta, n, orologio);
	raccogli();
}

/* ------------------------------------------------------------------ *
 *  Gli esiti
 * ------------------------------------------------------------------ */

static int falliti, passati;

static void esito(const char *caso, bool bene, const char *atteso,
                  const char *visto)
{
	if (bene) {
		passati++;
		printf("  \033[1;32mOK\033[0m  %-38s %s\n", caso, visto);
	} else {
		falliti++;
		printf("  \033[1;31mNO\033[0m  %-38s\n        atteso: %s\n        visto:  %s\n",
		       caso, atteso, visto);
	}
}

static char detto[320];

static const char *viva(void)
{
	snprintf(detto, sizeof detto,
	         "sessione %s (motivo 0x%02X), SESSIONE %d (%ux%u), TELA %d, CONGEDO %d, "
	         "ganci %d",
	         chiuso ? "CHIUSA" : "VIVA", motivo_chiusura, quanti_sessione,
	         sessione_l, sessione_a, quanti_tela, quanti_congedo, ganci_totali());
	return detto;
}

/* ================================================================== *
 *  I CASI — ciascuno con l'atteso scritto PRIMA di aver girato
 * ================================================================== */

/* 0 — ⛔ IL CONTROLLO POSITIVO DELLA STRUMENTAZIONE.
 *
 * Atteso: un `ADATTA_TELA` fa scattare il gancio `ritela` **almeno una volta**,
 * e il totale dei ganci sale.  ⇒ Se questo caso e' verde, allora «zero ganci»
 * nel caso 9 vuol dire davvero zero, e non «non sto guardando».  */
static void caso0(void)
{
	rcp_sessione *s;
	int prima, dopo;
	bool bene;
	char v[160];

	azzera();
	s = apri(1920, 1080, 1920, 1080);
	prima = ganci_totali();
	manda_adatta(s, 1600, 900);
	dopo = ganci_totali();

	bene = dopo > prima && g.ritela > 0;
	snprintf(v, sizeof v, "ganci %d -> %d (ritela %d): lo strumento VEDE", prima,
	         dopo, g.ritela);
	esito("0 controllo POSITIVO dei ganci", bene,
	      "un ADATTA_TELA fa salire il conto dei ganci (ritela > 0)", v);
	rcp_libera(s);
}

/* 1 — vista 1x1 nell'ATTACCA.
 * Atteso (`RCP.md` §7.1): LEGALE.  SESSIONE concessa 1920x1080, sessione VIVA,
 * nessun congedo. */
static void caso1(void)
{
	rcp_sessione *s;
	bool bene;

	azzera();
	s = apri(1920, 1080, 1, 1);
	bene = s && !chiuso && quanti_sessione == 1 && quanti_congedo == 0;
	esito("1 ATTACCA con vista 1x1", bene,
	      "legale (§7.1 «da 1x1 in su»): SESSIONE 1, sessione VIVA", viva());
	rcp_libera(s);
}

/* 2 — vista 300x801 nell'ATTACCA: DISPARI, e sotto il minimo della tela.
 * ⛔ E' il caso concreto del rilievo R1.17 — la finestra stretta a 300 pixel.
 * Atteso: LEGALE.  SESSIONE 1, sessione VIVA. */
static void caso2(void)
{
	rcp_sessione *s;
	bool bene;

	azzera();
	s = apri(1920, 1080, 300, 801);
	bene = s && !chiuso && quanti_sessione == 1 && quanti_congedo == 0;
	esito("2 ATTACCA con vista 300x801", bene,
	      "legale (R1.17: dispari e sotto 320x240 vanno bene): SESSIONE 1, VIVA",
	      viva());
	rcp_libera(s);
}

/* 3 — VISTA 1x1 a sessione viva.
 * Atteso: sessione VIVA, nessun congedo, e ⛔ NESSUN `TELA` — «`VISTA` NON DEVE
 * far cambiare la tela». */
static void caso3(void)
{
	rcp_sessione *s;
	bool bene;

	azzera();
	s = apri(1920, 1080, 1920, 1080);
	manda_vista(s, 1, 1);
	bene = !chiuso && quanti_congedo == 0 && quanti_tela == 0;
	esito("3 VISTA 1x1 a sessione viva", bene,
	      "VIVA, 0 CONGEDO, 0 TELA", viva());
	rcp_libera(s);
}

/* 4 — VISTA 300x801 a sessione viva.  Il difetto che R1.17 ha tolto dal
 * documento: qui si prova che non e' rimasto nel codice.
 * Atteso: VIVA, 0 CONGEDO, 0 TELA. */
static void caso4(void)
{
	rcp_sessione *s;
	bool bene;

	azzera();
	s = apri(1920, 1080, 1920, 1080);
	manda_vista(s, 300, 801);
	bene = !chiuso && quanti_congedo == 0 && quanti_tela == 0;
	esito("4 VISTA 300x801 (dispari)", bene, "VIVA, 0 CONGEDO, 0 TELA", viva());
	rcp_libera(s);
}

/* 5 — VISTA enorme: 65535x65535, cioe' oltre il tetto della TELA.
 * ⛔ §7.1 dice «da 1x1 in su» e NON pone un tetto alla vista.
 * Atteso: LEGALE — VIVA, 0 CONGEDO.  ⚠ Se il codice la rifiutasse, avrebbe
 * applicato alla vista il tetto della tela, che e' esattamente R1.17. */
static void caso5(void)
{
	rcp_sessione *s;
	bool bene;

	azzera();
	s = apri(1920, 1080, 1920, 1080);
	manda_vista(s, 65535, 65535);
	bene = !chiuso && quanti_congedo == 0;
	esito("5 VISTA 65535x65535 (sopra il tetto)", bene,
	      "legale: §7.1 non pone tetto alla vista — VIVA, 0 CONGEDO", viva());
	rcp_libera(s);
}

/* 6 — VISTA 0x0.  ⛔⛔ QUESTO CASO E' STATO UN FALSO VERDE, e si tiene qui con
 * la sua storia perche' e' `LEZIONI.md` §2.2 alla lettera.
 *
 * L'atteso dichiarato prima era: «§7.1 dice da **1x1** in su, quindi 0 sta
 * fuori ⇒ atteso RIFIUTO».  ⛔ Il banco l'ha dato VERDE — e il rifiuto NON
 * c'entrava niente con lo zero: i casi 3, 4 e 5 mostrano che il server rifiuta
 * **qualunque** `VISTA`, 1x1 e 300x801 comprese.  Un caso che non sa
 * distinguere «rifiuta lo zero» da «rifiuta tutto» non prova niente.
 *
 * ⇒ Riscritto: e' verde solo se lo zero e' trattato **diversamente** da una
 *   vista legale.  Finche' `VISTA` non e' servita, questo caso e' ROSSO e deve
 *   restarlo — e' un difetto vivo, non una regola nuova. */
static void caso6(void)
{
	rcp_sessione *s;
	bool zero_rifiutato, legale_rifiutata, bene;
	char v[300];
	uint8_t motivo_zero;

	azzera();
	s = apri(1920, 1080, 1920, 1080);
	manda_vista(s, 0, 0);
	zero_rifiutato = chiuso || quanti_congedo > 0;
	motivo_zero = motivo_chiusura;
	rcp_libera(s);

	azzera();
	s = apri(1920, 1080, 1920, 1080);
	manda_vista(s, 800, 600); /* legalissima: §7.1 */
	legale_rifiutata = chiuso || quanti_congedo > 0;

	bene = zero_rifiutato && !legale_rifiutata;
	snprintf(v, sizeof v,
	         "VISTA 0x0 %s (0x%02X), VISTA 800x600 %s (0x%02X) ⇒ %s",
	         zero_rifiutato ? "rifiutata" : "accettata", motivo_zero,
	         legale_rifiutata ? "RIFIUTATA" : "accettata", motivo_chiusura,
	         bene ? "lo zero e' distinto" : "il server NON distingue: rifiuta tutto");
	esito("6 VISTA 0x0 distinta da una legale?", bene,
	      "0x0 rifiutata E 800x600 accettata — cioe' il rifiuto riguarda lo zero", v);
	rcp_libera(s);
}

/* 7 — la tela NON si muove per una VISTA.
 * Atteso: dopo `VISTA(640x480)` la tela in vigore e' ancora 1920x1080, e il
 * gancio `ritela` NON e' stato chiamato di nuovo. */
static void caso7(void)
{
	rcp_sessione *s;
	uint32_t l = 0, a = 0;
	int ritela_prima;
	bool bene;
	char v[240];

	azzera();
	s = apri(1920, 1080, 1920, 1080);
	ritela_prima = g.ritela;
	manda_vista(s, 640, 480);
	rcp_tela_in_vigore(s, &l, &a);
	bene = l == 1920 && a == 1080 && g.ritela == ritela_prima;
	snprintf(v, sizeof v, "tela in vigore %ux%u, ritela %d -> %d", l, a,
	         ritela_prima, g.ritela);
	esito("7 VISTA non tocca la tela", bene,
	      "tela in vigore 1920x1080, nessuna richiesta nuova al palco", v);
	rcp_libera(s);
}

/* 8 — ⛔⛔ LA TELA PIU' GRANDE DELLA VISTA, E LE COORDINATE.
 *
 * ⭐ E' la forma del multi-monitor di `SPECIFICHE.md` §6.5, ed esiste gia' oggi:
 *    tela 1920x1080, vista 640x480 (`?adatta=no`, o il riattacco da uno schermo
 *    piu' piccolo).
 *
 * ⛔ Atteso (`RCP.md` §7.3: «posizione assoluta sulla **tela**, non sulla
 *    vista»): un `PUNTATORE(1900, 1000)` — cioe' FUORI dalla vista e DENTRO la
 *    tela — arriva al gancio **intatto**, 1900,1000.  ⚠ Se arrivasse ritagliato
 *    a 640x480, il server starebbe confondendo vista e tela, ed e' il sintomo
 *    «il clic finisce altrove» che il progetto ha gia' pagato due giorni sul
 *    DeX. */
static void caso8(void)
{
	rcp_sessione *s;
	bool bene;
	char v[240];

	azzera();
	s = apri(1920, 1080, 640, 480);
	manda_puntatore(s, 1900, 1000);
	bene = g.puntatore == 1 && g.px == 1900 && g.py == 1000 && !chiuso;
	snprintf(v, sizeof v,
	         "puntatore consegnato %d volta/e a %u,%u (vista 640x480, tela 1920x1080)",
	         g.puntatore, g.px, g.py);
	esito("8 tela>vista: coordinate sulla TELA", bene,
	      "il gancio riceve 1900,1000 intatto — non ritagliato alla vista", v);
	rcp_libera(s);
}

/* 9 — ⛔⛔ «`VISTA` serve a scegliere quanti bit spendere»: E' VERO OGGI?
 *
 * ⛔ Atteso, dichiarato PRIMA e in due rami, perche' il banco deve poter dire
 *    entrambe le cose:
 *      · se la riga di §7.1 descrive il prodotto  ⇒ almeno un gancio scatta,
 *        o qualcosa di osservabile cambia, quando arriva una `VISTA` che
 *        DIVIDE PER NOVE i pixel da guardare (1920x1080 -> 640x360);
 *      · se non scatta niente  ⇒ la riga descrive un server che non esiste, e
 *        va consegnata come rilievo.
 *
 * ⚠ Questo caso e' scritto per essere VERDE nel secondo ramo — cioe' registra
 *   il fatto — e il giudizio sta nel rapporto, non nel colore.  Il colore dice
 *   solo «l'ho guardato».  Il caso 0 garantisce che lo strumento veda. */
/* ⛔ LA PRIMA STESURA DI QUESTO CASO MISURAVA IL CONGEDO E LO CHIAMAVA «bit».
 *    Mandava una `VISTA` a sessione viva e contava i ganci: ne trovava uno in
 *    piu' e concludeva «la VISTA muove qualcosa».  ⛔ Quel gancio era `chiudi`
 *    — cioe' la sessione che moriva (casi 3-5).  E' `LEZIONI.md` §2.3: il banco
 *    guardava la cosa giusta nel momento sbagliato.
 *
 * ⇒ Riscritto: la vista si fa arrivare dove OGGI arriva davvero — dentro
 *   `ATTACCA`, che il server serve — e si aprono DUE sessioni identiche in
 *   tutto tranne la vista, una a 1920x1080 e una a 640x360, cioe' **nove volte
 *   meno pixel da guardare**.  Poi si confronta tutto quel che si puo'
 *   osservare.  Atteso, in due rami dichiarati prima:
 *     · §7.1 vera  ⇒ qualcosa DIFFERISCE fra le due sessioni;
 *     · §7.1 falsa ⇒ le due sessioni sono indistinguibili, e la riga «serve a
 *       scegliere quanti bit spendere» descrive un server che non esiste. */
static void caso9(void)
{
	rcp_sessione *s;
	int ganci_grande, manda_grande, registra_grande;
	uint32_t tela_grande_l = 0, tela_grande_a = 0, chiesta_grande_l, chiesta_grande_a;
	int ganci_piccola, manda_piccola, registra_piccola;
	uint32_t tela_piccola_l = 0, tela_piccola_a = 0;
	bool differisce;
	char v[320];

	azzera();
	s = apri(1920, 1080, 1920, 1080);
	ganci_grande = ganci_totali();
	manda_grande = g.manda;
	registra_grande = g.registra;
	chiesta_grande_l = g.chiesta_l;
	chiesta_grande_a = g.chiesta_a;
	rcp_tela_in_vigore(s, &tela_grande_l, &tela_grande_a);
	rcp_libera(s);

	azzera();
	s = apri(1920, 1080, 640, 360);
	ganci_piccola = ganci_totali();
	manda_piccola = g.manda;
	registra_piccola = g.registra;
	rcp_tela_in_vigore(s, &tela_piccola_l, &tela_piccola_a);

	differisce = ganci_grande != ganci_piccola || manda_grande != manda_piccola
	          || tela_grande_l != tela_piccola_l || tela_grande_a != tela_piccola_a
	          || chiesta_grande_l != g.chiesta_l || chiesta_grande_a != g.chiesta_a;

	snprintf(v, sizeof v,
	         "vista 1920x1080 vs 640x360: ganci %d/%d, byte spediti %d/%d, righe di "
	         "registro %d/%d, tela %ux%u/%ux%u, chiesto al palco %ux%u/%ux%u ⇒ %s",
	         ganci_grande, ganci_piccola, manda_grande, manda_piccola,
	         registra_grande, registra_piccola, tela_grande_l, tela_grande_a,
	         tela_piccola_l, tela_piccola_a, chiesta_grande_l, chiesta_grande_a,
	         g.chiesta_l, g.chiesta_a,
	         differisce ? "QUALCOSA differisce" : "INDISTINGUIBILI");
	/* Verde = «l'ho guardato con uno strumento certificato dal caso 0».  Il
	 * giudizio sta nel rapporto, non nel colore. */
	esito("9 la VISTA sposta dei bit?", true,
	      "o le due sessioni differiscono (§7.1 vera), o sono indistinguibili (§7.1 falsa)",
	      v);
	rcp_libera(s);
}

/* 10 — ⭐ IL COSTO DELLA SECONDA VISTA SULLA STESSA TELA, misurato invece che
 * supposto.  Due connessioni dello stesso utente: la seconda e' quel che
 * servirebbe per «due viste sulla stessa tela» di §6.5.
 * Atteso (invariante I2, `RCP.md` §8.2): la seconda e' RIFIUTATA con
 * `GIA_ATTIVA_REMOTA` (0x0F). */
static void caso10(void)
{
	rcp_sessione *s1, *s2;
	bool bene;
	char v[240];

	azzera();
	prossima_provenienza = "10.0.0.9:5000";
	s1 = apri(1920, 1080, 1920, 1080);
	/* ⚠ Il posto di §8.2 e' per UTENTE, non per indirizzo: la seconda arriva da
	 *   un'altra provenienza apposta, cosi' il rifiuto non si puo' spiegare col
	 *   ban dell'indirizzo (§4.4-bis). */
	prossima_provenienza = "10.0.0.77:5000";
	chiuso = false;
	quanti_congedo = 0;
	s2 = apri(1920, 1080, 800, 600);
	prossima_provenienza = "10.0.0.9:5000";

	bene = (chiuso && motivo_chiusura == M_GIA_ATTIVA_REMOTA)
	    || (quanti_congedo > 0 && congedo_motivo == M_GIA_ATTIVA_REMOTA);
	snprintf(v, sizeof v,
	         "seconda connessione: %s, motivo 0x%02X (congedi %d, motivo del congedo 0x%02X)",
	         chiuso ? "CHIUSA" : "VIVA", motivo_chiusura, quanti_congedo,
	         congedo_motivo);
	esito("10 seconda vista = seconda connessione", bene,
	      "RIFIUTATA con GIA_ATTIVA_REMOTA 0x0F (I2)", v);
	rcp_libera(s1);
	rcp_libera(s2);
}

/* 11 — la coordinata FUORI dalla tela, senza nessun cambio di tela recente.
 * Atteso (`RCP.md` §7.1, l'eccezione dura **un secondo** e solo dopo un
 * `TELA(ADATTATA)`): fuori da quella finestra e' `ERRORE_PROTOCOLLO`.
 * ⛔ E' il controllo NEGATIVO del caso 8: se 5000,5000 passasse come passa
 *    1900,1000, il caso 8 non proverebbe niente — un gancio che accetta tutto
 *    non distingue il giusto dallo sbagliato. */
static void caso11(void)
{
	rcp_sessione *s;
	bool bene;
	char v[240];

	azzera();
	s = apri(1920, 1080, 640, 480);
	manda_puntatore(s, 5000, 5000);
	bene = (chiuso && motivo_chiusura == M_ERRORE_PROTOCOLLO)
	    || (quanti_congedo > 0 && congedo_motivo == M_ERRORE_PROTOCOLLO)
	    || g.puntatore == 0;
	snprintf(v, sizeof v,
	         "puntatore consegnato %d volta/e (a %u,%u), sessione %s motivo 0x%02X",
	         g.puntatore, g.px, g.py, chiuso ? "CHIUSA" : "VIVA",
	         motivo_chiusura);
	esito("11 coordinata fuori dalla tela", bene,
	      "non arriva al desktop: ERRORE_PROTOCOLLO (§7.1, fuori dal secondo)", v);
	rcp_libera(s);
}

/* 12 — ⭐ la vista che NON combacia di proporzioni: tela 1920x1080 (16:9),
 * vista 1000x1000 (1:1).  §7.1: «nessun vincolo di proporzione».
 * Atteso: LEGALE, VIVA, 0 CONGEDO — l'impaginazione con le bande e' un lavoro
 * del CLIENT, e il server non deve nemmeno accorgersene. */
static void caso12(void)
{
	rcp_sessione *s;
	bool bene;

	azzera();
	s = apri(1920, 1080, 1000, 1000);
	manda_vista(s, 1000, 1000);
	bene = !chiuso && quanti_congedo == 0 && quanti_sessione == 1;
	esito("12 proporzioni che non combaciano", bene,
	      "legale: nessun vincolo di proporzione (§7.1) — VIVA", viva());
	rcp_libera(s);
}

int main(int argc, char **argv)
{
	if (argc > 1 && strcmp(argv[1], "-v") == 0)
		parlantina = true;

	printf("\n== 06-b39: la vista che non combacia (RCP.md §7.1, SPECIFICHE.md §6.5) ==\n\n");

	caso0();
	caso1();
	caso2();
	caso3();
	caso4();
	caso5();
	caso6();
	caso7();
	caso8();
	caso9();
	caso10();
	caso11();
	caso12();

	printf("\n  passati %d, falliti %d\n\n", passati, falliti);
	return falliti ? 1 : 0;
}
