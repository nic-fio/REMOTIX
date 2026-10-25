/*
 * 02-walls-test.c — ⭐ 1.5 (DECISIONS.md §11.50): the network side's walls,
 *                   `src/walls.c` INCLUDED (its statics reachable), on a desk.
 *
 * Two halves, and the half that runs depends on who runs it:
 *
 *   · as an ordinary user (rxtest build, uid 1000): the failure paths — no
 *     options, an unknown user, not root — each must refuse with its reason
 *     and leave the process as it was (same uid, same mount namespace); and
 *     the SELinux context rewrite;
 *   · as root in a container that may mount (`--privileged`, or
 *     `--cap-add SYS_ADMIN --security-opt seccomp=unconfined`): a missing and
 *     a foreign-owned directory refuse; then, in a fork, the walls for real
 *     with the user `nobody`: / read-only (EROFS even in a directory nobody
 *     owns), the two directories writable, /tmp private and empty, uid/gid
 *     nobody, no supplementary group, every capability set 0, NoNewPrivs 1 —
 *     and the parent's tree untouched afterwards.
 *
 *   cd src && make test-walls                     (either half, by uid)
 *   root: podman run --rm --network=none --privileged -v TREE:/albero \
 *           -w /albero/src localhost/remotix-costruzione make test-walls
 *
 * ⭐ 1.5 (audit split R5/R6), two cases that need no mounts: `own_network()` and `scope_abstract_sockets()` are called in a FORK
 *   with sockets made BEFORE them — an abstract listener, a path listener, two UDP sockets and a TCP listener on 127.0.0.1, a
 *   socketpair:
 *     · after `own_network()` (needs CAP_SYS_ADMIN: root, or `unshare -r`; else the case says it is skipped) a connect() to the
 *       abstract name is refused, a path socket still connects, the inherited UDP socket still sends and the inherited TCP listener
 *       still accepts a connection made from OUTSIDE, the socketpair works, a new socket cannot reach the host's 127.0.0.1, the
 *       private loopback is up, and getaddrinfo() of a numeric address and of localhost answers;
 *     · after `scope_abstract_sockets()` (any user; the kernel needs Landlock ABI 6, else it says so) a connect() to the abstract
 *       name is EPERM while a path socket, UDP and a socketpair still work.
 *   Under `unshare -r` the first runs on an ordinary desk; the real walls still need root.
 *
 * Exit 0 all passed · 1 a check failed · 3 could not look (root without the
 * power to mount, or no user `nobody`).  The last line is «N passed, M
 * failed, of K».
 */
#include "walls.c"

#include <pwd.h>

#include <arpa/inet.h>
#include <netdb.h>
#include <netinet/in.h>
#include <poll.h>
#include <sys/un.h>
#include <sys/wait.h>

static int passed, failed;

#define CHECK(cond, ...)                                                   \
	do {                                                               \
		if (cond) {                                                \
			passed++;                                          \
			printf("  ok   ");                                 \
		} else {                                                   \
			failed++;                                          \
			printf("  FAIL ");                                 \
		}                                                          \
		printf(__VA_ARGS__);                                       \
		printf("\n");                                              \
	} while (0)

static ino_t mnt_ns(void)
{
	struct stat st;
	return stat("/proc/self/ns/mnt", &st) == 0 ? st.st_ino : 0;
}

static struct rootside_options opts(uid_t uid, gid_t gid, const char *state, const char *run)
{
	struct rootside_options o;
	memset(&o, 0, sizeof o);
	o.remotix_uid = uid;
	o.remotix_gid = gid;
	o.net_state_dir = state;
	o.net_run_dir = run;
	return o;
}

static void case_context(void)
{
	char out[128];
	CHECK(context_with_type("system_u:system_r:remotix_t:s0", "remotix_net_t", out,
	                        sizeof out) &&
	          strcmp(out, "system_u:system_r:remotix_net_t:s0") == 0,
	      "context: the type is replaced, the level kept («%s»)", out);
	CHECK(context_with_type("system_u:system_r:remotix_t:s0-s0:c0.c1023", "remotix_net_t",
	                        out, sizeof out) &&
	          strcmp(out, "system_u:system_r:remotix_net_t:s0-s0:c0.c1023") == 0,
	      "context: a level with «:» inside is kept whole («%s»)", out);
	CHECK(context_with_type("u:r:t", "x_t", out, sizeof out) && strcmp(out, "u:r:x_t") == 0,
	      "context: no level («%s»)", out);
	CHECK(!context_with_type("u:r", "x_t", out, sizeof out), "context: two fields refused");
	CHECK(!context_with_type("u:r::s0", "x_t", out, sizeof out), "context: empty type refused");
	CHECK(!context_with_type("system_u:system_r:remotix_t:s0", "remotix_net_t", out, 10),
	      "context: a buffer too small refused");
}

