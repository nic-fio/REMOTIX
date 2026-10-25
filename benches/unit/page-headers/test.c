/*
 * test.c — the security headers that src/page.c sends on EVERY answer (macro PAGE_SECURITY) are exactly the expected ones,
 * and the longest answer head still fits the buffer `char head[N]` of compose_build() with room to spare.
 *
 * WHY: the CSP is enforced by the browser, not by the server: a change to one directive (connect-src back to `'self' https:`,
 * `worker-src blob:` lost, an `'unsafe-eval'` slipped in) breaks nothing that a unit test sees and is found, if at all, by a
 * session that does not open.  This test is the guard: any change of the headers makes it fail and says which directive.
 * (What proves the CSP works is a real browser: 15-f001 / 15-f004 on Chrome and Firefox, see NOTE-rifiniture.md.)
 *
 * HOW: no linking with page.c.  The test reads the SOURCE of page.c (path in argv[1]) and rebuilds the text of PAGE_SECURITY
 * and ISOLATION from their `#define` (concatenating the string literals as the compiler does, escapes \r \n \\ \"), reads the
 * size N of `char head[N]`, and checks:
 *   1. the whole of PAGE_SECURITY equals the EXPECTED text below, byte for byte;
 *   2. the directives one by one (so the failure message names the directive): default-src 'self', connect-src 'self' with
 *      NO `https:` anywhere, worker-src blob:, media-src blob:, object-src 'none', base-uri 'none', form-action 'self',
 *      frame-ancestors 'none', script-src without 'unsafe-eval', Referrer-Policy: no-referrer, Permissions-Policy (clipboard
 *      for self, camera/microphone/geolocation/payment/usb off), every header line ends with CRLF and the text has exactly
 *      three header lines;
 *   3. the format of compose_build() is still the one this test assumes (its fixed pieces are found in the source);
 *   4. the LONGEST head is shorter than N by at least MARGIN bytes.  Its pieces are TAKEN FROM THE SOURCE, not guessed: the
 *      longest status line and the longest Content-Type among the calls of compose(), compose_with(), compose_tail() and
 *      compose_build(); the longest run of string literals written just before a PAGE_SECURITY (the gzip answer's
 *      Content-Encoding and Vary, Retry-After, ...); a 20-digit Content-Length; ISOLATION; the fixed headers.
 * If a check 1 fails on purpose (the CSP was changed on purpose), update EXPECTED here, in the same commit as the change.
 *
 * BUILD AND RUN (a second; nothing under /media/REMOTIX-15 is written; run from the root of the tree):
 *   nice -n 19 ionice -c3 podman run --rm --network=none --cpus=1 --memory=512m -v "$PWD:/albero:ro" localhost/remotix-fuzz sh -c '
 *     cd /tmp && clang -g -O1 -fsanitize=address,undefined -fno-sanitize-recover=undefined -std=gnu11 -D_GNU_SOURCE -Wall -Wextra \
 *        /albero/benches/unit/page-headers/test.c -o test && ./test /albero/src/page.c'
 * Exit code 0 = every check passed, 1 = a check failed, 2 = the source could not be read or understood.
 * (Any C compiler does: gcc -std=gnu11 -Wall -Wextra benches/unit/page-headers/test.c -o /tmp/ph && /tmp/ph src/page.c)
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MARGIN 512 /* bytes that must stay free in `head` after the longest answer */

/* The expected PAGE_SECURITY, as the browser will read it. */
static const char EXPECTED[] =
	"Content-Security-Policy: default-src 'self'; "
	"script-src 'self' 'unsafe-inline' 'wasm-unsafe-eval'; "
	"style-src 'self' 'unsafe-inline'; "
	"img-src 'self' data: blob:; media-src blob:; worker-src blob:; "
	"connect-src 'self'; font-src 'self'; "
	"object-src 'none'; base-uri 'none'; form-action 'self'; "
	"frame-ancestors 'none'\r\n"
	"Referrer-Policy: no-referrer\r\n"
	"Permissions-Policy: clipboard-read=(self), clipboard-write=(self), "
	"camera=(), microphone=(), geolocation=(), payment=(), usb=(), "
	"serial=(), hid=(), midi=(), accelerometer=(), gyroscope=(), "
	"magnetometer=(), display-capture=()\r\n";

