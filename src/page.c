/*
 * page.c — see page.h.
 */
#include "page.h"

#include "rcp.h"
#include "log.h"

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

#define MAX_CLIENTS 32
#define MAX_REQUEST 8192

/* ⛔ THE TWO CROSS-ORIGIN ISOLATION HEADERS, PLUS THE THIRD THEY IMPLY.
 *
 *    `SPECS.md` §11.5 makes them a PRODUCT constraint: without them, on
 *    Firefox and Safari the page's timers fall on a 1 ms grid — against a
 *    ceiling of 50 (`STUDIES.md` §web §6.3, P6) — and shared memory does not exist.
 *
 * ⚠ And they go on EVERY response, not only on the page: this is what «changes
 *   how the server serves every resource» means in bytes. */
#define ISOLATION                                                             \
	"Cross-Origin-Opener-Policy: same-origin\r\n"                              \
	"Cross-Origin-Embedder-Policy: require-corp\r\n"                           \
	"Cross-Origin-Resource-Policy: same-origin\r\n"

enum phase { F_HANDSHAKE, F_READ, F_WRITE, F_DONE };

typedef struct {
	int fd;
	SSL *ssl;
	enum phase phase;
	char request[MAX_REQUEST];
	size_t nrequest;
	char *response;
	size_t nresponse, oresponse;
	char provenance[80];
	/* ⚠ Which event OpenSSL is waiting for: without this the wrong event is
	 *   watched and the connection stays stuck until something else
	 *   expires. */
	bool wants_to_write;
} client;

struct page {
	int fd;
	SSL_CTX *ctx;
	const certificates *cert;
	char *html;
	size_t nhtml;
	client clients[MAX_CLIENTS];
};

/* ------------------------------------------------------------------------ */

static char *read_file(const char *fpath, size_t *how_much)
{
	FILE *f = fopen(fpath, "rb");
	char *d;
	long n;
	if (!f) {
		registro_dice(LOG_PAGE, "⛔ cannot open %s: %s", fpath,
		              strerror(errno));
		return NULL;
	}
	fseek(f, 0, SEEK_END);
	n = ftell(f);
	fseek(f, 0, SEEK_SET);
	if (n <= 0) {
		fclose(f);
		registro_dice(LOG_PAGE, "⛔ %s is empty", fpath);
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
		registro_dice(LOG_PAGE, "⛔ %s cannot be read in full", fpath);
		return NULL;
	}
	d[n] = 0;
	fclose(f);
	*how_much = (size_t)n;
	return d;
}

/* Replaces every occurrence of `sign` with `value`.  Returns a new string,
 * to be freed. */
static char *replace(const char *text, const char *sign, const char *value)
{
	size_t ls = strlen(sign), lv = strlen(value), cap, o = 0;
	const char *p = text;
	char *report;

	cap = strlen(text) + 1;
	for (const char *q = strstr(text, sign); q; q = strstr(q + ls, sign))
		cap += lv;
	report = malloc(cap);
	if (!report)
		return NULL;
	for (;;) {
		const char *q = strstr(p, sign);
		if (!q) {
			size_t r = strlen(p);
			memcpy(report + o, p, r + 1);
			return report;
		}
		memcpy(report + o, p, (size_t)(q - p));
		o += (size_t)(q - p);
		memcpy(report + o, value, lv);
		o += lv;
		p = q + ls;
	}
}

/* ------------------------------------------------------------------------ */

static void client_close(client *c)
{
	if (c->ssl) {
		SSL_free(c->ssl);
		c->ssl = NULL;
	}
	if (c->fd >= 0) {
		close(c->fd);
		c->fd = -1;
	}
	free(c->response);
	c->response = NULL;
	c->nresponse = c->oresponse = c->nrequest = 0;
	c->phase = F_DONE;
}

