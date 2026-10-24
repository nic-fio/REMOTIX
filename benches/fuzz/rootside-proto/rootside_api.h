/*
 * rootside_api.h — the pure part of the root side that `fuzz_rootside_proto.c` drives
 * (DECISIONS §11.50, src/rootside_proto.h).
 *
 * ⭐ When lane 1's `src/rootside.h` is in the tree it is THE declaration (this file only includes
 *    it).  Until then the same prototypes are declared here, copied from lane 1's draft of
 *    16 Oct 2026, and `stub_rootside.c` implements them from the contract alone — so the target
 *    builds and runs before the merge (it then fuzzes the harness and its model, not the product,
 *    and build.sh says so).  ⚠ If the merged rootside.h changes these signatures, the build of
 *    `rootside-proto` breaks: that is wanted, it is the seam telling.
 */
#ifndef RXFUZZ_ROOTSIDE_API_H
#define RXFUZZ_ROOTSIDE_API_H

#if defined(RXFUZZ_REAL_ROOTSIDE)
#include "rootside.h"
#else
#include "rootside_proto.h"

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <sys/types.h>

struct rootside_peer {
	uid_t remotix_uid;
	pid_t net_pid;
};
int rootside_check_packet(const struct rootside_peer *p, const void *buf, size_t len, bool has_cred,
                          pid_t cred_pid, uid_t cred_uid, char *why, size_t why_len);

#define ROOTSIDE_GRANTS_MAX 32
struct rootside_grant {
	bool used;
	uint8_t bytes[RXR_GRANT_BYTES];
	char user[RXR_USER_MAX];
	char rhost[RXR_RHOST_MAX];
	uint64_t expires_ms;
};
struct rootside_bounds {
	struct rootside_grant grants[ROOTSIDE_GRANTS_MAX];
	int in_flight;
	double tokens;
	uint64_t tokens_ms;
};
void rootside_bounds_init(struct rootside_bounds *b, uint64_t now_ms);
bool rootside_auth_admit(struct rootside_bounds *b, uint64_t now_ms);
void rootside_auth_done(struct rootside_bounds *b);
bool rootside_grant_mint(struct rootside_bounds *b, const char *user, const char *rhost, uint64_t now_ms,
                         uint8_t out[RXR_GRANT_BYTES]);
bool rootside_grant_take(struct rootside_bounds *b, const uint8_t bytes[RXR_GRANT_BYTES], uint64_t now_ms,
                         char user[RXR_USER_MAX], char rhost[RXR_RHOST_MAX]);
#endif

#endif
