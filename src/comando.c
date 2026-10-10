/*
 * comando.c — see comando.h.
 */
#include "comando.h"

#include "rcp.h"
#include "registro.h"

#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/un.h>
#include <unistd.h>

struct comando {
	int fd;
	char percorso[108];
};

/* ⛔ 200 ms, and the price is declared instead of hidden.  The line is read and
 *    answered INSIDE the server's `poll` loop, with a blocking read and write
 *    under a timeout: whoever opens the socket and stays silent stops the
 *    server for two tenths of a second.
 *
 * ⚠ It is acceptable because the key of that socket is `0600` on the
 *   machine's filesystem — whoever can open it can already stop the server in
 *   ten simpler ways — and because the line is short: a well-behaved client
 *   arrives whole in one packet.  ⛔ It must be written here and not
 *   elsewhere: a silent fallback produces two behaviours under the same label
 *   (`CODER.md` §4.2). */
static const struct timeval TETTO = {0, 200000};

static void scrivi_tutto(int fd, const char *testo)
{
	size_t n = strlen(testo);
	size_t o = 0;
	while (o < n) {
		ssize_t k = send(fd, testo + o, n - o, MSG_NOSIGNAL);
		if (k <= 0)
			return;
		o += (size_t)k;
	}
}

/* ⛔ A blank line is NOT an address, and the difference is paid for in a
 *    reassuring answer: `rcp_chiave_indirizzo("   ")` produces the key
 *    `[   ]`, which is never in the ban file — so `SBLOCCA` followed by
 *    spaces only would get the answer **NON-BANNATO**, that is «there was
 *    nothing to remove», which is the good face of `LEZIONI.md` §1.9 put on
 *    a command that has not even said whom to act on.  Here it is `NON-CAPITO`.
 *
 * ⚠ And here the two servers DIVERGE, and it is a finding of 11 Aug 2026:
 *   the graft (`01-b3-rcp-innesta.py`, `remotix_comando_servi`) only checks
 *   `riga.starts_with("SBLOCCA ")` and answers a blank line with
 *   `NON-BANNATO []`.  The cure belongs there and not here; this file does
 *   the right thing and declares it. */
static bool solo_spazi(const char *t)
{
	for (; *t; t++)
		if (*t != ' ' && *t != '\t')
			return false;
	return true;
}

