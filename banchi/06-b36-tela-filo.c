/*
 * 06-b36-tela-filo.c — LA TELA SUL FILO: `RCP.md` §7.1 per intero, e le due
 *                      righe che nessuno aveva mai preteso.
 *
 *   06-b36-tela-filo            gira tutti i casi
 *   06-b36-tela-filo <n>        gira solo il caso n
 *   PARLANTINA=1 06-b36-tela-filo <n>   stampa il registro della sessione
 *
 * ---------------------------------------------------------------------------
 * ⛔ PERCHE' ESISTE ACCANTO A `04-b31-tela.c`, INVECE DI DENTRO
 *
 * `04-b31` prova **che a ogni `ADATTA_TELA` risponda esattamente un `TELA`**, e
 * lo prova bene: diciannove casi, dodici guasti innestati.  ⛔ Ma guarda **il
 * filo e i contatori**, e §7.1 ha due meta' che dal filo non si vedono:
 *
 *   1. ⛔ **IL RIPIEGO CHE SI DICHIARA NEL REGISTRO** — `SPECIFICHE.md` §6.3 e
 *      §4.5: *«il ripiego si dichiara nel registro»*, e `RCP.md` §3: *«ogni
 *      tolleranza va scritta nel registro.  Una tolleranza silenziosa e'
 *      indistinguibile da un difetto»*.  ⚠ Un banco che conta i `TELA` resta
 *      **verde** il giorno in cui la riga sparisce, e il ripiego torna muto —
 *      che e' esattamente la forma E2 contro cui quelle righe sono state
 *      scritte.  ⇒ Qui il registro si CATTURA e i casi lo PRETENDONO.
 *
 *   2. ⛔⛔ **LE COORDINATE IN VOLO** — la terza eccezione dichiarata di §3,
 *      §7.1: *«dopo aver mandato `TELA(ADATTATA)` il server DEVE accettare per
 *      un secondo coordinate di input valide sulla tela precedente, saturandole
 *      alla nuova e scrivendolo nel registro; passato quel secondo, sono
 *      `ERRORE_PROTOCOLLO`»*.  ⚠ Nessun banco l'aveva mai esercitata: il codice
 *      c'era, e il codice non provato e' codice che non si sa se funziona.
 *
 * ⇒ E siccome le due meta' vogliono **il canale di input** (§2.5) e **il
 *   registro**, che `04-b31` non monta, il banco e' un altro invece che un
 *   capitolo in fondo: ⛔ il 19/19 di `04-b31` non si tocca.
 *
 * ---------------------------------------------------------------------------
 * ⛔ QUEL CHE QUESTO BANCO NON PROVA, dichiarato invece che scoperto
 *
 *   · **non prova che il compositore ridimensioni**: qui il palco e' una
 *     variabile di questo file.  Quello e' `[M]` di `banchi/04-in8-misura.c` e
 *     della sottofase 6.3, che prova la stessa regola sul PRODOTTO VERO;
 *   · **non prova che le coordinate arrivino al desktop**: qui i ganci
 *     d'iniezione contano e basta.  Quello e' `src/input.c`, sottofase 6.1;
 *   · **non prova la pagina**: `src/pagina.html` e' la sottofase 6.5.
 *
 * ---------------------------------------------------------------------------
 * ⛔ L'ATTESO SI DICHIARA PRIMA (regola B0.4 di `LEZIONI.md`): ogni caso porta
 *    la sua riga «ATTESO», scritta prima di girare, e il banco confronta con
 *    quella.  Un banco che stampa quel che e' successo e lo chiama risultato
 *    non misura niente.
 */
#include "../src/rcp.h"

#include <stdarg.h>
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

/* ------------------------------------------------------------------ *
 *  Il palco finto
 * ------------------------------------------------------------------ */

static struct {
	uint32_t chiesta_l, chiesta_a;
	int quante_richieste;
	bool accetta;
	bool concede_altro;
	uint32_t altro_l, altro_a;
	bool misura_nota;
	uint32_t misura_l, misura_a;
} palco;

static int nascita_richieste;

static int dopo_la_nascita(void) { return palco.quante_richieste - nascita_richieste; }

static void raccogli(void);

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

static void palco_consegna(rcp_sessione *s, uint64_t ora)
{
	palco_risponde(s, palco.chiesta_l, palco.chiesta_a, ora);
}

/* ⛔ «Il palco e' andato dove voleva LUI»: `voluta` = 0x0, cioe' «non risponde a
 *    nessuna richiesta nostra».  E' il caso di §7.1 che l'arbitro non nomina. */
static void palco_di_testa_sua(rcp_sessione *s, uint32_t l, uint32_t a,
                               uint64_t ora)
{
	palco.misura_nota = true;
	palco.misura_l = l;
	palco.misura_a = a;
	rcp_tela_dal_palco(s, 0, 0, l, a, ora);
	raccogli();
}

/* ------------------------------------------------------------------ *
 *  ⛔ IL REGISTRO SI CATTURA — e' la meta' che `04-b31` non guarda
 * ------------------------------------------------------------------ */

#define REG_CAP 65536
static char registro[REG_CAP];
static size_t registro_n;
static bool parlantina;

static void registro_azzera(void)
{
	registro_n = 0;
	registro[0] = 0;
}

static void g_registra(void *ctx, const char *riga)
{
	(void)ctx;
	size_t n = strlen(riga);
	if (parlantina)
		printf("      | %s\n", riga);
	if (registro_n + n + 2 >= REG_CAP)
		return;
	memcpy(registro + registro_n, riga, n);
	registro_n += n;
	registro[registro_n++] = '\n';
	registro[registro_n] = 0;
}

/* ⛔ «La riga c'e'?» — e si cerca una sottostringa, non una riga intera: il
 *    testo del registro cambia (e deve poter cambiare), il FATTO che dichiara
 *    no.  ⚠ Chi cerca la frase intera scrive un banco che diventa rosso a ogni
 *    riscrittura di un commento, e allora lo si smette di guardare. */
static bool dice(const char *pezzo) { return strstr(registro, pezzo) != NULL; }

/* Tutti e tre i pezzi, nella stessa riga di registro: serve a non farsi
 * ingannare da due righe diverse che portano una parola per uno. */
static bool dice_insieme(const char *a, const char *b, const char *c)
{
	const char *p = registro;
	while (*p) {
		const char *fine = strchr(p, '\n');
		size_t n = fine ? (size_t)(fine - p) : strlen(p);
		char riga[2048];
		if (n < sizeof riga) {
			memcpy(riga, p, n);
			riga[n] = 0;
			if (strstr(riga, a) && strstr(riga, b) && (!c || strstr(riga, c)))
				return true;
		}
		if (!fine)
			break;
		p = fine + 1;
	}
	return false;
}

/* ------------------------------------------------------------------ *
 *  I ganci
 * ------------------------------------------------------------------ */

static bool chiuso;
static uint8_t motivo_chiusura;

/* ⛔ Il canale di input: qui non si inietta niente: si REGISTRA che cosa `rcp.c`
 *    ha deciso di consegnare.  E' l'unico modo di vedere la SATURAZIONE di §7.1
 *    — un banco che guardasse solo «la sessione e' viva» non distinguerebbe una
 *    coordinata saturata da una accettata cosi' com'era. */
static struct {
	int quanti;
	uint32_t ultimo_x, ultimo_y;
} iniettato;

