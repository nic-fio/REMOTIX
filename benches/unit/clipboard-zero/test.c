/*
 * test.c — unit test of the READ path of the session's clipboard, with a ZERO in the middle (F-014E) and the other
 * ways a text can be refused: the loop over the three TEXT_TYPES with memchr() and the UTF-8 check, through the REAL
 * read_text() of the two products:
 *   GNOME  src/clipboard.c      (read_text → call_for_fd → SelectionRead on Mutter's D-Bus → slurp_fd)
 *   KDE    src/clipboard_kde.c  (read_text → read_type → wlr-data-control `receive` on a pipe)
 * F-014E (benches/15-suite) runs on KDE only: on GNOME there is no way to put a zero in Mutter's selection from a
 * session (no wlr-data-control).  This test covers GNOME's zero; for KDE it is the same four cases at unit level.
 *
 * HOW: the REAL .c is #included (never modified), selected by -DKDE (clipboard_kde.c) or nothing (clipboard.c).
 * The only things replaced are the OUTSIDE calls, by macros defined AFTER the headers and BEFORE the product's source:
 *   GNOME  g_dbus_connection_call_with_unix_fd_list_sync → a function that returns a pipe with the bytes of the type
 *   KDE    zwlr_data_control_offer_v1_receive / wl_display_flush → write the bytes of the type into the pipe
 * (the static helpers call_for_fd/slurp_fd/read_type stay the REAL ones).  The log is captured here (log_says_in,
 * log_detail_in); everything else the .c links to is generated as a stub that TRAPS if reached.  Each case sets what each
 * of the three types "delivers" (or nothing: the type is absent / cannot be read).
 *
 * Cases (the same six on both):
 *   (a) «abc\0def» on all three types      ⇒ NULL, one «with a zero in the middle — not announced» per type, and NO «valid UTF-8»
 *                                            line (the zero is judged BEFORE the UTF-8 check)
 *   (b) valid text with accents            ⇒ returned, length = its UTF-8 length, no zero line
 *   (c) invalid UTF-8 without a zero       ⇒ NULL, «not valid UTF-8», no zero line
 *   (d) first type with a zero, second OK  ⇒ the second one is returned (length of the second), ONE zero line
 *   (e) every type delivers 0 bytes        ⇒ NULL, no crash (UBSan: memchr on an empty buffer)
 *   (f) first type missing, second valid   ⇒ the second one is returned
 *
 * BUILD AND RUN (a second; nothing under /media/REMOTIX-15 is written; run from the root of the tree).  Same command with
 * K="-DKDE" and SRC=clipboard_kde for the KDE half; with K="" for GNOME:
 *   for K in "" "-DKDE"; do nice -n 19 ionice -c3 podman run --rm --cpus=2 --memory=2g --network=none -e K="$K" -v "$PWD:/albero:ro" localhost/remotix-fuzz sh -c '
 *     mkdir -p /tmp/g && cd /tmp/g && for p in wlr-data-control-unstable-v1 ext-data-control-v1; do
 *       f=/albero/src/protocols/$p.xml; wayland-scanner client-header $f $p-client-protocol.h; done &&
 *     PK="gio-2.0 gio-unix-2.0 wayland-client" &&
 *     F="-g -O1 -fsanitize=address,undefined -fno-sanitize-recover=undefined -std=gnu11 -D_GNU_SOURCE -Wno-unused-parameter $K \
 *        -I/albero/src -I/tmp/g $(pkg-config --cflags $PK)" &&
 *     L="$(pkg-config --libs $PK) -lpthread -lm" &&
 *     clang $F -c /albero/benches/unit/clipboard-zero/test.c -o t.o &&
 *     { clang -fsanitize=address,undefined t.o $L -o t0 2> link1.log || true; } &&
 *     { echo "#include <stdio.h>"; grep -o "undefined reference to .[A-Za-z_0-9]*" link1.log | sed "s/.*to .//" | sort -u |
 *       while read -r n; do echo "void $n(void); void $n(void) { fputs(\"STUB reached: $n\", stderr); fputc(10, stderr); __builtin_trap(); }"; done; } > s.c &&
 *     clang $F -c s.c -o s.o && clang -fsanitize=address,undefined t.o s.o $L -o test && ./test'; done
 * Exit code 0 = every case as expected.  RXTEST_LOG=1 prints the product's log lines.
 */
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <gio/gio.h>
#include <gio/gunixfdlist.h>
#include "log.h"

