/*
 * test.c — the TWO implementations of the address key must give the SAME key (§1.9-bis, closed by §11.53 / §11.40):
 *   address_key()      src/transport.c   the connection caps (pending per address / per /48), on a sockaddr
 *   rcp_key_address()  src/rcp.c         the login ban, on TEXT («1.2.3.4», «[2001:db8::1]:443», «fe80::1%eth0» ...)
 * A drift between the two would let an attacker be counted under one key by the caps and under another by the ban.
 *
 * HOW: the REAL src/transport.c is #included (so its static address_key() can be called) and the REAL src/rcp.c is compiled
 * as a separate object; neither is modified.  The log is benches/fuzz/rcp-msg/stubs_log.c; everything else the two files link
 * to (ngtcp2, PAM, helper ...) is generated as a stub that TRAPS if reached.  Each row of the table is a text given to
 * rcp_key_address() and the bare address the same peer would have as a sockaddr; the 16-byte key of address_key() and the
 * address inside rcp_key_address()'s «[...]» answer (parsed back, IPv4 as ::ffff:a.b.c.d) must be equal.  A text that is
 * not an address (bare == NULL) has no sockaddr: rcp_key_address() must keep it, «[text]», unparsed.  Idempotence is checked too.
 *
 * BUILD AND RUN (a few seconds; nothing under /media/REMOTIX-15 is written; run from the root of the tree):
 *   nice -n 19 ionice -c3 podman run --rm --cpus=2 -v "$PWD:/albero:ro" localhost/remotix-fuzz sh -c '
 *     cd /tmp && F="-g -O1 -fsanitize=address,undefined -fno-sanitize-recover=undefined -std=gnu11 -D_GNU_SOURCE \
 *        -Wno-unused-parameter -I/albero/src -I/albero/benches/fuzz/rcp-msg" &&
 *     clang $F -c /albero/benches/unit/address-key/test.c -o t.o && clang $F -c /albero/src/rcp.c -o r.o &&
 *     clang $F -c /albero/benches/fuzz/rcp-msg/stubs_log.c -o l.o &&
 *     { clang -fsanitize=address,undefined t.o r.o l.o -o t0 2> link1.log || true; } &&
 *     { echo "#include <stdio.h>"; grep -o "undefined reference to .[A-Za-z_0-9]*" link1.log | sed "s/.*to .//" | sort -u |
 *       while read -r n; do echo "void $n(void); void $n(void) { fputs(\"STUB reached: $n\", stderr); fputc(10, stderr); __builtin_trap(); }"; done; } > s.c &&
 *     clang $F -c s.c -o s.o && clang -fsanitize=address,undefined t.o r.o l.o s.o -o test && ./test'
 * Exit code 0 = every row equal.
 */
#include "transport.c"

#include <stdio.h>

static int checks, bad;

#define CHECK(cond, ...) do { checks++; if (!(cond)) { bad++; printf("FAIL: "); printf(__VA_ARGS__); printf("\n"); } } while (0)

struct row { const char *text; const char *bare; };   /* bare == NULL: not an address */

static const struct row ROWS[] = {
	/* IPv4: whole; with port */
	{"192.168.0.2", "192.168.0.2"}, {"192.168.0.2:4433", "192.168.0.2"}, {"[192.168.0.2]:4433", "192.168.0.2"}, {"[10.1.2.3]", "10.1.2.3"},
	{"127.0.0.1", "127.0.0.1"}, {"0.0.0.0", "0.0.0.0"}, {"255.255.255.255", "255.255.255.255"},
	/* v4-mapped and NAT64: the IPv4 inside */
	{"::ffff:1.2.3.4", "::ffff:1.2.3.4"}, {"[::ffff:1.2.3.4]:443", "::ffff:1.2.3.4"}, {"::ffff:0102:0304", "::ffff:0102:0304"},
	{"64:ff9b::1.2.3.4", "64:ff9b::1.2.3.4"}, {"[64:ff9b::c000:201]:443", "64:ff9b::c000:201"},
	/* loopback: whole */
	{"::1", "::1"}, {"[::1]", "::1"}, {"[::1]:443", "::1"},
	/* global IPv6: the /64 */
	{"2001:db8:1:2:dead:beef:0:1", "2001:db8:1:2:dead:beef:0:1"}, {"[2001:db8:1:2:dead:beef:0:1]:443", "2001:db8:1:2:dead:beef:0:1"},
	{"2001:db8:1:2::", "2001:db8:1:2::"}, {"[2001:db8:ffff:ffff:ffff:ffff:ffff:ffff]", "2001:db8:ffff:ffff:ffff:ffff:ffff:ffff"},
	{"2a00:1450:4002:41c::8a", "2a00:1450:4002:41c::8a"}, {"::", "::"}, {"::2", "::2"},
	/* link-local, with and without zone */
	{"fe80::1", "fe80::1"}, {"fe80::1%eth0", "fe80::1"}, {"[fe80::abcd:1%enp3s0]:443", "fe80::abcd:1"}, {"fe80::5ea1:441a:978d:6d0e%eth0", "fe80::5ea1:441a:978d:6d0e"},
	/* not an address: kept as it was */
	{"", NULL}, {"hello", NULL}, {"[not an address]", NULL}, {"1.2.3", NULL}, {"1.2.3.4.5", NULL}, {"999.1.1.1", NULL}, {"2001:db8::zz", NULL},
	{"[1.2.3", NULL}, {"::ffff:1.2.3", NULL},
};

