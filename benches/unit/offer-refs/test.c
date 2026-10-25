/* test.c — the reference count of the offers of src/clipboard_kde.c (audit of the session, S-R9: use after free of the Wayland offer).
 * The REAL clipboard_kde.c is #included; the only Wayland call the count reaches is wl_proxy_marshal_flags() (the destructor request of the inline wrapper; with wl_proxy_get_version()), defined here as a counter (so libwayland is NOT linked; every
 * other undefined symbol gets a trap stub generated at link time, as in benches/unit/child-flood).  What is checked:
 *   1. a new offer (refs 1) is destroyed once by one offer_free();
 *   2. with a reference held by a reader, the owner's offer_free() (what on_selection does) does NOT destroy: the proxy is still valid for the reader;
 *      the LAST drop destroys, exactly once;
 *   3. 8 threads take and drop references in a loop while the base reference is dropped: destroyed exactly once, after all of them;
 *   4. NULL is accepted;
 *   5. read_text() takes the reference under the lock BEFORE releasing it (source order) and every return releases it (3 offer_free(held) in read_text).
 * BUILD AND RUN (a few seconds; nothing under /media/REMOTIX-15 is written; run from the root of the tree):
 *   nice -n 19 ionice -c3 podman run --rm --cpus=2 --memory=2g --network=none -v "$PWD:/albero:ro" localhost/remotix-fuzz sh -c '
 *     mkdir -p /tmp/g && cd /tmp/g && for p in wlr-data-control-unstable-v1 ext-data-control-v1; do
 *       f=/albero/src/protocols/$p.xml; wayland-scanner client-header $f $p-client-protocol.h; done &&
 *     PK="gio-2.0 gio-unix-2.0 wayland-client" &&
 *     F="-g -O1 -fsanitize=address,undefined -fno-sanitize-recover=undefined -std=gnu11 -D_GNU_SOURCE -Wno-unused-parameter -I/albero/src -I/albero/benches/fuzz/child-msg -I/tmp/g $(pkg-config --cflags $PK)" &&
 *     L="$(pkg-config --libs $PK) -lpthread -lm" &&
 *     clang $F -c /albero/benches/unit/offer-refs/test.c -o t.o && clang $F -c /albero/benches/fuzz/child-msg/stubs_log.c -o l.o &&
 *       { clang -fsanitize=address,undefined t.o l.o $L -o t0 2> link1.log || true; } &&
 *       { echo "#include <stdio.h>"; grep -o "undefined reference to .[A-Za-z_0-9]*" link1.log | sed "s/.*to .//" | sort -u |
 *         while read -r n; do echo "void $n(void); void $n(void) { fputs(\"STUB reached: $n\", stderr); fputc(10, stderr); __builtin_trap(); }"; done; } > s.c &&
 *     clang $F -c s.c -o s.o && clang -fsanitize=address,undefined t.o l.o s.o $L -o test && cd /albero && /tmp/g/test'
 * Exit code 0 = every check passed, 1 = a check failed.
 */
#include "clipboard_kde.c"

#include <stdio.h>
#include <pthread.h>

static int bad;
#define CHECK(c, w) do { if (!(c)) { bad++; printf("FAIL: %s\n", w); } } while (0)

static int destroyed;
uint32_t wl_proxy_get_version(struct wl_proxy *proxy);
uint32_t wl_proxy_get_version(struct wl_proxy *proxy)
{
	(void)proxy;
	return 1;
}
struct wl_proxy *wl_proxy_marshal_flags(struct wl_proxy *proxy, uint32_t opcode, const struct wl_interface *iface, uint32_t version, uint32_t flags, ...);
struct wl_proxy *wl_proxy_marshal_flags(struct wl_proxy *proxy, uint32_t opcode, const struct wl_interface *iface, uint32_t version, uint32_t flags, ...)
{
	(void)proxy; (void)opcode; (void)iface; (void)version; (void)flags;
	__atomic_add_fetch(&destroyed, 1, __ATOMIC_SEQ_CST);   /* the only request the count reaches is the destructor */
	return NULL;
}

static Offer *fresh(void)
{
	Offer *o = g_new0(Offer, 1);

	o->refs = 1;
	o->proxy = (struct zwlr_data_control_offer_v1 *)(uintptr_t)0x1000;
	o->mime = g_ptr_array_new_with_free_func(g_free);
	return o;
}

static Offer *shared;
static void *worker(void *arg)
{
	(void)arg;
	for (int i = 0; i < 20000; i++) {
		Offer *h = offer_ref(shared);

		if (__atomic_load_n(&destroyed, __ATOMIC_SEQ_CST) != 0)
			__atomic_add_fetch(&destroyed, 1000000, __ATOMIC_SEQ_CST);   /* destroyed while we hold a reference: the bug */
		offer_free(h);
	}
	return NULL;
}

int main(void)
{
	Offer *o;
	pthread_t th[8];

	o = fresh();
	offer_free(o);
	CHECK(destroyed == 1, "1. a new offer is destroyed by one offer_free()");

	destroyed = 0;
	o = fresh();
	{
		Offer *held = offer_ref(o);
		offer_free(o);                     /* on_selection replaces the selection */
		CHECK(destroyed == 0, "2. the owner dropped it but a reader holds it: NOT destroyed");
		offer_free(held);
		CHECK(destroyed == 1, "2b. the last drop destroys, once");
	}

	destroyed = 0;
	shared = fresh();
	{
		Offer *mine = offer_ref(shared);   /* the "last reader" */
		for (int i = 0; i < 8; i++)
			pthread_create(&th[i], NULL, worker, NULL);
		offer_free(shared);                /* the base reference goes while the readers run */
		for (int i = 0; i < 8; i++)
			pthread_join(th[i], NULL);
		CHECK(destroyed == 0, "3. 8 threads x 20000 take/drop while the base reference is dropped: nobody saw it destroyed");
		offer_free(mine);
		CHECK(destroyed == 1, "3b. the last one destroys exactly once");
	}
	offer_free(NULL);
	CHECK(1, "4. NULL accepted");

	{
		FILE *f = fopen("src/clipboard_kde.c", "r");
		static char src[2u << 20];
		size_t n;
		char *fn, *ref, *unlock, *end;
		int rel = 0;

		if (!f) { puts("(run from the root of the tree)"); bad++; }
		else {
			n = fread(src, 1, sizeof src - 1, f); src[n] = 0; fclose(f);
			fn = strstr(src, "static char *read_text(ClipboardKde *clipboard, size_t *byte)\n{");
			end = fn ? strstr(fn, "\n}\n") : NULL;
			ref = fn ? strstr(fn, "held = offer_ref(offer);") : NULL;
			unlock = fn ? strstr(fn, "g_mutex_unlock(&clipboard->state);") : NULL;
			CHECK(ref && unlock && ref < unlock, "5. read_text takes the reference BEFORE it releases the lock");
			for (char *p = fn; p && p < end && (p = strstr(p, "offer_free(held);")) && p < end; p++)
				rel++;
			CHECK(rel == 3, "5b. the three returns of read_text release it");
		}
	}
	printf("%s\n", bad ? "FAILED" : "OK: all checks passed");
	return bad ? 1 : 0;
}