#ifdef KDE
#include <wayland-client.h>
#include "ext-data-control-v1-client-protocol.h"
#include "wlr-data-control-unstable-v1-client-protocol.h"
#endif

/* ── what each type "delivers" in the current case ─────────────────────── */
#define NT 3
static const char *const MIME[NT] = {"text/plain;charset=utf-8", "UTF8_STRING", "text/plain"};
struct payload { const char *bytes; size_t len; };       /* bytes == NULL: the type is absent / cannot be read */
static struct payload offered[NT];

static const struct payload *payload_of(const char *mime)
{
	for (int i = 0; i < NT; i++)
		if (g_ascii_strcasecmp(mime, MIME[i]) == 0 && offered[i].bytes)
			return &offered[i];
	return NULL;
}

#ifdef KDE
/* wlr-data-control: `receive(mime, fd)` — the owner writes the bytes into fd; the product closes its copy of the write end */
static void test_receive(struct zwlr_data_control_offer_v1 *proxy, const char *mime, int fd)
{
	const struct payload *p = payload_of(mime);
	(void)proxy;
	if (p && p->len && write(fd, p->bytes, p->len) != (ssize_t)p->len)
		perror("write");
}
#define zwlr_data_control_offer_v1_receive(proxy, mime, fd) test_receive(proxy, mime, fd)
#define wl_display_flush(display) 0
#else
/* Mutter's SelectionRead: the reply carries a descriptor — a pipe already filled and closed on the write side */
static GVariant *test_selection_read(GDBusConnection *c, const gchar *bus, const gchar *path, const gchar *iface,
                                     const gchar *method, GVariant *parameters, const GVariantType *reply_type,
                                     GDBusCallFlags flags, gint timeout, GUnixFDList *fds, GUnixFDList **out_fds,
                                     GCancellable *cancel, GError **error)
{
	g_autoptr(GVariant) args = parameters ? g_variant_ref_sink(parameters) : NULL;
	const char *mime = NULL;
	int fd[2];
	GUnixFDList *list;
	gint idx;

	g_variant_get_child(args, 0, "&s", &mime);
	const struct payload *p = payload_of(mime);
	if (!p) {
		g_set_error(error, G_IO_ERROR, G_IO_ERROR_FAILED, "no such type");
		return NULL;
	}
	if (pipe(fd) != 0)
		abort();
	if (p->len && write(fd[1], p->bytes, p->len) != (ssize_t)p->len)
		perror("write");
	close(fd[1]);
	list = g_unix_fd_list_new();
	idx = g_unix_fd_list_append(list, fd[0], error);
	close(fd[0]);
	*out_fds = list;
	return g_variant_ref_sink(g_variant_new("(h)", idx));
}
#define g_dbus_connection_call_with_unix_fd_list_sync test_selection_read
#endif

/* ── the product's log, captured ───────────────────────────────────────── */
static char captured[16384];

static void add_line(const char *fmt, va_list ap)
{
	char buf[2048];
	size_t n = strlen(captured);

	vsnprintf(buf, sizeof buf, fmt, ap);
	if (getenv("RXTEST_LOG"))
		fprintf(stderr, "[log] %s\n", buf);
	snprintf(captured + n, sizeof captured - n, "%s\n", buf);
}

void log_says_in(const char *file, int text_line, const char *area, const char *fmt, ...)
{
	va_list ap;
	va_start(ap, fmt);
	add_line(fmt, ap);
	va_end(ap);
}

void log_detail_in(const char *file, int text_line, const char *area, const char *fmt, ...)
{
	va_list ap;
	va_start(ap, fmt);
	add_line(fmt, ap);
	va_end(ap);
}

#ifdef KDE
#include "clipboard_kde.c"
#else
#include "clipboard.c"
#endif

/* ── the cases ─────────────────────────────────────────────────────────── */
static int count(const char *needle)
{
	int n = 0;

	for (const char *p = captured; (p = strcasestr(p, needle)); p += strlen(needle))
		n++;
	return n;
}

#define ZERO_LINE "with a zero in the middle — not announced"
#define NOT_UTF8 "not valid UTF-8"

