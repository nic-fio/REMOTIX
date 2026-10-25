/*
 * test.c — EIGHT USERS BEHIND ONE IPv4 ADDRESS (a NAT, an office) must never be cut by a limit (1.5: the requirement «8 users per machine»).
 *
 * Many limits came in together: the rate of new handshakes, the AUTH bucket and the login pauses of the root side, the login tables of rcp.c,
 * the accept bucket of the page, the per-address cap of pending connections, the message buckets. Each one is tested alone; this test puts
 * them TOGETHER on the one scene that matters for the target: after a server restart eight people behind the same address reload the page, log in
 * (with ONE wrong password each, then the right one) and work for two minutes.
 *
 * It runs the REAL logic, nothing copied:
 *   - hsrate.h (hs_take, with the limits of the header and the key made as transport.c's address_key() does it for an IPv4 address);
 *   - msgrate.h (the buckets per kind of message, one set per session);
 *   - pagebucket.h (bucket_of, with the rates read from src/page.c; the arrival is parked in order up to PAGE_RATE_WAIT_MS, then served «busy», as page.c does);
 *   - rootside.c (LINKED: rootside_auth_admit, rootside_login_admit, rootside_login_done — the AUTH bucket 3/s burst 8, and the pauses per uid, per
 *     (uid, address) and per address);
 *   - rcp.c (#included: login_reserve / login_resolve, the tables of the network side: user-on-address 5, address 12, in flight);
 *   - the cap of pending connections per address, MAX_PENDING and PENDING_PER_48 read from src/transport.c (no pure header: the number is read, the count is here);
 *   - PAGE_PER_ADDRESS (connections at once from one address, served or parked) read from src/page.c: past it the connection is closed at accept.
 * The numbers that live in .c files are READ from the sources (argv[1] = the src directory) and compared with what the test was built for: if a limit
 * changes, the test says «out of date» and fails, it does not go on with an old number.
 *
 * Time is simulated in milliseconds (10 ms steps). PAM takes 2 s to refuse (pam_fail_delay) and 150 ms to admit; the server answers a refusal at the
 * floor of 2.5 s (REJECT_FLOOR) and an admission at 1 s; a refused login makes the page open a NEW connection for the next try (RCP §4.4: no retry
 * on the same connection). A load of the page costs `conns` TCP connections.
 *
 * SCENARIOS (ALL of them MUST pass since the margins of 1.5; the last line of the sweep is information):
 *   A spread     the eight reload one every 4 s, 6 s to type the password, 5 s to retype it after the refusal (people differ by +-2 s);
 *   B together   the eight reload within 100 ms, 3 s to type, 3 s to retype, people differing by +-2 s — and ALL ALIKE TO THE MILLISECOND (the worst case);
 *   C scripted   everybody within 100 ms, 0 s to type, 0.2 s to retype (a script, or a page that retries by itself);
 *   sweep        the all-alike scenario with 1..3 connections per page load and 0..2 wrong passwords each (required); then 4 connections and 3 wrong
 *                passwords each (information: it says where each limit starts to cut beyond the target).
 * Then two minutes of work for each user: a 1 kHz mouse, 30 keys a second, a 250 Hz wheel, a 300-character automatic typing at 1 ms, a key request
 * every 500 ms, three layout changes and two window drags of 20 resizes a second for 5 s — none of it may be dropped.
 *
 * Every cut is printed with the user, the time and the limit that did it. Exit code 0 = A and B had no cut, 1 = a cut (or the test is out of date).
 *
 * BUILD AND RUN (a few seconds; from the root of the tree; rootside.c is linked and its dependencies are stubs that trap if reached):
 *   nice -n 19 ionice -c3 podman run --rm --cpus=2 --memory=2g --network=none -v "$PWD:/albero:ro" localhost/remotix-fuzz sh -c '
 *     cd /tmp && PK="gio-2.0 libpipewire-0.3 libdrm libva libva-drm vulkan opus libei-1.0 xkbcommon" &&
 *     F="-g -O1 -fsanitize=address,undefined -fno-sanitize-recover=undefined -std=gnu11 -D_GNU_SOURCE -Wno-unused-parameter -I/albero/src -I/albero/benches/fuzz/rcp-msg $(pkg-config --cflags $PK)" &&
 *     L="$(pkg-config --libs gio-2.0) -lpam -lpthread -ldl -lm" &&
 *     clang $F -c /albero/benches/unit/otto-utenti-nat/test.c -o t.o && clang $F -c /albero/src/rootside.c -o r.o && clang $F -c /albero/benches/fuzz/rcp-msg/stubs_log.c -o l.o &&
 *     { clang -fsanitize=address,undefined t.o r.o l.o $L -o t0 2> link1.log || true; } &&
 *     { echo "#include <stdio.h>"; grep -o "undefined reference to .[A-Za-z_0-9]*" link1.log | sed "s/.*to .//" | sort -u |
 *       while read -r n; do echo "void $n(void); void $n(void) { fputs(\"STUB reached: $n\", stderr); fputc(10, stderr); __builtin_trap(); }"; done; } > s.c &&
 *     clang $F -c s.c -o s.o && clang -fsanitize=address,undefined t.o r.o l.o s.o $L -o test && cd /albero && /tmp/test src'
 */
