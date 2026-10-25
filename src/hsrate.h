/* hsrate.h — the RATE of new handshakes (audit R4, conto-handshake.md, 25 Oct 2026).
 *
 * ⛔ Why: the caps of transport.c (8 pending per address, 32 per /48, 128 in all) bound how many connections are open, not how fast they
 *    come: a client that closes at once frees its place and starts again, so ONE address can make 200-800 handshakes a second and a /48 can
 *    saturate the single thread that also carries the video (one handshake = 0.3-1.2 ms of CPU, 6.5 ms for a heavy key-exchange group).
 *    The Retry already proves the address is real; it does not slow it down.
 *
 * Three token buckets, taken together, AFTER the Retry token is verified and BEFORE accept_conn():
 *   · one per address (IPv4, or IPv6 /64 — transport.c's address_key()):  4 a second, burst 16;
 *   · one per IPv6 /48 (for IPv4 the key itself):                           16 a second, burst 32;
 *   · one for everybody:                                                  200 a second, burst 32
 *     (tls-gruppi limits the key-exchange groups, so a handshake costs about 1.2 ms at the worst: 200 a second is at most a quarter of the loop;
 *      with about 50 addresses at 4 a second an attacker therefore uses up the global bucket and the NEW logins are refused for as long as it lasts —
 *      the sessions already open are not touched).
 * A handshake needs a token from ALL THREE; if any is empty it is refused and NO bucket is charged (a refused attempt costs the
 * attacker nothing more and the honest ones nothing at all).
 *
 * ⛔ MEMORY: the tables have a FIXED size (HS_ADDR_SLOTS, HS_NET_SLOTS) and evict the LEAST RECENTLY SEEN entry when full: an attacker with
 *    more addresses than slots only makes his own entries and other idle ones start again from a full bucket — the global bucket still
 *    bounds the total.  Nothing here grows.
 *
 * No dependency (no log, no clock): `now` is in nanoseconds, passed by the caller, so benches/unit/hs-rate tests the logic alone. Tokens
 * are counted in thousandths. */
#ifndef REMOTIX_HSRATE_H
#define REMOTIX_HSRATE_H

#include <stdbool.h>
#include <stdint.h>
#include <string.h>

#define HS_ADDR_SLOTS 256
#define HS_NET_SLOTS 128

struct hs_limits {
	unsigned addr_rate, addr_burst;   /* per address: tokens a second, bucket size */
	unsigned net_rate, net_burst;     /* per /48 */
	unsigned all_rate, all_burst;     /* for everybody */
};

#define HS_ADDR_RATE 4
#define HS_ADDR_BURST 16
#define HS_NET_RATE 16
#define HS_NET_BURST 32
#define HS_ALL_RATE 200
#define HS_ALL_BURST 32
#define HS_LIMITS_DEFAULT { HS_ADDR_RATE, HS_ADDR_BURST, HS_NET_RATE, HS_NET_BURST, HS_ALL_RATE, HS_ALL_BURST }

struct hs_bucket {
	uint8_t key[16];
	uint64_t milli;   /* thousandths of a token */
	uint64_t last;    /* the instant `milli` is valid at */
	uint64_t seen;    /* the value of hs_rate.tick when this entry was last asked for: the LRU clock (a counter, not the time: many attempts share an instant) */
	bool used;
};

struct hs_rate {
	struct hs_bucket addr[HS_ADDR_SLOTS];
	struct hs_bucket net[HS_NET_SLOTS];
	struct hs_bucket all;
	uint64_t tick;    /* counts the calls of hs_take() */
};

enum { HS_OK = 0, HS_OVER_ADDRESS = 1, HS_OVER_NET = 2, HS_OVER_ALL = 3 };

static inline void hs_refill(struct hs_bucket *b, uint64_t now, unsigned rate, unsigned burst)
{
	uint64_t cap = (uint64_t)burst * 1000u, add;

	if (now < b->last) { /* the clock went back: start again from here */
		b->last = now;
		return;
	}
	if (!rate)
		return;
	add = (now - b->last) * rate / 1000000u;   /* ns × tokens/s = thousandths of a token ÷ 1e6 */
	if (!add)
		return;                              /* keep `last`: the fractions are not lost */
	if (b->milli + add >= cap) {                 /* full: the time beyond it buys nothing */
		b->milli = cap;
		b->last = now;
		return;
	}
	b->milli += add;
	b->last += add * 1000000u / rate;            /* only the time those tokens stand for: the remainder of the interval stays */
}

/* The entry of `key` in `tab` (n slots): the one it already has, else a free one, else the least recently seen — which starts again
 * from a FULL bucket. */
static inline struct hs_bucket *hs_slot(struct hs_bucket *tab, unsigned n, const uint8_t key[16], uint64_t now, uint64_t tick, unsigned burst)
{
	unsigned i, lru = 0;
	int free_i = -1;

	for (i = 0; i < n; i++) {
		if (tab[i].used && memcmp(tab[i].key, key, 16) == 0)
			goto found;
		if (!tab[i].used) {
			if (free_i < 0)
				free_i = (int)i;
		} else if (!tab[lru].used || tab[i].seen < tab[lru].seen) {
			lru = i;
		}
	}
	i = free_i >= 0 ? (unsigned)free_i : lru;
	memset(&tab[i], 0, sizeof tab[i]);
	memcpy(tab[i].key, key, 16);
	tab[i].used = true;
	tab[i].milli = (uint64_t)burst * 1000u;
	tab[i].last = now;
found:
	tab[i].seen = tick;
	return &tab[i];
}

/* One new handshake from `key` (the address) / `key48` at `now` (ns).  HS_OK = go ahead (one token taken from each bucket);
 * otherwise the first bucket that was empty, and nothing is charged. */
static inline int hs_take(struct hs_rate *h, const struct hs_limits *l, const uint8_t key[16], const uint8_t key48[16], uint64_t now)
{
	uint64_t tick = ++h->tick;
	struct hs_bucket *a = hs_slot(h->addr, HS_ADDR_SLOTS, key, now, tick, l->addr_burst);
	struct hs_bucket *n = hs_slot(h->net, HS_NET_SLOTS, key48, now, tick, l->net_burst);

	hs_refill(a, now, l->addr_rate, l->addr_burst);
	hs_refill(n, now, l->net_rate, l->net_burst);
	if (!h->all.used) {
		h->all.used = true;
		h->all.milli = (uint64_t)l->all_burst * 1000u;
		h->all.last = now;
	}
	hs_refill(&h->all, now, l->all_rate, l->all_burst);
	if (a->milli < 1000u)
		return HS_OVER_ADDRESS;
	if (n->milli < 1000u)
		return HS_OVER_NET;
	if (h->all.milli < 1000u)
		return HS_OVER_ALL;
	a->milli -= 1000u;
	n->milli -= 1000u;
	h->all.milli -= 1000u;
	return HS_OK;
}

#endif
