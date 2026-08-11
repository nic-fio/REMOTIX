/* 01-b8-prova-ban.c — i tre pezzi del ban che si sbagliano piu' facilmente, e
 * che nessuna prova sul filo puo' vedere da sola.
 *
 *   gcc -std=c11 -Wall -Wextra -Ibanchi/rcp -o /tmp/pb \
 *       banchi/01-b8-prova-ban.c banchi/rcp/rcp.c && /tmp/pb
 *
 * ⛔ E' la CERTIFICAZIONE di una parte di B8 (`LEZIONI.md` §1.2): tre proprieta'
 *    che sul filo si vedrebbero solo aspettando dodici ore, riavviando una
 *    macchina, o rompendo i permessi di un file che gira da root — dove root
 *    i permessi li ignora.
 *
 * Le QUATTRO parti, e perche' ciascuna sta qui:
 *
 *   1. la conversione fra l'orologio MONOTONO del server e l'ora ASSOLUTA che
 *      finisce sul disco.  Sul filo si vedrebbe solo dodici ore dopo;
 *   2. ⛔ «zero ban» e «non ho potuto leggere il file» — `LEZIONI.md` §1.9
 *      regola 1.  Il banco sul filo gira da ROOT dentro il contenitore, e per
 *      root un file con permessi 000 e' leggibile: quel controllo li' sarebbe
 *      verde per costruzione, e sarebbe il piu' vuoto di tutti;
 *   3. ⛔ la CHIAVE del ban porta le parentesi quadre — `[127.0.0.1]` — perche'
 *      `util::straddr()` dell'ospite le mette anche a IPv4.  Chi digita
 *      `127.0.0.1` al comando di sblocco deve arrivare allo stesso posto, o il
 *      comando risponde «non era bannato» a ogni indirizzo, per sempre e senza
 *      nessun sintomo.
 *   4. ⛔ che lo sblocco AZZERI IL CONTO anche quando non c'era nessun ban
 *      (sezione 5).  E' la riga su cui poggia l'intera strategia dei campioni
 *      di B8 — «sbloccare fra un blocco e l'altro» — ed era **scritta e mai
 *      misurata** in due file (rilievo A22).  Sul filo costerebbe consumare il
 *      conto di §4.4-bis di tutta la macchina (B0.3) per provare una riga.
 *
 * ⛔ E ogni parte porta il suo controllo che dice NO: senza, «il ban c'e'» e'
 *    soddisfatto anche da una guardia che dice sempre di si'.
 *
 * ⛔ E LO STATO D'USCITA HA CINQUE VALORI, non due:
 *      0  verde — e il verdetto dice su quante cose
 *      1  rosso — almeno un controllo e' fallito
 *      2  ⛔ nessun esito: zero controlli eseguiti
 *      3  ⛔ il giro non e' arrivato in fondo (sezioni o controlli mancanti)
 *      4  ⛔ uscita anticipata: il verdetto non e' stato dato affatto        */
#include "rcp.h"
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <time.h>
#include <unistd.h>

/* ⛔ TRE CONTATORI, NON UNO — rilievo A20 della revisione R12-A, 11 agosto 2026.
 *
 * Fino a stanotte qui ce n'era **uno solo**, `falliti_prova`, e il verdetto in
 * fondo era `printf("%s: %d controlli falliti")`: zero denominatore.  Bastava
 * un `return 0;` dopo la sezione 1 — o una `#if 0` attorno alle sezioni 2-4, o
 * un `#include` sbagliato che facesse saltare un blocco — perche' l'uscita
 * finisse con **«VERDE: 0 controlli falliti»** e stato d'uscita 0.
 *
 * ⛔ E' il verde su insieme vuoto di `LEZIONI.md` §1.9 regola 6 — *«tutti quelli
 *    provati sono andati bene» e' vero anche quando i provati sono zero* —
 *    dentro il file che certifica il ban, e sotto il commento di questo stesso
 *    file che dichiara di stampare il denominatore di ogni sezione.
 *
 * ⭐ La cura e' quella della regola: **anche un verdetto ha un denominatore, ed
 *    e' quante cose ha approvato**.  Qui se ne contano tre — controlli passati,
 *    controlli eseguiti, sezioni arrivate in fondo — e in fondo si pretende che
 *    siano quelli attesi, che e' l'unica forma che un `return 0;` di troppo non
 *    puo' soddisfare.                                                        */
