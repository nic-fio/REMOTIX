/*
 * test.c — the control message that fixes the SOURCE address of a reply (src/pktinfo.h, used by send_from() in
 * src/transport.c).  25 Oct 2026, b10 c-48: the UDP socket is on the wildcard, a plain sendto() lets the kernel pick the source,
 * and for a client at fd5a:…::10 writing to ::1 it picked fd5a:…::10 — the client (connected UDP, like any QUIC client that
 * checks the server address) never saw the reply, and the handshake never completed on the server.
 *
 * What is checked, on the REAL header (src/pktinfo.h, nothing copied):
 *   1. IPv6 socket, IPv6 local -> one IPV6_PKTINFO cmsg carrying exactly that address, interface 0;
 *   2. link-local local -> the same, and the interface is the scope id;
 *   3. IPv6 socket, IPv4 local (dual-stack, v4-mapped traffic) -> the address as ::ffff:a.b.c.d;
 *   4. IPv4 socket -> one IP_PKTINFO cmsg with ipi_spec_dst = the address;
 *   5. no cmsg (length 0) for: no local address, the wildcard (both families), a socket bound to ONE address
 *      (bound_any false: behaviour unchanged), a family the socket cannot carry (IPv6 local on an IPv4 socket), a short sockaddr;
 *   6. the cmsg is well formed (CMSG_FIRSTHDR/CMSG_DATA, cmsg_len = CMSG_LEN, controllen = CMSG_SPACE);
 *   8. the fall-back (pktinfo_sendmsg()): a source the kernel refuses (192.0.2.1 is not local: sendmsg gives EINVAL on a socket
 *      on 0.0.0.0) is retried ONCE without the cmsg and the datagram arrives, from the kernel's own source; a plain error with
 *      no cmsg (ctllen 0) is NOT retried; an error that is not one of EINVAL / EADDRNOTAVAIL / ENETUNREACH / ENODEV is not retried (ENODEV: pktinfo_refusal() by itself, no network needed);
 *   9. by reading src/transport.c (argv[1], optional): read_packet() clears `rx_local` after handling the datagram
 *      (`rx_locallen = 0` after the call to read_packet_1), and send_on() — what every connection uses — never goes
 *      through `rx_local`.
 *  10. by reading src/transport.c: the log line of a refused source begins with «⚠ the kernel refused » and is written at the
 *      1st-3rd refusal and every 256th, through the hook that pktinfo_sendmsg() runs BETWEEN the two attempts — the order and the
 *      cadence the quic-conn fuzz oracle (benches/fuzz/quic-conn, on_event_line / rxq_sendmsg) demands.
 *   7. the kernel, for real (loopback, IPv4): a socket on 0.0.0.0 that sends with the cmsg for 127.0.0.2 is seen by the
 *      receiver as coming FROM 127.0.0.2 (without the cmsg it comes from 127.0.0.1).
 *
 * BUILD AND RUN (a second; nothing under /media/REMOTIX-15 is written; run from the root of the tree):
 *   nice -n 19 ionice -c3 podman run --rm --network=none --cpus=1 --memory=512m -v "$PWD:/albero:ro" localhost/remotix-fuzz sh -c '
 *     cd /tmp && clang -g -O1 -fsanitize=address,undefined -fno-sanitize-recover=undefined -std=gnu11 -D_GNU_SOURCE -Wall -Wextra \
 *        -I/albero/src /albero/benches/unit/pktinfo/test.c -o test && ./test /albero/src/transport.c'
 * Exit code 0 = every check passed, 1 = a check failed.
 */
#include "pktinfo.h"

#include <arpa/inet.h>
#include <errno.h>
#include <stdio.h>
#include <unistd.h>

static int checks, bad;

/* the on_refused hook: counts the calls and keeps the errno and whether the cmsg was still on the message */
static struct { int calls, err; bool had_ctl; struct msghdr *mh; } hook;
static void on_refused(void *ctx, int err)
{
	(void)ctx;
	hook.calls++;
	hook.err = err;
	hook.had_ctl = hook.mh && hook.mh->msg_control != NULL;
}
#define CHECK(cond, ...) do { checks++; if (!(cond)) { bad++; printf("FAIL: "); printf(__VA_ARGS__); printf("\n"); } } while (0)