static void case_unprivileged(const struct passwd *nb)
{
	char why[512];
	uid_t u0 = getuid();
	ino_t ns0 = mnt_ns();
	struct rootside_options o;

	CHECK(walls_apply(NULL, why, sizeof why) == -1 && why[0], "no options: refused («%s»)",
	      why);
	o = opts(0, 0, "/nonexistent", "/nonexistent");
	CHECK(walls_apply(&o, why, sizeof why) == -1 && strstr(why, "must not be root"),
	      "uid 0 as the network user: refused («%s»)", why);
	o = opts(1234, 0, "/nonexistent", "/nonexistent");
	CHECK(walls_apply(&o, why, sizeof why) == -1 && strstr(why, "must not be root"),
	      "gid 0 as the network group: refused («%s»)", why);
	if (nb && geteuid() != 0) {
		o = opts(nb->pw_uid, nb->pw_gid, "/nonexistent", "/nonexistent");
		CHECK(walls_apply(&o, why, sizeof why) == -1 && strstr(why, "must run as root"),
		      "not root: refused, said («%s»)", why);
	}
	CHECK(getuid() == u0 && mnt_ns() == ns0,
	      "after the refusals: same uid (%ld) and same mount namespace", (long)getuid());
}

static bool make_dir(const char *p, uid_t u, gid_t g, mode_t m)
{
	return mkdir(p, m) == 0 && chown(p, u, g) == 0 && chmod(p, m) == 0;
}

static bool write_in(const char *dir, int *err)
{
	char p[600];
	snprintf(p, sizeof p, "%s/w", dir);
	int fd = open(p, O_WRONLY | O_CREAT | O_TRUNC | O_CLOEXEC, 0600);
	*err = fd < 0 ? errno : 0;
	if (fd < 0)
		return false;
	close(fd);
	unlink(p);
	return true;
}

static uint64_t status_value(const char *key)
{
	FILE *f = fopen("/proc/self/status", "re");
	char line[256];
	uint64_t v = UINT64_MAX;
	size_t k = strlen(key);
	while (f && fgets(line, sizeof line, f))
		if (strncmp(line, key, k) == 0)
			v = strtoull(line + k, NULL, strcmp(key, "NoNewPrivs:") == 0 ? 10 : 16);
	if (f)
		fclose(f);
	return v;
}

/* ── ⭐ 1.5: the private network and the Landlock scope, in a fork ────────── */

static void rep(int out, bool ok, const char *fmt, ...) __attribute__((format(printf, 3, 4)));
static void rep(int out, bool ok, const char *fmt, ...)
{
	char b[400];
	va_list ap;
	int n = snprintf(b, sizeof b, "%d ", ok ? 1 : 0);

	va_start(ap, fmt);
	n += vsnprintf(b + n, sizeof b - (size_t)n - 2, fmt, ap);
	va_end(ap);
	if ((size_t)n > sizeof b - 2) /* vsnprintf returns what it WOULD have written */
		n = (int)sizeof b - 2;
	b[n++] = '\n';
	if (write(out, b, (size_t)n) < 0)
		_exit(70);
}

static int udp_on_loopback(uint16_t *port)
{
	struct sockaddr_in a = { .sin_family = AF_INET, .sin_addr.s_addr = htonl(INADDR_LOOPBACK) };
	socklen_t l = sizeof a;
	int s = socket(AF_INET, SOCK_DGRAM, 0);

	if (s < 0 || bind(s, (struct sockaddr *)&a, sizeof a) != 0 || getsockname(s, (struct sockaddr *)&a, &l) != 0)
		return -1;
	*port = ntohs(a.sin_port);
	return s;
}

static int abstract_listener(char *name, size_t cap)
{
	struct sockaddr_un a;
	socklen_t len;
	int s = socket(AF_UNIX, SOCK_STREAM, 0);

	snprintf(name, cap, "remotix-walls-test-%ld", (long)getpid());
	memset(&a, 0, sizeof a);
	a.sun_family = AF_UNIX;
	memcpy(a.sun_path + 1, name, strlen(name));
	len = (socklen_t)(offsetof(struct sockaddr_un, sun_path) + 1 + strlen(name));
	if (s < 0 || bind(s, (struct sockaddr *)&a, len) != 0 || listen(s, 4) != 0)
		return -1;
	return s;
}

static int connect_abstract(const char *name)
{
	struct sockaddr_un a;
	int s = socket(AF_UNIX, SOCK_STREAM, 0), e;

	memset(&a, 0, sizeof a);
	a.sun_family = AF_UNIX;
	memcpy(a.sun_path + 1, name, strlen(name));
	if (s < 0)
		return -1;
	if (connect(s, (struct sockaddr *)&a, (socklen_t)(offsetof(struct sockaddr_un, sun_path) + 1 + strlen(name))) == 0) {
		close(s);
		return 0;
	}
	e = errno;
	close(s);
	return e;
}

static int connect_path(const char *path)
{
	struct sockaddr_un a;
	int s = socket(AF_UNIX, SOCK_STREAM, 0), ok;

	memset(&a, 0, sizeof a);
	a.sun_family = AF_UNIX;
	snprintf(a.sun_path, sizeof a.sun_path, "%s", path);
	if (s < 0)
		return 0;
	ok = connect(s, (struct sockaddr *)&a, sizeof a) == 0;
	close(s);
	return ok;
}

struct netfds {
	int abs_l, path_l, udp_a, udp_b, tcp_l, sp[2];
	uint16_t port_a, port_b, port_tcp;
	char abs_name[64], path[108];
};