static void servi(int fd)
{
	char buf[256];
	char chiave[64];
	ssize_t letti;
	size_t n;

	setsockopt(fd, SOL_SOCKET, SO_RCVTIMEO, &TETTO, sizeof TETTO);
	setsockopt(fd, SOL_SOCKET, SO_SNDTIMEO, &TETTO, sizeof TETTO);

	/* ⚠ ONE SINGLE `recv`, AND IT IS A DECLARED CHOICE.  A client that split
	 *   the line into two writes would get `NON-CAPITO` on the first piece.
	 *   ⭐ Reading in a loop up to the end of line would cost the 200 ms
	 *   ceiling **for every** round, that is it would multiply by N the time
	 *   in which a silent client stops all the QUIC connections — which is
	 *   the price declared above, and buying it N times for a case that
	 *   neither of the two known clients produces (both write the line in a
	 *   single `send`: `01-b8-sblocca.py` with `sendall`, `nc -U` one line at
	 *   a time) would be optimising in the wrong direction.
	 * ⛔ And the way this case fails is SAFE: `NON-CAPITO` is a distinct
	 *   answer, loud and written in the log — it is confused neither with
	 *   «removed» nor with «was not banned». */
	letti = recv(fd, buf, sizeof buf - 1, 0);
	if (letti <= 0) {
		registro_dice(REG_RCP,
		              "⚠ empty command on the unblock socket (read %zd bytes): "
		              "I removed nothing",
		              letti);
		scrivi_tutto(fd, "NON-CAPITO riga vuota\n");
		return;
	}
	buf[letti] = 0;
	n = strlen(buf);
	while (n && (buf[n - 1] == '\n' || buf[n - 1] == '\r'))
		buf[--n] = 0;

	if (strcmp(buf, "PING") == 0) {
		/* ⭐ And the PING is written too: it is the denominator of B0.3, and a
		 *    denominator that leaves no trace is of no use to anyone. */
		registro_dice(REG_RCP, "command PING — the unblock socket is alive, and "
		                       "I touched no ban");
		scrivi_tutto(fd, "PONG\n");
		return;
	}

	if (strncmp(buf, "SBLOCCA ", 8) != 0 || buf[8] == 0 ||
	    solo_spazi(buf + 8)) {
		char fuori[320];
		registro_dice(REG_RCP,
		              "⚠ unknown command «%s» on the unblock socket: I "
		              "removed nothing (the forms are «SBLOCCA <address>» and "
		              "«PING»)",
		              buf);
		snprintf(fuori, sizeof fuori, "NON-CAPITO %s\n", buf);
		scrivi_tutto(fd, fuori);
		return;
	}

	/* ⛔ The key is built by `rcp.c`, not by this file: whoever gives the
	 *    command types `192.168.0.2`, and the ban file has `[192.168.0.2]`
	 *    written in it.  If this file built it on its own, the day the two
	 *    forms diverged the command would answer «was not banned» to every
	 *    address, silently and forever — §4.4-bis forbids it with a ⛔. */
	rcp_chiave_indirizzo(buf + 8, chiave, sizeof chiave);
	{
		bool era = rcp_sblocca(chiave, registro_ora_ms());
		char fuori[160];
		/* ⛔ «Every unblock is written in the log, or a ban removed and a ban
		 *    never triggered look the same» (§4.4-bis).  The two lines are
		 *    different, and so is the answer to whoever gives the command. */
		if (era)
			/* ⛔ AND HERE THERE WAS A THING SAID AND NOT KNOWN — corrected on
			 *    11 Aug 2026.  This line said «and the ban file has been
			 *    rewritten», and this file does not know that: `rcp_sblocca()`
			 *    calls `salva_ban(NULL, ora)`, and with the session at `NULL`
			 *    that function stays silent on EVERYTHING — failed `fopen`,
			 *    failed `rename`.  If the file could not be written, the ban
			 *    would vanish from memory, stay on disk, come back at restart,
			 *    and the log would have just declared the opposite.  ⚠ It is
			 *    the exact form of R12.1 — «exits 0 saying it worked» — shrunk
			 *    and moved inside its own cure.
			 * ⭐ The real cure is not here: `rcp_sblocca()` must be able to say
			 *    whether it wrote the file (today it returns a single `bool`,
			 *    and `percorso_ban` is `static` inside `rcp.c`).  Until it says
			 *    so, this line declares what it knows and no more, and whoever
			 *    measures looks at the file from outside — `01-b8-sblocca.py
			 *    --ban-file`, which reads it before and after. */
			registro_dice(REG_RCP,
			              "⛔ UNBLOCKED on command the address %s (asked "
			              "«%s»): the ban was there and has been removed from the "
			              "memory of this process, and the ban file has been "
			              "requested for writing — ⚠ whether that write "
			              "succeeded this module does NOT know (§4.4-bis)",
			              chiave, buf + 8);
		else
			registro_dice(REG_RCP,
			              "unblock asked for %s (asked «%s»): it was NOT "
			              "banned, I removed nothing (§4.4-bis) — ⚠ and the "
			              "attempt count of that address restarts "
			              "from zero anyway",
			              chiave, buf + 8);
		snprintf(fuori, sizeof fuori, "%s %s\n", era ? "TOLTO" : "NON-BANNATO",
		         chiave);
		scrivi_tutto(fd, fuori);
	}
}

/* ------------------------------------------------------------------------ */