static void compose(client *c, const char *state, const char *kind,
                    const char *body, size_t nbody, const char *extra)
{
	char head[768];
	int n;

	n = snprintf(head, sizeof head,
	             "HTTP/1.1 %s\r\n"
	             "Content-Type: %s\r\n"
	             "Content-Length: %zu\r\n"
	             ISOLATION
	             "Cache-Control: no-store\r\n"
	             "X-Content-Type-Options: nosniff\r\n"
	             "Connection: close\r\n"
	             "%s"
	             "\r\n",
	             state, kind, nbody, extra ? extra : "");
	if (n < 0)
		return;
	c->response = malloc((size_t)n + nbody);
	if (!c->response)
		return;
	memcpy(c->response, head, (size_t)n);
	memcpy(c->response + n, body, nbody);
	c->nresponse = (size_t)n + nbody;
	c->oresponse = 0;
	c->phase = F_WRITE;
}

static void serve(page *p, client *c)
{
	/* ⛔⭐ ONE THOUSAND AND NOT TWO HUNDRED FIFTY-SIX — 17 Aug 2026, and the reason
	 *     is a measurement that LIED.  The page's diary (`/diary?…`) travels
	 *     in the query string, percent-encoded: 250 bytes of target are fewer
	 *     than 150 real characters, and as soon as the line also carried the
	 *     video counts it reached the log CUT IN HALF — «… holes%» — without
	 *     anything saying so.  ⚠ The missing number looks the same as the
	 *     number that is zero.
	 * ⛔ And BOTH GROW, or nothing grows: the target is a COPY of `fpath`
	 *    taken before the cut at `?` (line below), so the real ceiling is set
	 *    by `fpath`.  ⚠ Widening `target` alone would have been a cure
	 *    that does not cure, with the air of having done it. */
	char method[16] = {0}, fpath[1024] = {0}, target[1024] = {0};
	const char *sp1, *sp2;
	char address[64];
	uint64_t remain = 0;
	bool banned;

	sp1 = memchr(c->request, ' ', c->nrequest);
	if (!sp1) {
		compose(c, "400 Bad Request", "text/plain; charset=utf-8",
		        "request is unreadable\n", 22, NULL);
		return;
	}
	{
		size_t n = (size_t)(sp1 - c->request);
		if (n >= sizeof method)
			n = sizeof method - 1;
		memcpy(method, c->request, n);
	}
	sp2 = memchr(sp1 + 1, ' ', c->nrequest - (size_t)(sp1 + 1 - c->request));
	if (!sp2) {
		compose(c, "400 Bad Request", "text/plain; charset=utf-8",
		        "request is unreadable\n", 22, NULL);
		return;
	}
	{
		size_t n = (size_t)(sp2 - sp1 - 1);
		if (n >= sizeof fpath)
			n = sizeof fpath - 1;
		memcpy(fpath, sp1 + 1, n);
	}

	/* ⛔⭐ THE REQUEST TARGET IS NOT THE PATH — defect B-20,
	 *     measured on 13 Aug 2026.
	 *
	 * `[M]` Before this line the comparison below was
	 * `strcmp(fpath, "/")` on the WHOLE target, query string included:
	 * `GET /` gave **200 on 166107 bytes** and `GET /?video=worker` gave
	 * **404 on 9 bytes**.  RFC 9110 §4.1 says the opposite — the query string
	 * is a component of the URI in its own right, not a piece of the path, and
	 * whoever decides what to needs looks at the path.
	 *
	 * ⛔ AND THE REAL CONSEQUENCE IS NOT THE WORKER, it is that `page.html`
	 *    has always documented TWO switches turned on from the query string —
	 *    `?canvas=desincronizzata` (§6.1 of `STUDIES.md` §web) and
	 *    `?video=worker` — and **neither of them was ever reachable through
	 *    the product**: the comment pointed to a road the server closed with
	 *    a 404.  ⚠ Nobody had noticed because the benches needs the page from
	 *    a Python `http.server`, which ignores the `?` — that is, the defect
	 *    lived EXACTLY in the gap between the bench and the product.
	 *
	 * ⭐ The cure cuts, and cuts ONLY at the `?` (and the `#`, should it ever
	 *    arrive: a browser does not send the fragment, but any client can send
	 *    it, and then the path stays the path).  ⛔ The check is NOT loosened:
	 *    `/nonexistent?x=1` keeps giving 404 like `/nonexistent`, because what
	 *    changes is which string is compared, not the comparison.  ⚠ And if
	 *    the target were so long that it did not fit in `fpath`, the
	 *    truncation above takes the `?` away too: the result is a path that
	 *    matches nothing, that is 404 — the prudent outcome, not a hole.
	 *
	 * ⚠ AND THE WHOLE TARGET GOES INTO THE LOG, not the cut path: after this
	 *   cure the switches really turn on, and a log that wrote `/` for
	 *   `/?canvas=desincronizzata` would make invisible precisely the only thing
	 *   this line has just made possible. */
	/* ⚠ The size is dictated by the SOURCE: this way the line holds even on
	 *   the day the two arrays were no longer the same length. */
	memcpy(target, fpath, sizeof fpath - 1);
	fpath[strcspn(fpath, "?#")] = 0;

	/* ⛔ The ban key is made by `rcp.c`, not by this file: `rcp.h` says so with
	 *    a ⛔, and the reason is that the key format is known by one module
	 *    only.  ⚠ Whoever built it on their own would look for `192.168.0.2`
	 *    where `[192.168.0.2]` is written, and the page would say «you are not
	 *    banned» to someone who is — that is, precisely to whom §4.2 wants to
	 *    see the sentence. */
	rcp_key_address(c->provenance, address, sizeof address);
	banned = rcp_banned(address, log_now_ms(), &remain);

	registro_dice(LOG_PAGE, "%s %s from %s%s", method, target, c->provenance,
	              banned ? " (address BANNED)" : "");

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
	if (strcmp(fpath, "/fingerprint") == 0) {
		char body[512];
		int n = snprintf(body, sizeof body,
		                 "{\"algorithm\":\"sha-256\",\"fingerprint\":\"%s\","
		                 "\"hex\":\"%s\",\"rotations\":%u}\n",
		                 p->cert->fingerprint, p->cert->fingerprint_hex,
		                 p->cert->rotations);
		compose(c, "200 OK", "application/json; charset=utf-8", body,
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
	if (strcmp(fpath, "/diary") == 0) {
		/* ⚠ SHORTER than `target` on purpose: this way the ceiling hit
		 *   first is this one, which can say so — and not the one over there,
		 *   which truncates silently. */
		char clean[900];
		size_t j = 0;
		/* ⚠ The text arrives in the QUERY STRING, not in a body: this server
		 *   does not read requests beyond the first line, and a `GET` with
		 *   the query is what the page can send without anyone adding a body
		 *   reader.  ⛔ `target` is the whole line as it arrived: the `?`
		 *   is skipped by hand. */
		const char *b = strchr(target, '?');
		b = b ? b + 1 : "";
		for (size_t i = 0; b[i] && j + 1 < sizeof clean; i++) {
			unsigned char x = (unsigned char)b[i];
			/* Printable ASCII only: a log line must not be able to carry a
			 * newline (it would split the log in two) nor control bytes. */
			clean[j++] = (x >= 0x20 && x < 0x7F) ? (char)x : ' ';
		}
		clean[j] = '\0';
		/* ⛔ AND A CUT IS DECLARED.  A line cut silently looks like a short
		 *    line, and whoever reads it counts the numbers that are there
		 *    instead of noticing the ones that are missing. */
		registro_dice(LOG_PAGE, "📄 the page of %s says: %s%s",
		              c->provenance, clean,
		              j + 1 >= sizeof clean ? "  ⛔CUT HERE" : "");
		compose(c, "204 No Content", "text/plain; charset=utf-8", "", 0, NULL);
		return;
	}

	if (strcmp(fpath, "/") != 0 && strcmp(fpath, "/index.html") != 0) {
		compose(c, "404 Not Found", "text/plain; charset=utf-8",
		        "not here\n", 9, NULL);
		return;
	}

	/* ⛔⭐ THE BAN NOTICE — §4.4-bis, and the two findings this part paid
	 *     for on the night of 10 Aug 2026.
	 *
	 * ⛔ **B-9**: the sentence contained `l'address`, that is a
	 *    **JavaScript** escape for the apostrophe, and it was substituted in TWO
	 *    places of the page with two different syntaxes — inside a JS string
	 *    and inside a `<div>`.  In the JS string the escape became an
	 *    apostrophe; in the `<div>` it did not, because HTML does not know
	 *    `\uXXXX` escapes.  The banned owner — the one for whom §4.4-bis
	 *    wrote three normative points — read on the screen, literally,
	 *    «unblock l'address from_ server» (the Italian page of the time:
	 *    «unblock the address from the server»).
	 *    ⚠ And there was no text right for both: the cure was to separate the
	 *      two markers, not to fix the sentence.  ⛔ And there was the worse
	 *      harm: the text ended up **inside a JS string** without any
	 *      neutralisation — today it is fixed and contains no quotes, the day
	 *      a datum we do not decide ended up there that line is an injection.
	 *
	 * ⭐ The cure: the sentence lives ONLY in the HTML, and the JavaScript no
	 *    longer receives any text — it reads `data-banned` from the `<body>`.
	 *    A datum that does not enter a program cannot break it.
	 *
	 * ⛔ **R12.2**: the meter of §4.4-bis (`benches/01-b8-stopwatch.py`)
	 *    searches the document for `data-banned`, `data-remaining-ms`, the
	 *    substring «attempts esauriti» and the `id="hours"`/`id="minutes"`.  This
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
		char warning[640] = "";
		char remain_txt[32];
		unsigned long long minutes = (remain + 59999u) / 60000u;

		if (banned) {
			/* ⛔ §4.4-bis: «the page loads anyway and shows the refusal —
			 *    attempts exhausted.  Not a network error, not a silence:
			 *    whoever is banned by mistake is almost always the owner,
			 *    and must be able to understand what happened to them.» */
			snprintf(warning, sizeof warning,
			         /* ⚠ No `id` on this `<b>`: the page already has an
			          * `id="outcome"` and two elements with the same `id`
			          * would make `getElementById` take the wrong one —
			          * that is, the connection outcome would appear
			          * inside the ban notice. */
			         "<b>attempts exhausted</b>: three failed login "
			         "attempts came from this address, and for this "
			         "reason it stays out. There are still "
			         "<b id=\"hours\">%llu</b> hours and "
			         "<b id=\"minutes\">%llu</b> minutes to go. There are two "
			         "ways back in: waiting for the expiry, or with the "
			         "unblock command on the serving machine — which requires "
			         "access to that machine, and is the way for whoever "
			         "banned themselves from their own phone.",
			         minutes / 60, minutes % 60);
		}
		snprintf(remain_txt, sizeof remain_txt, "%llu",
		         (unsigned long long)remain);

		a = replace(p->html, "__FINGERPRINT__", p->cert->fingerprint);
		if (!a) {
			compose(c, "500 Internal Server Error",
			        "text/plain; charset=utf-8", "no mem.\n", 8, NULL);
			return;
		}
		b = replace(a, "__WARNING__", warning);
		free(a);
		if (!b) {
			compose(c, "500 Internal Server Error",
			        "text/plain; charset=utf-8", "no mem.\n", 8, NULL);
			return;
		}
		cc = replace(b, "__BANNED__", banned ? "yes" : "no");
		free(b);
		if (!cc) {
			compose(c, "500 Internal Server Error",
			        "text/plain; charset=utf-8", "no mem.\n", 8, NULL);
			return;
		}
		d = replace(cc, "__REMAINING_MS__", remain_txt);
		free(cc);
		if (!d) {
			compose(c, "500 Internal Server Error",
			        "text/plain; charset=utf-8", "no mem.\n", 8, NULL);
			return;
		}
		compose(c, "200 OK", "text/html; charset=utf-8", d, strlen(d), NULL);
		free(d);
	}
}

