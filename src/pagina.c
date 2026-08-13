/*
 * pagina.c — vedi pagina.h.
 */
#include "pagina.h"

#include "rcp.h"
#include "registro.h"

#include <errno.h>
#include <fcntl.h>
#include <netdb.h>
#include <netinet/in.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <unistd.h>

#include <openssl/err.h>

#define MAX_CLIENTI 32
#define MAX_RICHIESTA 8192

/* ⛔ LE DUE INTESTAZIONI DI ISOLAMENTO FRA ORIGINI, PIU' LA TERZA CHE IMPLICANO.
 *
 *    `SPECIFICHE.md` §11.5 le rende un vincolo di PRODOTTO: senza, su Firefox e
 *    Safari i cronometri della pagina cadono su una griglia da 1 ms — su un
 *    tetto di 50 (`web.md` §6.3, P6) — e la memoria condivisa non esiste.
 *
 * ⚠ E si mettono su OGNI risposta, non solo sulla pagina: e' quel che «cambia
 *   come il server serve ogni risorsa» significa in byte. */
#define ISOLAMENTO                                                             \
	"Cross-Origin-Opener-Policy: same-origin\r\n"                              \
	"Cross-Origin-Embedder-Policy: require-corp\r\n"                           \
	"Cross-Origin-Resource-Policy: same-origin\r\n"

enum fase { F_STRETTA, F_LEGGE, F_SCRIVE, F_FINITA };

typedef struct {
	int fd;
	SSL *ssl;
	enum fase fase;
	char richiesta[MAX_RICHIESTA];
	size_t nrichiesta;
	char *risposta;
	size_t nrisposta, orisposta;
	char provenienza[80];
	/* ⚠ Quale evento OpenSSL sta aspettando: senza questo si sorveglia
	 *   l'evento sbagliato e la connessione resta ferma finche' non scade
	 *   qualcos'altro. */
	bool vuole_scrivere;
} cliente;

struct pagina {
	int fd;
	SSL_CTX *ctx;
	const certificati *cert;
	char *html;
	size_t nhtml;
	cliente clienti[MAX_CLIENTI];
};

/* ------------------------------------------------------------------------ */

static char *leggi_file(const char *percorso, size_t *quanto)
{
	FILE *f = fopen(percorso, "rb");
	char *d;
	long n;
	if (!f) {
		registro_dice(REG_PAGINA, "⛔ non apro %s: %s", percorso,
		              strerror(errno));
		return NULL;
	}
	fseek(f, 0, SEEK_END);
	n = ftell(f);
	fseek(f, 0, SEEK_SET);
	if (n <= 0) {
		fclose(f);
		registro_dice(REG_PAGINA, "⛔ %s e' vuoto", percorso);
		return NULL;
	}
	d = malloc((size_t)n + 1);
	if (!d) {
		fclose(f);
		return NULL;
	}
	if (fread(d, 1, (size_t)n, f) != (size_t)n) {
		free(d);
		fclose(f);
		registro_dice(REG_PAGINA, "⛔ %s non si legge per intero", percorso);
		return NULL;
	}
	d[n] = 0;
	fclose(f);
	*quanto = (size_t)n;
	return d;
}

/* Sostituisce ogni occorrenza di `segno` con `valore`.  Restituisce una stringa
 * nuova, da liberare. */
static char *sostituisci(const char *testo, const char *segno, const char *valore)
{
	size_t ls = strlen(segno), lv = strlen(valore), cap, o = 0;
	const char *p = testo;
	char *fuori;

	cap = strlen(testo) + 1;
	for (const char *q = strstr(testo, segno); q; q = strstr(q + ls, segno))
		cap += lv;
	fuori = malloc(cap);
	if (!fuori)
		return NULL;
	for (;;) {
		const char *q = strstr(p, segno);
		if (!q) {
			size_t r = strlen(p);
			memcpy(fuori + o, p, r + 1);
			return fuori;
		}
		memcpy(fuori + o, p, (size_t)(q - p));
		o += (size_t)(q - p);
		memcpy(fuori + o, valore, lv);
		o += lv;
		p = q + ls;
	}
}

