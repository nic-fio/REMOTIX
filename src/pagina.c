/*
 * pagina.c — see pagina.h.
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

/* ⛔ THE TWO CROSS-ORIGIN ISOLATION HEADERS, PLUS THE THIRD THEY IMPLY.
 *
 *    `SPECIFICHE.md` §11.5 makes them a PRODUCT constraint: without them, on
 *    Firefox and Safari the page's timers fall on a 1 ms grid — against a
 *    ceiling of 50 (`STUDI.md` §web §6.3, P6) — and shared memory does not exist.
 *
 * ⚠ And they go on EVERY response, not only on the page: this is what «changes
 *   how the server serves every resource» means in bytes. */
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
	/* ⚠ Which event OpenSSL is waiting for: without this the wrong event is
	 *   watched and the connection stays stuck until something else
	 *   expires. */
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
		registro_dice(REG_PAGINA, "⛔ cannot open %s: %s", percorso,
		              strerror(errno));
		return NULL;
	}
	fseek(f, 0, SEEK_END);
	n = ftell(f);
	fseek(f, 0, SEEK_SET);
	if (n <= 0) {
		fclose(f);
		registro_dice(REG_PAGINA, "⛔ %s is empty", percorso);
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
		registro_dice(REG_PAGINA, "⛔ %s cannot be read in full", percorso);
		return NULL;
	}
	d[n] = 0;
	fclose(f);
	*quanto = (size_t)n;
	return d;
}

