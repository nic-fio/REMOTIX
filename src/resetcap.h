/* resetcap.h — a cap of Stateless Resets PER ADDRESS, in front of the global one (audit R9, 25 Oct 2026).
 *
 * ⛔ Why: transport.c answers a packet for a connection that does not exist with a Stateless Reset (RFC 9000 §10.3), at most RESET_PER_SECOND (100)
 *    a second FOR EVERYBODY.  Whoever sends short packets for unknown connection ids — one address is enough — consumes that cap, and the real
 *    clients that have really lost their connection (the server restarted) get no Reset and wait out their 30 s of idle time.  No amplification
 *    (the Reset is one byte shorter than the packet that triggered it), so the harm is only to those clients.
 *    Now an address (transport.c's address_key(): IPv4 address, or IPv6 /64) may use at most RESET_PER_ADDRESS (5) of the 100 in a second, and the
 *    ones it is refused do not count against the global cap: one address cannot take it away from the others.
 *
 * ⚠ Declared limit: with about 20 addresses at 5 a second an attacker still uses up the global cap.
 * ⛔ MEMORY: RESET_ADDR_SLOTS entries, fixed.  A full table gives the place of the entry of the OLDEST second (an attacker with more addresses
 *    than slots only recycles his own, and then each address counts as new: the global cap still bounds the total).
 *
 * No dependency (no log, no clock): `second` is the caller's, so benches/unit/reset-cap tests the logic alone. */
#ifndef REMOTIX_RESETCAP_H
#define REMOTIX_RESETCAP_H

#include <stdbool.h>
#include <stdint.h>
#include <string.h>

#define RESET_ADDR_SLOTS 64
#define RESET_PER_ADDRESS 5

struct reset_addr {
	struct {
		uint8_t key[16];
		uint64_t second;
		unsigned count;
		bool used;
	} e[RESET_ADDR_SLOTS];
};

/* May `key` have one more Stateless Reset in `second`?  true = yes (and it is counted for that address); false = it has had `per_address`. */
static inline bool reset_addr_take(struct reset_addr *t, const uint8_t key[16], uint64_t second, unsigned per_address)
{
	unsigned i, pick = 0;
	bool have_free = false;

	for (i = 0; i < RESET_ADDR_SLOTS; i++) {
		if (t->e[i].used && memcmp(t->e[i].key, key, 16) == 0)
			goto found;
		if (!t->e[i].used) {
			if (!have_free)
				pick = i;
			have_free = true;
		} else if (!have_free && (!t->e[pick].used || t->e[i].second < t->e[pick].second)) {
			pick = i;
		}
	}
	i = pick;
	memset(&t->e[i], 0, sizeof t->e[i]);
	memcpy(t->e[i].key, key, 16);
	t->e[i].used = true;
	t->e[i].second = second;
found:
	if (t->e[i].second != second) {
		t->e[i].second = second;
		t->e[i].count = 0;
	}
	if (t->e[i].count >= per_address)
		return false;
	t->e[i].count++;
	return true;
}

#endif