/* ------------------------------------------------------------------------ */

static void move_client(page *p, client *c, short events)
{
	int rv;

	(void)events;
	c->wants_to_write = false;

	if (c->phase == F_HANDSHAKE) {
		rv = SSL_accept(c->ssl);
		if (rv == 1) {
			c->phase = F_READ;
		} else {
			int e = SSL_get_error(c->ssl, rv);
			if (e == SSL_ERROR_WANT_WRITE) {
				c->wants_to_write = true;
				return;
			}
			if (e == SSL_ERROR_WANT_READ)
				return;
			/* ⚠ A failed TLS handshake is the most common thing that
			 *   happens to this listener: it is the user who has NOT yet
			 *   granted the exception on the long-lived certificate
			 *   (`RCP.md` §4.1).  It is said in a low voice, or the log
			 *   becomes unreadable at every load. */
			log_detail(LOG_PAGE,
			                   "TLS handshake failed with %s (error %d) "
			                   "— usually it is the warning about the certificate "
			                   "not yet accepted",
			                   c->provenance, e);
			ERR_clear_error();
			client_close(c);
			return;
		}
	}

	if (c->phase == F_READ) {
		for (;;) {
			size_t readings = 0;
			rv = SSL_read_ex(c->ssl, c->request + c->nrequest,
			                 sizeof c->request - c->nrequest - 1, &readings);
			if (rv != 1) {
				int e = SSL_get_error(c->ssl, rv);
				if (e == SSL_ERROR_WANT_WRITE)
					c->wants_to_write = true;
				if (e == SSL_ERROR_WANT_READ || e == SSL_ERROR_WANT_WRITE)
					return;
				client_close(c);
				return;
			}
			c->nrequest += readings;
			c->request[c->nrequest] = 0;
			if (strstr(c->request, "\r\n\r\n") ||
			    strstr(c->request, "\n\n")) {
				serve(p, c);
				break;
			}
			if (c->nrequest + 1 >= sizeof c->request) {
				/* ⛔ The length is checked before allocating, and it is
				 *    the same rule of `RCP.md` §6.1 applied to HTTP. */
				compose(c, "431 Request Header Fields Too Large",
				        "text/plain; charset=utf-8", "request headers too "
				                                     "long.\n",
				        26, NULL);
				break;
			}
		}
	}

	if (c->phase == F_WRITE) {
		while (c->oresponse < c->nresponse) {
			size_t written = 0;
			rv = SSL_write_ex(c->ssl, c->response + c->oresponse,
			                  c->nresponse - c->oresponse, &written);
			if (rv != 1) {
				int e = SSL_get_error(c->ssl, rv);
				if (e == SSL_ERROR_WANT_WRITE) {
					c->wants_to_write = true;
					return;
				}
				if (e == SSL_ERROR_WANT_READ)
					return;
				client_close(c);
				return;
			}
			c->oresponse += written;
		}
		SSL_shutdown(c->ssl);
		client_close(c);
	}
}