#include "rcp.c"

#include "hsrate.h"
#include "rootside.h"
#include "rootside_proto.h"

#define PAGE_ACCEPT_RATE 8
#define PAGE_ACCEPT_BURST 32
#define PAGE_RATE_KEYS 256
#define PAGE_KEYS_PER_32 32
#include "pagebucket.h"

#include <stdio.h>

#define NUSERS 8
#define STEP_MS 10u

static int failures;
static char src_dir[512] = "src";

/* ---------------------------------------------------------------- the numbers that live in .c files, read from the sources */
static long read_define(const char *file, const char *name)
{
	char path[1024], line[1024], pat[128];
	FILE *f;
	long v = -1;

	snprintf(path, sizeof path, "%s/%s", src_dir, file);
	snprintf(pat, sizeof pat, "#define %s ", name);
	f = fopen(path, "r");
	if (!f)
		return -1;
	while (fgets(line, sizeof line, f)) {
		if (strncmp(line, pat, strlen(pat)) == 0) {
			v = strtol(line + strlen(pat), NULL, 10);
			break;
		}
	}
	fclose(f);
	return v;
}

static void expect_define(const char *file, const char *name, long built_for)
{
	long v = read_define(file, name);

	if (v != built_for) {
		printf("OUT OF DATE: %s %s is %ld, this test was written for %ld: update the test\n", file, name, v, built_for);
		failures++;
	}
}

static long pending_per_address, pending_per_48, max_pending, page_wait_ms, page_per_address;

/* ---------------------------------------------------------------- one simulation */
struct params {
	const char *name;
	unsigned reload_gap_ms;   /* between one user's reload and the next one's */
	unsigned think_ms;        /* from the page being there to the first Enter */
	unsigned retype_ms;       /* from the refusal to the next Enter */
	int conns;                /* TCP connections per page load */
	int wrong;                /* wrong passwords before the right one */
	bool work;                /* the two minutes of work */
	unsigned jitter_ms;       /* each person's own +-jitter on the time to type and to retype (a seeded generator); 0 = all exactly alike */
	unsigned seed;
};

struct cut {
	int user;
	uint64_t at_ms;
	char what[160];
};
#define MAX_CUTS 64

struct result {
	int ncuts;
	struct cut cuts[MAX_CUTS];
	/* the margins: how close each limit came */
	unsigned hs_addr_min_milli, hs_all_min_milli;
	unsigned page_min_milli;
	double auth_min_tokens;
	int pending_max;
	int host_inside_max;      /* rcp: failures of the address in the window, this one included */
	int work_dropped;
	uint64_t last_login_ms;
};

