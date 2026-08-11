/*
 * comando.c — vedi comando.h.
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

/* ⛔ 200 ms, e il prezzo si dichiara invece di nasconderlo.  La riga si legge e
 *    si risponde DENTRO il ciclo `poll` del server, con una lettura e una
 *    scrittura bloccanti a tempo: chi apre il socket e tace ferma il server per
 *    due decimi di secondo.
 *
 * ⚠ E' accettabile perche' la chiave di quel socket e' `0600` sul filesystem
 *   della macchina — chi lo puo' aprire puo' gia' fermare il server in dieci
 *   modi piu' semplici — e perche' la riga e' corta: un client che si comporta
 *   arriva intera in un pacchetto.  ⛔ Va scritto qui e non altrove: un ripiego
 *   silenzioso produce due comportamenti sotto la stessa etichetta
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

static void servi(int fd)
{
	char buf[256];
	char chiave[64];
	ssize_t letti;
	size_t n;

	setsockopt(fd, SOL_SOCKET, SO_RCVTIMEO, &TETTO, sizeof TETTO);
	setsockopt(fd, SOL_SOCKET, SO_SNDTIMEO, &TETTO, sizeof TETTO);

	letti = recv(fd, buf, sizeof buf - 1, 0);
	if (letti <= 0) {
		registro_dice(REG_RCP,
		              "⚠ comando vuoto sul socket di sblocco (letti %zd byte): "
		              "non ho tolto niente",
		              letti);
		scrivi_tutto(fd, "NON-CAPITO riga vuota\n");
		return;
	}
	buf[letti] = 0;
	n = strlen(buf);
	while (n && (buf[n - 1] == '\n' || buf[n - 1] == '\r'))
		buf[--n] = 0;

	if (strcmp(buf, "PING") == 0) {
		/* ⭐ E si scrive anche il PING: e' il denominatore di B0.3, e un
		 *    denominatore che non lascia traccia non serve a nessuno. */
		registro_dice(REG_RCP, "comando PING — il socket di sblocco e' vivo, e "
		                       "non ho toccato nessun ban");
		scrivi_tutto(fd, "PONG\n");
		return;
	}

	if (strncmp(buf, "SBLOCCA ", 8) != 0 || buf[8] == 0) {
		char fuori[320];
		registro_dice(REG_RCP,
		              "⚠ comando sconosciuto «%s» sul socket di sblocco: non ho "
		              "tolto niente (le forme sono «SBLOCCA <indirizzo>» e "
		              "«PING»)",
		              buf);
		snprintf(fuori, sizeof fuori, "NON-CAPITO %s\n", buf);
		scrivi_tutto(fd, fuori);
		return;
	}

	/* ⛔ La chiave la costruisce `rcp.c`, non questo file: chi comanda digita
	 *    `192.168.0.2`, e nel file dei ban c'e' scritto `[192.168.0.2]`.  Se
	 *    se la costruisse questo file, il giorno in cui le due forme
	 *    divergessero il comando risponderebbe «non era bannato» a ogni
	 *    indirizzo, in silenzio e per sempre — §4.4-bis lo vieta con un ⛔. */
	rcp_chiave_indirizzo(buf + 8, chiave, sizeof chiave);
	{
		bool era = rcp_sblocca(chiave, registro_ora_ms());
		char fuori[160];
		/* ⛔ «Ogni sblocco si scrive nel registro, o un ban tolto e un ban mai
		 *    scattato hanno lo stesso aspetto» (§4.4-bis).  Le due righe sono
		 *    diverse, e lo e' anche la risposta a chi comanda. */
		if (era)
			registro_dice(REG_RCP,
			              "⛔ SBLOCCATO su comando l'indirizzo %s (chiesto "
			              "«%s»): il ban c'era ed e' stato tolto, e il file dei "
			              "ban e' stato riscritto (§4.4-bis)",
			              chiave, buf + 8);
		else
			registro_dice(REG_RCP,
			              "sblocco chiesto per %s (chiesto «%s»): NON era "
			              "bannato, non ho tolto niente (§4.4-bis) — ⚠ e il "
			              "conto dei tentativi di quell'indirizzo riparte "
			              "comunque da zero",
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
		/* ⛔ E l'assenza si DICE: §4.4-bis vuole due strade d'uscita dal ban,
		 *    e senza questo socket ne resta una sola — le dodici ore.  Chi
		 *    accende il server deve poterlo leggere, o «il ban non si toglie»
		 *    sembrera' un difetto del comando invece che una sua assenza. */
		registro_dice(REG_RCP,
		              "⛔ nessun --comando-socket: il ban si toglie SOLO col "
		              "passare delle 12 ore.  §4.4-bis ne vuole due, di "
		              "strade, e questa meta' non c'e'.");
		return NULL;
	}

	memset(&dove, 0, sizeof dove);
	dove.sun_family = AF_UNIX;
	if (strlen(percorso) >= sizeof dove.sun_path) {
		registro_dice(REG_RCP,
		              "⛔ il percorso del socket di comando e' troppo lungo "
		              "(%zu byte, il massimo e' %zu): il comando di sblocco non "
		              "ci sara'",
		              strlen(percorso), sizeof dove.sun_path - 1);
		return NULL;
	}
	memcpy(dove.sun_path, percorso, strlen(percorso));

	/* ⚠ Si toglie il file vecchio: un socket lasciato li' da un'esecuzione
	 *   precedente fa fallire `bind` con EADDRINUSE, e il sintomo — «il comando
	 *   non risponde» — somiglia in tutto a un server morto. */
	unlink(percorso);

	fd = socket(AF_UNIX, SOCK_STREAM | SOCK_NONBLOCK, 0);
	if (fd < 0 || bind(fd, (struct sockaddr *)&dove, sizeof dove) != 0 ||
	    listen(fd, 4) != 0) {
		registro_dice(REG_RCP,
		              "⛔ il socket del comando di sblocco non parte su «%s»: "
		              "%s.  Il ban si potra' togliere solo aspettando 12 ore "
		              "(§4.4-bis).",
		              percorso, strerror(errno));
		if (fd >= 0)
			close(fd);
		return NULL;
	}

	/* ⛔ 0600, e la ragione e' la regola: la chiave che questo comando chiede
	 *    e' «l'accesso alla macchina».  Un socket leggibile da chiunque la
	 *    renderebbe «l'accesso a un utente qualunque della macchina», che e'
	 *    una chiave diversa e piu' facile. */
	if (chmod(percorso, 0600) != 0)
		registro_dice(REG_RCP,
		              "⚠ non ho potuto mettere 0600 su «%s»: %s — il comando di "
		              "sblocco c'e', ma la chiave che chiede e' piu' larga di "
		              "quel che §4.4-bis suppone",
		              percorso, strerror(errno));

	k = calloc(1, sizeof *k);
	if (!k) {
		close(fd);
		unlink(percorso);
		return NULL;
	}
	k->fd = fd;
	snprintf(k->percorso, sizeof k->percorso, "%s", percorso);
	registro_dice(REG_RCP,
	              "il comando di sblocco ascolta su «%s» (0600) — «SBLOCCA "
	              "<indirizzo>» oppure «PING» (RCP.md §4.4-bis)",
	              percorso);
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
					              "accept sul socket di sblocco: %s",
					              strerror(errno));
				break;
			}
			servi(fd);
			close(fd);
		}
	}
}