static int falliti_prova = 0;
static int passati_prova = 0;
static int sezioni_prova = 0;

static void esige(int cond, const char *che)
{
	printf("    %s  %s\n", cond ? "OK" : "NO", che);
	if (cond)
		passati_prova++;
	else
		falliti_prova++;
}

/* ⚠ Il denominatore di ogni sezione si stampa: quanti controlli, e su che
 *   cosa.  Un elenco di OK senza il numero di quel che ha guardato non e' una
 *   misura (`LEZIONI.md` §1.9 regola 4). */
static void sezione(const char *titolo)
{
	sezioni_prova++;
	printf("\n  == [sezione %d] %s\n", sezioni_prova, titolo);
}

/* ⛔ E LA META' DEL RILIEVO A20 CHE NESSUN CONTATORE PUO' PRENDERE.
 *
 * I tre contatori qui sopra vedono una `#if 0` attorno a un blocco, un
 * `#include` sbagliato, una sezione che non arriva in fondo: il verdetto gira
 * lo stesso e trova i numeri piccoli.  ⛔ Ma un `return 0;` messo in mezzo al
 * `main` **salta il verdetto insieme al resto**, e un programma che esce senza
 * dire niente esce **0** — cioe' il caso concreto che il rilievo nomina per
 * primo resterebbe verde.
 *
 * ⭐ La cura e' l'unica che non dipende da dove qualcuno mette un `return`:
 *    il congedo del processo passa da qui **sempre**, e se il verdetto non e'
 *    stato dato lo stato d'uscita non e' zero.  «Non ho concluso» e «ho
 *    concluso che va bene» sono due fatti diversi, ed e' la stessa regola di
 *    §1.9 applicata allo stato d'uscita invece che a un conteggio.            */
static bool verdetto_dato = false;
static void al_congedo(void)
{
	if (verdetto_dato)
		return;
	fprintf(stderr,
	        "\n  ⛔ USCITA ANTICIPATA: questo programma e' finito SENZA dare un "
	        "verdetto.\n     Ha eseguito %d controlli in %d sezioni e non ha "
	        "concluso niente:\n     «non ho concluso» non e' «e' andato tutto "
	        "bene».\n",
	        passati_prova + falliti_prova, sezioni_prova);
	fflush(NULL);
	_exit(4);
}

/* ═══════════════════════════════════════════════════════════════════════════
 * ⛔ IL FINTO OSPITE — serve alla sezione 5, e a nient'altro.
 *
 * `rcp.h` mette la verifica delle credenziali fra i **ganci**, «perche' un
 * banco lo possa sostituire dichiarandolo».  E' l'unico modo di far salire il
 * contatore di §4.4-bis da qui: senza una sessione vera il conto non si muove,
 * e senza il conto la sezione 5 non ha niente da misurare.
 * ═══════════════════════════════════════════════════════════════════════════ */
enum { T_CIAO = 0x0001, T_ECCOMI = 0x0002, T_CREDENZIALI = 0x0003,
       T_AMMESSO = 0x0004, T_RESPINTO = 0x0005 };

struct ospite {
	int eccomi;      /* quanti ECCOMI sono usciti */
	int ammesso;     /* quanti AMMESSO */
	int respinto;    /* quanti RESPINTO */
	uint8_t motivo;  /* il motivo dell'ultimo RESPINTO */
};