/* ------------------------------------------------------------------------ */

size_t page_descriptors(page *p, struct pollfd *dove, size_t cap)
{
	size_t n = 0;
	if (cap == 0)
		return 0;
	dove[n].fd = p->fd;
	dove[n].events = POLLIN;
	dove[n].revents = 0;
	n++;
	for (size_t i = 0; i < MAX_CLIENTS && n < cap; i++) {
		if (p->clients[i].phase == F_DONE || p->clients[i].fd < 0)
			continue;
		dove[n].fd = p->clients[i].fd;
		dove[n].events = p->clients[i].wants_to_write ? POLLOUT : POLLIN;
		dove[n].revents = 0;
		n++;
	}
	return n;
}

static void accept_page(page *p)
{
	for (;;) {
		struct sockaddr_storage da;
		socklen_t dalen = sizeof da;
		int fd;
		client *c = NULL;
		char host[NI_MAXHOST], serv[NI_MAXSERV];

		fd = accept4(p->fd, (struct sockaddr *)&da, &dalen, SOCK_NONBLOCK);
		if (fd < 0) {
			if (errno != EAGAIN && errno != EWOULDBLOCK && errno != EINTR)
				registro_dice(LOG_PAGE, "accept: %s", strerror(errno));
			return;
		}
		for (size_t i = 0; i < MAX_CLIENTS; i++)
			if (p->clients[i].phase == F_DONE && p->clients[i].fd < 0) {
				c = &p->clients[i];
				break;
			}
		if (!c) {
			/* ⛔ It is said.  A silent refusal would be indistinguishable
			 *    from a dead server — and whoever is outside sees the same
			 *    face in both cases (`LESSONS.md` §1.9). */
			registro_dice(LOG_PAGE,
			              "⛔ already %d TCP connections: the new one is refused",
			              MAX_CLIENTS);
			close(fd);
			return;
		}
		memset(c, 0, sizeof *c);
		c->fd = fd;
		if (getnameinfo((struct sockaddr *)&da, dalen, host, sizeof host, serv,
		                sizeof serv, NI_NUMERICHOST | NI_NUMERICSERV) == 0)
			snprintf(c->provenance, sizeof c->provenance,
			         da.ss_family == AF_INET6 ? "[%s]:%s" : "%s:%s", host,
			         serv);
		else
			snprintf(c->provenance, sizeof c->provenance, "?");

		c->ssl = SSL_new(p->ctx);
		if (!c->ssl) {
			close(fd);
			c->fd = -1;
			c->phase = F_DONE;
			return;
		}
		SSL_set_fd(c->ssl, fd);
		SSL_set_accept_state(c->ssl);
		c->phase = F_HANDSHAKE;
		move_client(p, c, 0);
	}
}