static bool net_setup(struct netfds *f)
{
	struct sockaddr_in a = { .sin_family = AF_INET, .sin_addr.s_addr = htonl(INADDR_LOOPBACK) };
	struct sockaddr_un u;
	socklen_t l = sizeof a;

	memset(f, 0, sizeof *f);
	f->abs_l = abstract_listener(f->abs_name, sizeof f->abs_name);
	snprintf(f->path, sizeof f->path, "/tmp/remotix-walls-test-sock.%ld", (long)getpid());
	unlink(f->path);
	memset(&u, 0, sizeof u);
	u.sun_family = AF_UNIX;
	snprintf(u.sun_path, sizeof u.sun_path, "%s", f->path);
	f->path_l = socket(AF_UNIX, SOCK_STREAM, 0);
	if (f->path_l < 0 || bind(f->path_l, (struct sockaddr *)&u, sizeof u) != 0 || listen(f->path_l, 4) != 0)
		return false;
	f->udp_a = udp_on_loopback(&f->port_a);
	f->udp_b = udp_on_loopback(&f->port_b);
	f->tcp_l = socket(AF_INET, SOCK_STREAM, 0);
	if (f->tcp_l < 0 || bind(f->tcp_l, (struct sockaddr *)&a, sizeof a) != 0 || listen(f->tcp_l, 4) != 0 ||
	    getsockname(f->tcp_l, (struct sockaddr *)&a, &l) != 0)
		return false;
	f->port_tcp = ntohs(a.sin_port);
	return f->abs_l >= 0 && f->udp_a >= 0 && f->udp_b >= 0 && socketpair(AF_UNIX, SOCK_SEQPACKET, 0, f->sp) == 0;
}

static void net_common_checks(int out, struct netfds *f, const char *when)
{
	struct sockaddr_in to = { .sin_family = AF_INET, .sin_addr.s_addr = htonl(INADDR_LOOPBACK) };
	char buf[16] = "";
	struct pollfd p;

	rep(out, connect_path(f->path), "%s: a socket on a PATH still connects", when);
	to.sin_port = htons(f->port_b);
	p = (struct pollfd){ .fd = f->udp_b, .events = POLLIN };
	rep(out, sendto(f->udp_a, "udp", 3, 0, (struct sockaddr *)&to, sizeof to) == 3 && poll(&p, 1, 2000) == 1 &&
	        recv(f->udp_b, buf, sizeof buf, 0) == 3 && memcmp(buf, "udp", 3) == 0,
	    "%s: the inherited UDP socket still sends (and its peer receives)", when);
	memset(buf, 0, sizeof buf);
	rep(out, write(f->sp[0], "pair", 4) == 4 && read(f->sp[1], buf, sizeof buf) == 4 && memcmp(buf, "pair", 4) == 0,
	    "%s: the inherited socketpair (the channel to the root side) still works", when);
}

/* The private network, in a fork.  `ready` carries the TCP port to the parent, who connects from OUTSIDE and sends "hi". */
static void net_child(int out, int ready)
{
	struct netfds f;
	char why[256] = "", line[32], buf[8] = "";
	struct addrinfo hints, *res = NULL;
	struct sockaddr_in me = { .sin_family = AF_INET, .sin_addr.s_addr = htonl(INADDR_LOOPBACK) }, to = me;
	struct pollfd p;
	socklen_t l = sizeof me;
	int s, c;

	if (!net_setup(&f)) {
		rep(out, false, "the sockets of the test could not be made (%s)", strerror(errno));
		_exit(0);
	}
	rep(out, connect_abstract(f.abs_name) == 0, "before: the abstract listener is reachable (the test would prove nothing otherwise)");
	rep(out, own_network(why, sizeof why) == 0, "own_network(): ok («%s»)", why);
	snprintf(line, sizeof line, "%u\n", (unsigned)f.port_tcp);
	if (write(ready, line, strlen(line)) < 0)
		_exit(71);
	{
		int e = connect_abstract(f.abs_name);

		rep(out, e != 0, "after: a connect() to the ABSTRACT socket is refused (errno %d: %s)", e, e ? strerror(e) : "it connected!");
	}
	net_common_checks(out, &f, "after");
	/* the TCP listener, inherited: the parent connects from outside the namespace and the child accepts */
	p = (struct pollfd){ .fd = f.tcp_l, .events = POLLIN };
	c = poll(&p, 1, 5000) == 1 ? accept(f.tcp_l, NULL, NULL) : -1;
	rep(out, c >= 0 && read(c, buf, sizeof buf) >= 2 && memcmp(buf, "hi", 2) == 0,
	    "after: the inherited TCP listener still accepts a connection made from outside");
	/* a NEW socket cannot reach the host's loopback */
	s = socket(AF_INET, SOCK_STREAM, 0);
	to.sin_port = htons(f.port_tcp);
	{
		int rc = s >= 0 ? connect(s, (struct sockaddr *)&to, sizeof to) : 0, ce = errno;

		rep(out, s >= 0 && rc != 0, "after: a new socket cannot connect to the host's 127.0.0.1 listener (errno %d)", ce);
	}
	/* the private loopback is up: a UDP socket talks to itself */
	{
		int u = socket(AF_INET, SOCK_DGRAM, 0);

		me.sin_port = 0;
		rep(out, u >= 0 && bind(u, (struct sockaddr *)&me, sizeof me) == 0 && getsockname(u, (struct sockaddr *)&me, &l) == 0 &&
		        sendto(u, "lo", 2, 0, (struct sockaddr *)&me, sizeof me) == 2 && (p = (struct pollfd){ .fd = u, .events = POLLIN }, poll(&p, 1, 1000) == 1),
		    "after: the private loopback is up (a UDP socket reaches itself)");
	}
	memset(&hints, 0, sizeof hints);
	hints.ai_flags = AI_NUMERICHOST | AI_NUMERICSERV;
	hints.ai_socktype = SOCK_DGRAM;
	rep(out, getaddrinfo("127.0.0.1", "7447", &hints, &res) == 0, "after: getaddrinfo() of a numeric address answers");
	if (res)
		freeaddrinfo(res);
	res = NULL;
	hints.ai_flags = 0;
	rep(out, getaddrinfo("localhost", "7447", &hints, &res) == 0, "after: getaddrinfo(\"localhost\") answers (NSS, /etc/hosts)");
	if (res)
		freeaddrinfo(res);
	unlink(f.path);
	_exit(0);
}