static void o_manda(void *ctx, const uint8_t *dati, size_t len)
{
	struct ospite *o = ctx;
	if (len < 6)
		return;
	uint16_t tipo = (uint16_t)((dati[0] << 8) | dati[1]);
	if (tipo == T_ECCOMI)
		o->eccomi++;
	else if (tipo == T_AMMESSO)
		o->ammesso++;
	else if (tipo == T_RESPINTO) {
		o->respinto++;
		o->motivo = len > 6 ? dati[6] : 0;
	}
}
static void o_chiudi(void *ctx, uint8_t motivo) { (void)ctx; (void)motivo; }
static void o_registra(void *ctx, const char *riga) { (void)ctx; (void)riga; }
/* ⚠ La parola giusta e' una sola, ed e' dichiarata: cosi' «sbagliata» e
 *   «giusta» sono due casi e non due nomi della stessa cosa. */
static bool o_verifica(void *ctx, const char *utente, const char *parola)
{
	(void)ctx;
	(void)utente;
	return strcmp(parola, "parola-giusta") == 0;
}

static size_t metti_str(uint8_t *b, size_t i, const char *t)
{
	size_t n = strlen(t);
	b[i++] = (uint8_t)(n >> 8);
	b[i++] = (uint8_t)(n & 0xFF);
	memcpy(b + i, t, n);
	return i + n;
}

static size_t inquadra(uint8_t *b, uint16_t tipo, const uint8_t *corpo, size_t len)
{
	b[0] = (uint8_t)(tipo >> 8);
	b[1] = (uint8_t)(tipo & 0xFF);
	b[2] = (uint8_t)((len >> 24) & 0xFF);
	b[3] = (uint8_t)((len >> 16) & 0xFF);
	b[4] = (uint8_t)((len >> 8) & 0xFF);
	b[5] = (uint8_t)(len & 0xFF);
	memcpy(b + 6, corpo, len);
	return 6 + len;
}

/* Un tentativo intero da `provenienza`, con `parola`.  Restituisce:
 *   0x00  AMMESSO
 *   0x07  RESPINTO CREDENZIALI_ERRATE
 *   0x08  RESPINTO TROPPI_TENTATIVI
 *   0xFF  ⛔ non e' arrivata nessuna risposta — e NON e' un rifiuto.  */
static uint8_t un_tentativo(const char *provenienza, uint64_t ora,
                            const char *parola)
{
	static const char *const VOCI[] = {
	    "video.codec", "hevc,av1", "video.profondita", "8,10",
	    "audio.codec", "opus,pcm", "video.livello", "5.1",
	    "video.misura_massima", "3840x2160", "appunti.testo", "si",
	    "input.tocco", "no", "client.nome", "01-b8-prova-ban", NULL};
	struct ospite o = {0, 0, 0, 0};
	rcp_ganci g = {&o, o_manda, o_chiudi, o_registra, o_verifica};
	rcp_sessione *s = rcp_apri(&g, provenienza, ora);
	if (!s)
		return 0xFF;

	uint8_t corpo[1024], frame[1100];
	size_t i = 0;
	corpo[i++] = 0;
	corpo[i++] = 1;           /* versione 1 */
	int quante = 0;
	for (int k = 0; VOCI[k]; k += 2)
		quante++;
	corpo[i++] = (uint8_t)(quante >> 8);
	corpo[i++] = (uint8_t)(quante & 0xFF);
	for (int k = 0; VOCI[k]; k += 2) {
		i = metti_str(corpo, i, VOCI[k]);
		i = metti_str(corpo, i, VOCI[k + 1]);
	}
	size_t n = inquadra(frame, T_CIAO, corpo, i);
	rcp_ricevi(s, frame, n, ora);
	if (o.eccomi != 1) {
		rcp_libera(s);
		return 0xFF;         /* ⛔ senza ECCOMI il tentativo non e' avvenuto */
	}

	i = metti_str(corpo, 0, "utente-di-prova");
	i = metti_str(corpo, i, parola);
	n = inquadra(frame, T_CREDENZIALI, corpo, i);
	rcp_ricevi(s, frame, n, ora);
	/* ⛔ Il secondo fisso di §4.4-bis: il tempo arriva da fuori (`rcp.h`), e
	 *    senza farlo scorrere il verdetto non esce mai. */
	rcp_tempo(s, ora + 1500);
	uint8_t esito = 0xFF;
	if (o.ammesso)
		esito = 0x00;
	else if (o.respinto)
		esito = o.motivo;
	rcp_libera(s);
	return esito;
}