static void note_cut(struct result *r, int user, uint64_t at, const char *fmt, ...)
{
	va_list ap;

	if (r->ncuts >= MAX_CUTS)
		return;
	r->cuts[r->ncuts].user = user;
	r->cuts[r->ncuts].at_ms = at;
	va_start(ap, fmt);
	vsnprintf(r->cuts[r->ncuts].what, sizeof r->cuts[r->ncuts].what, fmt, ap);
	va_end(ap);
	r->ncuts++;
}

enum phase { P_WAIT_RELOAD, P_PAGE, P_TYPING, P_PAM, P_REJECTED, P_ADMITTING, P_WORK, P_DONE, P_CUT };

struct user {
	enum phase ph;
	char name[16], uid[8];
	uint64_t reload_at, next_at;
	int conns_left, conns_served;
	uint64_t page_arrive[8], page_done_at;
	int wrong_left;
	uint64_t pam_done_at, close_at;
	bool pam_good;
	unsigned taken;       /* rootside_login_admit's places */
	bool pending;         /* a pre-login connection of this user is counted at the address */
	struct msg_gate gate[MC_COUNT];
	uint64_t work_start;
	unsigned long work_n;
};

/* the parked page connections, in arrival order */
struct parked {
	int user, idx;
	uint64_t arrived;
};

static uint32_t rng;
static uint32_t rnd(void) { rng = rng * 1664525u + 1013904223u; return rng >> 8; }
/* base + a person's own jitter in [-j, +j] */
static uint64_t human(unsigned base, unsigned j)
{
	if (!j)
		return base;
	int64_t v = (int64_t)base + (int64_t)(rnd() % (2u * j + 1u)) - (int64_t)j;
	return v < 0 ? 0 : (uint64_t)v;
}