/* Landlock's scope, in a fork (any user). */
static void landlock_child(int out)
{
	struct netfds f;
	bool scoped;

	if (!net_setup(&f)) {
		rep(out, false, "the sockets of the test could not be made (%s)", strerror(errno));
		_exit(0);
	}
	if (prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) != 0) {
		rep(out, false, "PR_SET_NO_NEW_PRIVS failed");
		_exit(0);
	}
	notes[0] = '\0';
	scope_abstract_sockets();
	scoped = strstr(notes, "abstract unix sockets scoped") != NULL; /* ⚠ not «not scoped» */
	if (scoped) {
		int e = connect_abstract(f.abs_name);

		rep(out, e == EPERM, "landlock: a connect() to an abstract socket made outside is EPERM (errno %d)", e);
		net_common_checks(out, &f, "landlock");
	} else {
		rep(out, true, "landlock: (skipped) %s", notes);
	}
	unlink(f.path);
	_exit(0);
}

static void drain_report(int in)
{
	FILE *f = fdopen(in, "r");
	char line[420];

	while (f && fgets(line, sizeof line, f)) {
		line[strcspn(line, "\n")] = '\0';
		CHECK(line[0] == '1', "%s", line + 2);
	}
	if (f)
		fclose(f);
}

static bool can_new_net(void)
{
	pid_t p = fork();
	int st;

	if (p == 0)
		_exit(unshare(CLONE_NEWNET) == 0 ? 0 : 1);
	return p > 0 && waitpid(p, &st, 0) == p && WIFEXITED(st) && WEXITSTATUS(st) == 0;
}

static void case_network(void)
{
	int res[2], rdy[2], st;
	pid_t p;
	char port[16] = "";

	if (!can_new_net()) {
		printf("  (the private network needs CAP_SYS_ADMIN: root, or `unshare -r`; skipped)\n");
		return;
	}
	if (pipe(res) != 0 || pipe(rdy) != 0)
		return;
	p = fork();
	if (p == 0) {
		close(res[0]);
		close(rdy[0]);
		net_child(res[1], rdy[1]);
	}
	close(res[1]);
	close(rdy[1]);
	if (read(rdy[0], port, sizeof port - 1) > 0) {
		struct sockaddr_in a = { .sin_family = AF_INET, .sin_addr.s_addr = htonl(INADDR_LOOPBACK) };
		int s = socket(AF_INET, SOCK_STREAM, 0);

		a.sin_port = htons((uint16_t)atoi(port));
		if (s >= 0 && connect(s, (struct sockaddr *)&a, sizeof a) == 0)
			(void)write(s, "hi", 2);
		/* the descriptor stays open until the child has read: it closes with this process's turn below */
		drain_report(res[0]);
		if (s >= 0)
			close(s);
	} else {
		drain_report(res[0]);
	}
	close(rdy[0]);
	(void)waitpid(p, &st, 0);
}