static int checks, bad;

static void check(int ok, const char *what)
{
	checks++;
	if (!ok) {
		bad++;
		printf("FAIL  %s\n", what);
	} else {
		printf("  ok  %s\n", what);
	}
}

static char *slurp(const char *path, size_t *n)
{
	FILE *f = fopen(path, "rb");
	char *b;
	long sz;

	if (!f)
		return NULL;
	fseek(f, 0, SEEK_END);
	sz = ftell(f);
	fseek(f, 0, SEEK_SET);
	b = malloc((size_t)sz + 1);
	if (!b || fread(b, 1, (size_t)sz, f) != (size_t)sz) {
		fclose(f);
		free(b);
		return NULL;
	}
	fclose(f);
	b[sz] = 0;
	*n = (size_t)sz;
	return b;
}

/* The text of `#define NAME` (continued by backslash-newline): the concatenation of its string literals. NULL if not found. */
static char *macro_text(const char *src, const char *name)
{
	char key[96];
	const char *p = src, *q;
	char *out;
	size_t o = 0;

	snprintf(key, sizeof key, "#define %s", name);
	for (;;) {
		p = strstr(p, key);
		if (!p)
			return NULL;
		if (p == src || p[-1] == '\n') {
			const char *e = p + strlen(key);

			if (*e == ' ' || *e == '\t' || *e == '\\')
				break;
		}
		p += strlen(key);
	}
	q = p + strlen(key);
	out = malloc(strlen(q) + 1);
	if (!out)
		return NULL;
	for (;;) {
		char c = *q;

		if (!c)
			break;
		if (c == '\n') {
			if (q > p && q[-1] == '\\') { /* continued */
				q++;
				continue;
			}
			break;
		}
		if (c == '"') {
			q++;
			while (*q && *q != '"') {
				if (*q == '\\' && q[1]) {
					q++;
					out[o++] = *q == 'r' ? '\r' : *q == 'n' ? '\n' : *q == 't' ? '\t' : *q;
					q++;
				} else {
					out[o++] = *q++;
				}
			}
			if (*q == '"')
				q++;
			continue;
		}
		q++;
	}
	out[o] = 0;
	return out;
}


/* Decodes the string literal that starts at the opening quote q (q[0] == '"') into out; returns the position after the closing quote. */
static const char *literal(const char *q, char *out, size_t cap)
{
	size_t o = 0;

	q++;
	while (*q && *q != '"') {
		char c = *q;

		if (c == '\\' && q[1]) {
			q++;
			c = *q == 'r' ? '\r' : *q == 'n' ? '\n' : *q == 't' ? '\t' : *q;
		}
		if (o + 1 < cap)
			out[o++] = c;
		q++;
	}
	out[o] = 0;
	return *q == '"' ? q + 1 : q;
}

static const char *skip_ws(const char *p)
{
	while (*p == ' ' || *p == '\t' || *p == '\n' || *p == '\r')
		p++;
	return p;
}

/* The longest state and the longest Content-Type among the calls  compose*(c, "state", "kind", ...)  of the source. */
static void longest_state_kind(const char *src, char *state, size_t scap, char *kind, size_t kcap, int *calls)
{
	static const char *const names[] = {"compose_build(", "compose_tail(", "compose_with(", "compose("};
	size_t k;

	state[0] = kind[0] = 0;
	*calls = 0;
	for (k = 0; k < sizeof names / sizeof *names; k++) {
		const char *p = src;
		size_t nl = strlen(names[k]);

		while ((p = strstr(p, names[k])) != NULL) {
			const char *q = p + nl;
			char st[128], kd[128];

			/* skip the longer name that contains this one (compose_tail( does not contain compose( , but be safe) */
			if (p > src && (p[-1] == '_' || (p[-1] >= 'a' && p[-1] <= 'z')))
				goto next;
			q = skip_ws(q);
			if (*q != 'c')
				goto next;
			q = skip_ws(q + 1);
			if (*q != ',')
				goto next;
			q = skip_ws(q + 1);
			if (*q != '"')
				goto next; /* the definition: `client *c, const char *state` */
			q = literal(q, st, sizeof st);
			q = skip_ws(q);
			if (*q != ',')
				goto next;
			q = skip_ws(q + 1);
			if (*q != '"')
				goto next;
			literal(q, kd, sizeof kd);
			(*calls)++;
			if (strlen(st) > strlen(state))
				snprintf(state, scap, "%s", st);
			if (strlen(kd) > strlen(kind))
				snprintf(kind, kcap, "%s", kd);
next:
			p += nl;
		}
	}
}