static void scenario(const struct params *P, struct result *R)
{
	static struct hs_rate hs;
	static struct bucket rate[PAGE_RATE_KEYS], over[2];
	static struct rootside_bounds bounds;
	struct hs_limits lim = HS_LIMITS_DEFAULT;
	struct user u[NUSERS];
	struct parked q[NUSERS * 8];
	int nq = 0, pending = 0;
	uint64_t served_until[NUSERS * 8];  /* the connections being served: they hold a slot of the address until then */
	int nserved = 0;
	uint8_t key[16] = {0};
	const char *addr = "192.0.2.10";
	uint64_t now;
	uint64_t end = 0;

	rng = 12345u + P->seed * 7919u;
	memset(R, 0, sizeof *R);
	R->hs_addr_min_milli = R->hs_all_min_milli = R->page_min_milli = 1u << 30;
	R->auth_min_tokens = 1e9;
	memset(&hs, 0, sizeof hs);
	memset(rate, 0, sizeof rate);
	memset(over, 0, sizeof over);
	rootside_bounds_init(&bounds, 1000);
	/* the network side's login tables: a restarted server starts with none (the ban file of a first start holds nothing) */
	memset(attempts, 0, sizeof attempts);
	memset(&u, 0, sizeof u);
	key[10] = key[11] = 0xff;
	key[12] = 192; key[13] = 0; key[14] = 2; key[15] = 10;

	for (int i = 0; i < NUSERS; i++) {
		snprintf(u[i].name, sizeof u[i].name, "user%d", i + 1);
		snprintf(u[i].uid, sizeof u[i].uid, "%d", 1001 + i);
		u[i].reload_at = 1000 + (uint64_t)i * (P->reload_gap_ms ? P->reload_gap_ms : 12);
		u[i].ph = P_WAIT_RELOAD;
		u[i].wrong_left = P->wrong;
	}

	for (now = 1000;; now += STEP_MS) {
		bool all_done = true;

		/* 1. the parked page connections, in order, then the new arrivals */
		for (int k = 0; k < nserved;)
			if (served_until[k] <= now) {
				served_until[k] = served_until[--nserved];
			} else {
				k++;
			}
		for (int i = 0; i < NUSERS; i++) {
			if (u[i].ph == P_WAIT_RELOAD && now >= u[i].reload_at) {
				u[i].ph = P_PAGE;
				u[i].conns_left = P->conns;
				u[i].next_at = now;
			}
			if (u[i].ph == P_PAGE && u[i].conns_left > 0 && now >= u[i].next_at) {
				/* PAGE_PER_ADDRESS: the connections of this address being served or parked; past it the connection is CLOSED at accept */
				if ((long)(nq + nserved) >= page_per_address) {
					note_cut(R, i, now, "page: %d connections of the address already (served or parked), the cap is %ld: the connection is closed at accept",
					         nq + nserved, page_per_address);
					u[i].ph = P_CUT;
					continue;
				}
				q[nq].user = i;
				q[nq].idx = P->conns - u[i].conns_left;
				q[nq].arrived = now;
				nq++;
				u[i].conns_left--;
				u[i].next_at = now + 20; /* the browser opens them a few ms apart */
			}
		}
		while (nq > 0) {
			struct bucket *b = bucket_of(rate, over, addr, now, PAGE_ACCEPT_RATE, PAGE_ACCEPT_BURST);
			int i = q[0].user;

			if (b->milli >= 1000u) {
				b->milli -= 1000u;
				if (b->milli < R->page_min_milli)
					R->page_min_milli = b->milli;
				u[i].conns_served++;
				served_until[nserved++] = now + 300; /* the page is 900 KB */
				if (u[i].conns_served >= P->conns)
					u[i].page_done_at = now + 300;
				memmove(q, q + 1, (size_t)(nq - 1) * sizeof q[0]);
				nq--;
			} else if (now - q[0].arrived > (uint64_t)page_wait_ms) {
				note_cut(R, i, now, "page accept bucket of the address: connection %d waited more than %ld ms and was served BUSY (503)",
				         q[0].idx + 1, page_wait_ms);
				u[i].ph = P_CUT;
				memmove(q, q + 1, (size_t)(nq - 1) * sizeof q[0]);
				nq--;
			} else {
				break;
			}
		}

		for (int i = 0; i < NUSERS; i++) {
			struct user *x = &u[i];

			if (x->ph == P_PAGE && x->conns_served >= P->conns && now >= x->page_done_at) {
				x->ph = P_TYPING;
				x->next_at = now + human(P->think_ms, P->jitter_ms);
			}
			/* 2. an Enter: a new connection, the handshake, the login tables, the root side */
			if (x->ph == P_TYPING && now >= x->next_at) {
				int why;
				enum login_verdict lv;
				struct login_info info;
				uint64_t left;
				bool wrong = x->wrong_left > 0;

				why = hs_take(&hs, &lim, key, key, now * 1000000ull);
				{
					unsigned am = hs.addr[0].used ? (unsigned)hs.addr[0].milli : 0;

					for (int s = 0; s < HS_ADDR_SLOTS; s++)
						if (hs.addr[s].used && memcmp(hs.addr[s].key, key, 16) == 0 && hs.addr[s].milli < R->hs_addr_min_milli)
							R->hs_addr_min_milli = (unsigned)hs.addr[s].milli;
					(void)am;
					if (hs.all.used && hs.all.milli < R->hs_all_min_milli)
						R->hs_all_min_milli = (unsigned)hs.all.milli;
				}
				if (why != HS_OK) {
					note_cut(R, i, now, "handshake rate (%s bucket): the new connection is refused",
					         why == HS_OVER_ADDRESS ? "per address" : why == HS_OVER_NET ? "per /48" : "global");
					x->ph = P_CUT;
					continue;
				}
				if ((long)pending >= pending_per_address) {
					note_cut(R, i, now, "pre-login connections of the address: %d pending, the cap is %ld", pending, pending_per_address);
					x->ph = P_CUT;
					continue;
				}
				pending++;
				x->pending = true;
				if (pending > R->pending_max)
					R->pending_max = pending;
				lv = login_reserve(addr, x->name, now, &info);
				if (lv != LV_OK) {
					note_cut(R, i, now, "rcp login table (%s): verdict %d, level «%s»", lv == LV_BANNED ? "banned" : lv == LV_BUSY ? "busy" : "full/quota",
					         (int)lv, LEVEL_NAME[info.kind]);
					pending--;
					x->pending = false;
					x->ph = P_CUT;
					continue;
				}
				if (!rootside_auth_admit(&bounds, now)) {
					note_cut(R, i, now, "root side AUTH bucket (%d per second, burst %d): NOT CHECKED (0x0E on the page)", RXR_AUTH_PER_S, RXR_AUTH_BURST);
					login_resolve(addr, x->name, false, now, &(struct login_result){0}); /* the booking is given back as a failure here: conservative */
					pending--;
					x->pending = false;
					x->ph = P_CUT;
					continue;
				}
				if (bounds.tokens < R->auth_min_tokens)
					R->auth_min_tokens = bounds.tokens;
				x->taken = 0;
				why = rootside_login_admit(&bounds, x->uid, addr, now, &left, &x->taken);
				if (why != RXR_LOGIN_OK) {
					static const char *const names[] = {"OK", "(uid, address) paused", "uid paused", "address paused", "(uid, address) busy",
					                                    "uid busy", "address busy", "table full"};
					note_cut(R, i, now, "root side login pause: %s (code %d)", why >= 0 && why < 8 ? names[why] : "?", why);
					rootside_auth_done(&bounds);
					pending--;
					x->pending = false;
					x->ph = P_CUT;
					continue;
				}
				x->pam_good = !wrong;
				x->pam_done_at = now + (wrong ? 2000 : 150);
				x->ph = P_PAM;
			}
			/* 3. PAM answers */
			if (x->ph == P_PAM && now >= x->pam_done_at) {
				struct login_result lr;
				struct rootside_login_event ev;

				rootside_auth_done(&bounds);
				rootside_login_done(&bounds, x->uid, addr, now, x->taken, x->pam_good ? RXR_LOGIN_ACCEPTED : RXR_LOGIN_REFUSED, &ev);
				login_resolve(addr, x->name, x->pam_good, now, &lr);
				if (lr.inside[LK_KEY] > R->host_inside_max)
					R->host_inside_max = lr.inside[LK_KEY];
				if (x->pam_good) {
					x->ph = P_ADMITTING;
					x->close_at = now + 850; /* the fixed second from CREDENTIALS, 150 ms already spent in PAM */
				} else {
					x->wrong_left--;
					x->ph = P_REJECTED;
					x->close_at = now + 500; /* REJECT_FLOOR 2.5 s from CREDENTIALS, 2 s already in PAM */
				}
			}
			if (x->ph == P_REJECTED && now >= x->close_at) {
				pending--;
				x->pending = false;
				x->ph = P_TYPING;
				x->next_at = now + human(P->retype_ms, P->jitter_ms);
			}
			if (x->ph == P_ADMITTING && now >= x->close_at) {
				pending--;
				x->pending = false;
				x->ph = P_WORK;
				x->work_start = now;
				R->last_login_ms = now;
			}
			if (x->ph == P_WORK) {
				if (!P->work) {
					x->ph = P_DONE;
				} else if (now - x->work_start >= 120000u) {
					x->ph = P_DONE;
				}
			}
			if (x->ph != P_DONE && x->ph != P_CUT)
				all_done = false;
		}

		/* 4. the work of the users who are in: one pass per simulated millisecond inside the 10 ms step */
		for (int i = 0; i < NUSERS; i++) {
			struct user *x = &u[i];

			if (x->ph != P_WORK)
				continue;
			for (unsigned ms = 0; ms < STEP_MS; ms++) {
				uint64_t t = now + ms;
				uint64_t rel = t - x->work_start;
				struct msg_gate_closed cl;
				unsigned ps, bs;
				bool ok = true;

#define SEND(c)                                                                                              \
	do {                                                                                                 \
		msg_class_rate(c, &ps, &bs);                                                                 \
		if (!msg_gate_admit(&x->gate[c], t, ps, bs, &cl)) {                                          \
			R->work_dropped++;                                                                   \
			ok = false;                                                                          \
		}                                                                                            \
	} while (0)
				SEND(MC_POINTER);                                    /* a 1 kHz mouse, continuously */
				if (rel % 33 == 0)
					SEND(MC_KEY_POSITION);                       /* 30 keys a second */
				if (rel % 4 == 0)
					SEND(MC_WHEEL);                              /* a 250 Hz wheel */
				if (rel >= 5000 && rel < 5300)
					SEND(MC_LETTER);                             /* 300 characters at 1 ms: a password manager typing */
				if (rel % 500 == 0)
					SEND(MC_REQUEST_KEY);                        /* a key request every 500 ms */
				if (rel == 20000 || rel == 40000 || rel == 60000)
					SEND(MC_LAYOUT);                             /* three layout changes */
				if (((rel >= 30000 && rel < 35000) || (rel >= 80000 && rel < 85000)) && rel % 50 == 0)
					SEND(MC_FIT_CANVAS);                         /* a window drag: 20 resizes a second for 5 s, twice */
				if (rel == 1000 && 0)
					SEND(MC_BUTTON);
				(void)ok;
#undef SEND
			}
			x->work_n++;
		}

		if (all_done && nq == 0) {
			end = now;
			break;
		}
		if (now > 600000) { /* a safety net: the simulation is never longer than ten minutes */
			end = now;
			break;
		}
	}
	(void)end;
	if (R->work_dropped)
		note_cut(R, -1, 0, "message buckets: %d messages dropped during the work", R->work_dropped);
}