static int g_punt(void *ctx, uint32_t x, uint32_t y)
{
	(void)ctx;
	iniettato.quanti++;
	iniettato.ultimo_x = x;
	iniettato.ultimo_y = y;
	return 0;
}
static int g_puls(void *ctx, uint16_t c, int p) { (void)ctx; (void)c; (void)p; return 0; }
static int g_rot(void *ctx, int32_t x, int32_t y) { (void)ctx; (void)x; (void)y; return 0; }
static int g_lett(void *ctx, uint32_t c) { (void)ctx; (void)c; return 0; }
static int g_pos(void *ctx, uint16_t c, int p) { (void)ctx; (void)c; (void)p; return 0; }
static int g_rilascia(void *ctx) { (void)ctx; return 0; }

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
static bool g_verifica(void *ctx, const char *utente, const char *parola)
{
	(void)ctx;
	return strcmp(utente, "prova") == 0 && strcmp(parola, "prova2026") == 0;
}

/* ------------------------------------------------------------------ *
 *  La lettura di quel che il server ha spedito
 * ------------------------------------------------------------------ */

#define T_SESSIONE 0x0007u
#define T_VISTA 0x0008u
#define T_TELA 0x000Eu
#define T_ADATTA_TELA 0x000Bu
#define T_CIAO 0x0001u
#define T_CREDENZIALI 0x0003u
#define T_ATTACCA 0x0006u
#define T_PUNTATORE 0x0101u

struct tela_vista {
	uint8_t esito, motivo;
	uint32_t l, a;
};

static int quanti_tela;
static struct tela_vista ultima_tela;
static uint32_t sessione_l, sessione_a;

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

/* ⛔ La vista dell'`ATTACCA`, quando un caso ne vuole una DIVERSA dalla tela.
 *    ⚠ Non si puo' usare «0 = non scelta» come sentinella: lo zero e'
 *    precisamente il valore che il caso 23 deve poter mandare, e un valore
 *    sentinella implicito e' quel che §6.0 vieta. */
static bool vista_scelta;
static uint32_t vista_att_l, vista_att_a;

static rcp_sessione *apri_sessione(uint32_t tela_l, uint32_t tela_a,
                                   const char *max_misura, bool con_palco,
                                   bool con_input)
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
	if (con_palco) {
		g.ritela = g_ritela;
		g.tela_del_palco = g_tela_del_palco;
	}
	/* ⛔ I cinque ganci o nessuno: `rcp.c` guarda il primo e pretende gli altri
	 *    (un canale che sa muovere il puntatore e non sa rilasciare un pulsante
	 *    lascia il desktop peggio di come l'ha trovato). */
	if (con_input) {
		g.input_puntatore = g_punt;
		g.input_pulsante = g_puls;
		g.input_rotella = g_rot;
		g.input_lettera = g_lett;
		g.input_posizione = g_pos;
		g.input_rilascia_tutto = g_rilascia;
	}

	chiuso = false;
	fuori_n = 0;
	memset(&iniettato, 0, sizeof iniettato);
	orologio = 1000;
	s = rcp_apri(&g, "10.0.0.9:5000", orologio);
	if (!s)
		return NULL;

	p = corpo;
	mette16(&p, 1);
	mette16(&p, max_misura ? 4 : 3);
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

	p = corpo;
	mettestr(&p, "prova");
	mettestr(&p, "prova2026");
	n = incornicia(busta, T_CREDENZIALI, corpo, (size_t)(p - corpo));
	rcp_ricevi(s, busta, n, orologio);
	orologio += 1500;
	rcp_tempo(s, orologio);

	p = corpo;
	mette32(&p, tela_l);
	mette32(&p, tela_a);
	mette32(&p, vista_scelta ? vista_att_l : tela_l);
	mette32(&p, vista_scelta ? vista_att_a : tela_a);
	mettestr(&p, "it");
	n = incornicia(busta, T_ATTACCA, corpo, (size_t)(p - corpo));
	rcp_ricevi(s, busta, n, orologio);
	raccogli();
	nascita_richieste = palco.quante_richieste;
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

/* ⛔ §6.1 — la lunghezza DICHIARATA e i campi che il tipo prevede: qui si
 *    dichiara di piu' di quel che si scrive.  Serve a un caso solo, e quel caso
 *    e' il piu' scomodo del banco. */