/* ------------------------------------------------------------------------ */

static void cliente_chiudi(cliente *c)
{
	if (c->ssl) {
		SSL_free(c->ssl);
		c->ssl = NULL;
	}
	if (c->fd >= 0) {
		close(c->fd);
		c->fd = -1;
	}
	free(c->risposta);
	c->risposta = NULL;
	c->nrisposta = c->orisposta = c->nrichiesta = 0;
	c->fase = F_FINITA;
}

static void componi(cliente *c, const char *stato, const char *tipo,
                    const char *corpo, size_t ncorpo, const char *extra)
{
	char testa[768];
	int n;

	n = snprintf(testa, sizeof testa,
	             "HTTP/1.1 %s\r\n"
	             "Content-Type: %s\r\n"
	             "Content-Length: %zu\r\n"
	             ISOLAMENTO
	             "Cache-Control: no-store\r\n"
	             "X-Content-Type-Options: nosniff\r\n"
	             "Connection: close\r\n"
	             "%s"
	             "\r\n",
	             stato, tipo, ncorpo, extra ? extra : "");
	if (n < 0)
		return;
	c->risposta = malloc((size_t)n + ncorpo);
	if (!c->risposta)
		return;
	memcpy(c->risposta, testa, (size_t)n);
	memcpy(c->risposta + n, corpo, ncorpo);
	c->nrisposta = (size_t)n + ncorpo;
	c->orisposta = 0;
	c->fase = F_SCRIVE;
}