/* Replaces every occurrence of `segno` with `valore`.  Returns a new string,
 * to be freed. */
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
	/* ⛔⭐ ONE THOUSAND AND NOT TWO HUNDRED FIFTY-SIX — 17 Aug 2026, and the reason
	 *     is a measurement that LIED.  The page's diary (`/diario?…`) travels
	 *     in the query string, percent-encoded: 250 bytes of target are fewer
	 *     than 150 real characters, and as soon as the line also carried the
	 *     video counts it reached the log CUT IN HALF — «… buchi%» — without
	 *     anything saying so.  ⚠ The missing number looks the same as the
	 *     number that is zero.
	 * ⛔ And BOTH GROW, or nothing grows: the target is a COPY of `percorso`
	 *    taken before the cut at `?` (line below), so the real ceiling is set
	 *    by `percorso`.  ⚠ Widening `bersaglio` alone would have been a cure
	 *    that does not cure, with the air of having done it. */
	char metodo[16] = {0}, percorso[1024] = {0}, bersaglio[1024] = {0};
	const char *sp1, *sp2;
	char indirizzo[64];
	uint64_t restano = 0;
	bool bannato;

	sp1 = memchr(c->richiesta, ' ', c->nrichiesta);
	if (!sp1) {
		componi(c, "400 Bad Request", "text/plain; charset=utf-8",
		        "request is unreadable\n", 22, NULL);
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
		        "request is unreadable\n", 22, NULL);
		return;
	}
	{
		size_t n = (size_t)(sp2 - sp1 - 1);
		if (n >= sizeof percorso)
			n = sizeof percorso - 1;
		memcpy(percorso, sp1 + 1, n);
	}

	/* ⛔⭐ THE REQUEST TARGET IS NOT THE PATH — defect B-20,
	 *     measured on 13 Aug 2026.
	 *
	 * `[M]` Before this line the comparison below was
	 * `strcmp(percorso, "/")` on the WHOLE target, query string included:
	 * `GET /` gave **200 on 166107 bytes** and `GET /?video=worker` gave
	 * **404 on 9 bytes**.  RFC 9110 §4.1 says the opposite — the query string
	 * is a component of the URI in its own right, not a piece of the path, and
	 * whoever decides what to serve looks at the path.
	 *
	 * ⛔ AND THE REAL CONSEQUENCE IS NOT THE WORKER, it is that `pagina.html`
	 *    has always documented TWO switches turned on from the query string —
	 *    `?tela=desincronizzata` (§6.1 of `STUDI.md` §web) and
	 *    `?video=worker` — and **neither of them was ever reachable through
	 *    the product**: the comment pointed to a road the server closed with
	 *    a 404.  ⚠ Nobody had noticed because the benches serve the page from
	 *    a Python `http.server`, which ignores the `?` — that is, the defect
	 *    lived EXACTLY in the gap between the bench and the product.
	 *
	 * ⭐ The cure cuts, and cuts ONLY at the `?` (and the `#`, should it ever
	 *    arrive: a browser does not send the fragment, but any client can send
	 *    it, and then the path stays the path).  ⛔ The check is NOT loosened:
	 *    `/inesistente?x=1` keeps giving 404 like `/inesistente`, because what
	 *    changes is which string is compared, not the comparison.  ⚠ And if
	 *    the target were so long that it did not fit in `percorso`, the
	 *    truncation above takes the `?` away too: the result is a path that
	 *    matches nothing, that is 404 — the prudent outcome, not a hole.
	 *
	 * ⚠ AND THE WHOLE TARGET GOES INTO THE LOG, not the cut path: after this
	 *   cure the switches really turn on, and a log that wrote `/` for
	 *   `/?tela=desincronizzata` would make invisible precisely the only thing
	 *   this line has just made possible. */
	/* ⚠ The size is dictated by the SOURCE: this way the line holds even on
	 *   the day the two arrays were no longer the same length. */
	memcpy(bersaglio, percorso, sizeof percorso - 1);
	percorso[strcspn(percorso, "?#")] = 0;

	/* ⛔ The ban key is made by `rcp.c`, not by this file: `rcp.h` says so with
	 *    a ⛔, and the reason is that the key format is known by one module
	 *    only.  ⚠ Whoever built it on their own would look for `192.168.0.2`
	 *    where `[192.168.0.2]` is written, and the page would say «you are not
	 *    banned» to someone who is — that is, precisely to whom §4.2 wants to
	 *    see the sentence. */
	rcp_chiave_indirizzo(c->provenienza, indirizzo, sizeof indirizzo);
	bannato = rcp_bannato(indirizzo, registro_ora_ms(), &restano);

	registro_dice(REG_PAGINA, "%s %s from %s%s", metodo, bersaglio, c->provenienza,
	              bannato ? " (address BANNED)" : "");

	/* ⛔ THE ENDPOINT FROM WHICH THE PAGE FETCHES THE UPDATED FINGERPRINT (§4.1-bis).
	 *
	 *    «A tab left open for two weeks holds the fingerprint of a
	 *    certificate that has been rotated in the meantime: on reconnection
	 *    the browser refuses, and the symptom is *it no longer connects and
	 *    does not say why*.»  Of the two cures, this is the one chosen:
	 *    reloading the page works and throws the state away.
	 *
	 * ⛔ And it does not go through RCP: the session is not open yet, so
	 *    there is no channel on which to ask.  It is fetched from the server
	 *    that served it, with an ordinary request. */
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

	/* ⛔⭐ THE PAGE'S DIARY — where the CLIENT's numbers become readable.
	 *
	 *      `[M]` 17 Aug 2026, and it comes from a defect of my own method: for
	 *      four cures in a row I chased the audio jitter having the numbers of
	 *      **three links out of four** — the child says how many blocks it
	 *      produces, the server how many it sends, and **nothing was known
	 *      about the page**: how many arrive, how many get played, how many
	 *      holes the playback makes.
	 *
	 * ⛔ And the page's diagnostics panel was not enough: when the desktop is
	 *    on the page is full screen and that panel **is not reachable**.
	 *    ⇒ Asking the user to read it was asking them something that cannot
	 *    be done.
	 *
	 * ⚠ It is a DIAGNOSTIC endpoint, not a protocol one: it does not open a
	 *   session, does not touch state, and what it writes ends up in the log
	 *   like any other line.  ⛔ The body is truncated and cleaned before
	 *   writing it: it comes from outside, so it is an input, not a datum. */
	if (strcmp(percorso, "/diario") == 0) {
		/* ⚠ SHORTER than `bersaglio` on purpose: this way the ceiling hit
		 *   first is this one, which can say so — and not the one over there,
		 *   which truncates silently. */
		char pulito[900];
		size_t j = 0;
		/* ⚠ The text arrives in the QUERY STRING, not in a body: this server
		 *   does not read requests beyond the first line, and a `GET` with
		 *   the query is what the page can send without anyone adding a body
		 *   reader.  ⛔ `bersaglio` is the whole line as it arrived: the `?`
		 *   is skipped by hand. */
		const char *b = strchr(bersaglio, '?');
		b = b ? b + 1 : "";
		for (size_t i = 0; b[i] && j + 1 < sizeof pulito; i++) {
			unsigned char x = (unsigned char)b[i];
			/* Printable ASCII only: a log line must not be able to carry a
			 * newline (it would split the log in two) nor control bytes. */
			pulito[j++] = (x >= 0x20 && x < 0x7F) ? (char)x : ' ';
		}
		pulito[j] = '\0';
		/* ⛔ AND A CUT IS DECLARED.  A line cut silently looks like a short
		 *    line, and whoever reads it counts the numbers that are there
		 *    instead of noticing the ones that are missing. */
		registro_dice(REG_PAGINA, "📄 the page of %s says: %s%s",
		              c->provenienza, pulito,
		              j + 1 >= sizeof pulito ? "  ⛔CUT HERE" : "");
		componi(c, "204 No Content", "text/plain; charset=utf-8", "", 0, NULL);
		return;
	}

	if (strcmp(percorso, "/") != 0 && strcmp(percorso, "/index.html") != 0) {
		componi(c, "404 Not Found", "text/plain; charset=utf-8",
		        "not here\n", 9, NULL);
		return;
	}

	/* ⛔⭐ THE BAN NOTICE — §4.4-bis, and the two findings this part paid
	 *     for on the night of 10 Aug 2026.
	 *
	 * ⛔ **B-9**: the sentence contained `l'indirizzo`, that is a
	 *    **JavaScript** escape for the apostrophe, and it was substituted in TWO
	 *    places of the page with two different syntaxes — inside a JS string
	 *    and inside a `<div>`.  In the JS string the escape became an
	 *    apostrophe; in the `<div>` it did not, because HTML does not know
	 *    `\uXXXX` escapes.  The banned owner — the one for whom §4.4-bis
	 *    wrote three normative points — read on the screen, literally,
	 *    «sblocca l'indirizzo dal server» (the Italian page of the time:
	 *    «unblock the address from the server»).
	 *    ⚠ And there was no text right for both: the cure was to separate the
	 *      two markers, not to fix the sentence.  ⛔ And there was the worse
	 *      harm: the text ended up **inside a JS string** without any
	 *      neutralisation — today it is fixed and contains no quotes, the day
	 *      a datum we do not decide ended up there that line is an injection.
	 *
	 * ⭐ The cure: the sentence lives ONLY in the HTML, and the JavaScript no
	 *    longer receives any text — it reads `data-bannato` from the `<body>`.
	 *    A datum that does not enter a program cannot break it.
	 *
	 * ⛔ **R12.2**: the meter of §4.4-bis (`banchi/01-b8-cronometro.py`)
	 *    searches the document for `data-bannato`, `data-restano-ms`, the
	 *    substring «tentativi esauriti» and the `id="ore"`/`id="minuti"`.  This
	 *    page had NONE of them: pointed at this server, the bench would have
	 *    given three reds **on a server that does ban**, and the red would
	 *    have landed on the wrong defendant.  ⚠ The names are not the bench's:
	 *    they are the form in which the other half of the project already
	 *    wrote the same thing, and having two would be form E2 of `REVIEWER.md`.
	 *
	 * ⚠ And the minutes are rounded UP, as in the graft: saying «0 hours
	 *   left» to someone who still has 59 minutes to wait is worse than saying
	 *   nothing. */
	{
		char *a, *b, *cc, *d;
		/* ⚠ 640 and not 320: the whole sentence plus the two numbers must fit
		 *   in ENTIRELY.  `[M]` night of 10 Aug 2026 — with 320 the compiler
		 *   said «directive output truncated writing 227 bytes into a
		 *   region of size between 131 and 144», and what the banned user
		 *   would have read would have ended mid-sentence.  A truncated notice
		 *   is worse than no notice: §4.4-bis wants it to be UNDERSTOOD. */
		char avviso[640] = "";
		char restano_txt[32];
		unsigned long long minuti = (restano + 59999u) / 60000u;

		if (bannato) {
			/* ⛔ §4.4-bis: «the page loads anyway and shows the refusal —
			 *    attempts exhausted.  Not a network error, not a silence:
			 *    whoever is banned by mistake is almost always the owner,
			 *    and must be able to understand what happened to them.» */
			snprintf(avviso, sizeof avviso,
			         /* ⚠ No `id` on this `<b>`: the page already has an
			          * `id="esito"` and two elements with the same `id`
			          * would make `getElementById` take the wrong one —
			          * that is, the connection outcome would appear
			          * inside the ban notice. */
			         "<b>attempts exhausted</b>: three failed login "
			         "attempts came from this address, and for this "
			         "reason it stays out. There are still "
			         "<b id=\"ore\">%llu</b> hours and "
			         "<b id=\"minuti\">%llu</b> minutes to go. There are two "
			         "ways back in: waiting for the expiry, or with the "
			         "unblock command on the serving machine — which requires "
			         "access to that machine, and is the way for whoever "
			         "banned themselves from their own phone.",
			         minuti / 60, minuti % 60);
		}
		snprintf(restano_txt, sizeof restano_txt, "%llu",
		         (unsigned long long)restano);

		a = sostituisci(p->html, "__IMPRONTA__", p->cert->impronta);
		if (!a) {
			componi(c, "500 Internal Server Error",
			        "text/plain; charset=utf-8", "no mem.\n", 8, NULL);
			return;
		}
		b = sostituisci(a, "__AVVISO__", avviso);
		free(a);
		if (!b) {
			componi(c, "500 Internal Server Error",
			        "text/plain; charset=utf-8", "no mem.\n", 8, NULL);
			return;
		}
		cc = sostituisci(b, "__BANNATO__", bannato ? "si" : "no");
		free(b);
		if (!cc) {
			componi(c, "500 Internal Server Error",
			        "text/plain; charset=utf-8", "no mem.\n", 8, NULL);
			return;
		}
		d = sostituisci(cc, "__RESTANO_MS__", restano_txt);
		free(cc);
		if (!d) {
			componi(c, "500 Internal Server Error",
			        "text/plain; charset=utf-8", "no mem.\n", 8, NULL);
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
			/* ⚠ A failed TLS handshake is the most common thing that
			 *   happens to this listener: it is the user who has NOT yet
			 *   granted the exception on the long-lived certificate
			 *   (`RCP.md` §4.1).  It is said in a low voice, or the log
			 *   becomes unreadable at every load. */
			registro_dettaglio(REG_PAGINA,
			                   "TLS handshake failed with %s (error %d) "
			                   "— usually it is the warning about the certificate "
			                   "not yet accepted",
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
				/* ⛔ The length is checked before allocating, and it is
				 *    the same rule of `RCP.md` §6.1 applied to HTTP. */
				componi(c, "431 Request Header Fields Too Large",
				        "text/plain; charset=utf-8", "request headers too "
				                                     "long.\n",
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
			/* ⛔ It is said.  A silent refusal would be indistinguishable
			 *    from a dead server — and whoever is outside sees the same
			 *    face in both cases (`LEZIONI.md` §1.9). */
			registro_dice(REG_PAGINA,
			              "⛔ already %d TCP connections: the new one is refused",
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
		registro_dice(REG_PAGINA, "⛔ %s:%s does not resolve", indirizzo, porta);
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
		registro_dice(REG_PAGINA, "⛔ cannot bind to %s:%s over TCP: %s", indirizzo,
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
	/* ⛔ The positive check of the marker: if the page does NOT contain
	 *    `__IMPRONTA__`, the substitution would succeed «doing nothing» and
	 *    the server would serve forever a page without a fingerprint — with
	 *    the symptom «WebTransport does not connect» and no error naming the
	 *    fingerprint (`LEZIONI.md` §1.9: a tool that finds nothing is not
	 *    clean, it is uncertified). */
	/* ⛔ AND THE MARKERS ARE FOUR, not one — night of 10 Aug 2026, finding
	 *    R12.2.  `__BANNATO__` and `__RESTANO_MS__` are what the meter of
	 *    §4.4-bis reads to say whether the ban is there and for how long: a
	 *    page without those markers would be served perfectly well, and the
	 *    bench would say «the ban did not trigger» on a server that does ban.
	 *    ⚠ A substitution that «succeeds doing nothing» is the seventh guise
	 *    of `LEZIONI.md` §1.9, and it holds for all four. */
	{
		static const char *const SEGNI[] = {"__IMPRONTA__", "__AVVISO__",
		                                    "__BANNATO__", "__RESTANO_MS__",
		                                    NULL};
		for (int i = 0; SEGNI[i]; i++)
			if (!strstr(p->html, SEGNI[i])) {
				registro_dice(REG_PAGINA,
				              "⛔ %s does not contain the marker %s: the page "
				              "would serve an answer that is not there — and a "
				              "substitution that succeeds doing nothing would "
				              "not tell anyone.  Not starting.",
				              file_html, SEGNI[i]);
				pagina_chiudi(p);
				return NULL;
			}
	}

	/* ⛔⭐ AND EACH OF THE TWO ATTRIBUTES MUST APPEAR ONLY ONCE.
	 *
	 *     `[M]` night of 10 Aug 2026, and I did it myself while curing R12.2:
	 *     the style sheet said `#avviso { display:none }` under an attribute
	 *     selector on `data-bannato`, and that selector puts the string
	 *     `data-bannato=«si»` INSIDE the `<style>`, that is BEFORE the `<body>`.
	 *     ⛔ Whoever reads the document with a search — and that is what the
	 *     meter of §4.4-bis does — takes the FIRST occurrence: it read
	 *     «banned» on a free address.  ⚠ The page was right, the measurement
	 *     was not, and the red would have landed on the wrong defendant.
	 *
	 * ⭐ The cure lives in the PROGRAM and not in a comment (invariant I7): the
	 *    second occurrence cannot be introduced without the server refusing to
	 *    start — not even inside a comment, which is bytes served to the
	 *    browser as much as the rest. */
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
				              "⛔ %s contains «%s» %d times instead of only "
				              "once: whoever reads the document searching for that "
				              "string would take the wrong occurrence and "
				              "would measure nobody's ban (§4.4-bis).  "
				              "Not starting.",
				              file_html, UNICI[i], quante);
				pagina_chiudi(p);
				return NULL;
			}
		}
	}

	registro_dice(REG_PAGINA,
	              "listening over TCP on %s:%s — page %s (%zu bytes), cross-origin "
	              "isolated (COOP+COEP+CORP, SPECIFICHE.md §11.5)",
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