static void manda_adatta_lunga(rcp_sessione *s, uint32_t l, uint32_t a,
                               size_t coda)
{
	uint8_t corpo[32], busta[64];
	uint8_t *p = corpo;
	size_t n;
	mette32(&p, l);
	mette32(&p, a);
	for (size_t k = 0; k < coda; k++)
		mette(&p, 0);
	n = incornicia(busta, T_ADATTA_TELA, corpo, 8 + coda);
	rcp_ricevi(s, busta, n, orologio);
	raccogli();
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

/* §7.3: `PUNTATORE` ├── u32 id ├── u64 istante ├── u32 x └── u32 y */
static void manda_puntatore(rcp_sessione *s, uint32_t id, uint32_t x, uint32_t y,
                            uint64_t ora)
{
	uint8_t corpo[32], busta[64];
	uint8_t *p = corpo;
	size_t n;
	mette32(&p, id);
	mette64(&p, ora * 1000u);
	mette32(&p, x);
	mette32(&p, y);
	n = incornicia(busta, T_PUNTATORE, corpo, 20);
	rcp_ricevi_input(s, 7, busta, n, ora);
	raccogli();
}

/* ------------------------------------------------------------------ *
 *  I casi
 * ------------------------------------------------------------------ */

static int falliti, passati;
static char detto[512];

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

static void azzera(void)
{
	rcp_azzera_registro_sessioni();
	memset(&palco, 0, sizeof palco);
	palco.accetta = true;
	memset(&ultima_tela, 0, sizeof ultima_tela);
	memset(&iniettato, 0, sizeof iniettato);
	quanti_tela = 0;
	sessione_l = sessione_a = 0;
	vista_scelta = false;
	registro_azzera();
}

/* La vista che il prossimo `ATTACCA` dichiarera'.  Vale per una sola apertura:
 * `azzera()` la rimette com'era. */
static void vista_dell_attacco(uint32_t l, uint32_t a)
{
	vista_scelta = true;
	vista_att_l = l;
	vista_att_a = a;
}

/* =====================================================================
 *  A · IL RIPIEGO SI DICHIARA NEL REGISTRO
 *      `SPECIFICHE.md` §6.3 · `RCP.md` §4.5 · `RCP.md` §3 ultimo capoverso
 * ===================================================================== */

/* 1 — ⛔ `COMPOSITORE_INCAPACE` **dichiarato**: non basta il byte sul filo.
 *
 *     `SPECIFICHE.md` §6.3 lo chiede con queste parole: *«si verifica che la
 *     riga ci sia, non che "funzioni lo stesso"»*.  ⚠ Il byte 1 nel `TELA` dice
 *     al CLIENT di spegnere la voce; la riga di registro dice a CHI DIAGNOSTICA
 *     **quale** ripiego e **perche'** — e senza, un ospite senza palco e un
 *     ospite col palco rotto hanno lo stesso aspetto.
 *
 *     ATTESO: `TELA(RIFIUTATA, COMPOSITORE_INCAPACE)`, sessione VIVA, e ⛔ una
 *     riga sola che nomina insieme `COMPOSITORE_INCAPACE`, il gancio mancante
 *     (`ritela`) e la tela che RESTA. */
static void caso1(void)
{
	rcp_sessione *s;
	bool bene;

	azzera();
	s = apri_sessione(1920, 1080, NULL, false, false);
	manda_adatta(s, 1600, 900);
	bene = quanti_tela == 1 && ultima_tela.esito == 2 && ultima_tela.motivo == 1
	    && ultima_tela.l == 1920 && ultima_tela.a == 1080 && !chiuso
	    && dice_insieme("COMPOSITORE_INCAPACE", "ritela", "1920x1080");
	snprintf(detto, sizeof detto,
	         "TELA esito %u motivo %u -> %ux%u; il registro %s",
	         ultima_tela.esito, ultima_tela.motivo, ultima_tela.l, ultima_tela.a,
	         dice_insieme("COMPOSITORE_INCAPACE", "ritela", "1920x1080")
	             ? "DICE quale ripiego, perche' e con che tela si continua"
	             : "⛔ NON dichiara il ripiego");
	esito("1 COMPOSITORE_INCAPACE dichiarato", bene,
	      "TELA(RIFIUTATA, COMPOSITORE_INCAPACE) E la riga di registro che nomina "
	      "il gancio mancante e la tela che resta",
	      detto);
	rcp_libera(s);
}

/* 2 — ⛔⭐ IL RIPIEGO DI `SPECIFICHE.md` §6.3, cioe' LA FORMA KDE: la sessione
 *      grafica e' gia' viva a un'altra misura e non la puo' cambiare.  §4.5:
 *      *«la tela concessa puo' essere diversa da quella chiesta […] e il server
 *      DEVE aver scritto il ripiego nel registro»*.
 *
 *      ⚠ Qui il palco e' a 1912x1044 e il client chiede 1920x1080.  Il caso 8 di
 *      `04-b31` prova che `SESSIONE` concede quella del palco; ⛔ nessuno
 *      provava che **la riga ci fosse**.
 *
 *      ATTESO: `SESSIONE` concede 1912x1044, e UNA riga porta insieme «RIPIEGO
 *      DICHIARATO», la misura CHIESTA e la misura CONCESSA. */
static void caso2(void)
{
	rcp_sessione *s;
	bool bene, riga;

	azzera();
	palco.misura_nota = true;
	palco.misura_l = 1912;
	palco.misura_a = 1044;
	s = apri_sessione(1920, 1080, NULL, true, false);
	riga = dice_insieme("RIPIEGO DICHIARATO", "1920x1080", "1912x1044");
	bene = sessione_l == 1912 && sessione_a == 1044 && !chiuso && riga;
	snprintf(detto, sizeof detto, "SESSIONE concede %ux%u; il registro %s",
	         sessione_l, sessione_a,
	         riga ? "DICE chiesta e concessa nella stessa riga"
	              : "⛔ NON dichiara il ripiego");
	esito("2 il ripiego di §6.3 (forma KDE)", bene,
	      "SESSIONE 1912x1044 E una riga «RIPIEGO DICHIARATO» con 1920x1080 e "
	      "1912x1044",
	      detto);
	rcp_libera(s);
}

/* 3 — il ripiego del TETTO DEL DECODIFICATORE su `ADATTA_TELA` (§4.5).  Il caso
 *     10 di `04-b31` prova la riduzione; qui si pretende che sia DETTA — «un
 *     pixel detto vale piu' di un pixel nascosto in una scala».
 *
 *     ATTESO: al palco 2560x1440, e una riga «RIPIEGO DICHIARATO» che porta
 *     insieme la misura chiesta (3840x2160) e il tetto (2560x1440). */
static void caso3(void)
{
	rcp_sessione *s;
	bool bene, riga;

	azzera();
	s = apri_sessione(1920, 1080, "2560x1440", true, false);
	manda_adatta(s, 3840, 2160);
	riga = dice_insieme("RIPIEGO DICHIARATO", "3840x2160", "2560x1440");
	bene = dopo_la_nascita() == 1 && palco.chiesta_l == 2560
	    && palco.chiesta_a == 1440 && riga && !chiuso;
	snprintf(detto, sizeof detto, "al palco %ux%u; il registro %s",
	         palco.chiesta_l, palco.chiesta_a,
	         riga ? "DICE chiesta e tetto" : "⛔ NON dichiara la riduzione");
	esito("3 il tetto del client dichiarato", bene,
	      "al palco 2560x1440 E una riga «RIPIEGO DICHIARATO» con 3840x2160 e il "
	      "tetto",
	      detto);
	rcp_libera(s);
}

/* 4 — `MISURA_FUORI_LIMITI` si scrive, e la riga dice CHE COSA e CON CHE COSA
 *     SI CONTINUA.  §3.1 punto 1: «si dice che cosa non si e' capito», e §4.5 e'
 *     il limite violato.
 *
 *     ATTESO: `TELA(RIFIUTATA, MISURA_FUORI_LIMITI)`, sessione viva, e una riga
 *     che porta insieme la misura rifiutata, «§4.5» e la tela che resta. */
static void caso4(void)
{
	rcp_sessione *s;
	bool bene, riga;

	azzera();
	s = apri_sessione(1920, 1080, NULL, true, false);
	manda_adatta(s, 1600, 230);
	riga = dice_insieme("1600x230", "§4.5", "1920x1080");
	bene = quanti_tela == 1 && ultima_tela.esito == 2 && ultima_tela.motivo == 2
	    && dopo_la_nascita() == 0 && !chiuso && riga;
	snprintf(detto, sizeof detto, "TELA esito %u motivo %u; il registro %s",
	         ultima_tela.esito, ultima_tela.motivo,
	         riga ? "DICE misura, §4.5 e tela che resta" : "⛔ NON lo scrive");
	esito("4 MISURA_FUORI_LIMITI dichiarata", bene,
	      "TELA(RIFIUTATA, MISURA_FUORI_LIMITI) E la riga con 1600x230, §4.5 e "
	      "1920x1080",
	      detto);
	rcp_libera(s);
}

/* 5 — `NON_ORA` del FONDO si scrive, e la riga dice il tetto e il perche'.
 *     §7.1: «un silenzio lascia il client ad aspettare per sempre».
 *
 *     ATTESO: dopo `RCP_TELA_ATTESA_MS` esce UN `TELA(RIFIUTATA, NON_ORA)` e una
 *     riga che porta insieme «NON_ORA», la misura chiesta e il tetto in ms. */
static void caso5(void)
{
	rcp_sessione *s;
	bool bene, riga;

	azzera();
	s = apri_sessione(1920, 1080, NULL, true, false);
	manda_adatta(s, 1600, 900);
	orologio += RCP_TELA_ATTESA_MS + 1;
	rcp_tempo(s, orologio);
	raccogli();
	riga = dice_insieme("NON_ORA", "1600x900", "3000 ms");
	bene = quanti_tela == 1 && ultima_tela.esito == 2 && ultima_tela.motivo == 3
	    && !chiuso && riga;
	snprintf(detto, sizeof detto, "TELA esito %u motivo %u; il registro %s",
	         ultima_tela.esito, ultima_tela.motivo,
	         riga ? "DICE NON_ORA, la misura e il tetto" : "⛔ NON lo scrive");
	esito("5 NON_ORA del fondo dichiarato", bene,
	      "TELA(RIFIUTATA, NON_ORA) E la riga con NON_ORA, 1600x900 e 3000 ms",
	      detto);
	rcp_libera(s);
}

/* =====================================================================
 *  B · ⛔⛔ LE COORDINATE IN VOLO — la terza eccezione dichiarata di §3
 *      §7.1: «dopo aver mandato TELA(ADATTATA) il server DEVE accettare per
 *      un secondo coordinate di input valide sulla tela PRECEDENTE,
 *      saturandole alla nuova e SCRIVENDOLO NEL REGISTRO; passato quel
 *      secondo, sono ERRORE_PROTOCOLLO.»
 * ===================================================================== */

/* Porta una sessione da 1920x1080 a 1280x720 con un `ADATTA_TELA` servito, e
 * restituisce l'istante del `TELA(ADATTATA)` — cioe' l'inizio del secondo. */
static rcp_sessione *rimpicciolisci(uint64_t *quando)
{
	rcp_sessione *s = apri_sessione(1920, 1080, NULL, true, true);
	manda_adatta(s, 1280, 720);
	palco_consegna(s, orologio);
	*quando = orologio;
	return s;
}

/* 6 — ⭐ DENTRO IL SECONDO: accettata, SATURATA, e SCRITTA nel registro.
 *
 *     La scena vera: la pagina divide la posizione del mouse per il fattore di
 *     scala e arrotonda per eccesso; il messaggio parte prima che il `TELA`
 *     arrivi.  ⛔ Chiudere la sessione per un arrotondamento e' quel che
 *     `SPECIFICHE.md` §8.3 vieta.
 *
 *     ATTESO (a 500 ms dal `TELA`): il puntatore VIENE INIETTATO, alle
 *     coordinate SATURATE (1279,719) e non a (1900,1000); la sessione e' viva; e
 *     ⛔ una riga di registro nomina il secondo di grazia, la coordinata
 *     arrivata e quella saturata — §3: «ogni tolleranza va scritta». */
static void caso6(void)
{
	rcp_sessione *s;
	uint64_t t0;
	bool bene, riga;

	azzera();
	s = rimpicciolisci(&t0);
	registro_azzera(); /* si guarda solo quel che succede DOPO il cambio */
	manda_puntatore(s, 1, 1900, 1000, t0 + 500);
	riga = dice_insieme("GRAZIA", "(1900,1000)", "(1279,719)");
	bene = !chiuso && iniettato.quanti == 1 && iniettato.ultimo_x == 1279
	    && iniettato.ultimo_y == 719 && riga;
	snprintf(detto, sizeof detto,
	         "iniettati %d, ultimo (%u,%u), sessione %s; il registro %s",
	         iniettato.quanti, iniettato.ultimo_x, iniettato.ultimo_y,
	         chiuso ? "CHIUSA" : "viva",
	         riga ? "SCRIVE la tolleranza" : "⛔ TACE la tolleranza");
	esito("6 la grazia: dentro il secondo", bene,
	      "iniettato (1279,719) — saturato, non chiuso — e la riga «SECONDO DI "
	      "GRAZIA» con (1900,1000) e (1279,719)",
	      detto);
	rcp_libera(s);
}

/* 7 — ⛔ IL CONFINE, e va guardato perche' e' dove le due letture si separano:
 *     «per un secondo» si puo' scrivere `<` o `<=`, e la differenza e' un
 *     millisecondo in cui una sessione vive o muore.
 *
 *     ATTESO: a **1000 ms esatti** dal `TELA` la coordinata vecchia PASSA
 *     ancora (il secondo e' compreso); a **1001 ms** e' `ERRORE_PROTOCOLLO`. */
static void caso7(void)
{
	rcp_sessione *s;
	uint64_t t0;
	bool bene;
	int dentro = 0;
	bool chiuso_al_confine, chiuso_dopo;

	azzera();
	s = rimpicciolisci(&t0);
	manda_puntatore(s, 1, 1900, 1000, t0 + 1000);
	dentro = iniettato.quanti;
	chiuso_al_confine = chiuso;
	rcp_libera(s);

	azzera();
	s = rimpicciolisci(&t0);
	manda_puntatore(s, 1, 1900, 1000, t0 + 1001);
	chiuso_dopo = chiuso;
	bene = dentro == 1 && !chiuso_al_confine && chiuso_dopo
	    && motivo_chiusura == RCP_ERRORE_PROTOCOLLO && iniettato.quanti == 0;
	snprintf(detto, sizeof detto,
	         "a 1000 ms: %d iniettati, sessione %s; a 1001 ms: %d iniettati, "
	         "sessione %s (motivo %#04x)",
	         dentro, chiuso_al_confine ? "CHIUSA" : "viva", iniettato.quanti,
	         chiuso_dopo ? "chiusa" : "VIVA", motivo_chiusura);
	esito("7 la grazia: il confine del secondo", bene,
	      "1000 ms dentro (iniettata), 1001 ms fuori (ERRORE_PROTOCOLLO)", detto);
	rcp_libera(s);
}

/* 8 — OLTRE IL SECONDO: `ERRORE_PROTOCOLLO`, e ⛔ la riga deve dire **da quanto**
 *     e' scaduto — «fuori intervallo» da solo manderebbe a cercare il difetto
 *     nel client anche quando il difetto e' un secondo scaduto di poco.
 *
 *     ATTESO (a 1500 ms): sessione CHIUSA con `ERRORE_PROTOCOLLO`, niente
 *     iniettato, e una riga che nomina la grazia SCADUTA e i 500 ms di ritardo. */
static void caso8(void)
{
	rcp_sessione *s;
	uint64_t t0;
	bool bene, riga;

	azzera();
	s = rimpicciolisci(&t0);
	registro_azzera();
	manda_puntatore(s, 1, 1900, 1000, t0 + 1500);
	riga = dice_insieme("scaduto", "500", "1280x720");
	bene = chiuso && motivo_chiusura == RCP_ERRORE_PROTOCOLLO
	    && iniettato.quanti == 0 && riga;
	snprintf(detto, sizeof detto,
	         "sessione %s (motivo %#04x), iniettati %d; il registro %s",
	         chiuso ? "chiusa" : "VIVA", motivo_chiusura, iniettato.quanti,
	         riga ? "dice da quanto e' scaduta" : "⛔ non dice da quanto");
	esito("8 la grazia: oltre il secondo", bene,
	      "ERRORE_PROTOCOLLO, niente iniettato, e la riga che dice «scaduto da "
	      "500 ms»",
	      detto);
	rcp_libera(s);
}

/* 9 — ⛔ LA GRAZIA NON E' UNA TOLLERANZA GENERALE — §7.1: «copre le coordinate
 *     della tela vecchia, non le coordinate sbagliate».  Se coprisse tutto
 *     sarebbe l'indulgenza che §3 esiste per togliere, e il difetto del client
 *     non si vedrebbe piu'.
 *
 *     ATTESO: dentro il secondo, (5000,5000) — che nessuna delle due tele ha mai
 *     avuto — CHIUDE lo stesso, con `ERRORE_PROTOCOLLO`. */
static void caso9(void)
{
	rcp_sessione *s;
	uint64_t t0;
	bool bene, riga;

	azzera();
	s = rimpicciolisci(&t0);
	registro_azzera();
	manda_puntatore(s, 1, 5000, 5000, t0 + 200);
	riga = dice_insieme("1920x1080", "(5000,5000)", NULL);
	bene = chiuso && motivo_chiusura == RCP_ERRORE_PROTOCOLLO
	    && iniettato.quanti == 0 && riga;
	snprintf(detto, sizeof detto, "sessione %s, iniettati %d; il registro %s",
	         chiuso ? "chiusa" : "VIVA", iniettato.quanti,
	         riga ? "nomina anche la tela PRECEDENTE" : "⛔ non la nomina");
	esito("9 la grazia non copre l'errore vero", bene,
	      "(5000,5000) dentro il secondo CHIUDE lo stesso, e la riga nomina "
	      "tutt'e due le tele",
	      detto);
	rcp_libera(s);
}

/* 10 — ⛔ SENZA UN CAMBIO DI TELA NON C'E' NESSUNA GRAZIA: il `DEVE` di §7.3
 *      resta intero.  ⚠ E' la meta' che rende la grazia una regola e non un
 *      buco: un banco che provasse solo la tolleranza sarebbe verde anche su un
 *      server che non controlla piu' niente.
 *
 *      ATTESO: su una sessione mai adattata, (1900,1000) su tela 1280x720
 *      CHIUDE subito. */
static void caso10(void)
{
	rcp_sessione *s;
	bool bene;

	azzera();
	s = apri_sessione(1280, 720, NULL, true, true);
	manda_puntatore(s, 1, 1900, 1000, orologio);
	bene = chiuso && motivo_chiusura == RCP_ERRORE_PROTOCOLLO
	    && iniettato.quanti == 0;
	snprintf(detto, sizeof detto, "sessione %s (motivo %#04x), iniettati %d",
	         chiuso ? "chiusa" : "VIVA", motivo_chiusura, iniettato.quanti);
	esito("10 nessuna grazia senza cambio", bene,
	      "ERRORE_PROTOCOLLO subito: la grazia ha una data d'inizio", detto);
	rcp_libera(s);
}

/* 11 — ⭐ I DUE PIXEL CHE SI SOMIGLIANO, e sbagliarli e' gia' costato un
 *      rilievo: su tela 1280x720 il pixel **1279** e' l'ultimo VALIDO e passa
 *      per la strada normale — **senza** grazia e **senza** riga di tolleranza —
 *      mentre **1280** e' fuori e ci passa.
 *
 *      ⛔ E' il caso che smaschera due difetti opposti: un `>` invece di `>=`
 *      (che perderebbe la colonna di destra) e una grazia che si prende anche
 *      quel che non le serve (che sporcherebbe il registro a ogni movimento).
 *
 *      ATTESO: (1279,719) iniettato tale e quale e ZERO righe di grazia;
 *      (1280,720) iniettato SATURATO a (1279,719) con la sua riga. */
static void caso11(void)
{
	rcp_sessione *s;
	uint64_t t0;
	bool bene, grazia_di_troppo, grazia_giusta;

	azzera();
	s = rimpicciolisci(&t0);
	registro_azzera();
	manda_puntatore(s, 1, 1279, 719, t0 + 100);
	grazia_di_troppo = dice("GRAZIA");
	bene = !chiuso && iniettato.quanti == 1 && iniettato.ultimo_x == 1279
	    && iniettato.ultimo_y == 719 && !grazia_di_troppo;
	if (bene) {
		registro_azzera();
		manda_puntatore(s, 2, 1280, 720, t0 + 200);
		grazia_giusta = dice("GRAZIA");
		bene = !chiuso && iniettato.quanti == 2 && iniettato.ultimo_x == 1279
		    && iniettato.ultimo_y == 719 && grazia_giusta;
	}
	snprintf(detto, sizeof detto,
	         "iniettati %d, ultimo (%u,%u), sessione %s", iniettato.quanti,
	         iniettato.ultimo_x, iniettato.ultimo_y, chiuso ? "CHIUSA" : "viva");
	esito("11 l'ultimo pixel e il primo fuori", bene,
	      "1279 passa dalla strada normale (nessuna riga di grazia), 1280 passa "
	      "dalla grazia e si satura a 1279",
	      detto);
	rcp_libera(s);
}

/* =====================================================================
 *  C · ⏳ LA REGOLA CHE MANCA ALL'ARBITRO: «il palco cambia misura da se'»
 *      §7.1 (riquadro del 15 agosto): il server NON manda nessun `TELA` non
 *      sollecitato e RICHIAMA il palco con un'attesa che cresce.
 * ===================================================================== */

/* 12 — ⛔ IL PALCO CAMBIA **DUE VOLTE DI FILA**, e a due misure DIVERSE.
 *
 *      ⚠ Il caso 9 di `04-b31` ripete la stessa misura: un codice che si
 *      ricordasse «di questa mi sono gia' lamentato» resterebbe verde li' e
 *      manderebbe un `TELA` non richiesto alla seconda misura.  ⛔ E un `TELA`
 *      non richiesto fa chiudere una sessione SANA (§6.2, e il client non ha
 *      nessuna `ADATTA_TELA` in sospeso con cui trattenerlo).
 *
 *      ATTESO: ZERO `TELA` in tutto il caso; la tela in vigore resta 1920x1080;
 *      il palco viene richiamato a 1920x1080 e mai alle sue misure. */
static void caso12(void)
{
	rcp_sessione *s;
	uint32_t l = 0, a = 0;
	int tela_tot = 0;
	bool bene;

	azzera();
	s = apri_sessione(1920, 1080, NULL, true, false);
	palco_di_testa_sua(s, 1280, 720, orologio);
	tela_tot += quanti_tela;
	/* l'attesa cresce: si fa scorrere il tempo, o il richiamo non riparte */
	orologio += RCP_TELA_RICHIAMO_MS + 1;
	palco_di_testa_sua(s, 1024, 768, orologio);
	tela_tot += quanti_tela;
	orologio += 2 * RCP_TELA_RICHIAMO_MS + 1;
	palco_di_testa_sua(s, 800, 600, orologio);
	tela_tot += quanti_tela;
	rcp_tela_in_vigore(s, &l, &a);
	bene = tela_tot == 0 && l == 1920 && a == 1080 && !chiuso
	    && palco.chiesta_l == 1920 && palco.chiesta_a == 1080
	    && dopo_la_nascita() == 3;
	snprintf(detto, sizeof detto,
	         "TELA usciti %d, tela in vigore %ux%u, richiami %d, ultimo al palco "
	         "%ux%u",
	         tela_tot, l, a, dopo_la_nascita(), palco.chiesta_l, palco.chiesta_a);
	esito("12 il palco cambia tre volte da se'", bene,
	      "ZERO TELA, tela in vigore 1920x1080, il palco richiamato a 1920x1080 "
	      "ogni volta",
	      detto);
	rcp_libera(s);
}

/* 13 — ⛔⛔ IL PALCO CAMBIA DA SE' **MENTRE UN `ADATTA_TELA` E' IN VOLO**, ed e'
 *      la scena che il riquadro di §7.1 nomina per prima: *«un rimontaggio della
 *      sessione grafica dopo una caduta»*.  L'utente ha appena chiesto
 *      1600x900; il palco si rimonta a 1024x768 di suo.
 *
 *      ⚠ Che il server non mandi un `TELA` non sollecitato e' fuori discussione.
 *      ⛔ Ma il richiamo A QUALE MISURA va fatto?  Richiamarlo alla tela **in
 *      vigore** (1920x1080) contraddice la richiesta che il server ha girato un
 *      istante prima, e **condanna al `NON_ORA`** una `ADATTA_TELA` che stava per
 *      riuscire: il palco andrebbe a 1920x1080, il fondo scadrebbe, e l'utente
 *      vedrebbe la sua finestra rifiutata da un server che gli ha chiesto lui
 *      stesso di tornare indietro.
 *
 *      ⇒ ATTESO, dichiarato prima: ZERO `TELA` (nessuno sollecitato), la tela in
 *      vigore ancora 1920x1080, la richiesta ancora IN VOLO per 1600x900, e ⛔ il
 *      palco richiamato a **1600x900** — la misura in volo, non quella vecchia.
 *      Poi, quando il palco obbedisce, esce UN `TELA(ADATTATA 1600x900)`. */
static void caso13(void)
{
	rcp_sessione *s;
	uint32_t l = 0, a = 0, vl = 0, va = 0;
	int tela_tot = 0;
	bool bene;

	azzera();
	s = apri_sessione(1920, 1080, NULL, true, false);
	manda_adatta(s, 1600, 900);
	tela_tot += quanti_tela;
	/* ⛔ il palco si rimonta dove vuole lui, e non risponde a nessuno */
	palco_di_testa_sua(s, 1024, 768, orologio);
	tela_tot += quanti_tela;
	rcp_tela_in_vigore(s, &l, &a);
	bene = tela_tot == 0 && l == 1920 && a == 1080 && !chiuso
	    && rcp_tela_in_volo(s, &vl, &va) && vl == 1600 && va == 900
	    && palco.chiesta_l == 1600 && palco.chiesta_a == 900;
	if (bene) {
		palco_risponde(s, 1600, 900, orologio);
		rcp_tela_in_vigore(s, &l, &a);
		bene = quanti_tela == 1 && ultima_tela.esito == 1 && l == 1600
		    && a == 900 && !chiuso;
	}
	snprintf(detto, sizeof detto,
	         "TELA non sollecitati %d, in volo %ux%u, il palco richiamato a "
	         "%ux%u, tela in vigore %ux%u",
	         tela_tot, vl, va, palco.chiesta_l, palco.chiesta_a, l, a);
	esito("13 il palco cambia con una in volo", bene,
	      "ZERO TELA non sollecitati, e il palco richiamato a 1600x900 — la "
	      "misura IN VOLO, non la tela vecchia",
	      detto);
	rcp_libera(s);
}

/* =====================================================================
 *  D · IL FONDO DI §7.1, I TRE MOTIVI, E I LIMITI DI §4.5 PER LATO
 * ===================================================================== */

/* 14 — ⛔ I QUATTRO SPIGOLI DI §4.5, **PER LATO**: 320x240 .. 7680x4320.
 *
 *      ⚠ Il caso 17 di `04-b31` prova un lato solo (l'altezza sotto il minimo).
 *      Un controllo scritto su un lato solo — o con i due minimi scambiati —
 *      resterebbe verde li' e concederebbe una tela che `ATTACCA` rifiuterebbe
 *      al ri-attacco: il server che non concede in `SESSIONE` una tela che
 *      aveva concesso lui stesso in `TELA`.
 *
 *      ATTESO: tutti e quattro `TELA(RIFIUTATA, MISURA_FUORI_LIMITI)`, sessione
 *      VIVA ogni volta, e ZERO richieste al palco. */
static void caso14(void)
{
	static const uint32_t FUORI[4][2] = {
	    {318, 600},    /* larghezza sotto il minimo  */
	    {1600, 238},   /* altezza sotto il minimo    */
	    {7682, 1080},  /* larghezza oltre il massimo */
	    {1920, 4322},  /* altezza oltre il massimo   */
	};
	bool bene = true;
	int quali = 0;

	for (int k = 0; k < 4 && bene; k++) {
		rcp_sessione *s;
		azzera();
		s = apri_sessione(1920, 1080, NULL, true, false);
		manda_adatta(s, FUORI[k][0], FUORI[k][1]);
		bene = quanti_tela == 1 && ultima_tela.esito == 2
		    && ultima_tela.motivo == 2 && ultima_tela.l == 1920
		    && ultima_tela.a == 1080 && dopo_la_nascita() == 0 && !chiuso;
		if (bene)
			quali++;
		rcp_libera(s);
	}
	snprintf(detto, sizeof detto,
	         "%d spigoli su 4 rifiutati con MISURA_FUORI_LIMITI e sessione viva",
	         quali);
	esito("14 i limiti di §4.5 per lato", bene,
	      "318x600, 1600x238, 7682x1080, 1920x4322: tutti e quattro "
	      "MISURA_FUORI_LIMITI, palco intatto, sessione viva",
	      detto);
}

/* 15 — ⭐ E I LIMITI ESATTI DEVONO PASSARE: 320x240 e 7680x4320 sono DENTRO
 *      (§4.5 dice «fra», estremi compresi).  ⚠ Senza questo caso un `<=` scritto
 *      per errore al posto di `<` chiuderebbe fuori le due misure che l'arbitro
 *      nomina, e nessuno se ne accorgerebbe: il caso 14 resterebbe verde.
 *
 *      ATTESO: tutt'e due GIRATE al palco (nessun `TELA` subito), alla misura
 *      chiesta esatta. */
static void caso15(void)
{
	rcp_sessione *s;
	bool bene;
	int piccola = 0;

	azzera();
	s = apri_sessione(1920, 1080, NULL, true, false);
	manda_adatta(s, 320, 240);
	bene = quanti_tela == 0 && dopo_la_nascita() == 1 && palco.chiesta_l == 320
	    && palco.chiesta_a == 240 && !chiuso;
	piccola = bene;
	rcp_libera(s);

	if (bene) {
		azzera();
		s = apri_sessione(1920, 1080, NULL, true, false);
		manda_adatta(s, 7680, 4320);
		bene = quanti_tela == 0 && dopo_la_nascita() == 1
		    && palco.chiesta_l == 7680 && palco.chiesta_a == 4320 && !chiuso;
		rcp_libera(s);
	}
	snprintf(detto, sizeof detto,
	         "320x240 %s, 7680x4320 girata a %ux%u", piccola ? "girata" : "⛔ NO",
	         palco.chiesta_l, palco.chiesta_a);
	esito("15 gli estremi di §4.5 sono dentro", bene,
	      "320x240 e 7680x4320 girate al palco tali e quali, nessun TELA subito",
	      detto);
}

/* 16 — ⛔ TRE `ADATTA_TELA` INCATENATE: **tre** `TELA`.  §7.1: «a ogni
 *      `ADATTA_TELA` il server DEVE rispondere con un `TELA`», e §6.2 fa TENERE
 *      IL CONTO al client — se il conto non torna a zero, la sua coda dei
 *      fotogrammi trattenuti cresce senza fine, cioe' la sua memoria.
 *
 *      ⚠ `04-b31` ne prova due (casi 3 e 14).  Tre non e' «due piu' uno»: e' il
 *      caso in cui una catena tenuta con una variabile sola invece che con uno
 *      stato si scopre — chi trascina un bordo ne manda venti al secondo.
 *
 *      ATTESO: NON_ORA alla prima, NON_ORA alla seconda, e ADATTATA 1024x768
 *      alla terza quando il palco consegna.  Tre `TELA` in tutto, e la tela
 *      finisce sull'ULTIMA misura chiesta. */
static void caso16(void)
{
	rcp_sessione *s;
	uint32_t l = 0, a = 0;
	int tot = 0, non_ora = 0;
	bool bene;

	azzera();
	s = apri_sessione(1920, 1080, NULL, true, false);
	manda_adatta(s, 1600, 900);
	tot += quanti_tela;
	manda_adatta(s, 1280, 720);
	tot += quanti_tela;
	non_ora += (quanti_tela == 1 && ultima_tela.motivo == 3);
	manda_adatta(s, 1024, 768);
	tot += quanti_tela;
	non_ora += (quanti_tela == 1 && ultima_tela.motivo == 3);
	bene = tot == 2 && non_ora == 2 && !chiuso;
	if (bene) {
		palco_risponde(s, 1024, 768, orologio);
		tot += quanti_tela;
		rcp_tela_in_vigore(s, &l, &a);
		bene = quanti_tela == 1 && ultima_tela.esito == 1 && l == 1024
		    && a == 768 && tot == 3 && !chiuso;
	}
	snprintf(detto, sizeof detto, "TELA in tutto %d (di cui %d NON_ORA), tela "
	                              "in vigore %ux%u",
	         tot, non_ora, l, a);
	esito("16 tre ADATTA_TELA incatenate", bene,
	      "TRE TELA per TRE ADATTA_TELA: NON_ORA, NON_ORA, ADATTATA 1024x768",
	      detto);
	rcp_libera(s);
}

/* =====================================================================
 *  E · `VISTA` (0x0008) — «la vista e' della connessione, la tela della
 *      sessione»
 *      §7.1: «VISTA NON DEVE far cambiare la tela, e in RCP/1 non cambia
 *      nemmeno la misura di quel che si codifica» · «qualunque misura da
 *      1x1 in su e' legale, dispari compresa» (rilievo R1.17).
 * ===================================================================== */

/* 17 — ⛔ UNA `VISTA` **1x1** E' LEGALE, e la sessione DEVE restarci viva.
 *
 *      La scena di R1.17: l'utente stringe la finestra del browser, o apre la
 *      pagina affiancata sul telefono.  §7.1 e' esplicito — i limiti della tela
 *      **alla vista non si applicano**, perche' la vista non tocca nessun
 *      codificatore.  ⛔ Un server che chiude qui **chiude la sessione perche'
 *      l'utente ha ridimensionato una finestra**, che e' alla lettera il sintomo
 *      che quel rilievo e' stato scritto per rendere impossibile.
 *
 *      ATTESO: sessione VIVA, ZERO `TELA` (la vista non e' un `ADATTA_TELA`),
 *      tela in vigore INTATTA, e ZERO richieste al palco. */
static void caso17(void)
{
	rcp_sessione *s;
	uint32_t l = 0, a = 0;
	bool bene;

	azzera();
	s = apri_sessione(1920, 1080, NULL, true, false);
	manda_vista(s, 1, 1);
	rcp_tela_in_vigore(s, &l, &a);
	bene = !chiuso && quanti_tela == 0 && l == 1920 && a == 1080
	    && dopo_la_nascita() == 0;
	snprintf(detto, sizeof detto,
	         "sessione %s (motivo %#04x), TELA %d, tela %ux%u, richieste al "
	         "palco %d",
	         chiuso ? "CHIUSA" : "viva", motivo_chiusura, quanti_tela, l, a,
	         dopo_la_nascita());
	esito("17 VISTA 1x1 e' legale", bene,
	      "sessione viva, zero TELA, tela 1920x1080 intatta, palco intatto",
	      detto);
	rcp_libera(s);
}

/* 18 — ⛔ UNA `VISTA` **300x801** — sotto il minimo della tela E dispari — e'
 *      legale.  ⚠ E' il caso che smaschera chi ha scritto UNA `valida_misura()`
 *      e l'ha chiamata quattro volte: su un telefono a fattore 2,75 la vista e'
 *      dispari quasi sempre (393 pixel logici valgono 1080,75 fisici), e
 *      arrotondare sarebbe la forma d'errore E2.
 *
 *      ATTESO: sessione VIVA, zero `TELA`, tela intatta. */
static void caso18(void)
{
	rcp_sessione *s;
	uint32_t l = 0, a = 0;
	bool bene;

	azzera();
	s = apri_sessione(1920, 1080, NULL, true, false);
	manda_vista(s, 300, 801);
	rcp_tela_in_vigore(s, &l, &a);
	bene = !chiuso && quanti_tela == 0 && l == 1920 && a == 1080;
	snprintf(detto, sizeof detto, "sessione %s (motivo %#04x), TELA %d, tela %ux%u",
	         chiuso ? "CHIUSA" : "viva", motivo_chiusura, quanti_tela, l, a);
	esito("18 VISTA 300x801 e' legale", bene,
	      "sessione viva: i limiti della tela alla vista non si applicano",
	      detto);
	rcp_libera(s);
}

/* 19 — ⛔⭐ LA VISTA NON TOCCA LA TELA, **nemmeno dopo un adattamento**: e' il
 *      `NON DEVE` di §7.1 letto per intero.  ⚠ La forma sbagliata che questo
 *      caso esclude non e' «chiude», e' «funziona troppo»: un server che
 *      prendesse la vista per una richiesta di tela farebbe rimpicciolire il
 *      desktop di chi ha solo stretto la finestra — e senza mandare nessun
 *      `TELA`, cioe' con i due lati che si separano in silenzio (E2).
 *
 *      ATTESO: adattata a 1280x720; poi `VISTA(640x360)` e `VISTA(3840x2160)`
 *      non cambiano niente — la tela resta 1280x720, e non esce nessun `TELA`. */
static void caso19(void)
{
	rcp_sessione *s;
	uint64_t t0;
	uint32_t l = 0, a = 0;
	int tot = 0;
	bool bene;

	azzera();
	s = rimpicciolisci(&t0);
	tot = 0;
	manda_vista(s, 640, 360);
	tot += quanti_tela;
	manda_vista(s, 3840, 2160);
	tot += quanti_tela;
	rcp_tela_in_vigore(s, &l, &a);
	bene = !chiuso && tot == 0 && l == 1280 && a == 720
	    && palco.chiesta_l == 1280 && palco.chiesta_a == 720;
	snprintf(detto, sizeof detto,
	         "sessione %s, TELA dopo le due VISTA %d, tela %ux%u, ultimo al "
	         "palco %ux%u",
	         chiuso ? "CHIUSA" : "viva", tot, l, a, palco.chiesta_l,
	         palco.chiesta_a);
	esito("19 la VISTA non cambia la tela", bene,
	      "dopo VISTA 640x360 e VISTA 3840x2160 la tela resta 1280x720 e nessun "
	      "TELA esce",
	      detto);
	rcp_libera(s);
}

/* =====================================================================
 *  F · §6.1 E §3 — LA LUNGHEZZA SI GIUDICA **PRIMA** DEGLI EFFETTI
 * ===================================================================== */

/* 20 — ⭐ LA VISTA SI **TIENE**, e questo caso esiste perche' senza di lui i
 *      casi 17-19 sarebbero verdi anche su un server che legge i due `u32` e li
 *      butta.  ⛔ Un campo del protocollo che il server dichiara di aver capito
 *      e non ha da nessuna parte e' la forma esatta del parser indulgente che
 *      §3 esiste per togliere: il giorno in cui qualcuno ci contasse sopra —
 *      «quanti bit spendere», §7.1 — troverebbe uno zero.
 *
 *      ATTESO: la vista parte da quella dell'`ATTACCA` (1920x1080), e dopo
 *      `VISTA(640x360)` vale 640x360.  ⛔ E la TELA non si muove. */
static void caso20(void)
{
	rcp_sessione *s;
	uint32_t vl = 0, va = 0, tl = 0, ta = 0;
	bool bene, dall_attacco;

	azzera();
	s = apri_sessione(1920, 1080, NULL, true, false);
	dall_attacco = rcp_vista(s, &vl, &va) && vl == 1920 && va == 1080;
	manda_vista(s, 640, 360);
	rcp_vista(s, &vl, &va);
	rcp_tela_in_vigore(s, &tl, &ta);
	bene = dall_attacco && !chiuso && vl == 640 && va == 360 && tl == 1920
	    && ta == 1080;
	snprintf(detto, sizeof detto,
	         "dall'ATTACCA %s, dopo VISTA la vista e' %ux%u e la tela %ux%u",
	         dall_attacco ? "1920x1080" : "⛔ NON tenuta", vl, va, tl, ta);
	esito("20 la vista si tiene", bene,
	      "vista 1920x1080 dall'ATTACCA, poi 640x360; la tela resta 1920x1080",
	      detto);
	rcp_libera(s);
}

/* 21 — ⛔ E LO ZERO NON E' UNA VISTA.  §7.1 dice «da **1x1** in su»: uno zero ne
 *      sta fuori come 100000 sta fuori dalla tela, e §6.0 vieta i valori
 *      sentinella impliciti.  ⚠ E' la meta' che impedisce alla cura di §7.1 di
 *      diventare «la vista non si controlla piu'»: una tolleranza generale
 *      sarebbe l'indulgenza che §3 toglie.
 *
 *      ATTESO: `VISTA(0x800)` e `VISTA(300x0)` chiudono con `ERRORE_PROTOCOLLO`;
 *      e una `VISTA` prima di `SESSIONE` chiude anche lei (§7.1 la ammette solo
 *      a sessione aperta). */
static void caso21(void)
{
	rcp_sessione *s;
	bool bene, primo, secondo;

	azzera();
	s = apri_sessione(1920, 1080, NULL, true, false);
	manda_vista(s, 0, 800);
	primo = chiuso && motivo_chiusura == RCP_ERRORE_PROTOCOLLO;
	rcp_libera(s);

	azzera();
	s = apri_sessione(1920, 1080, NULL, true, false);
	manda_vista(s, 300, 0);
	secondo = chiuso && motivo_chiusura == RCP_ERRORE_PROTOCOLLO;
	bene = primo && secondo;
	snprintf(detto, sizeof detto, "0x800 %s, 300x0 %s",
	         primo ? "rifiutata" : "⛔ ACCETTATA",
	         secondo ? "rifiutata" : "⛔ ACCETTATA");
	esito("21 lo zero non e' una vista", bene,
	      "VISTA(0x800) e VISTA(300x0): ERRORE_PROTOCOLLO tutt'e due", detto);
	rcp_libera(s);
}

/* 22 — ⛔⛔ UN `ADATTA_TELA` CON LA LUNGHEZZA SBAGLIATA NON DEVE FARE NIENTE.
 *
 *      §6.1: «un ricevente che legge una lunghezza incoerente con quel che il
 *      tipo prevede DEVE chiudere con `ERRORE_PROTOCOLLO`»; §3: «**NON DEVE
 *      proseguire**».  ⚠ E' il rilievo **R9.4**, che `rcp.c` dichiara di aver
 *      corretto in cima a `misura_campi()`: *«il difetto era l'ORDINE, non il
 *      controllo»* — un `ATTACCA` con un byte in coda prendeva il posto,
 *      spediva `SESSIONE` e **poi** congedava.
 *
 *      ⛔ Qui la stessa forma sul messaggio piu' recente: se `ADATTA_TELA` non
 *      e' nell'elenco di `misura_campi()`, un corpo di 12 byte gira il palco e
 *      fa uscire un `TELA` **prima** del congedo.  Il palco e' un compositore
 *      vero: ridimensionarlo riavvia il flusso PipeWire, e su Mutter distrugge e
 *      ricrea i dispositivi di `libei`.
 *
 *      ⛔ E si guardano DUE strade, perche' i due effetti sono diversi e un
 *      controllo messo a meta' ne fermerebbe uno solo: la misura AMMESSA gira il
 *      palco (un compositore vero: riavvia il flusso PipeWire e su Mutter
 *      ricrea i dispositivi di `libei`), la misura FUORI LIMITI fa uscire un
 *      `TELA` **prima** del `CONGEDO` — byte spediti in risposta a un messaggio
 *      che il server sta per dichiarare illegale.
 *
 *      ATTESO, tutt'e due le volte: sessione CHIUSA con `ERRORE_PROTOCOLLO`,
 *      **ZERO** `TELA` sul filo e **ZERO** richieste al palco. */
static void caso22(void)
{
	rcp_sessione *s;
	bool bene, ammessa, fuori;
	int tela_fuori;

	azzera();
	s = apri_sessione(1920, 1080, NULL, true, false);
	manda_adatta_lunga(s, 1600, 900, 4);
	ammessa = chiuso && motivo_chiusura == RCP_ERRORE_PROTOCOLLO
	       && quanti_tela == 0 && dopo_la_nascita() == 0;
	snprintf(detto, sizeof detto,
	         "misura ammessa: sessione %s, TELA %d, richieste al palco %d",
	         chiuso ? "chiusa" : "VIVA", quanti_tela, dopo_la_nascita());
	rcp_libera(s);

	azzera();
	s = apri_sessione(1920, 1080, NULL, true, false);
	manda_adatta_lunga(s, 100000, 100000, 4);
	tela_fuori = quanti_tela;
	fuori = chiuso && motivo_chiusura == RCP_ERRORE_PROTOCOLLO
	     && quanti_tela == 0 && dopo_la_nascita() == 0;
	bene = ammessa && fuori;
	snprintf(detto + strlen(detto), sizeof detto - strlen(detto),
	         "; misura fuori limiti: TELA %d", tela_fuori);
	esito("22 ADATTA_TELA con la lunghezza falsa", bene,
	      "ERRORE_PROTOCOLLO e NESSUN effetto, sulle due strade: zero TELA, zero "
	      "richieste al palco",
	      detto);
	rcp_libera(s);
}

/* 23 — ⛔ LA VISTA DELL'`ATTACCA`, e i suoi due estremi opposti nello stesso
 *      caso perche' provano la stessa riga da due lati.
 *
 *      §4.5 descrive il campo `vista` e **non gli mette nessun limite**; §7.1
 *      dopo R1.17 dice qual e' l'intervallo: «qualunque misura da **1x1 in su**
 *      e' legale, dispari compresa».
 *
 *      ⭐ E questo caso esiste perche' `01-b5-violazioni.py` prova gia' `1x1` e
 *      `300x801` dalla RETE, ⛔ ma **nessuno** nel deposito manda un `ATTACCA`
 *      con un lato della vista a **zero**: il ramo che lo rifiuta e' codice
 *      scritto e mai percorso, ed e' esattamente la cosa che questo progetto
 *      chiama «una prova verde col difetto vivo» quando manca.
 *
 *      ATTESO: `ATTACCA` con vista **1x1** apre la sessione (la vista vale 1x1,
 *      la tela 1920x1080); `ATTACCA` con vista **1920x0** e' `ERRORE_PROTOCOLLO`
 *      e la sessione NON si apre — nessun `SESSIONE` sul filo. */
static void caso23(void)
{
	rcp_sessione *s;
	uint32_t vl = 0, va = 0, tl = 0, ta = 0;
	bool bene, minima, zero;

	azzera();
	vista_dell_attacco(1, 1);
	s = apri_sessione(1920, 1080, NULL, true, false);
	minima = !chiuso && rcp_vista(s, &vl, &va) && vl == 1 && va == 1
	      && rcp_tela_in_vigore(s, &tl, &ta) && tl == 1920 && ta == 1080
	      && sessione_l == 1920;
	rcp_libera(s);

	azzera();
	vista_dell_attacco(1920, 0);
	s = apri_sessione(1920, 1080, NULL, true, false);
	zero = chiuso && motivo_chiusura == RCP_ERRORE_PROTOCOLLO
	    && sessione_l == 0;
	bene = minima && zero;
	snprintf(detto, sizeof detto,
	         "vista 1x1: %s (vista tenuta %ux%u, tela %ux%u); vista 1920x0: %s",
	         minima ? "sessione aperta" : "⛔ RIFIUTATA", vl, va, tl, ta,
	         zero ? "ERRORE_PROTOCOLLO, nessuna SESSIONE" : "⛔ ACCETTATA");
	esito("23 la vista dell'ATTACCA", bene,
	      "1x1 apre la sessione e si tiene; un lato a zero e' ERRORE_PROTOCOLLO "
	      "e non apre niente",
	      detto);
	rcp_libera(s);
}

int main(int argc, char **argv)
{
	int solo = argc > 1 ? atoi(argv[1]) : 0;
	void (*casi[])(void) = {caso1,  caso2,  caso3,  caso4,  caso5,
	                        caso6,  caso7,  caso8,  caso9,  caso10,
	                        caso11, caso12, caso13, caso14, caso15,
	                        caso16, caso17, caso18, caso19, caso20,
	                        caso21, caso22, caso23};
	const int quanti = (int)(sizeof casi / sizeof casi[0]);

	parlantina = getenv("PARLANTINA") != NULL;
	printf("\n== 06-b36: la tela sul filo (RCP.md §7.1 per intero) ==\n\n");
	for (int i = 0; i < quanti; i++) {
		if (solo && solo != i + 1)
			continue;
		casi[i]();
	}
	printf("\n  passati %d, falliti %d\n\n", passati, falliti);
	return falliti ? 1 : 0;
}