static void servi(pagina *p, cliente *c)
{
	char metodo[16] = {0}, percorso[256] = {0}, bersaglio[256] = {0};
	const char *sp1, *sp2;
	char indirizzo[64];
	uint64_t restano = 0;
	bool bannato;

	sp1 = memchr(c->richiesta, ' ', c->nrichiesta);
	if (!sp1) {
		componi(c, "400 Bad Request", "text/plain; charset=utf-8",
		        "richiesta illeggibile\n", 22, NULL);
		return;
	}
	{
		size_t n = (size_t)(sp1 - c->richiesta);
		if (n >= sizeof metodo)
			n = sizeof metodo - 1;
		memcpy(metodo, c->richiesta, n);
	}
	sp2 = memchr(sp1 + 1, ' ', c->nrichiesta - (size_t)(sp1 + 1 - c->richiesta));
	if (!sp2) {
		componi(c, "400 Bad Request", "text/plain; charset=utf-8",
		        "richiesta illeggibile\n", 22, NULL);
		return;
	}
	{
		size_t n = (size_t)(sp2 - sp1 - 1);
		if (n >= sizeof percorso)
			n = sizeof percorso - 1;
		memcpy(percorso, sp1 + 1, n);
	}

	/* ⛔⭐ IL BERSAGLIO DELLA RICHIESTA NON E' IL PERCORSO — difetto B-20,
	 *     misurato il 13 agosto 2026.
	 *
	 * `[M]` Prima di questa riga il confronto qui sotto era
	 * `strcmp(percorso, "/")` sul bersaglio INTERO, stringa di ricerca
	 * compresa: `GET /` dava **200 su 166107 byte** e `GET /?video=worker`
	 * dava **404 su 9 byte**.  RFC 9110 §4.1 dice l'opposto — la stringa di
	 * ricerca e' un componente a se' della URI, non un pezzo del percorso, e
	 * chi decide che cosa servire guarda il percorso.
	 *
	 * ⛔ E LA CONSEGUENZA VERA NON E' IL WORKER, e' che `pagina.html`
	 *    documenta da sempre DUE interruttori che si accendono dalla stringa
	 *    di ricerca — `?tela=desincronizzata` (§6.1 di `web.md`) e
	 *    `?video=worker` — e **nessuno dei due e' mai stato raggiungibile
	 *    attraverso il prodotto**: il commento indicava una strada che il
	 *    server chiudeva con un 404.  ⚠ Nessuno se n'era accorto perche' i
	 *    banchi la pagina la servono da un `http.server` di Python, che il `?`
	 *    lo ignora — cioe' il difetto viveva ESATTAMENTE nella fessura fra il
	 *    banco e il prodotto.
	 *
	 * ⭐ La cura taglia, e taglia SOLO il `?` (e il `#`, se mai arrivasse: un
	 *    browser il frammento non lo manda, ma un client qualunque puo'
	 *    mandarlo, e allora il percorso resta il percorso).  ⛔ Il controllo
	 *    NON si allenta: `/inesistente?x=1` continua a dare 404 come
	 *    `/inesistente`, perche' quel che cambia e' quale stringa si confronta,
	 *    non il confronto.  ⚠ E se il bersaglio fosse cosi' lungo da non
	 *    entrare in `percorso`, il troncamento di qui sopra si porta via anche
	 *    il `?`: il risultato e' un percorso che non combacia con niente,
	 *    cioe' 404 — l'esito prudente, non un buco.
	 *
	 * ⚠ E NEL REGISTRO CI VA IL BERSAGLIO INTERO, non il percorso tagliato:
	 *   dopo questa cura gli interruttori si accendono davvero, e un registro
	 *   che scrivesse `/` per `/?tela=desincronizzata` renderebbe invisibile
	 *   proprio l'unica cosa che questa riga ha appena reso possibile. */
	memcpy(bersaglio, percorso, sizeof bersaglio - 1);
	percorso[strcspn(percorso, "?#")] = 0;

	/* ⛔ La chiave del ban la fa `rcp.c`, non questo file: `rcp.h` lo dice con
	 *    un ⛔, e la ragione e' che il formato della chiave lo sa un modulo
	 *    solo.  ⚠ Chi se la costruisse da se' cercherebbe `192.168.0.2` dove
	 *    sta scritto `[192.168.0.2]`, e la pagina direbbe «non sei bannato» a
	 *    chi lo e' — cioe' proprio a chi §4.2 vuole che veda la frase. */
	rcp_chiave_indirizzo(c->provenienza, indirizzo, sizeof indirizzo);
	bannato = rcp_bannato(indirizzo, registro_ora_ms(), &restano);

	registro_dice(REG_PAGINA, "%s %s da %s%s", metodo, bersaglio, c->provenienza,
	              bannato ? " (indirizzo BANNATO)" : "");

	/* ⛔ L'ENDPOINT DA CUI LA PAGINA RITIRA L'IMPRONTA AGGIORNATA (§4.1-bis).
	 *
	 *    «Una scheda lasciata aperta due settimane tiene l'impronta di un
	 *    certificato che nel frattempo e' stato ruotato: alla riconnessione
	 *    il browser rifiuta, e il sintomo e' *non si collega piu' e non dice
	 *    perche'*.»  Delle due cure, questa e' quella scelta: ricaricare la
	 *    pagina funziona e butta via lo stato.
	 *
	 * ⛔ E non passa da RCP: la sessione non e' ancora aperta, quindi non
	 *    c'e' un canale su cui chiedere.  La si ritira dal server che l'ha
	 *    servita, con una richiesta ordinaria. */
	if (strcmp(percorso, "/impronta") == 0) {
		char corpo[512];
		int n = snprintf(corpo, sizeof corpo,
		                 "{\"algoritmo\":\"sha-256\",\"impronta\":\"%s\","
		                 "\"esadecimale\":\"%s\",\"rotazioni\":%u}\n",
		                 p->cert->impronta, p->cert->impronta_esa,
		                 p->cert->rotazioni);
		componi(c, "200 OK", "application/json; charset=utf-8", corpo,
		        (size_t)n, NULL);
		return;
	}

	if (strcmp(percorso, "/") != 0 && strcmp(percorso, "/index.html") != 0) {
		componi(c, "404 Not Found", "text/plain; charset=utf-8",
		        "non c'e'\n", 9, NULL);
		return;
	}

	/* ⛔⭐ L'AVVISO DEL BAN — §4.4-bis, e i due rilievi che questa parte ha
	 *     pagato la notte del 10 agosto 2026.
	 *
	 * ⛔ **B-9**: la frase conteneva `l'indirizzo`, cioe' un escape
	 *    **JavaScript** per l'apostrofo, e veniva sostituita in DUE punti della
	 *    pagina con due sintassi diverse — dentro una stringa JS e dentro un
	 *    `<div>`.  Nella stringa JS l'escape diventava un apostrofo; nel `<div>`
	 *    no, perche' l'HTML gli escape `\uXXXX` non li conosce.  Il
	 *    proprietario bannato — quello per cui §4.4-bis ha scritto tre punti
	 *    normativi — leggeva sullo schermo, alla lettera,
	 *    «sblocca l'indirizzo dal server».
	 *    ⚠ E non esisteva un testo giusto per tutt'e due: la cura era separare
	 *      i due segni, non aggiustare la frase.  ⛔ E c'era il male peggiore:
	 *      il testo finiva **dentro una stringa JS** senza nessuna
	 *      neutralizzazione — oggi e' fisso e non contiene virgolette, il
	 *      giorno in cui ci finisse un dato che non decidiamo noi quella riga
	 *      e' un'iniezione.
	 *
	 * ⭐ La cura: la frase sta SOLO nell'HTML, e il JavaScript non riceve piu'
	 *    nessun testo — legge `data-bannato` dal `<body>`.  Un dato che non
	 *    entra in un programma non lo puo' rompere.
	 *
	 * ⛔ **R12.2**: il misuratore di §4.4-bis (`banchi/01-b8-cronometro.py`)
	 *    cerca nel documento `data-bannato`, `data-restano-ms`, la sottostringa
	 *    «tentativi esauriti» e gli `id="ore"`/`id="minuti"`.  Questa pagina non
	 *    ne aveva NESSUNO: puntato a questo server, il banco avrebbe dato tre
	 *    rossi **su un server che il ban lo fa**, e il rosso sarebbe finito
	 *    sull'imputato sbagliato.  ⚠ I nomi non sono del banco: sono la forma in
	 *    cui l'altra meta' del progetto ha gia' scritto la stessa cosa, e averne
	 *    due sarebbe la forma E2 di `REVIEWER.md`.
	 *
	 * ⚠ E i minuti si arrotondano PER ECCESSO, come nell'innesto: dire «restano
	 *   0 ore» a chi ha ancora 59 minuti da aspettare e' peggio che non dire
	 *   niente. */
	{
		char *a, *b, *cc, *d;
		/* ⚠ 640 e non 320: la frase intera piu' i due numeri ci deve stare
		 *   TUTTA.  `[M]` 10 agosto 2026 notte — con 320 il compilatore
		 *   diceva «directive output truncated writing 227 bytes into a
		 *   region of size between 131 and 144», e quel che l'utente bannato
		 *   avrebbe letto sarebbe finito a meta' frase.  Un avviso troncato
		 *   e' peggio di nessun avviso: §4.4-bis vuole che si CAPISCA. */
		char avviso[640] = "";
		char restano_txt[32];
		unsigned long long minuti = (restano + 59999u) / 60000u;

		if (bannato) {
			/* ⛔ §4.4-bis: «la pagina si carica lo stesso e mostra il
			 *    rifiuto — tentativi esauriti.  Non un errore di rete, non
			 *    un silenzio: chi e' bannato per errore e' quasi sempre il
			 *    proprietario, e deve poter capire che cosa gli e'
			 *    successo.» */
			snprintf(avviso, sizeof avviso,
			         /* ⚠ Niente `id` su questo `<b>`: la pagina ha gia' un
			          * `id="esito"` e due elementi con lo stesso `id`
			          * farebbero prendere a `getElementById` quello
			          * sbagliato — cioe' l'esito del collegamento
			          * comparirebbe dentro l'avviso del ban. */
			         "<b>tentativi esauriti</b>: da questo "
			         "indirizzo sono arrivati tre tentativi di accesso "
			         "falliti, e per questo resta fuori. Mancano ancora "
			         "<b id=\"ore\">%llu</b> ore e "
			         "<b id=\"minuti\">%llu</b> minuti. Si rientra in due "
			         "modi: aspettando la scadenza, oppure col comando di "
			         "sblocco sulla macchina che serve — che chiede l'accesso "
			         "a quella macchina, ed &egrave; la via di chi si &egrave; "
			         "bannato dal proprio telefono.",
			         minuti / 60, minuti % 60);
		}
		snprintf(restano_txt, sizeof restano_txt, "%llu",
		         (unsigned long long)restano);

		a = sostituisci(p->html, "__IMPRONTA__", p->cert->impronta);
		if (!a) {
			componi(c, "500 Internal Server Error",
			        "text/plain; charset=utf-8", "memoria\n", 8, NULL);
			return;
		}
		b = sostituisci(a, "__AVVISO__", avviso);
		free(a);
		if (!b) {
			componi(c, "500 Internal Server Error",
			        "text/plain; charset=utf-8", "memoria\n", 8, NULL);
			return;
		}
		cc = sostituisci(b, "__BANNATO__", bannato ? "si" : "no");
		free(b);
		if (!cc) {
			componi(c, "500 Internal Server Error",
			        "text/plain; charset=utf-8", "memoria\n", 8, NULL);
			return;
		}
		d = sostituisci(cc, "__RESTANO_MS__", restano_txt);
		free(cc);
		if (!d) {
			componi(c, "500 Internal Server Error",
			        "text/plain; charset=utf-8", "memoria\n", 8, NULL);
			return;
		}
		componi(c, "200 OK", "text/html; charset=utf-8", d, strlen(d), NULL);
		free(d);
	}
}