int main(void)
{
	/* ⛔ Prima di qualunque cosa: il congedo che rifiuta di uscire zero senza
	 *    un verdetto (vedi `al_congedo`). */
	atexit(al_congedo);
	const uint64_t ORA = 1000000; /* un orologio monotono qualunque */
	const char *f = "/tmp/remotix-b8-ban.txt";
	time_t adesso = time(NULL);

	/* ═══ 1. l'ora assoluta sul disco, e l'ora monotona in memoria ═══════ */
	sezione("1. il file dei ban: ora assoluta sul disco, monotona in memoria");
	FILE *w = fopen(f, "w");
	/* ⛔ Le quadre ci sono perche' ci sono nella chiave vera: `util::straddr()`
	 *    scrive `[1.2.3.4]:44661`, e il file dei ban riceve quel che
	 *    `solo_indirizzo()` ne lascia.  Scrivere qui `1.2.3.4` proverebbe una
	 *    forma che il server non produce mai. */
	fprintf(w, "[1.2.3.4] %lld\n", (long long)adesso + 3600); /* fra un'ora */
	fprintf(w, "[9.9.9.9] %lld\n", (long long)adesso - 10);   /* gia' scaduto */
	fclose(w);

	int quanti = rcp_ban_carica(f, ORA);
	printf("  caricati: %d  (righe nel file: 2, di cui 1 gia' scaduta)\n", quanti);
	esige(quanti == 1, "carica UNA riga sola: la scaduta si scarta");

	uint64_t restano = 0;
	esige(rcp_bannato("[1.2.3.4]:44661", ORA, &restano),
	      "l'indirizzo bannato e' bannato — e la PORTA non lo confonde");
	printf("  restano: %llu ms (attesi ~3600000)\n",
	       (unsigned long long)restano);
	esige(restano > 3590000 && restano <= 3600000,
	      "la scadenza assoluta e' tornata monotona senza deriva");

	esige(!rcp_bannato("[9.9.9.9]:1", ORA, NULL),
	      "⛔ il controllo che dice NO: la riga scaduta non e' stata caricata");
	esige(!rcp_bannato("[5.5.5.5]:1", ORA, NULL),
	      "⛔ e un indirizzo mai visto non e' bannato (la guardia non inventa)");

	/* Dodici ore dopo, lo stesso ban e' finito da se'. */
	esige(!rcp_bannato("[1.2.3.4]:44661", ORA + 43200000u, NULL),
	      "il ban scade da se' col passare del tempo");

	/* ═══ 2. la chiave del ban, e le quattro forme in cui arriva ═════════ */
	sezione("2. ⛔ la CHIAVE porta le quadre, e chi comanda digita senza");
	{
		struct {
			const char *dato;
			const char *atteso;
		} casi[] = {
		    {"127.0.0.1", "[127.0.0.1]"},
		    {"127.0.0.1:53", "[127.0.0.1]"},
		    {"[127.0.0.1]", "[127.0.0.1]"},
		    {"[127.0.0.1]:55680", "[127.0.0.1]"},
		    {"fe80::1", "[fe80::1]"},
		    {"[fe80::1]:44661", "[fe80::1]"},
		};
		int n = (int)(sizeof casi / sizeof casi[0]);
		printf("  forme provate: %d\n", n);
		for (int i = 0; i < n; i++) {
			char chiave[64];
			rcp_chiave_indirizzo(casi[i].dato, chiave, sizeof chiave);
			char che[160];
			snprintf(che, sizeof che, "«%s» → «%s» (atteso «%s»)", casi[i].dato,
			         chiave, casi[i].atteso);
			esige(strcmp(chiave, casi[i].atteso) == 0, che);
		}
		/* ⛔ E il controllo che dice NO: due indirizzi DIVERSI non devono
		 *    finire sulla stessa chiave, o il ban di uno chiuderebbe fuori
		 *    l'altro e nessun banco lo vedrebbe. */
		char a[64], b[64];
		rcp_chiave_indirizzo("127.0.0.1", a, sizeof a);
		rcp_chiave_indirizzo("127.0.0.2", b, sizeof b);
		esige(strcmp(a, b) != 0,
		      "⛔ il controllo che dice NO: due indirizzi diversi danno due "
		      "chiavi diverse");
	}

	/* ═══ 3. lo sblocco, e le sue DUE risposte ══════════════════════════ */
	sezione("3. il comando di sblocco: «non era bannato» e «l'ho tolto»");
	/* ⛔ Lo si chiama con la forma che DIGITA UNA PERSONA — senza quadre — che e'
	 *    il caso vero: se questa riga usasse `[1.2.3.4]` proverebbe la strada
	 *    che nessun essere umano percorre, e il comando resterebbe rotto per
	 *    tutti gli altri.  E' la certificazione della certificazione. */
	{
		char chiave[64];
		rcp_chiave_indirizzo("1.2.3.4", chiave, sizeof chiave);
		esige(rcp_sblocca(chiave, ORA),
		      "lo sblocco dice TRUE su un indirizzo davvero bannato — e "
		      "l'indirizzo era stato digitato SENZA le quadre");
		esige(!rcp_bannato("[1.2.3.4]:44661", ORA, NULL),
		      "e dopo non e' piu' bannato");
		esige(!rcp_sblocca(chiave, ORA),
		      "⛔ e sblocca due volte dice FALSE: «non c'era» e «l'ho tolto» sono "
		      "due fatti diversi");
	}

	/* ⛔ E LO STESSO CON UN INDIRIZZO IPv6, che e' l'unica forma in cui il
	 *    difetto si vede.  ⚠ Questa prova e' nata dalla CERTIFICAZIONE di
	 *    questo file: rimettendo a mano il vecchio `solo_indirizzo()` — quello
	 *    che tagliava sempre agli ultimi due punti — il banco restava VERDE,
	 *    perche' con IPv4 `[1.2.3.4]` non ha nessun due punti da tagliare.  Il
	 *    difetto viveva tutto in `[fe80::1]`, che quel taglio riduceva a
	 *    `[fe80:`, e nessun controllo lo attraversava.  ⛔ Un banco che non
	 *    diventa rosso quando il difetto torna non e' una prova di correttezza
	 *    (`LEZIONI.md` §1.3). */
	{
		rcp_azzera_registro_sessioni();
		FILE *s = fopen(f, "w");
		fprintf(s, "[fe80::1] %lld\n", (long long)adesso + 3600);
		fclose(s);
		int n6 = rcp_ban_carica(f, ORA);
		printf("  ban IPv6 caricati: %d (atteso 1)\n", n6);
		esige(n6 == 1, "un ban IPv6 si rilegge dal file");
		esige(rcp_bannato("[fe80::1]:44661", ORA, NULL),
		      "e con la porta addosso e' bannato (e' la forma della sessione)");
		char chiave6[64];
		rcp_chiave_indirizzo("fe80::1", chiave6, sizeof chiave6);
		esige(rcp_sblocca(chiave6, ORA),
		      "⛔ e lo sblocco lo TROVA anche senza porta: «[fe80::1]» non si "
		      "taglia agli ultimi due punti, o diventerebbe «[fe80:»");
		esige(!rcp_bannato("[fe80::1]:44661", ORA, NULL),
		      "e dopo l'IPv6 non e' piu' bannato");
	}

	/* ⛔ E lo sblocco e' finito sul DISCO, non solo in memoria: se restasse in
	 *    memoria, il riavvio rimetterebbe il ban che qualcuno ha tolto. */
	{
		FILE *r = fopen(f, "r");
		char riga[128];
		int righe = 0;
		while (fgets(riga, sizeof riga, r))
			righe++;
		fclose(r);
		esige(righe == 0,
		      "lo sblocco e' stato scritto sul file, non solo in memoria");
	}

	/* ═══ 4. ⛔ «zero ban» e «non ho potuto leggere» ═════════════════════ */
	sezione("4. ⛔ zero ban e «non ho potuto guardare» — LEZIONI.md §1.9");
	{
		rcp_azzera_registro_sessioni();
		/* a. il file non c'e' ancora: zero, e NON e' un errore */
		const char *mai = "/tmp/remotix-b8-ban-che-non-esiste.txt";
		unlink(mai);
		int r = rcp_ban_carica(mai, ORA);
		printf("  file assente        → %d (atteso 0)\n", r);
		esige(r == 0, "un file che non esiste ancora vale ZERO ban, non un errore");

		/* b. il file c'e' ed e' vuoto: zero, e l'ho letto */
		const char *vuoto = "/tmp/remotix-b8-ban-vuoto.txt";
		FILE *v = fopen(vuoto, "w");
		fclose(v);
		r = rcp_ban_carica(vuoto, ORA);
		printf("  file vuoto          → %d (atteso 0)\n", r);
		esige(r == 0, "un file vuoto vale ZERO ban");

		/* c. ⛔ il file c'e' e NON si legge: -1, mai 0.
		 *    ⚠ Con i permessi a 000 questa prova e' vera solo per un utente
		 *      normale: da root sarebbe verde per costruzione, ed e' la
		 *      ragione per cui questo controllo NON puo' stare nel banco sul
		 *      filo, che gira da root dentro il contenitore. */
		const char *chiuso = "/tmp/remotix-b8-ban-chiuso.txt";
		FILE *c = fopen(chiuso, "w");
		fprintf(c, "[7.7.7.7] %lld\n", (long long)adesso + 3600);
		fclose(c);
		chmod(chiuso, 0);
		errno = 0;
		r = rcp_ban_carica(chiuso, ORA);
		int da_root = (geteuid() == 0);
		printf("  file senza permessi → %d (atteso %s)%s\n", r,
		       da_root ? "1, perche' giri da ROOT" : "-1",
		       da_root ? "  ⚠ da root i permessi non fermano nessuno: questo "
		                 "controllo NON e' stato eseguito"
		               : "");
		if (da_root) {
			printf("    ??  ⛔ SALTATO: rilancia questa prova da utente "
			       "normale, o non prova niente\n");
			falliti_prova++; /* ⛔ un controllo saltato non e' un controllo passato */
		} else {
			esige(r == -1,
			      "⛔ un file che c'e' e non si legge vale -1, NON zero: «vuoto» "
			      "e «proibito» non devono avere la stessa faccia");
			esige(!rcp_bannato("[7.7.7.7]:1", ORA, NULL),
			      "⛔ e il controllo che dice NO: da un file illeggibile non "
			      "esce nessun ban inventato");
		}
		chmod(chiuso, 0600);
		unlink(chiuso);

		/* d. e un percorso il cui genitore non e' una directory: -1 */
		const char *storto = "/tmp/remotix-b8-ban-vuoto.txt/dentro.txt";
		r = rcp_ban_carica(storto, ORA);
		printf("  percorso impossibile → %d (atteso -1)\n", r);
		esige(r == -1,
		      "⛔ e un percorso che non si puo' nemmeno aprire vale -1: "
		      "ENOTDIR non e' «nessun ban»");

		unlink(vuoto);
		/* ⚠ E si spegne la persistenza prima di uscire: `rcp_ban_carica()`
		 *   ricorda il percorso ANCHE quando fallisce, e il primo ban
		 *   successivo cercherebbe di scrivere li'. */
		rcp_ban_carica(NULL, ORA);
	}

	/* ═══ 5. ⛔ LO SBLOCCO AZZERA IL CONTO ANCHE QUANDO NON C'ERA UN BAN ═══ */
	/* ⛔ Rilievo A22, 11 agosto 2026.  `01-b8-sblocca.py` stampa, su
	 *    `NON-BANNATO`, *«e il conto dei tentativi di quell'indirizzo riparte
	 *    comunque da zero»*, e `simula()` di `01-b8-cronometro.py` modella lo
	 *    sblocco come `falliti[ind] = 0` **sempre**.  ⛔ Nessuno dei due lo
	 *    verificava, e su quel comportamento poggia l'INTERA strategia dei
	 *    campioni di B8: «sbloccare fra un blocco e l'altro».  Se `rcp_sblocca()`
	 *    azzerasse la voce **solo quando un ban c'e'**, i fallimenti si
	 *    accumulerebbero fra i blocchi e i campioni comincerebbero a tornare
	 *    `limitatore` — cioe' il banco misurerebbe il ban credendo di misurare
	 *    PAM.
	 *
	 * ⚠ E si misura QUI e non sul filo per la ragione di sempre: sul filo
	 *   servirebbero tre autenticazioni fallite vere, cioe' consumare il conto
	 *   di §4.4-bis di tutta la macchina (B0.3) per provare una riga.
	 *
	 * ⛔ E ogni controllo ha il suo controllo che dice NO, o «il ban non e'
	 *    scattato» sarebbe soddisfatto anche da un modulo che non conta.       */
	sezione("5. ⛔ lo sblocco azzera il conto anche su un indirizzo NON bannato");
	{
		rcp_azzera_registro_sessioni();
		const uint64_t T = 5000000;

		/* ⭐ IL CONTROLLO POSITIVO DELLO STRUMENTO, PRIMA DI TUTTO: se il
		 *    finto ospite non riuscisse a far arrivare un tentativo in fondo,
		 *    ogni «il ban non e' scattato» che segue vorrebbe dire «non ho
		 *    misurato niente» (`REVIEWER.md` §1 domanda 5). */
		esige(un_tentativo("[10.0.0.1]:1", T, "parola-giusta") == 0x00,
		      "⭐ controllo positivo: un tentativo con la parola GIUSTA arriva "
		      "ad AMMESSO — lo strumento sa far succedere quel che conta");
		esige(un_tentativo("[10.0.0.1]:2", T, "sbagliata") == RCP_CREDENZIALI_ERRATE,
		      "⭐ e uno con la parola sbagliata arriva a CREDENZIALI_ERRATE: "
		      "lo strumento sa produrre anche i fallimenti che contano");

		/* a. il controllo che dice NO: senza sblocco, tre fallimenti bannano */
		rcp_azzera_registro_sessioni();
		for (int k = 0; k < 3; k++)
			un_tentativo("[10.0.0.2]:9", T, "sbagliata");
		esige(un_tentativo("[10.0.0.2]:9", T, "parola-giusta")
		          == RCP_TROPPI_TENTATIVI,
		      "⛔ il controllo che dice NO: SENZA sblocco, tre fallimenti "
		      "bannano e il quarto — con la parola GIUSTA — e' TROPPI_TENTATIVI");

		/* b. due fallimenti, poi lo sblocco su un indirizzo NON bannato */
		rcp_azzera_registro_sessioni();
		char chiave[64];
		rcp_chiave_indirizzo("10.0.0.3", chiave, sizeof chiave);
		for (int k = 0; k < 2; k++)
			un_tentativo("[10.0.0.3]:9", T, "sbagliata");
		esige(!rcp_bannato("[10.0.0.3]:9", T, NULL),
		      "a due fallimenti l'indirizzo NON e' ancora bannato (soglia 3)");
		esige(!rcp_sblocca(chiave, T),
		      "⛔ e lo sblocco risponde FALSE — «non era bannato» — che e' "
		      "esattamente il caso in cui la riga di 01-b8-sblocca.py parla");

		/* c. ⭐ LA RIGA CHE NESSUNO AVEVA MISURATO: il conto e' ripartito da
		 *    zero, quindi i due fallimenti successivi NON bannano. */
		un_tentativo("[10.0.0.3]:9", T, "sbagliata");
		un_tentativo("[10.0.0.3]:9", T, "sbagliata");
		esige(un_tentativo("[10.0.0.3]:9", T, "parola-giusta") == 0x00,
		      "⭐ IL CONTO E' RIPARTITO DA ZERO: dopo uno sblocco su un "
		      "indirizzo NON bannato, altri due fallimenti non fanno tre — e la "
		      "strategia dei campioni di B8 poggia su questa riga");
		esige(!rcp_bannato("[10.0.0.3]:9", T, NULL),
		      "⛔ e il controllo che dice NO: l'indirizzo non e' bannato "
		      "nemmeno adesso (se il conto non fosse ripartito, 2+2 farebbero "
		      "quattro e il ban sarebbe scattato al terzo)");
	}

	/* ═══ ⛔ IL VERDETTO, E IL SUO DENOMINATORE ═════════════════════════════ */
	/* ⛔ `LEZIONI.md` §1.9 regola 6: «anche un verdetto ha un denominatore, ed
	 *    e' quante cose ha approvato, e se e' zero non si da' nessun esito».
	 *    ⚠ E qui non basta «diverso da zero»: un `return 0;` messo in mezzo
	 *      lascerebbe un denominatore piccolo ma non nullo, e un numero piccolo
	 *      da solo non si distingue da un giro corto.  Quindi si dichiara
	 *      QUANTI dovevano essere, e il confronto lo fa il banco (B0.4).       */
	{
		int da_root_qui = (geteuid() == 0);
		/* ⚠ Da root la sezione 4 salta due controlli e ne conta uno fallito al
		 *   loro posto: il numero atteso e' diverso, e si dichiara invece di
		 *   essere allargato quando non torna. */
		/* ⚠ I due numeri si contano a mano, sezione per sezione: 6 + 7 + 8 +
		 *   (5 da utente normale, 3 da root) + 7.  ⛔ Chi aggiunge un `esige()`
		 *   aggiorna questa riga nello stesso commit: e' il prezzo del
		 *   denominatore, ed e' piu' basso di un verde su insieme vuoto. */
		const int SEZIONI_ATTESE = 5;
		const int CONTROLLI_ATTESI = da_root_qui ? 31 : 33;
		printf("\n  == il denominatore di QUESTO verdetto\n");
		printf("    sezioni arrivate in fondo : %d (attese %d)\n",
		       sezioni_prova, SEZIONI_ATTESE);
		printf("    controlli eseguiti        : %d (attesi %d%s)\n",
		       passati_prova + falliti_prova, CONTROLLI_ATTESI,
		       da_root_qui ? ", da root" : "");
		printf("    di cui APPROVATI          : %d\n", passati_prova);
		printf("    di cui falliti            : %d\n", falliti_prova);

		if (passati_prova + falliti_prova == 0) {
			printf("\n  ⛔ NESSUN ESITO: questo giro ha approvato ZERO cose.\n");
			printf("     «Tutti quelli provati sono andati bene» e' vero anche "
			       "quando i provati sono zero\n");
			verdetto_dato = true;
			return 2;
		}
		if (sezioni_prova != SEZIONI_ATTESE
		    || passati_prova + falliti_prova != CONTROLLI_ATTESI) {
			printf("\n  ⛔ ROSSO: il giro non e' arrivato in fondo — %d sezioni "
			       "su %d, %d controlli su %d.\n",
			       sezioni_prova, SEZIONI_ATTESE,
			       passati_prova + falliti_prova, CONTROLLI_ATTESI);
			printf("     ⛔ Non si allarga l'atteso finche' torna verde: o e' "
			       "stato aggiunto un controllo e questi due numeri vanno "
			       "aggiornati insieme, o un pezzo del file non e' stato "
			       "eseguito.\n");
			verdetto_dato = true;
			return 3;
		}
		printf("\n  %s: %d controlli falliti su %d approvati, in %d sezioni\n",
		       falliti_prova ? "ROSSO" : "VERDE", falliti_prova, passati_prova,
		       sezioni_prova);
		verdetto_dato = true;
		return falliti_prova ? 1 : 0;
	}
}