/* "[x]" -> the 16-byte form (IPv4 as ::ffff:a.b.c.d); 0 if x is not an address */
static int parse_report(const char *report, uint8_t out[16])
{
	char inner[128];
	size_t n = strlen(report);
	struct in_addr a4;

	if (n < 3 || report[0] != '[' || report[n - 1] != ']' || n - 2 >= sizeof inner)
		return 0;
	memcpy(inner, report + 1, n - 2);
	inner[n - 2] = 0;
	if (inet_pton(AF_INET, inner, &a4) == 1) {
		memset(out, 0, 16);
		out[10] = out[11] = 0xff;
		memcpy(out + 12, &a4, 4);
		return 1;
	}
	return inet_pton(AF_INET6, inner, out) == 1;
}

int main(void)
{
	for (size_t i = 0; i < sizeof ROWS / sizeof ROWS[0]; i++) {
		const struct row *r = &ROWS[i];
		char report[128], again[128];
		uint8_t from_text[16], key[16], key48[16];

		rcp_key_address(r->text, report, sizeof report);
		if (!r->bare) {
			CHECK(strchr(report, '[') == report, "«%s»: not an address, the answer is still bracketed: %s", r->text, report);
			CHECK(!parse_report(report, from_text), "«%s»: not an address, yet it was given a key: %s", r->text, report);
			rcp_key_address(report, again, sizeof again);
			CHECK(strcmp(report, again) == 0 || parse_report(again, from_text) == 0, "«%s»: not stable: «%s» then «%s»", r->text, report, again);
			continue;
		}
		/* the sockaddr of the same peer */
		struct sockaddr_storage ss;
		memset(&ss, 0, sizeof ss);
		struct in_addr a4;
		struct in6_addr a6;
		if (inet_pton(AF_INET, r->bare, &a4) == 1) {
			struct sockaddr_in *s4 = (struct sockaddr_in *)&ss;
			s4->sin_family = AF_INET;
			s4->sin_addr = a4;
			s4->sin_port = htons(4433);
		} else {
			struct sockaddr_in6 *s6 = (struct sockaddr_in6 *)&ss;
			CHECK(inet_pton(AF_INET6, r->bare, &a6) == 1, "row «%s»: the bare address «%s» does not parse (a defect of the table)", r->text, r->bare);
			s6->sin6_family = AF_INET6;
			s6->sin6_addr = a6;
			s6->sin6_port = htons(4433);
		}
		address_key((struct sockaddr *)&ss, key, key48);
		CHECK(parse_report(report, from_text), "«%s»: rcp_key_address gave «%s», which is not a bracketed address", r->text, report);
		CHECK(memcmp(from_text, key, 16) == 0, "«%s»: rcp_key_address «%s» and address_key DISAGREE", r->text, report);
		rcp_key_address(report, again, sizeof again);
		CHECK(strcmp(report, again) == 0, "«%s»: not idempotent: «%s» then «%s»", r->text, report, again);
		/* the /48 of the caps is the key itself for everything but a plain global IPv6 */
		CHECK(memcmp(key48, key, 6) == 0, "«%s»: the /48 key must share the first 48 bits of the key", r->text);
	}
	printf("\n%d checks, %d failed\n", checks, bad);
	return bad ? 1 : 0;
}