/* The longest run of string literals written just before a use of PAGE_SECURITY (the "extra" headers of an answer). */
static size_t longest_extra(const char *src, char *best, size_t cap, int *uses)
{
	const char *p = src;
	size_t blen = 0;

	best[0] = 0;
	*uses = 0;
	while ((p = strstr(p, "PAGE_SECURITY")) != NULL) {
		const char *e = p;
		char buf[1024];
		size_t pieces = 0;

		p += 13;
		if (e >= src + 8 && strncmp(e - 8, "#define ", 8) == 0)
			continue;
		/* walk back over adjacent string literals */
		buf[0] = 0;
		for (;;) {
			const char *q = e;
			const char *open;
			char piece[512];

			while (q > src && (q[-1] == ' ' || q[-1] == '\t' || q[-1] == '\n' || q[-1] == '\r'))
				q--;
			if (q == src || q[-1] != '"')
				break;
			open = q - 2;
			while (open > src && !(*open == '"' && (open == src || open[-1] != '\\')))
				open--;
			literal(open, piece, sizeof piece);
			if (strlen(piece) + strlen(buf) + 1 < sizeof buf) {
				memmove(buf + strlen(piece), buf, strlen(buf) + 1);
				memcpy(buf, piece, strlen(piece));
			}
			pieces++;
			e = open;
		}
		(*uses)++;
		if (strlen(buf) > blen) {
			blen = strlen(buf);
			snprintf(best, cap, "%s", buf);
		}
	}
	return blen;
}

static int has(const char *h, const char *needle)
{
	return strstr(h, needle) != NULL;
}