static void report(const struct params *P, const struct result *R, bool required)
{
	printf("[%s] reload every %u ms, type %u ms, retype %u ms, %d page connections, %d wrong password(s) each: %s\n", P->name, P->reload_gap_ms,
	       P->think_ms, P->retype_ms, P->conns, P->wrong, R->ncuts ? "CUT" : "nobody cut");
	for (int i = 0; i < R->ncuts; i++)
		printf("    ✗ user%d at +%llu ms: %s\n", R->cuts[i].user + 1, (unsigned long long)(R->cuts[i].at_ms ? R->cuts[i].at_ms - 1000 : 0), R->cuts[i].what);
	printf("    margins: handshake address bucket low point %.1f of %d tokens, global %.1f of %d; page bucket low point %.1f of %d; "
	       "AUTH bucket low point %.1f of %d; pending connections peak %d of %ld; failures of the address in the window peak %d of %d\n",
	       R->hs_addr_min_milli == (1u << 30) ? (double)HS_ADDR_BURST : R->hs_addr_min_milli / 1000.0, HS_ADDR_BURST,
	       R->hs_all_min_milli == (1u << 30) ? (double)HS_ALL_BURST : R->hs_all_min_milli / 1000.0, HS_ALL_BURST,
	       R->page_min_milli == (1u << 30) ? (double)PAGE_ACCEPT_BURST : R->page_min_milli / 1000.0, PAGE_ACCEPT_BURST,
	       R->auth_min_tokens > 1e8 ? (double)RXR_AUTH_BURST : R->auth_min_tokens, RXR_AUTH_BURST, R->pending_max, pending_per_address,
	       R->host_inside_max, LIMIT[LK_KEY]);
	if (required && R->ncuts)
		failures++;
}