/* ------------------------------------------------------------------------ */

static void muovi_cliente(pagina *p, cliente *c, short eventi)
{
	int rv;

	(void)eventi;
	c->vuole_scrivere = false;

	if (c->fase == F_STRETTA) {
		rv = SSL_accept(c->ssl);
		if (rv == 1) {
			c->fase = F_LEGGE;
		} else {
			int e = SSL_get_error(c->ssl, rv);
			if (e == SSL_ERROR_WANT_WRITE) {
				c->vuole_scrivere = true;
				return;
			}
			if (e == SSL_ERROR_WANT_READ)
				return;
			/* ⚠ Una stretta TLS fallita e' la cosa piu' comune che
			 *   succeda a questo ascoltatore: e' l'utente che NON ha
			 *   ancora concesso l'eccezione sul certificato longevo
			 *   (`RCP.md` §4.1).  Si dice a voce bassa, o il registro
			 *   diventa illeggibile ad ogni caricamento. */
			registro_dettaglio(REG_PAGINA,
			                   "stretta TLS non riuscita con %s (errore %d) "
			                   "— di solito e' l'avviso sul certificato "
			                   "non ancora accettato",
			                   c->provenienza, e);
			ERR_clear_error();
			cliente_chiudi(c);
			return;
		}
	}

	if (c->fase == F_LEGGE) {
		for (;;) {
			size_t letti = 0;
			rv = SSL_read_ex(c->ssl, c->richiesta + c->nrichiesta,
			                 sizeof c->richiesta - c->nrichiesta - 1, &letti);
			if (rv != 1) {
				int e = SSL_get_error(c->ssl, rv);
				if (e == SSL_ERROR_WANT_WRITE)
					c->vuole_scrivere = true;
				if (e == SSL_ERROR_WANT_READ || e == SSL_ERROR_WANT_WRITE)
					return;
				cliente_chiudi(c);
				return;
			}
			c->nrichiesta += letti;
			c->richiesta[c->nrichiesta] = 0;
			if (strstr(c->richiesta, "\r\n\r\n") ||
			    strstr(c->richiesta, "\n\n")) {
				servi(p, c);
				break;
			}
			if (c->nrichiesta + 1 >= sizeof c->richiesta) {
				/* ⛔ La lunghezza si controlla prima di allocare, ed e'
				 *    la stessa regola di `RCP.md` §6.1 applicata a HTTP. */
				componi(c, "431 Request Header Fields Too Large",
				        "text/plain; charset=utf-8", "intestazioni troppo "
				                                     "lunghe\n",
				        26, NULL);
				break;
			}
		}
	}

	if (c->fase == F_SCRIVE) {
		while (c->orisposta < c->nrisposta) {
			size_t scritti = 0;
			rv = SSL_write_ex(c->ssl, c->risposta + c->orisposta,
			                  c->nrisposta - c->orisposta, &scritti);
			if (rv != 1) {
				int e = SSL_get_error(c->ssl, rv);
				if (e == SSL_ERROR_WANT_WRITE) {
					c->vuole_scrivere = true;
					return;
				}
				if (e == SSL_ERROR_WANT_READ)
					return;
				cliente_chiudi(c);
				return;
			}
			c->orisposta += scritti;
		}
		SSL_shutdown(c->ssl);
		cliente_chiudi(c);
	}
}

