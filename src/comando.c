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

/* ⛔ Una riga bianca NON e' un indirizzo, e la differenza si paga in una
 *    risposta che rassicura: `rcp_chiave_indirizzo("   ")` produce la chiave
 *    `[   ]`, che nel file dei ban non c'e' mai — quindi `SBLOCCA` seguito da
 *    soli spazi si sentirebbe rispondere **NON-BANNATO**, cioe' «non c'era
 *    niente da togliere», che e' la faccia buona di `LEZIONI.md` §1.9 messa su
 *    un comando che non ha nemmeno detto su chi agire.  Qui e' `NON-CAPITO`.
 *
 * ⚠ E qui i due server DIVERGONO, ed e' un rilievo dell'11 agosto 2026:
 *   l'innesto (`01-b3-rcp-innesta.py`, `remotix_comando_servi`) prova solo
 *   `riga.starts_with("SBLOCCA ")` e a una riga bianca risponde
 *   `NON-BANNATO []`.  La cura sta li' e non qui; questo file fa la cosa
 *   giusta e lo dichiara. */
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

	/* ⚠ UNA `recv` SOLA, ED E' UNA SCELTA DICHIARATA.  Un client che spezzasse
	 *   la riga in due scritture si sentirebbe rispondere `NON-CAPITO` sul
	 *   primo pezzo.  ⭐ Leggere in ciclo fino al fine riga costerebbe il tetto
	 *   di 200 ms **per ogni** giro, cioe' moltiplicherebbe per N il tempo in
	 *   cui un client che tace ferma tutte le connessioni QUIC — che e' il
	 *   prezzo dichiarato qui sopra, e comprarlo N volte per un caso che
	 *   nessuno dei due client conosciuti produce (tutt'e due scrivono la riga
	 *   in una `send` sola: `01-b8-sblocca.py` con `sendall`, `nc -U` una riga
	 *   per volta) sarebbe ottimizzare nella direzione sbagliata.
	 * ⛔ E il modo in cui questo caso fallisce e' SICURO: `NON-CAPITO` e' una
	 *   risposta distinta, forte e scritta nel registro — non si confonde ne'
	 *   con «tolto» ne' con «non era bannato». */
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

	if (strncmp(buf, "SBLOCCA ", 8) != 0 || buf[8] == 0 ||
	    solo_spazi(buf + 8)) {
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
			/* ⛔ E QUI C'ERA UNA COSA DETTA E NON SAPUTA — corretta l'11
			 *    agosto 2026.  Questa riga diceva «e il file dei ban e' stato
			 *    riscritto», e questo file non lo sa: `rcp_sblocca()` chiama
			 *    `salva_ban(NULL, ora)`, e con la sessione a `NULL` quella
			 *    funzione tace su TUTTO — `fopen` fallito, `rename` fallito.
			 *    Se il file non si potesse scrivere, il ban sparirebbe dalla
			 *    memoria, resterebbe sul disco, tornerebbe al riavvio, e il
			 *    registro avrebbe appena dichiarato il contrario.  ⚠ E' la
			 *    forma esatta di R12.1 — «esce 0 dicendo che ha funzionato» —
			 *    rimpicciolita e spostata dentro la sua stessa cura.
			 * ⭐ La cura vera non e' qui: `rcp_sblocca()` deve poter dire se il
			 *    file l'ha scritto (oggi restituisce un `bool` solo, e
			 *    `percorso_ban` e' `static` dentro `rcp.c`).  Finche' non lo
			 *    dice, questa riga dichiara quel che sa e non di piu', e chi
			 *    misura guarda il file da fuori — `01-b8-sblocca.py
			 *    --ban-file`, che lo legge prima e dopo. */
			registro_dice(REG_RCP,
			              "⛔ SBLOCCATO su comando l'indirizzo %s (chiesto "
			              "«%s»): il ban c'era ed e' stato tolto dalla memoria "
			              "di questo processo, e il file dei ban e' stato "
			              "chiesto in scrittura — ⚠ se quella scrittura sia "
			              "riuscita questo modulo NON lo sa (§4.4-bis)",
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
	if (fd >= 0) {
		/* ⛔ 0600 SI OTTIENE PRIMA DI ESISTERE, non dopo — corretto l'11 agosto
		 *    2026.  `bind()` crea il nodo con `0777 & ~umask`, cioe' con quel
		 *    che si e' trovato in casa; la `chmod()` che veniva dopo lasciava
		 *    una finestra — corta ma vera — in cui il socket del comando di
		 *    sblocco stava sul filesystem **aperto a chiunque**.  ⚠ In quella
		 *    finestra la chiave che §4.4-bis chiede («l'accesso alla macchina»)
		 *    e' «l'accesso a un utente qualunque della macchina», che e' la
		 *    chiave piu' facile che quella regola esiste per non concedere.
		 * ⭐ La `umask` si rimette com'era subito: e' un dato del processo, e
		 *    lasciarla stretta cambierebbe i permessi di tutto quel che il
		 *    server crea dopo — compreso il file dei ban. */
		mode_t vecchia = umask(0177);
		if (bind(fd, (struct sockaddr *)&dove, sizeof dove) != 0 ||
		    listen(fd, 4) != 0) {
			umask(vecchia);
			registro_dice(REG_RCP,
			              "⛔ il socket del comando di sblocco non parte su "
			              "«%s»: %s.  Il ban si potra' togliere solo "
			              "aspettando 12 ore (§4.4-bis).",
			              percorso, strerror(errno));
			close(fd);
			return NULL;
		}
		umask(vecchia);
	} else {
		registro_dice(REG_RCP,
		              "⛔ il socket del comando di sblocco non parte su «%s»: "
		              "%s.  Il ban si potra' togliere solo aspettando 12 ore "
		              "(§4.4-bis).",
		              percorso, strerror(errno));
		return NULL;
	}

	/* ⚠ E la `chmod` resta, come cintura oltre alle bretelle: una `umask` non
	 *   protegge un filesystem che rifiuta i permessi (certi montaggi), e su
	 *   quelli si vuole almeno provare. */
	if (chmod(percorso, 0600) != 0)
		registro_dice(REG_RCP,
		              "⚠ non ho potuto mettere 0600 su «%s»: %s",
		              percorso, strerror(errno));

	k = calloc(1, sizeof *k);
	if (!k) {
		close(fd);
		unlink(percorso);
		return NULL;
	}
	k->fd = fd;
	snprintf(k->percorso, sizeof k->percorso, "%s", percorso);

	/* ⛔ E I PERMESSI SI RILEGGONO INVECE DI DICHIARARLI.  La riga di prima
	 *    diceva «(0600)» sempre, anche quando la `chmod` era appena fallita e
	 *    la riga di avviso stava due righe sopra: due frasi contraddittorie
	 *    nello stesso registro, e quella che si legge per ultima e' quella
	 *    falsa.  Qui si stampa il modo che il filesystem dice davvero — e se
	 *    non si e' potuto nemmeno chiedere, si dice anche quello
	 *    (`LEZIONI.md` §1.9: vuoto e proibito non hanno la stessa faccia). */
	{
		struct stat st;
		if (stat(percorso, &st) != 0)
			registro_dice(REG_RCP,
			              "il comando di sblocco ascolta su «%s» — ⚠ e i suoi "
			              "permessi non li ho potuti rileggere (%s): «SBLOCCA "
			              "<indirizzo>» oppure «PING» (RCP.md §4.4-bis)",
			              percorso, strerror(errno));
		else
			registro_dice(REG_RCP,
			              "il comando di sblocco ascolta su «%s» (%04o%s) — "
			              "«SBLOCCA <indirizzo>» oppure «PING» "
			              "(RCP.md §4.4-bis)",
			              percorso, (unsigned)(st.st_mode & 07777),
			              (st.st_mode & 07777) == 0600
			                  ? ""
			                  : " ⛔ e NON e' 0600: la chiave di §4.4-bis e' "
			                    "piu' larga di «l'accesso alla macchina»");
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
					              "accept sul socket di sblocco: %s",
					              strerror(errno));
				break;
			}
			servi(fd);
			close(fd);
		}
	}
}