static struct sockaddr_in6 v6(const char *text, unsigned scope)
{
	struct sockaddr_in6 a;
	memset(&a, 0, sizeof a);
	a.sin6_family = AF_INET6;
	a.sin6_port = htons(7451);
	a.sin6_scope_id = scope;
	inet_pton(AF_INET6, text, &a.sin6_addr);
	return a;
}

static struct sockaddr_in v4(const char *text)
{
	struct sockaddr_in a;
	memset(&a, 0, sizeof a);
	a.sin_family = AF_INET;
	a.sin_port = htons(7451);
	inet_pton(AF_INET, text, &a.sin_addr);
	return a;
}

/* the one cmsg of `ctl`, checked for form; NULL if absent */
static struct cmsghdr *one(union pktinfo_ctl *ctl, size_t len, int level, int type, size_t datalen)
{
	struct msghdr mh;
	struct cmsghdr *cm;
	memset(&mh, 0, sizeof mh);
	mh.msg_control = ctl;
	mh.msg_controllen = len;
	cm = CMSG_FIRSTHDR(&mh);
	CHECK(cm != NULL, "no cmsg in %zu bytes", len);
	if (!cm)
		return NULL;
	CHECK(cm->cmsg_level == level && cm->cmsg_type == type, "cmsg level/type %d/%d, wanted %d/%d",
	      cm->cmsg_level, cm->cmsg_type, level, type);
	CHECK(cm->cmsg_len == CMSG_LEN(datalen), "cmsg_len %zu, wanted %zu", (size_t)cm->cmsg_len, (size_t)CMSG_LEN(datalen));
	CHECK(len == CMSG_SPACE(datalen), "controllen %zu, wanted %zu", len, (size_t)CMSG_SPACE(datalen));
	CHECK(CMSG_NXTHDR(&mh, cm) == NULL, "more than one cmsg");
	return cm;
}