/* ------------------------------------------------------------------------ */

size_t pagina_descrittori(pagina *p, struct pollfd *dove, size_t cap)
{
	size_t n = 0;
	if (cap == 0)
		return 0;
	dove[n].fd = p->fd;
	dove[n].events = POLLIN;
	dove[n].revents = 0;
	n++;
	for (size_t i = 0; i < MAX_CLIENTI && n < cap; i++) {
		if (p->clienti[i].fase == F_FINITA || p->clienti[i].fd < 0)
			continue;
		dove[n].fd = p->clienti[i].fd;
		dove[n].events = p->clienti[i].vuole_scrivere ? POLLOUT : POLLIN;
		dove[n].revents = 0;
		n++;
	}
	return n;
}

static void accetta(pagina *p)
{
	for (;;) {
		struct sockaddr_storage da;
		socklen_t dalen = sizeof da;
		int fd;
		cliente *c = NULL;
		char host[NI_MAXHOST], serv[NI_MAXSERV];

		fd = accept4(p->fd, (struct sockaddr *)&da, &dalen, SOCK_NONBLOCK);
		if (fd < 0) {
			if (errno != EAGAIN && errno != EWOULDBLOCK && errno != EINTR)
				registro_dice(REG_PAGINA, "accept: %s", strerror(errno));
			return;
		}
		for (size_t i = 0; i < MAX_CLIENTI; i++)
			if (p->clienti[i].fase == F_FINITA && p->clienti[i].fd < 0) {
				c = &p->clienti[i];
				break;
			}
		if (!c) {
			/* ⛔ Si dice.  Un rifiuto silenzioso sarebbe indistinguibile
			 *    da un server morto — e chi e' fuori vede la stessa
			 *    faccia in tutt'e due i casi (`LEZIONI.md` §1.9). */
			registro_dice(REG_PAGINA,
			              "⛔ gia' %d connessioni TCP: la nuova si rifiuta",
			              MAX_CLIENTI);
			close(fd);
			return;
		}
		memset(c, 0, sizeof *c);
		c->fd = fd;
		if (getnameinfo((struct sockaddr *)&da, dalen, host, sizeof host, serv,
		                sizeof serv, NI_NUMERICHOST | NI_NUMERICSERV) == 0)
			snprintf(c->provenienza, sizeof c->provenienza,
			         da.ss_family == AF_INET6 ? "[%s]:%s" : "%s:%s", host,
			         serv);
		else
			snprintf(c->provenienza, sizeof c->provenienza, "?");

		c->ssl = SSL_new(p->ctx);
		if (!c->ssl) {
			close(fd);
			c->fd = -1;
			c->fase = F_FINITA;
			return;
		}
		SSL_set_fd(c->ssl, fd);
		SSL_set_accept_state(c->ssl);
		c->fase = F_STRETTA;
		muovi_cliente(p, c, 0);
	}
}