/* The same scenario over many seeds: how many runs cut somebody, and the first cut. */
static int many(const struct params *P, int runs, bool required, struct result *first_bad)
{
	int bad = 0;

	for (int k = 0; k < runs; k++) {
		struct params Q = *P;
		struct result R;

		Q.seed = (unsigned)k;
		Q.work = k == 0 ? P->work : false; /* the two minutes of work are the same for all seeds: once is enough */
		scenario(&Q, &R);
		if (R.ncuts) {
			if (!bad)
				*first_bad = R;
			bad++;
		}
	}
	printf("[%s] reload every %u ms, type %u ms retype %u ms (each person +-%u ms), %d page connection(s), %d wrong password(s) each, %d run(s): %s\n",
	       P->name, P->reload_gap_ms, P->think_ms, P->retype_ms, P->jitter_ms, P->conns, P->wrong, runs,
	       bad ? "CUT" : "nobody cut in any run");
	if (bad) {
		printf("    %d of %d runs cut somebody; the first:\n", bad, runs);
		for (int i = 0; i < first_bad->ncuts && i < 4; i++)
			printf("    ✗ user%d at +%llu ms: %s\n", first_bad->cuts[i].user + 1,
			       (unsigned long long)(first_bad->cuts[i].at_ms ? first_bad->cuts[i].at_ms - 1000 : 0), first_bad->cuts[i].what);
		if (required)
			failures++;
	}
	return bad;
}