void page_move(page *p, struct pollfd *dove, size_t amount)
{
	for (size_t k = 0; k < amount; k++) {
		if (dove[k].revents == 0)
			continue;
		if (dove[k].fd == p->fd) {
			accept_page(p);
			continue;
		}
		for (size_t i = 0; i < MAX_CLIENTS; i++)
			if (p->clients[i].fd == dove[k].fd &&
			    p->clients[i].phase != F_DONE) {
				move_client(p, &p->clients[i], dove[k].revents);
				break;
			}
	}
}

void page_context(page *p, SSL_CTX *ctx) { p->ctx = ctx; }

/* ------------------------------------------------------------------------ */

page *page_open(const char *address, const char *port, SSL_CTX *ctx,
                    const char *file_html, const certificates *cert)
{
	struct addrinfo hints, *result = NULL, *r;
	page *p;
	int fd = -1, uno = 1;

	memset(&hints, 0, sizeof hints);
	hints.ai_family = AF_UNSPEC;
	hints.ai_socktype = SOCK_STREAM;
	hints.ai_flags = AI_PASSIVE;

	if (getaddrinfo(address, port, &hints, &result) != 0) {
		registro_dice(LOG_PAGE, "⛔ %s:%s does not resolve", address, port);
		return NULL;
	}
	for (r = result; r; r = r->ai_next) {
		fd = socket(r->ai_family, r->ai_socktype | SOCK_NONBLOCK, r->ai_protocol);
		if (fd < 0)
			continue;
		setsockopt(fd, SOL_SOCKET, SO_REUSEADDR, &uno, sizeof uno);
		if (bind(fd, r->ai_addr, r->ai_addrlen) == 0 && listen(fd, 16) == 0)
			break;
		close(fd);
		fd = -1;
	}
	freeaddrinfo(result);
	if (fd < 0) {
		registro_dice(LOG_PAGE, "⛔ cannot bind to %s:%s over TCP: %s", address,
		              port, strerror(errno));
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
	for (size_t i = 0; i < MAX_CLIENTS; i++) {
		p->clients[i].fd = -1;
		p->clients[i].phase = F_DONE;
	}

	p->html = read_file(file_html, &p->nhtml);
	if (!p->html) {
		page_close(p);
		return NULL;
	}
	/* ⛔ The positive check of the marker: if the page does NOT contain
	 *    `__FINGERPRINT__`, the substitution would succeed «doing nothing» and
	 *    the server would needs forever a page without a fingerprint — with
	 *    the symptom «WebTransport does not connect» and no error naming the
	 *    fingerprint (`LESSONS.md` §1.9: a tool that finds nothing is not
	 *    clean, it is uncertified). */
	/* ⛔ AND THE MARKERS ARE FOUR, not one — night of 10 Aug 2026, finding
	 *    R12.2.  `__BANNED__` and `__REMAINING_MS__` are what the meter of
	 *    §4.4-bis reads to say whether the ban is there and for how long: a
	 *    page without those markers would be served perfectly well, and the
	 *    bench would say «the ban did not trigger» on a server that does ban.
	 *    ⚠ A substitution that «succeeds doing nothing» is the seventh guise
	 *    of `LESSONS.md` §1.9, and it holds for all four. */
	{
		static const char *const PLACEHOLDERS[] = {"__FINGERPRINT__", "__WARNING__",
		                                    "__BANNED__", "__REMAINING_MS__",
		                                    NULL};
		for (int i = 0; PLACEHOLDERS[i]; i++)
			if (!strstr(p->html, PLACEHOLDERS[i])) {
				registro_dice(LOG_PAGE,
				              "⛔ %s does not contain the marker %s: the page "
				              "would serve an answer that is not there — and a "
				              "substitution that succeeds doing nothing would "
				              "not tell anyone.  Not starting.",
				              file_html, PLACEHOLDERS[i]);
				page_close(p);
				return NULL;
			}
	}

	/* ⛔⭐ AND EACH OF THE TWO ATTRIBUTES MUST APPEAR ONLY ONCE.
	 *
	 *     `[M]` night of 10 Aug 2026, and I did it myself while curing R12.2:
	 *     the style sheet said `#warning { display:none }` under an attribute
	 *     selector on `data-banned`, and that selector puts the string
	 *     `data-banned=«yes»` INSIDE the `<style>`, that is BEFORE the `<body>`.
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
		static const char *const UNIQUE[] = {"data-banned=\"",
		                                    "data-remaining-ms=\"", NULL};
		for (int i = 0; UNIQUE[i]; i++) {
			int how_many = 0;
			for (const char *q = strstr(p->html, UNIQUE[i]); q;
			     q = strstr(q + strlen(UNIQUE[i]), UNIQUE[i]))
				how_many++;
			if (how_many != 1) {
				registro_dice(LOG_PAGE,
				              "⛔ %s contains «%s» %d times instead of only "
				              "once: whoever reads the document searching for that "
				              "string would take the wrong occurrence and "
				              "would measure nobody's ban (§4.4-bis).  "
				              "Not starting.",
				              file_html, UNIQUE[i], how_many);
				page_close(p);
				return NULL;
			}
		}
	}

	registro_dice(LOG_PAGE,
	              "listening over TCP on %s:%s — page %s (%zu bytes), cross-origin "
	              "isolated (COOP+COEP+CORP, SPECS.md §11.5)",
	              address, port, file_html, p->nhtml);
	return p;
}

void page_close(page *p)
{
	if (!p)
		return;
	for (size_t i = 0; i < MAX_CLIENTS; i++)
		if (p->clients[i].fd >= 0)
			client_close(&p->clients[i]);
	free(p->html);
	if (p->fd >= 0)
		close(p->fd);
	free(p);
}