void pagina_muovi(pagina *p, struct pollfd *dove, size_t quanti)
{
	for (size_t k = 0; k < quanti; k++) {
		if (dove[k].revents == 0)
			continue;
		if (dove[k].fd == p->fd) {
			accetta(p);
			continue;
		}
		for (size_t i = 0; i < MAX_CLIENTI; i++)
			if (p->clienti[i].fd == dove[k].fd &&
			    p->clienti[i].fase != F_FINITA) {
				muovi_cliente(p, &p->clienti[i], dove[k].revents);
				break;
			}
	}
}

void pagina_contesto(pagina *p, SSL_CTX *ctx) { p->ctx = ctx; }

/* ------------------------------------------------------------------------ */

pagina *pagina_apri(const char *indirizzo, const char *porta, SSL_CTX *ctx,
                    const char *file_html, const certificati *cert)
{
	struct addrinfo sugg, *ris = NULL, *r;
	pagina *p;
	int fd = -1, uno = 1;

	memset(&sugg, 0, sizeof sugg);
	sugg.ai_family = AF_UNSPEC;
	sugg.ai_socktype = SOCK_STREAM;
	sugg.ai_flags = AI_PASSIVE;

	if (getaddrinfo(indirizzo, porta, &sugg, &ris) != 0) {
		registro_dice(REG_PAGINA, "⛔ %s:%s non si risolve", indirizzo, porta);
		return NULL;
	}
	for (r = ris; r; r = r->ai_next) {
		fd = socket(r->ai_family, r->ai_socktype | SOCK_NONBLOCK, r->ai_protocol);
		if (fd < 0)
			continue;
		setsockopt(fd, SOL_SOCKET, SO_REUSEADDR, &uno, sizeof uno);
		if (bind(fd, r->ai_addr, r->ai_addrlen) == 0 && listen(fd, 16) == 0)
			break;
		close(fd);
		fd = -1;
	}
	freeaddrinfo(ris);
	if (fd < 0) {
		registro_dice(REG_PAGINA, "⛔ non mi lego a %s:%s in TCP: %s", indirizzo,
		              porta, strerror(errno));
		return NULL;
	}

	p = calloc(1, sizeof *p);
	if (!p) {
		close(fd);
		return NULL;
	}
	p->fd = fd;
	p->ctx = ctx;
	p->cert = cert;
	for (size_t i = 0; i < MAX_CLIENTI; i++) {
		p->clienti[i].fd = -1;
		p->clienti[i].fase = F_FINITA;
	}

	p->html = leggi_file(file_html, &p->nhtml);
	if (!p->html) {
		pagina_chiudi(p);
		return NULL;
	}
	/* ⛔ Il controllo positivo del segno: se la pagina NON contiene
	 *    `__IMPRONTA__`, la sostituzione riuscirebbe «senza fare niente» e il
	 *    server servirebbe per sempre una pagina senza impronta — con il
	 *    sintomo «WebTransport non si connette» e nessun errore che nomini
	 *    l'impronta (`LEZIONI.md` §1.9: uno strumento che non trova niente
	 *    non e' pulito, e' non certificato). */
	/* ⛔ E I SEGNI SONO QUATTRO, non uno — 10 agosto 2026 notte, rilievo
	 *    R12.2.  `__BANNATO__` e `__RESTANO_MS__` sono quel che il misuratore
	 *    di §4.4-bis legge per dire se il ban c'e' e per quanto: una pagina
	 *    senza quei segni verrebbe servita benissimo, e il banco direbbe «il
	 *    ban non e' scattato» su un server che il ban lo fa.  ⚠ Una
	 *    sostituzione che «riesce senza fare niente» e' la settima veste di
	 *    `LEZIONI.md` §1.9, e vale per tutti e quattro. */
	{
		static const char *const SEGNI[] = {"__IMPRONTA__", "__AVVISO__",
		                                    "__BANNATO__", "__RESTANO_MS__",
		                                    NULL};
		for (int i = 0; SEGNI[i]; i++)
			if (!strstr(p->html, SEGNI[i])) {
				registro_dice(REG_PAGINA,
				              "⛔ %s non contiene il segno %s: la pagina "
				              "servirebbe una risposta che non c'e' — e una "
				              "sostituzione che riesce senza fare niente non "
				              "lo direbbe a nessuno.  Non si parte.",
				              file_html, SEGNI[i]);
				pagina_chiudi(p);
				return NULL;
			}
	}

	/* ⛔⭐ E CIASCUNO DEI DUE ATTRIBUTI DEVE COMPARIRE UNA VOLTA SOLA.
	 *
	 *     `[M]` 10 agosto 2026 notte, e l'ho fatto io mentre curavo R12.2: il
	 *     foglio di stile diceva `#avviso { display:none }` sotto un selettore
	 *     d'attributo su `data-bannato`, e quel selettore mette la stringa
	 *     `data-bannato=«si»` DENTRO il `<style>`, cioe' PRIMA del `<body>`.
	 *     ⛔ Chi legge il documento con una ricerca — ed e' quel che fa il
	 *     misuratore di §4.4-bis — prende la PRIMA occorrenza: leggeva
	 *     «bannato» su un indirizzo libero.  ⚠ La pagina era giusta, la misura
	 *     no, e il rosso sarebbe finito sull'imputato sbagliato.
	 *
	 * ⭐ La cura sta nel PROGRAMMA e non in un commento (invariante I7): la
	 *    seconda occorrenza non si puo' introdurre senza che il server rifiuti
	 *    di partire — nemmeno dentro un commento, che e' byte serviti al
	 *    browser quanto il resto. */
	{
		static const char *const UNICI[] = {"data-bannato=\"",
		                                    "data-restano-ms=\"", NULL};
		for (int i = 0; UNICI[i]; i++) {
			int quante = 0;
			for (const char *q = strstr(p->html, UNICI[i]); q;
			     q = strstr(q + strlen(UNICI[i]), UNICI[i]))
				quante++;
			if (quante != 1) {
				registro_dice(REG_PAGINA,
				              "⛔ %s contiene «%s» %d volte invece di una "
				              "sola: chi legge il documento cercando quella "
				              "stringa prenderebbe l'occorrenza sbagliata e "
				              "misurerebbe il ban di nessuno (§4.4-bis).  "
				              "Non si parte.",
				              file_html, UNICI[i], quante);
				pagina_chiudi(p);
				return NULL;
			}
		}
	}

	registro_dice(REG_PAGINA,
	              "ascolto TCP su %s:%s — pagina %s (%zu byte), isolata fra "
	              "origini (COOP+COEP+CORP, SPECIFICHE.md §11.5)",
	              indirizzo, porta, file_html, p->nhtml);
	return p;
}

void pagina_chiudi(pagina *p)
{
	if (!p)
		return;
	for (size_t i = 0; i < MAX_CLIENTI; i++)
		if (p->clienti[i].fd >= 0)
			cliente_chiudi(&p->clienti[i]);
	free(p->html);
	if (p->fd >= 0)
		close(p->fd);
	free(p);
}