/* ⭐ 1.5 (audit split R7): the socket families allow list, in a fork (any user): the filter of walls.c, installed for real. */
static void families_child(int out)
{
	static const struct { int af; const char *name; } no[] = {
		{ AF_NETLINK, "AF_NETLINK" }, { AF_PACKET, "AF_PACKET" }, { AF_VSOCK, "AF_VSOCK" },
		{ AF_ALG, "AF_ALG" }, { AF_BLUETOOTH, "AF_BLUETOOTH" }, { AF_KEY, "AF_KEY" },
	};
	struct addrinfo hints, *res = NULL;
	char why[256] = "";
	int s, sv[2], e;
	bool v6_before;

	s = socket(AF_INET6, SOCK_DGRAM, 0); /* before the filter: a kernel without IPv6 must not make the check lie */
	v6_before = s >= 0;
	if (s >= 0)
		close(s);
	if (prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) != 0 || no_user_namespaces(why, sizeof why) != 0) {
		rep(out, false, "the seccomp filter could not be installed (%s)", why);
		_exit(0);
	}
	s = socket(AF_UNIX, SOCK_STREAM, 0);
	rep(out, s >= 0, "seccomp: socket(AF_UNIX) allowed"), close(s);
	s = socket(AF_INET, SOCK_DGRAM, 0);
	rep(out, s >= 0, "seccomp: socket(AF_INET) allowed"), close(s);
	rep(out, true, "seccomp: (AF_INET6 %s before the filter)", v6_before ? "works" : "is not available here");
	s = socket(AF_INET6, SOCK_DGRAM, 0);
	e = errno;
	rep(out, !v6_before || s >= 0, "seccomp: socket(AF_INET6) still works after the filter (errno %d)", s >= 0 ? 0 : e);
	if (s >= 0)
		close(s);
	rep(out, socketpair(AF_UNIX, SOCK_SEQPACKET, 0, sv) == 0, "seccomp: socketpair(AF_UNIX) allowed");
	errno = 0;
	s = socketpair(AF_NETLINK, SOCK_DGRAM, 0, sv);
	e = errno;
	rep(out, s != 0 && e == EAFNOSUPPORT, "seccomp: socketpair(AF_NETLINK) refused with EAFNOSUPPORT (errno %d)", e);
	for (size_t i = 0; i < sizeof no / sizeof no[0]; i++) {
		errno = 0;
		s = socket(no[i].af, SOCK_DGRAM, 0);
		e = errno;
		rep(out, s < 0 && e == EAFNOSUPPORT, "seccomp: socket(%s) refused with EAFNOSUPPORT (errno %d)", no[i].name, e);
		if (s >= 0)
			close(s);
	}
	memset(&hints, 0, sizeof hints);
	hints.ai_flags = AI_ADDRCONFIG;
	hints.ai_socktype = SOCK_DGRAM;
	rep(out, getaddrinfo("localhost", "7447", &hints, &res) == 0, "seccomp: getaddrinfo(localhost) with AI_ADDRCONFIG answers (netlink refused, glibc falls back)");
	if (res)
		freeaddrinfo(res);
	res = NULL;
	hints.ai_flags = AI_ADDRCONFIG | AI_NUMERICHOST;
	rep(out, getaddrinfo("127.0.0.1", "7447", &hints, &res) == 0, "seccomp: getaddrinfo(AI_ADDRCONFIG, 127.0.0.1) still answers (netlink refused, glibc falls back)");
	_exit(0);
}

static void case_families(void)
{
	int res[2], st;
	pid_t p;

	if (pipe(res) != 0)
		return;
	p = fork();
	if (p == 0) {
		close(res[0]);
		families_child(res[1]);
	}
	close(res[1]);
	drain_report(res[0]);
	(void)waitpid(p, &st, 0);
}

static void case_landlock(void)
{
	int res[2], st;
	pid_t p;

	if (pipe(res) != 0)
		return;
	p = fork();
	if (p == 0) {
		close(res[0]);
		landlock_child(res[1]);
	}
	close(res[1]);
	drain_report(res[0]);
	(void)waitpid(p, &st, 0);
}