int main(int argc, char **argv)
{
	size_t n = 0;
	char *src, *ps, *iso;
	const char *hp;
	int headsz = 0;
	size_t lines = 0, worst = 0, i;

	if (argc < 2) {
		fprintf(stderr, "usage: test <path of src/page.c>\n");
		return 2;
	}
	src = slurp(argv[1], &n);
	if (!src) {
		fprintf(stderr, "cannot read %s\n", argv[1]);
		return 2;
	}
	ps = macro_text(src, "PAGE_SECURITY");
	iso = macro_text(src, "ISOLATION");
	hp = strstr(src, "char head[");
	if (!ps || !iso || !hp || sscanf(hp, "char head[%d]", &headsz) != 1 || headsz <= 0) {
		fprintf(stderr, "cannot find PAGE_SECURITY, ISOLATION or `char head[N]` in %s: the test must be updated\n", argv[1]);
		return 2;
	}
	printf("PAGE_SECURITY: %zu bytes; ISOLATION: %zu bytes; head[%d]\n", strlen(ps), strlen(iso), headsz);

	/* 1. the whole text */
	if (strcmp(ps, EXPECTED) != 0) {
		size_t k = 0;

		while (ps[k] && EXPECTED[k] && ps[k] == EXPECTED[k])
			k++;
		printf("      first difference at byte %zu:\n      found:    «%.60s»\n      expected: «%.60s»\n", k, ps + k, EXPECTED + k);
	}
	check(strcmp(ps, EXPECTED) == 0, "PAGE_SECURITY is exactly the expected text");

	/* 2. directive by directive */
	check(has(ps, "Content-Security-Policy: default-src 'self'; "), "CSP starts with default-src 'self'");
	check(has(ps, "connect-src 'self';") && !has(ps, "connect-src 'self' "), "connect-src is 'self' alone");
	check(!has(ps, "https:") && !has(ps, "http:") && !has(ps, " *") && !has(ps, "wss:"), "no scheme or wildcard source anywhere");
	check(has(ps, "worker-src blob:;"), "worker-src blob: (the video worker is a blob)");
	check(has(ps, "media-src blob:;"), "media-src blob: (MSE)");
	check(has(ps, "object-src 'none';") && has(ps, "base-uri 'none';"), "object-src and base-uri 'none'");
	check(has(ps, "form-action 'self';"), "form-action 'self'");
	check(has(ps, "frame-ancestors 'none'\r\n"), "frame-ancestors 'none'");
	check(has(ps, "script-src 'self' 'unsafe-inline' 'wasm-unsafe-eval';") && !has(ps, " 'unsafe-eval'"),
	      "script-src has wasm-unsafe-eval and NOT 'unsafe-eval'");
	check(has(ps, "Referrer-Policy: no-referrer\r\n"), "Referrer-Policy: no-referrer");
	check(has(ps, "Permissions-Policy: clipboard-read=(self), clipboard-write=(self), ") && has(ps, "camera=()") &&
	          has(ps, "microphone=()") && has(ps, "geolocation=()") && has(ps, "payment=()") && has(ps, "usb=()"),
	      "Permissions-Policy: clipboard for self; camera, microphone, geolocation, payment, usb off");
	for (i = 0; ps[i]; i++) {
		if (ps[i] == '\n')
			lines++;
		if (ps[i] == '\n' && (i == 0 || ps[i - 1] != '\r'))
			lines += 1000; /* a bare LF: poison the count */
	}
	check(lines == 3, "exactly three header lines, every one ending with CRLF");

	/* 3. the format of compose_build() is the one assumed below */
	check(has(src, "\"HTTP/1.1 %s\\r\\n\"") && has(src, "\"Content-Type: %s\\r\\n\"") && has(src, "\"Content-Length: %zu\\r\\n\"") &&
	          has(src, "\"Cache-Control: no-store\\r\\n\"") && has(src, "\"X-Content-Type-Options: nosniff\\r\\n\"") &&
	          has(src, "\"Connection: close\\r\\n\"") && has(src, "ISOLATION\n") &&
	          has(src, "\"Content-Encoding: gzip\\r\\nVary: Accept-Encoding\\r\\n\" PAGE_SECURITY"),
	      "compose_build() still has the fixed headers this test counts (else update the test)");

	/* 4. the longest head, built like compose_build() and measured; its pieces come from the source */
	{
		char head[8192], state[128], kind[128], extra_pre[1024];
		int calls = 0, uses = 0;

		longest_state_kind(src, state, sizeof state, kind, sizeof kind, &calls);
		longest_extra(src, extra_pre, sizeof extra_pre, &uses);
		printf("      from the source: %d compose calls, longest status «%s», longest type «%s»; %d uses of PAGE_SECURITY, "
		       "longest extra before it: %zu bytes\n", calls, state, kind, uses, strlen(extra_pre));
		check(calls >= 8 && uses >= 5 && state[0] && kind[0], "the calls of compose*() and the uses of PAGE_SECURITY were found in the source");
		{
			char extra[2048];
			int len;

			snprintf(extra, sizeof extra, "%s%s", extra_pre, ps);
			len = snprintf(head, sizeof head,
			               "HTTP/1.1 %s\r\n"
			               "Content-Type: %s\r\n"
			               "Content-Length: %zu\r\n"
			               "%s"
			               "Cache-Control: no-store\r\n"
			               "X-Content-Type-Options: nosniff\r\n"
			               "Connection: close\r\n"
			               "%s"
			               "\r\n",
			               state, kind, (size_t)18446744073709551615ull, iso, extra);
			worst = (size_t)len;
		}
	}
	printf("      longest head: %zu bytes of %d (margin required %d)\n", worst, headsz, MARGIN);
	check(worst + MARGIN <= (size_t)headsz, "the longest head fits head[N] with the margin");
	check(headsz >= 2048, "head[N] has not been made smaller than 2048");

	printf("%d checks, %d failed\n", checks, bad);
	free(src);
	free(ps);
	free(iso);
	return bad ? 1 : 0;
}
