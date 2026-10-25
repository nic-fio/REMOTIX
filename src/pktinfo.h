/* pktinfo.h — the SOURCE ADDRESS of a reply (transport.c, send_from()).
 *
 * ⛔ Why: the UDP socket is bound to the wildcard (`::` or `0.0.0.0`).  With a plain
 *    `sendto()` the KERNEL picks the source address of every reply, and it does not
 *    have to be the address the client wrote to: on a host with several addresses
 *    (global + ULA + temporary IPv6, or any multi-homed IPv4) it picks by its own rules, and for a
 *    destination that is itself a local address (RFC 6724 rule 1) it picks THAT one.  A QUIC client
 *    drops, or treats as another path, a reply that does not come from the address
 *    it sent to: the handshake never completes on the server, and the client sees a
 *    server that does not answer.  `[M]` 25 Oct 2026, b10 c-48 (clients fd5a:…::10 -> ::1 on `lo`):
 *    a connected UDP6 client got NOTHING from a `sendto()` reply and got it with this cmsg.
 *    The datagram is read with IP_PKTINFO / IPV6_RECVPKTINFO already (read_packet()); here it is
 *    written back.
 *
 * pktinfo_cmsg() builds the control message that fixes the source to `local`, and
 * returns its length (0 = no control message: send as before).  No control message when
 *   · there is no local address, or it is the wildcard;
 *   · the socket is bound to ONE address (`bound_any` false): the source is already that one.
 * IPv6 socket: IPV6_PKTINFO with the address; an IPv4 `local` becomes ::ffff:a.b.c.d (v4-mapped
 * traffic on a dual-stack socket).  A link-local address carries its interface (the scope id).
 * IPv4 socket: IP_PKTINFO with ipi_spec_dst = the address. */
#ifndef REMOTIX_PKTINFO_H
#define REMOTIX_PKTINFO_H

#include <errno.h>
#include <netinet/in.h>
#include <string.h>
#include <sys/socket.h>
#include <stdbool.h>
#include <stddef.h>

/* big enough for either cmsg, aligned for struct cmsghdr */
union pktinfo_ctl {
	char buf[CMSG_SPACE(sizeof(struct in6_pktinfo)) > CMSG_SPACE(sizeof(struct in_pktinfo))
	         ? CMSG_SPACE(sizeof(struct in6_pktinfo)) : CMSG_SPACE(sizeof(struct in_pktinfo))];
	struct cmsghdr align;
};

static inline size_t pktinfo_cmsg(int sock_family, bool bound_any, const struct sockaddr *local,
                                  socklen_t locallen, union pktinfo_ctl *ctl)
{
	struct cmsghdr *cm;
	if (!bound_any || !local || locallen == 0)
		return 0;
	memset(ctl, 0, sizeof *ctl);
	if (sock_family == AF_INET6) {
		struct in6_pktinfo pk;
		memset(&pk, 0, sizeof pk);
		if (local->sa_family == AF_INET6 && locallen >= sizeof(struct sockaddr_in6)) {
			const struct sockaddr_in6 *s6 = (const struct sockaddr_in6 *)local;
			if (IN6_IS_ADDR_UNSPECIFIED(&s6->sin6_addr))
				return 0;
			pk.ipi6_addr = s6->sin6_addr;
			if (IN6_IS_ADDR_LINKLOCAL(&s6->sin6_addr))
				pk.ipi6_ifindex = s6->sin6_scope_id;
		} else if (local->sa_family == AF_INET && locallen >= sizeof(struct sockaddr_in)) {
			const struct sockaddr_in *s4 = (const struct sockaddr_in *)local;
			if (s4->sin_addr.s_addr == htonl(INADDR_ANY))
				return 0;
			pk.ipi6_addr.s6_addr[10] = pk.ipi6_addr.s6_addr[11] = 0xff;
			memcpy(pk.ipi6_addr.s6_addr + 12, &s4->sin_addr, 4);
		} else {
			return 0;
		}
		cm = (struct cmsghdr *)ctl;
		cm->cmsg_level = IPPROTO_IPV6;
		cm->cmsg_type = IPV6_PKTINFO;
		cm->cmsg_len = CMSG_LEN(sizeof pk);
		memcpy(CMSG_DATA(cm), &pk, sizeof pk);
		return CMSG_SPACE(sizeof pk);
	}
	if (sock_family == AF_INET && local->sa_family == AF_INET && locallen >= sizeof(struct sockaddr_in)) {
		const struct sockaddr_in *s4 = (const struct sockaddr_in *)local;
		struct in_pktinfo pk;
		if (s4->sin_addr.s_addr == htonl(INADDR_ANY))
			return 0;
		memset(&pk, 0, sizeof pk);
		pk.ipi_spec_dst = s4->sin_addr;
		cm = (struct cmsghdr *)ctl;
		cm->cmsg_level = IPPROTO_IP;
		cm->cmsg_type = IP_PKTINFO;
		cm->cmsg_len = CMSG_LEN(sizeof pk);
		memcpy(CMSG_DATA(cm), &pk, sizeof pk);
		return CMSG_SPACE(sizeof pk);
	}
	return 0;
}


/* The errors with which the kernel refuses the SOURCE we asked for, and not the datagram: EINVAL, EADDRNOTAVAIL,
 * ENETUNREACH, ENODEV (the address was just taken off the interface — a temporary IPv6 address expiring —, the
 * interface went away, or the address is not local any more). */
static inline bool pktinfo_refusal(int err)
{
	return err == EINVAL || err == EADDRNOTAVAIL || err == ENETUNREACH || err == ENODEV;
}

/* sendmsg() with the control message of pktinfo_cmsg() (`ctllen` > 0), and ONE retry without it when the kernel
 * refuses the source (pktinfo_refusal()).  Otherwise that connection would stay mute for ever, where before this file
 * the kernel chose a source.  `*refused_errno` is 0, or the errno of the FIRST attempt when the retry happened (the
 * caller writes ONE log line, rate limited, with it).  Returns the result of the last sendmsg(); errno is that
 * attempt's. */
static inline ssize_t pktinfo_sendmsg(int fd, struct msghdr *mh, size_t ctllen, int *refused_errno)
{
	ssize_t n;
	*refused_errno = 0;
	do {
		n = sendmsg(fd, mh, 0);
	} while (n < 0 && errno == EINTR);
	if (n < 0 && ctllen && pktinfo_refusal(errno)) {
		*refused_errno = errno;
		mh->msg_control = NULL;
		mh->msg_controllen = 0;
		do {
			n = sendmsg(fd, mh, 0);
		} while (n < 0 && errno == EINTR);
	}
	return n;
}

#endif