int main(int argc, char **argv)
{
	union pktinfo_ctl ctl;
	size_t n;
	struct cmsghdr *cm;
	struct in6_pktinfo p6;
	struct in_pktinfo p4;

	/* 1. IPv6 / IPv6 */
	{
		struct sockaddr_in6 l = v6("fd5a:f100:d000:1::10", 0);
		struct in6_addr want = l.sin6_addr;
		n = pktinfo_cmsg(AF_INET6, true, (struct sockaddr *)&l, sizeof l, &ctl);
		cm = one(&ctl, n, IPPROTO_IPV6, IPV6_PKTINFO, sizeof p6);
		if (cm) {
			memcpy(&p6, CMSG_DATA(cm), sizeof p6);
			CHECK(memcmp(&p6.ipi6_addr, &want, 16) == 0, "IPv6 source is not the local address");
			CHECK(p6.ipi6_ifindex == 0, "interface %u, wanted 0", p6.ipi6_ifindex);
		}
	}
	/* 2. link-local: the interface travels */
	{
		struct sockaddr_in6 l = v6("fe80::1", 7);
		n = pktinfo_cmsg(AF_INET6, true, (struct sockaddr *)&l, sizeof l, &ctl);
		cm = one(&ctl, n, IPPROTO_IPV6, IPV6_PKTINFO, sizeof p6);
		if (cm) {
			memcpy(&p6, CMSG_DATA(cm), sizeof p6);
			CHECK(p6.ipi6_ifindex == 7, "link-local interface %u, wanted 7", p6.ipi6_ifindex);
		}
	}
	/* 3. IPv6 socket, IPv4 local: v4-mapped */
	{
		struct sockaddr_in l = v4("192.0.2.9");
		struct in6_addr want;
		inet_pton(AF_INET6, "::ffff:192.0.2.9", &want);
		n = pktinfo_cmsg(AF_INET6, true, (struct sockaddr *)&l, sizeof l, &ctl);
		cm = one(&ctl, n, IPPROTO_IPV6, IPV6_PKTINFO, sizeof p6);
		if (cm) {
			memcpy(&p6, CMSG_DATA(cm), sizeof p6);
			CHECK(memcmp(&p6.ipi6_addr, &want, 16) == 0, "v4-mapped source is not ::ffff:192.0.2.9");
		}
	}
	/* 4. IPv4 socket */
	{
		struct sockaddr_in l = v4("192.0.2.9");
		n = pktinfo_cmsg(AF_INET, true, (struct sockaddr *)&l, sizeof l, &ctl);
		cm = one(&ctl, n, IPPROTO_IP, IP_PKTINFO, sizeof p4);
		if (cm) {
			memcpy(&p4, CMSG_DATA(cm), sizeof p4);
			CHECK(p4.ipi_spec_dst.s_addr == l.sin_addr.s_addr, "IPv4 ipi_spec_dst is not the local address");
			CHECK(p4.ipi_ifindex == 0, "IPv4 interface %d, wanted 0", p4.ipi_ifindex);
		}
	}
	/* 5. no cmsg */
	{
		struct sockaddr_in6 l6 = v6("fd5a:f100:d000:1::10", 0), any6 = v6("::", 0);
		struct sockaddr_in l4 = v4("192.0.2.9"), any4 = v4("0.0.0.0");
		CHECK(pktinfo_cmsg(AF_INET6, true, NULL, 0, &ctl) == 0, "no local address gave a cmsg");
		CHECK(pktinfo_cmsg(AF_INET6, true, (struct sockaddr *)&l6, 0, &ctl) == 0, "length 0 gave a cmsg");
		CHECK(pktinfo_cmsg(AF_INET6, true, (struct sockaddr *)&any6, sizeof any6, &ctl) == 0, "the IPv6 wildcard gave a cmsg");
		CHECK(pktinfo_cmsg(AF_INET6, true, (struct sockaddr *)&any4, sizeof any4, &ctl) == 0, "the IPv4 wildcard on an IPv6 socket gave a cmsg");
		CHECK(pktinfo_cmsg(AF_INET, true, (struct sockaddr *)&any4, sizeof any4, &ctl) == 0, "the IPv4 wildcard gave a cmsg");
		CHECK(pktinfo_cmsg(AF_INET6, false, (struct sockaddr *)&l6, sizeof l6, &ctl) == 0, "a socket bound to one IPv6 address gave a cmsg");
		CHECK(pktinfo_cmsg(AF_INET, false, (struct sockaddr *)&l4, sizeof l4, &ctl) == 0, "a socket bound to one IPv4 address gave a cmsg");
		CHECK(pktinfo_cmsg(AF_INET, true, (struct sockaddr *)&l6, sizeof l6, &ctl) == 0, "an IPv6 local on an IPv4 socket gave a cmsg");
		CHECK(pktinfo_cmsg(AF_INET6, true, (struct sockaddr *)&l6, sizeof(struct sockaddr_in6) - 1, &ctl) == 0, "a short sockaddr_in6 gave a cmsg");
		CHECK(pktinfo_cmsg(AF_INET, true, (struct sockaddr *)&l4, sizeof(struct sockaddr_in) - 1, &ctl) == 0, "a short sockaddr_in gave a cmsg");
	}
	/* 7. the kernel, for real (loopback IPv4: 0.0.0.0 -> 127.0.0.1, the source asked is 127.0.0.2) */
	{
		int rx = socket(AF_INET, SOCK_DGRAM, 0), tx = socket(AF_INET, SOCK_DGRAM, 0);
		struct sockaddr_in rxa = v4("127.0.0.1"), txa = v4("0.0.0.0"), from, l = v4("127.0.0.2");
		socklen_t fl = sizeof from, ml = sizeof rxa;
		char buf[16];
		int round;
		rxa.sin_port = 0;
		txa.sin_port = 0;
		CHECK(rx >= 0 && tx >= 0, "socket: %m");
		CHECK(bind(rx, (struct sockaddr *)&rxa, sizeof rxa) == 0, "bind rx: %m");
		CHECK(bind(tx, (struct sockaddr *)&txa, sizeof txa) == 0, "bind tx: %m");
		getsockname(rx, (struct sockaddr *)&rxa, &ml);
		for (round = 0; round < 2 && rx >= 0 && tx >= 0; round++) {
			struct iovec iov = {(void *)"ping", 4};
			struct msghdr mh;
			memset(&mh, 0, sizeof mh);
			mh.msg_name = &rxa;
			mh.msg_namelen = sizeof rxa;
			mh.msg_iov = &iov;
			mh.msg_iovlen = 1;
			if (round == 1) {   /* with the cmsg */
				n = pktinfo_cmsg(AF_INET, true, (struct sockaddr *)&l, sizeof l, &ctl);
				mh.msg_control = &ctl;
				mh.msg_controllen = n;
			}
			CHECK(sendmsg(tx, &mh, 0) == 4, "sendmsg round %d: %m", round);
			fl = sizeof from;
			CHECK(recvfrom(rx, buf, sizeof buf, MSG_DONTWAIT, (struct sockaddr *)&from, &fl) == 4, "recv round %d: %m", round);
			CHECK(from.sin_addr.s_addr == (round ? l.sin_addr.s_addr : rxa.sin_addr.s_addr),
			      "round %d: the receiver saw the source %s", round, inet_ntoa(from.sin_addr));
		}
		if (rx >= 0)
			close(rx);
		if (tx >= 0)
			close(tx);
	}
	/* 8. the fall-back */
	{
		int rx = socket(AF_INET, SOCK_DGRAM, 0), tx = socket(AF_INET, SOCK_DGRAM, 0), c;
		struct sockaddr_in rxa = v4("127.0.0.1"), txa = v4("0.0.0.0"), from, badsrc = v4("192.0.2.1");
		socklen_t fl = sizeof from, ml = sizeof rxa;
		char buf[16];
		rxa.sin_port = 0;
		txa.sin_port = 0;
		CHECK(rx >= 0 && tx >= 0, "socket: %m");
		CHECK(bind(rx, (struct sockaddr *)&rxa, sizeof rxa) == 0, "bind rx: %m");
		CHECK(bind(tx, (struct sockaddr *)&txa, sizeof txa) == 0, "bind tx: %m");
		getsockname(rx, (struct sockaddr *)&rxa, &ml);
		for (c = 0; c < 3 && rx >= 0 && tx >= 0; c++) {
			struct iovec iov = {(void *)"ping", 4};
			struct msghdr mh;
			int fb = -1;
			hook.mh = &mh;
			hook.calls = 0;
			ssize_t r;
			memset(&mh, 0, sizeof mh);
			mh.msg_name = &rxa;
			mh.msg_namelen = sizeof rxa;
			mh.msg_iov = &iov;
			mh.msg_iovlen = 1;
			n = pktinfo_cmsg(AF_INET, true, (struct sockaddr *)&badsrc, sizeof badsrc, &ctl);
			CHECK(n > 0, "no cmsg for 192.0.2.1");
			mh.msg_control = &ctl;
			mh.msg_controllen = n;
			if (c == 0) {          /* refused source: one retry, the datagram arrives */
				r = pktinfo_sendmsg(tx, &mh, n, on_refused, NULL);
				fb = hook.err;
				CHECK(r == 4 && pktinfo_refusal(fb), "refused source: result %zd, first errno %d (%m)", r, fb);   /* the kernel says ENETUNREACH here */
				CHECK(hook.calls == 1 && hook.had_ctl, "the hook ran %d times, cmsg still set at the call: %d (it must run BETWEEN the two attempts)", hook.calls, hook.had_ctl);
				fl = sizeof from;
				CHECK(recvfrom(rx, buf, sizeof buf, MSG_DONTWAIT, (struct sockaddr *)&from, &fl) == 4,
				      "the retried datagram did not arrive: %m");
				CHECK(from.sin_addr.s_addr == rxa.sin_addr.s_addr, "retried datagram came from %s", inet_ntoa(from.sin_addr));
			} else if (c == 1) {   /* ctllen 0 means no cmsg was asked: the error stands (bad destination) */
				struct sockaddr_in far = v4("192.0.2.1");
				mh.msg_control = NULL;
				mh.msg_controllen = 0;
				mh.msg_name = &far;
				close(tx);
				tx = socket(AF_INET, SOCK_DGRAM, 0);
				r = pktinfo_sendmsg(tx, &mh, 0, on_refused, NULL);
				CHECK(hook.calls == 0, "retried with no cmsg asked");
				(void)fb;
				(void)r;
			} else {               /* an error that is not about the source: not retried (EMSGSIZE) */
				static char big[70000];
				struct iovec iovb = {big, sizeof big};
				mh.msg_iov = &iovb;
				r = pktinfo_sendmsg(tx, &mh, n, on_refused, NULL);
				CHECK(r < 0 && hook.calls == 0 && errno == EMSGSIZE, "EMSGSIZE: result %zd, hook calls %d, errno %d", r, hook.calls, errno);
				(void)fb;
			}
		}
		if (rx >= 0)
			close(rx);
		if (tx >= 0)
			close(tx);
	}
	/* 8b. which errors are a refused source (no network needed) */
	CHECK(pktinfo_refusal(EINVAL) && pktinfo_refusal(EADDRNOTAVAIL) && pktinfo_refusal(ENETUNREACH) && pktinfo_refusal(ENODEV),
	      "a refused-source errno is not recognised");
	CHECK(!pktinfo_refusal(0) && !pktinfo_refusal(EMSGSIZE) && !pktinfo_refusal(EAGAIN) && !pktinfo_refusal(ECONNREFUSED) &&
	      !pktinfo_refusal(EPERM) && !pktinfo_refusal(ENOBUFS), "an ordinary send error is taken for a refused source");
	/* 9. reading the code */
	if (argc > 1) {
		FILE *f = fopen(argv[1], "r");
		static char src[4 << 20];
		size_t got = f ? fread(src, 1, sizeof src - 1, f) : 0;
		const char *a, *b, *c2;
		if (f)
			fclose(f);
		src[got] = 0;
		CHECK(got > 0, "cannot read %s", argv[1]);
		a = strstr(src, "\tread_packet_1(t, local, localelen, remote, remotelen, pi, data, len);");
		b = a ? strstr(a, "t->rx_locallen = 0;") : NULL;
		c2 = a ? strstr(a, "\n}\n") : NULL;
		CHECK(a && b && c2 && b < c2, "read_packet() does not clear rx_local after read_packet_1()");
		a = strstr(src, "static void send_on(");
		b = a ? strstr(a, "\n}\n") : NULL;
		c2 = a ? strstr(a, "rx_local") : NULL;
		CHECK(a && b && (!c2 || c2 > b), "send_on() uses rx_local");
	}
	if (argc > 1) {
		FILE *f = fopen(argv[1], "r");
		static char src[4 << 20];
		size_t got = f ? fread(src, 1, sizeof src - 1, f) : 0;
		const char *a;
		if (f)
			fclose(f);
		src[got] = 0;
		a = strstr(src, "static void pktinfo_refused_line(");
		CHECK(a != NULL, "pktinfo_refused_line() not found");
		CHECK(a && strstr(a, "refusals <= 3 || refusals % 256 == 0") != NULL, "cadence is not «1st-3rd and every 256th»");
		CHECK(a && strstr(a, "\"⚠ the kernel refused ") != NULL, "the line does not begin with «⚠ the kernel refused »");
		CHECK(strstr(src, "pktinfo_sendmsg(t->fd, &mh, ctllen, pktinfo_refused_line, NULL)") != NULL, "send_from() does not pass the hook");
	}
	printf("pktinfo: %d checks, %d failed\n", checks, bad);
	return bad ? 1 : 0;
}