comando *comando_apri(const char *percorso)
{
	struct sockaddr_un dove;
	comando *k;
	int fd;

	if (!percorso || !*percorso) {
		/* ⛔ And the absence is SAID: §4.4-bis wants two ways out of the ban,
		 *    and without this socket only one is left — the twelve hours.
		 *    Whoever starts the server must be able to read it, or «the ban
		 *    cannot be removed» will look like a defect of the command instead
		 *    of its absence. */
		registro_dice(REG_RCP,
		              "⛔ no --comando-socket: the ban is removed ONLY by "
		              "the passing of the 12 hours.  §4.4-bis wants two "
		              "ways, and this half is missing.");
		return NULL;
	}

	memset(&dove, 0, sizeof dove);
	dove.sun_family = AF_UNIX;
	if (strlen(percorso) >= sizeof dove.sun_path) {
		registro_dice(REG_RCP,
		              "⛔ the path of the command socket is too long "
		              "(%zu bytes, the maximum is %zu): there will be no "
		              "unblock command",
		              strlen(percorso), sizeof dove.sun_path - 1);
		return NULL;
	}
	memcpy(dove.sun_path, percorso, strlen(percorso));

	/* ⚠ The old file is removed: a socket left there by a previous run makes
	 *   `bind` fail with EADDRINUSE, and the symptom — «the command does not
	 *   answer» — looks in every way like a dead server. */
	unlink(percorso);

	fd = socket(AF_UNIX, SOCK_STREAM | SOCK_NONBLOCK, 0);
	if (fd >= 0) {
		/* ⛔ 0600 IS OBTAINED BEFORE EXISTING, not after — corrected on 11 Aug
		 *    2026.  `bind()` creates the node with `0777 & ~umask`, that is
		 *    with whatever was found at home; the `chmod()` that came after
		 *    left a window — short but real — in which the socket of the
		 *    unblock command sat on the filesystem **open to anyone**.  ⚠ In
		 *    that window the key §4.4-bis asks for («access to the machine»)
		 *    is «access to any user of the machine», which is the easiest key
		 *    that rule exists not to grant.
		 * ⭐ The `umask` is put back as it was right away: it is a datum of the
		 *    process, and leaving it tight would change the permissions of
		 *    everything the server creates afterwards — the ban file included. */
		mode_t vecchia = umask(0177);
		if (bind(fd, (struct sockaddr *)&dove, sizeof dove) != 0 ||
		    listen(fd, 4) != 0) {
			umask(vecchia);
			registro_dice(REG_RCP,
			              "⛔ the unblock command socket does not start on "
			              "«%s»: %s.  The ban can be removed only by "
			              "waiting 12 hours (§4.4-bis).",
			              percorso, strerror(errno));
			close(fd);
			return NULL;
		}
		umask(vecchia);
	} else {
		registro_dice(REG_RCP,
		              "⛔ the unblock command socket does not start on «%s»: "
		              "%s.  The ban can be removed only by waiting 12 hours "
		              "(§4.4-bis).",
		              percorso, strerror(errno));
		return NULL;
	}

	/* ⚠ And the `chmod` stays, as a belt on top of the braces: a `umask` does
	 *   not protect a filesystem that refuses permissions (certain mounts),
	 *   and on those we want at least to try. */
	if (chmod(percorso, 0600) != 0)
		registro_dice(REG_RCP,
		              "⚠ could not set 0600 on «%s»: %s",
		              percorso, strerror(errno));

	k = calloc(1, sizeof *k);
	if (!k) {
		close(fd);
		unlink(percorso);
		return NULL;
	}
	k->fd = fd;
	snprintf(k->percorso, sizeof k->percorso, "%s", percorso);

	/* ⛔ AND THE PERMISSIONS ARE READ BACK INSTEAD OF DECLARED.  The previous
	 *    line always said «(0600)», even when the `chmod` had just failed and
	 *    the warning line stood two lines above: two contradictory sentences
	 *    in the same log, and the one read last is the false one.  Here the
	 *    mode the filesystem really reports is printed — and if it could not
	 *    even be asked, that is said too (`LEZIONI.md` §1.9: empty and
	 *    forbidden do not have the same face). */
	{
		struct stat st;
		if (stat(percorso, &st) != 0)
			registro_dice(REG_RCP,
			              "the unblock command listens on «%s» — ⚠ and its "
			              "permissions could not be read back (%s): «SBLOCCA "
			              "<address>» or «PING» (RCP.md §4.4-bis)",
			              percorso, strerror(errno));
		else
			registro_dice(REG_RCP,
			              "the unblock command listens on «%s» (%04o%s) — "
			              "«SBLOCCA <address>» or «PING» "
			              "(RCP.md §4.4-bis)",
			              percorso, (unsigned)(st.st_mode & 07777),
			              (st.st_mode & 07777) == 0600
			                  ? ""
			                  : " ⛔ and it is NOT 0600: the key of §4.4-bis is "
			                    "wider than «access to the machine»");
	}
	return k;
}

void comando_chiudi(comando *k)
{
	if (!k)
		return;
	if (k->fd >= 0)
		close(k->fd);
	if (k->percorso[0])
		unlink(k->percorso);
	free(k);
}

size_t comando_descrittori(comando *k, struct pollfd *dove, size_t cap)
{
	if (!k || cap == 0)
		return 0;
	dove[0].fd = k->fd;
	dove[0].events = POLLIN;
	dove[0].revents = 0;
	return 1;
}

void comando_muovi(comando *k, struct pollfd *dove, size_t quanti)
{
	if (!k)
		return;
	for (size_t i = 0; i < quanti; i++) {
		if (dove[i].fd != k->fd || dove[i].revents == 0)
			continue;
		for (;;) {
			int fd = accept(k->fd, NULL, NULL);
			if (fd < 0) {
				if (errno != EAGAIN && errno != EWOULDBLOCK &&
				    errno != EINTR)
					registro_dice(REG_RCP,
					              "accept on the unblock socket: %s",
					              strerror(errno));
				break;
			}
			servi(fd);
			close(fd);
		}
	}
}
