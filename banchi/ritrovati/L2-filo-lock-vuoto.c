/* Un LOCK a corpo vuoto sopravvive al filo?  Il ramo nuovo di watch_thread si
 * accende su `n > 0 && t == RMX_MSG_LOCK`: se un messaggio senza payload
 * tornasse con n == 0 (che per rmx_sm_recv vuol dire EOF) il ramo non si
 * accenderebbe MAI e il gesto finirebbe nel cammino "il worker e' uscito". */
#include "session/sm-proto.h"
#include <stdio.h>
#include <unistd.h>
int main(void) {
	int sv[2];
	if (rmx_sm_socketpair(sv) < 0) { puts("ROSSA: socketpair"); return 1; }
	if (rmx_sm_send(sv[0], RMX_MSG_LOCK, NULL, 0, NULL, 0) < 0) {
		puts("ROSSA: send"); return 1;
	}
	uint32_t t = 0; char buf[RMX_SM_MAX_MSG]; size_t len = 99;
	int got[RMX_SM_MAX_FDS]; unsigned nfds = RMX_SM_MAX_FDS;
	int n = rmx_sm_recv(sv[1], &t, buf, sizeof buf, &len, got, &nfds);
	printf("n=%d  t=%u  len=%zu  nfds=%u\n", n, t, len, nfds);
	int ok = n > 0 && t == RMX_MSG_LOCK && len == 0 && nfds == 0;
	puts(ok ? "VERDE: il ramo `n > 0 && t == RMX_MSG_LOCK` si accende"
	        : "ROSSA: il ramo non si accenderebbe");
	return ok ? 0 : 1;
}