/* 0 = blind, else the walls were applied and checked */
static int case_root(const struct passwd *nb)
{
	char base[] = "/var/tmp/remotix-walls-test.XXXXXX";
	char state[600], run[600], outside[600], marker[600], why[512];
	struct rootside_options o;
	int err, rc = 1;

	if (!mkdtemp(base)) {
		printf("  BLIND: mkdtemp (%s)\n", strerror(errno));
		return 0;
	}
	(void)chmod(base, 0755); /* ⚠ mkdtemp makes it 0700: nobody could not even walk in */
	snprintf(state, sizeof state, "%s/state", base);
	snprintf(run, sizeof run, "%s/run", base);
	snprintf(outside, sizeof outside, "%s/outside", base);
	snprintf(marker, sizeof marker, "/tmp/remotix-walls-test-marker.%ld", (long)getpid());

	o = opts(nb->pw_uid, nb->pw_gid, "/tmp/remotix-walls-test-state", run);
	CHECK(walls_apply(&o, why, sizeof why) == -1 && strstr(why, "under /tmp"),
	      "root, state dir under /tmp: refused, named («%s»)", why);
	o = opts(nb->pw_uid, nb->pw_gid, state, run);
	CHECK(walls_apply(&o, why, sizeof why) == -1 && strstr(why, "does not exist") &&
	          strstr(why, state),
	      "root, missing state dir: refused, named («%s»)", why);
	CHECK(mkdir(state, 0700) == 0, "mkdir %s (root-owned)", state);
	CHECK(make_dir(run, nb->pw_uid, nb->pw_gid, 0700), "mkdir %s (nobody)", run);
	CHECK(walls_apply(&o, why, sizeof why) == -1 && strstr(why, "belongs to uid 0") &&
	          strstr(why, "chown"),
	      "root, state dir owned by root: refused with the fix («%s»)", why);
	CHECK(chown(state, nb->pw_uid, nb->pw_gid) == 0, "chown %s to nobody", state);
	CHECK(make_dir(outside, nb->pw_uid, nb->pw_gid, 0700),
	      "mkdir %s (nobody's, but outside the walls)", outside);
	int mfd = open(marker, O_WRONLY | O_CREAT | O_TRUNC, 0644);
	CHECK(mfd >= 0, "a marker in the host's /tmp (%s)", marker);
	if (mfd >= 0)
		close(mfd);

	/* review 3, F3: a mount of the host's, unmounted while the walls are up */
	char slave[700];
	int up[2], down[2];
	/* ⚠ under a SHARED mount, as systemd makes / on a host (a container's
	 *   mounts are private, and an unmount propagates through the mount point's
	 *   own mount): base bound onto itself and made shared, the tmpfs inside */
	char shared[640];
	snprintf(shared, sizeof shared, "%s/shared", base);
	CHECK(mkdir(shared, 0755) == 0 && mount(shared, shared, NULL, MS_BIND, NULL) == 0
	          && mount(NULL, shared, NULL, MS_SHARED, NULL) == 0,
	      "a shared mount at %s", shared);
	snprintf(slave, sizeof slave, "%s/slave", shared);
	CHECK(mkdir(slave, 0755) == 0 && mount("tmpfs", slave, "tmpfs", 0, "size=64k") == 0,
	      "a host tmpfs mounted at %s", slave);
	CHECK(pipe(up) == 0 && pipe(down) == 0, "two pipes");

	char cwd0[4096] = "";
	(void)!getcwd(cwd0, sizeof cwd0);
	fflush(stdout);
	pid_t pid = fork();
	if (pid == 0) {
		int bad = 0;
		close(up[0]);
		close(down[1]);
		ino_t ns0 = mnt_ns();
		if (walls_apply(&o, why, sizeof why) != 0) {
			printf("  walls_apply: %s\n", why);
			fflush(stdout);
			_exit(strstr(why, "unshare") || strstr(why, "a slave") ||
			              strstr(why, "mount_setattr") ? 200 : 1);
		}
#define CC(cond, ...) do { if (!(cond)) bad++; printf((cond) ? "  ok   " : "  FAIL "); \
	printf(__VA_ARGS__); printf("\n"); } while (0)
		CC(mnt_ns() != ns0, "child: a mount namespace of its own");
		CC(getuid() == nb->pw_uid && geteuid() == nb->pw_uid && getgid() == nb->pw_gid &&
		       getegid() == nb->pw_gid,
		   "child: uid/gid %ld/%ld (nobody)", (long)getuid(), (long)getgid());
		CC(getgroups(0, NULL) == 0, "child: no supplementary group");
		CC(!write_in(outside, &err) && err == EROFS,
		   "child: a directory nobody owns but outside the walls is read-only (%s)",
		   strerror(err));
		CC(!write_in("/var/tmp", &err) && err == EROFS, "child: /var/tmp is read-only (%s)",
		   strerror(err));
		CC(write_in(state, &err), "child: the state dir is writable (%s)",
		   err ? strerror(err) : "yes");
		CC(write_in(run, &err), "child: the run dir is writable (%s)",
		   err ? strerror(err) : "yes");
		/* lane 4's network-side review: what it writes it cannot execute */
		{
			char prog[4200];
			int pf;
			snprintf(prog, sizeof prog, "%s/x.sh", state);
			pf = open(prog, O_CREAT | O_TRUNC | O_WRONLY | O_CLOEXEC, 0755);
			if (pf >= 0) {
				(void)!write(pf, "#!/bin/sh\nexit 0\n", 17);
				close(pf);
			}
			errno = 0;
			char *const av[] = { prog, NULL };
			CC(pf >= 0 && execve(prog, av, environ) == -1 && errno == EACCES,
			   "child: a program written in the state dir does not execute (noexec: %s)",
			   strerror(errno));
			unlink(prog);
		}
		CC(write_in("/tmp", &err), "child: /tmp is writable (%s)",
		   err ? strerror(err) : "yes");
		CC(access(marker, F_OK) != 0, "child: /tmp is private (the host's marker is not there)");
		CC(status_value("CapEff:") == 0 && status_value("CapPrm:") == 0 &&
		       status_value("CapBnd:") == 0 && status_value("CapAmb:") == 0 &&
		       status_value("CapInh:") == 0,
		   "child: CapEff/CapPrm/CapBnd/CapAmb/CapInh all 0");
		CC(status_value("NoNewPrivs:") == 1, "child: NoNewPrivs 1");
		CC(setuid(0) != 0, "child: setuid(0) refused");
		{
			char cwd1[4096] = "";
			(void)!getcwd(cwd1, sizeof cwd1);
			CC(strncmp(cwd0, "/tmp", 4) == 0 ? strcmp(cwd1, "/") == 0 : strcmp(cwd1, cwd0) == 0,
			   "child: still in the root side's folder (%s), so a relative --page resolves as in 1.0",
			   cwd1);
		}
		/* review 3, F4 */
		{
			struct statvfs v;
			CC(statvfs("/", &v) == 0 && (v.f_flag & ST_NODEV) && (v.f_flag & ST_NOSUID),
			   "child: / is nodev and nosuid");
			int fd = open("/dev/null", O_RDWR);
			CC(fd >= 0 && write(fd, "x", 1) == 1, "child: /dev/null opens and takes a write");
			if (fd >= 0)
				close(fd);
			unsigned char r[8];
			fd = open("/dev/urandom", O_RDONLY);
			CC(fd >= 0 && read(fd, r, sizeof r) == (ssize_t)sizeof r, "child: /dev/urandom reads");
			if (fd >= 0)
				close(fd);
			CC(access("/dev/kvm", F_OK) != 0 && access("/dev/net/tun", F_OK) != 0
			       && access("/dev/fuse", F_OK) != 0 && access("/dev/sda", F_OK) != 0,
			   "child: no /dev/kvm, /dev/net/tun, /dev/fuse, /dev/sda in its /dev");
			CC(access("/dev/stdout", F_OK) == 0 && access("/dev/fd/0", F_OK) == 0,
			   "child: /dev/stdout and /dev/fd are there");
			CC(open("/dev/evil", O_CREAT | O_WRONLY, 0600) < 0, "child: its /dev is read-only");
			errno = 0;
			CC(unshare(CLONE_NEWUSER) != 0 && errno == EPERM,
			   "child: unshare(CLONE_NEWUSER) refused (%s)", strerror(errno));
			errno = 0;
			CC(syscall(__NR_clone3, NULL, 0) == -1 && errno == ENOSYS,
			   "child: clone3 says ENOSYS (glibc falls back to clone)");
			/* lane 4's network-side review: the kernel interfaces it never uses */
			errno = 0;
			CC(syscall(__NR_io_uring_setup, 1, NULL) == -1 && errno == ENOSYS,
			   "child: io_uring_setup says ENOSYS (%s)", strerror(errno));
			errno = 0;
			CC(syscall(__NR_userfaultfd, 0) == -1 && errno == EPERM,
			   "child: userfaultfd refused (%s)", strerror(errno));
			errno = 0;
			CC(syscall(__NR_perf_event_open, NULL, 0, -1, -1, 0) == -1 && errno == EPERM,
			   "child: perf_event_open refused (%s)", strerror(errno));
			errno = 0;
			CC(syscall(__NR_bpf, 0, NULL, 0) == -1 && errno == EPERM,
			   "child: bpf refused (%s)", strerror(errno));
			errno = 0;
			CC(syscall(__NR_keyctl, 0, 0, 0, 0, 0) == -1 && errno == EPERM,
			   "child: keyctl refused (%s)", strerror(errno));
			errno = 0;
			CC(syscall(__NR_add_key, "user", "x", "y", 1, 0) == -1 && errno == EPERM,
			   "child: add_key refused (%s)", strerror(errno));
			errno = 0;
			CC(syscall(__NR_ptrace, 0 /* PTRACE_TRACEME */, 0, 0, 0) == -1 && errno == EPERM,
			   "child: ptrace refused (%s)", strerror(errno));
			{
				char ch = 'x';
				int nf = open("/dev/null", O_RDWR);
				/* on /dev/null the kernel would say ENOTTY: EPERM is the filter's */
				errno = 0;
				CC(nf >= 0 && ioctl(nf, TIOCSTI, &ch) == -1 && errno == EPERM,
				   "child: ioctl TIOCSTI refused by the filter (%s)", strerror(errno));
				errno = 0;
				CC(nf >= 0 && (ioctl(nf, FIONREAD, &ch) == 0 || errno != EPERM),
				   "child: another ioctl still reaches the kernel (FIONREAD on /dev/null: %s, not EPERM)",
				   strerror(errno));
				if (nf >= 0)
					close(nf);
			}
			errno = 0;
			pid_t t = fork();
			if (t == 0)
				_exit(0);
			int fe = errno, ts = -1;
			pid_t w = t > 0 ? waitpid(t, &ts, 0) : -1;
			CC(t > 0 && w == t && WIFEXITED(ts) && WEXITSTATUS(ts) == 0,
			   "child: an ordinary fork still works (fork %ld %s, wait %ld, status %d)",
			   (long)t, strerror(fe), (long)w, ts);
		}
		/* review 3, F3: the host unmounts, the unmount reaches us */
		{
			char c = 1, line[1024];
			bool seen = false;
			FILE *mi;
			(void)!write(up[1], &c, 1);
			(void)!read(down[0], &c, 1);
			mi = fopen("/proc/self/mountinfo", "re");
			while (mi && fgets(line, sizeof line, mi))
				if (strstr(line, slave))
					seen = true;
			if (mi)
				fclose(mi);
			CC(!seen, "child: the host's umount of %s reached the walls (a slave, not private)",
			   slave);
		}
		{
			struct rlimit rl;
			/* 128 since 16 Oct 2026 (the coordinator): every network side of the uid counts */
			CC(getrlimit(RLIMIT_NPROC, &rl) == 0 && rl.rlim_cur == WALLS_NPROC_MAX
			       && rl.rlim_max == WALLS_NPROC_MAX && WALLS_NPROC_MAX == 128,
			   "child: RLIMIT_NPROC %d (review 2, L1; 128 since 16 Oct 2026)", WALLS_NPROC_MAX);
		}
		fflush(stdout);
		_exit(bad > 100 ? 100 : bad);
	}
	close(up[1]);
	close(down[0]);
	{
		char c;
		if (read(up[0], &c, 1) == 1) {
			CHECK(umount(slave) == 0, "the host unmounts %s", slave);
			(void)!write(down[1], &c, 1);
		}
	}
	close(up[0]);
	close(down[1]);
	int st = 0;
	waitpid(pid, &st, 0);
	(void)umount(slave);
	rmdir(slave);
	(void)umount(shared);
	rmdir(shared);
	if (WIFEXITED(st) && WEXITSTATUS(st) == 200) {
		printf("  BLIND: this root cannot mount (a container without SYS_ADMIN?)\n");
		rc = 0;
	} else {
		CHECK(WIFEXITED(st) && WEXITSTATUS(st) == 0, "child: every wall in place (exit %d)",
		      WIFEXITED(st) ? WEXITSTATUS(st) : -1);
		CHECK(write_in(outside, &err), "parent: its tree is untouched (%s still writable)",
		      outside);
	}
	unlink(marker);
	rmdir(state);
	rmdir(run);
	rmdir(outside);
	rmdir(base);
	return rc;
}