static char *read_one(size_t *len)
{
	*len = 0;
	captured[0] = 0;
#ifdef KDE
	ClipboardKde k;
	Offer offer;
	char *text;

	memset(&k, 0, sizeof k);
	offer.proxy = (struct zwlr_data_control_offer_v1 *)(void *)&offer;     /* never dereferenced: receive() is replaced */
	offer.mime = g_ptr_array_new_with_free_func(g_free);
	for (int i = 0; i < NT; i++)                 /* only the types that deliver something are OFFERED */
		if (offered[i].bytes)
			g_ptr_array_add(offer.mime, g_strdup(MIME[i]));
	k.current = &offer;
	text = read_text(&k, len);
	g_ptr_array_unref(offer.mime);
	return text;
#else
	Clipboard c;

	memset(&c, 0, sizeof c);
	return read_text(&c, len);
#endif
}

static int failures;

static void check(int ok, const char *what)
{
	printf("  %s %s\n", ok ? "OK  " : "FAIL", what);
	if (!ok) {
		failures++;
		fprintf(stderr, "--- log of the failed case ---\n%s------\n", captured);
	}
}

static void set(int i, const char *bytes, size_t len)
{
	offered[i].bytes = bytes;
	offered[i].len = len;
}

int main(void)
{
	static const char ZERO[] = "abc\0def";            /* 7 bytes */
	static const char GOOD[] = "ciao àèìòù € «ß»";
	static const char GOOD2[] = "second type àè";
	static const char BAD[] = "ab\xff\xfe" "cd";      /* invalid UTF-8, no zero */
	size_t len;
	char *t;

	printf("%s read_text()\n",
#ifdef KDE
	       "KDE clipboard_kde.c"
#else
	       "GNOME clipboard.c"
#endif
	);

	/* (a) a zero on all three types */
	for (int i = 0; i < NT; i++)
		set(i, ZERO, 7);
	t = read_one(&len);
	check(t == NULL, "(a) zero on all three types: nothing returned (not announced)");
	check(count(ZERO_LINE) == 3, "(a) one «" ZERO_LINE "» line per type (3)");
	check(count(NOT_UTF8) == 0, "(a) the log does NOT blame «not valid UTF-8» (zero judged before)");
	free(t);

	/* (b) valid text */
	for (int i = 0; i < NT; i++)
		set(i, GOOD, strlen(GOOD));
	t = read_one(&len);
	check(t != NULL && strcmp(t, GOOD) == 0, "(b) valid text: returned as it is");
	check(len == strlen(GOOD), "(b) its length is the UTF-8 length");
	check(count(ZERO_LINE) == 0 && count(NOT_UTF8) == 0, "(b) no refusal line");
	free(t);

	/* (c) invalid UTF-8, no zero */
	for (int i = 0; i < NT; i++)
		set(i, BAD, strlen(BAD));
	t = read_one(&len);
	check(t == NULL, "(c) invalid UTF-8: nothing returned");
	check(count(NOT_UTF8) == 3, "(c) «" NOT_UTF8 "» once per type (3)");
	check(count(ZERO_LINE) == 0, "(c) no zero line");
	free(t);

	/* (d) first type with a zero, second valid */
	set(0, ZERO, 7);
	set(1, GOOD2, strlen(GOOD2));
	set(2, GOOD, strlen(GOOD));
	t = read_one(&len);
	check(t != NULL && strcmp(t, GOOD2) == 0, "(d) the second type is the one announced");
	check(len == strlen(GOOD2), "(d) its length, not the zero text's");
	check(count(ZERO_LINE) == 1, "(d) exactly one zero line (the first type)");
	free(t);

	/* (e) every type delivers ZERO bytes (an emptied clipboard): nothing returned, nothing crashes */
	for (int i = 0; i < NT; i++)
		set(i, "", 0);
	t = read_one(&len);
	check(t == NULL, "(e) zero bytes on all types: nothing returned, no crash");
	check(count("delivered zero bytes") == 3, "(e) «delivered zero bytes» once per type (3)");
	check(count(ZERO_LINE) == 0 && count(NOT_UTF8) == 0, "(e) no «zero in the middle» / «not valid UTF-8» line (it is empty, not broken)");
	free(t);

	/* (f) first type absent / unreadable, second valid */
	set(0, NULL, 0);
	set(1, GOOD2, strlen(GOOD2));
	set(2, NULL, 0);
	t = read_one(&len);
	check(t != NULL && strcmp(t, GOOD2) == 0, "(f) first type missing: the second one is announced");
	check(len == strlen(GOOD2), "(f) its length");
	free(t);

	printf(failures ? "RESULT: %d FAILED\n" : "RESULT: all OK\n", failures);
	return failures ? 1 : 0;
}