int main(int argc, char **argv)
{
	struct result R, B;
	/* name, reload gap, think, retype, conns, wrong, work, jitter, seed */
	struct params A1 = {"A spread, 1 page connection", 4000, 6000, 5000, 1, 1, true, 2000, 0};
	struct params A2 = {"A spread, 2 page connections", 4000, 6000, 5000, 2, 1, true, 2000, 0};
	struct params H1 = {"B together, people differ, 1 page connection", 0, 3000, 3000, 1, 1, true, 2000, 0};
	struct params H2 = {"B together, people differ, 2 page connections", 0, 3000, 3000, 2, 1, true, 2000, 0};
	struct params S1 = {"B-sync: all alike to the millisecond, 1 page connection", 0, 3000, 3000, 1, 1, false, 0, 0};
	struct params S2 = {"B-sync: all alike to the millisecond, 2 page connections", 0, 3000, 3000, 2, 1, false, 0, 0};
	struct params C2 = {"C scripted", 0, 0, 200, 2, 1, false, 0, 0};

	if (argc > 1)
		snprintf(src_dir, sizeof src_dir, "%s", argv[1]);
	/* the numbers of the .c files this test was written for */
	expect_define("page.c", "PAGE_ACCEPT_RATE", 8);
	expect_define("page.c", "PAGE_ACCEPT_BURST", 32);
	expect_define("page.c", "PAGE_RATE_KEYS", 256);
	expect_define("page.c", "PAGE_KEYS_PER_32", 32);
	pending_per_address = read_define("transport.c", "PENDING_PER_ADDRESS");
	pending_per_48 = read_define("transport.c", "PENDING_PER_48");
	max_pending = read_define("transport.c", "MAX_PENDING");
	page_wait_ms = read_define("page.c", "PAGE_RATE_WAIT_MS");
	page_per_address = read_define("page.c", "PAGE_PER_ADDRESS");
	if (pending_per_address < 0 || max_pending < 0 || page_wait_ms < 0 || page_per_address < 0) {
		printf("OUT OF DATE: cannot read the limits of transport.c / page.c from «%s»\n", src_dir);
		return 1;
	}
	printf("limits read from the sources: pending per address %ld, per /48 %ld, in all %ld; page accept %d a second burst %d, parked up to %ld ms, %ld connections at once per address;\n"
	       "  handshakes per address %d/s burst %d, per /48 %d/s burst %d, global %d/s burst %d; root AUTH %d/s burst %d; root pauses (uid, address) %d / address %d / uid %d;\n"
	       "  rcp tables: user on address %d, address %d, /48 %d in 5-10 min\n\n",
	       pending_per_address, pending_per_48, max_pending, PAGE_ACCEPT_RATE, PAGE_ACCEPT_BURST, page_wait_ms, page_per_address, HS_ADDR_RATE, HS_ADDR_BURST, HS_NET_RATE,
	       HS_NET_BURST, HS_ALL_RATE, HS_ALL_BURST, RXR_AUTH_PER_S, RXR_AUTH_BURST, ROOTSIDE_LOGIN_PAIR_LIMIT, ROOTSIDE_LOGIN_HOST_LIMIT,
	       ROOTSIDE_LOGIN_USER_LIMIT, LIMIT[LK_USER], LIMIT[LK_KEY], LIMIT[LK_NET48]);

	struct params A3 = {"A spread, 3 page connections, 2 wrong passwords each", 4000, 6000, 5000, 3, 2, true, 2000, 0};
	struct params H3 = {"B together, people differ, 3 page connections, 2 wrong passwords each", 0, 3000, 3000, 3, 2, true, 2000, 0};

	printf("REQUIRED (a cut here makes the test red):\n");
	many(&A1, 50, true, &B);
	many(&A2, 50, true, &B);
	many(&A3, 50, true, &B);
	many(&H1, 50, true, &B);
	many(&H2, 50, true, &B);
	many(&H3, 50, true, &B);
	many(&S1, 1, true, &B);
	many(&S2, 1, true, &B);
	many(&C2, 1, true, &B);
	printf("\nINFORMATION (past the target):\n");
	scenario(&H2, &R);
	printf("  margins of B (people differ, 2 connections, run 0): handshake address bucket low point %.1f of %d tokens, global %.1f of %d; page bucket low point %.1f of %d; "
	       "AUTH bucket low point %.1f of %d; pending connections peak %d of %ld; failures of the address in the window peak %d of %d; messages dropped in the work: %d\n",
	       R.hs_addr_min_milli == (1u << 30) ? (double)HS_ADDR_BURST : R.hs_addr_min_milli / 1000.0, HS_ADDR_BURST,
	       R.hs_all_min_milli == (1u << 30) ? (double)HS_ALL_BURST : R.hs_all_min_milli / 1000.0, HS_ALL_BURST,
	       R.page_min_milli == (1u << 30) ? (double)PAGE_ACCEPT_BURST : R.page_min_milli / 1000.0, PAGE_ACCEPT_BURST,
	       R.auth_min_tokens > 1e8 ? (double)RXR_AUTH_BURST : R.auth_min_tokens, RXR_AUTH_BURST, R.pending_max, pending_per_address, R.host_inside_max,
	       LIMIT[LK_KEY], R.work_dropped);

	printf("\nSWEEP of the synchronised scenario (all alike): where does each limit start to cut? (conns 1..3 and wrong 0..2 are REQUIRED)\n");
	for (int conns = 1; conns <= 4; conns++)
		for (int wrong = 0; wrong <= 3; wrong++) {
			struct params S = S2;
			char nm[48];
			bool required = conns <= 3 && wrong <= 2;

			snprintf(nm, sizeof nm, "sweep c=%d w=%d", conns, wrong);
			S.name = nm;
			S.conns = conns;
			S.wrong = wrong;
			scenario(&S, &R);
			printf("  conns=%d wrong=%d%s: %s", conns, wrong, required ? " (required)" : "", R.ncuts ? "CUT" : "ok");
			if (R.ncuts)
				printf(" — first: user%d, %s", R.cuts[0].user + 1, R.cuts[0].what);
			printf("\n");
			if (required && R.ncuts)
				failures++;
		}
	printf("\n%s\n", failures ? "RESULT: a limit cut somebody in a REQUIRED scenario (or the test is out of date): see above" : "RESULT: nobody was cut in the required scenarios");
	return failures ? 1 : 0;
}