/* ⭐ 1.5 (AppArmor): `apparmor_exec_in()` with files in place of /sys and /proc */
static void put(const char *path, const char *text)
{
	FILE *f = fopen(path, "w");

	if (f) {
		fputs(text, f);
		fclose(f);
	}
}

static void slurp(const char *path, char *out, size_t n)
{
	FILE *f = fopen(path, "r");
	size_t k = 0;

	out[0] = '\0';
	if (f) {
		k = fread(out, 1, n - 1, f);
		fclose(f);
	}
	out[k] = '\0';
}

static void case_apparmor(void)
{
	char dir[] = "/tmp/remotix-test-aa.XXXXXX", en[160], pr[160], at[160], ol[160], got[160], why[256];
	int rc;

	if (!mkdtemp(dir)) {
		printf("  ??   no temporary directory for the AppArmor cases\n");
		return;
	}
	snprintf(en, sizeof en, "%s/enabled", dir);
	snprintf(pr, sizeof pr, "%s/profiles", dir);
	snprintf(at, sizeof at, "%s/attr-apparmor-exec", dir);
	snprintf(ol, sizeof ol, "%s/attr-exec", dir);

	notes[0] = '\0';
	rc = apparmor_exec_in(en, pr, at, ol, "remotix_network", why, sizeof why);
	CHECK(rc == 0 && strstr(walls_in_force(), "AppArmor: off"), "AppArmor: no kernel parameter file: off, go on");
	put(en, "N\n");
	put(at, "");
	notes[0] = '\0';
	rc = apparmor_exec_in(en, pr, at, ol, "remotix_network", why, sizeof why);
	slurp(at, got, sizeof got);
	CHECK(rc == 0 && !got[0] && strstr(walls_in_force(), "AppArmor: off"), "AppArmor: disabled: off, nothing written");
	put(en, "Y\n");
	put(pr, "remotix_networkx (enforce)\n/usr/bin/man (complain)\n");
	notes[0] = '\0';
	rc = apparmor_exec_in(en, pr, at, ol, "remotix_network", why, sizeof why);
	slurp(at, got, sizeof got);
	CHECK(rc == 0 && !got[0] && strstr(walls_in_force(), "NOT loaded"),
	      "AppArmor: on, only a profile with a longer name: not loaded, said, nothing written");
	put(pr, "docker-default (enforce)\nremotix_network (complain)\n");
	notes[0] = '\0';
	rc = apparmor_exec_in(en, pr, at, ol, "remotix_network", why, sizeof why);
	slurp(at, got, sizeof got);
	CHECK(rc == 0 && strcmp(got, "exec remotix_network") == 0 && strstr(walls_in_force(), "born in remotix_network"),
	      "AppArmor: loaded: «exec remotix_network» written to the attribute («%s»)", got);
	/* the older kernels: no per-LSM attribute, the generic one */
	{
		char missing[160];

		snprintf(missing, sizeof missing, "%s/no-such-dir/exec", dir);
		put(ol, "");
		notes[0] = '\0';
		rc = apparmor_exec_in(en, pr, missing, ol, "remotix_network", why, sizeof why);
		slurp(ol, got, sizeof got);
		CHECK(rc == 0 && strcmp(got, "exec remotix_network") == 0,
		      "AppArmor: no per-LSM attribute: the generic one is written");
		rc = apparmor_exec_in(en, pr, missing, missing, "remotix_network", why, sizeof why);
		CHECK(rc == -1 && strstr(why, "AppArmor"),
		      "AppArmor: loaded but no attribute to write: refused, the network side does not start (%s)", why);
		/* the write itself refused: the attribute is a directory */
		rc = apparmor_exec_in(en, pr, dir, dir, "remotix_network", why, sizeof why);
		CHECK(rc == -1 && strstr(why, "AppArmor"), "AppArmor: the attribute cannot be written: refused (%s)", why);
	}
	{
		char cmd[400];

		snprintf(cmd, sizeof cmd, "rm -f %s/enabled %s/profiles %s/attr-apparmor-exec %s/attr-exec && rmdir %s",
		         dir, dir, dir, dir, dir);
		if (system(cmd) != 0)
			printf("  (could not remove %s)\n", dir);
	}
	notes[0] = '\0';
}

int main(void)
{
	struct passwd *nb = getpwnam("nobody");
	bool blind = false;

	setvbuf(stdout, NULL, _IOLBF, 0);
	printf("02-walls-test (uid %ld)\n", (long)geteuid());
	case_context();
	case_apparmor();
	case_unprivileged(nb);
	case_landlock();
	case_families();
	case_network();
	if (geteuid() == 0) {
		if (!nb) {
			printf("  BLIND: no user nobody to wall in\n");
			blind = true;
		} else if (!case_root(nb)) {
			blind = true;
		}
	} else {
		printf("  (the walls for real need root: see the header for the command)\n");
	}
	printf("%d passed, %d failed, of %d\n", passed, failed, passed + failed);
	if (failed)
		return 1;
	return blind ? 3 : 0;
}
