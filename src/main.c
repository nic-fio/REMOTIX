/*
 * main.c — REMOTIX_V2, il server.
 *
 * ---------------------------------------------------------------------------
 * ⛔ CHE COS'E' QUESTO PROGRAMMA, E CHE COSA NON E' ANCORA
 *
 * E' il server di `SPECIFICHE.md` §1 alla FASE 1: la stretta di mano di RCP su
 * WebTransport, dai due lati, e la pagina servita dal server stesso.  ⛔ Niente
 * video, niente audio, niente input: quelli sono le fasi da 2 in poi.
 *
 * ⚠ Quel che l'utente vede e giudica: apre `https://indirizzo:7447`, clicca
 *   l'avviso la prima volta su quel dispositivo, digita utente e parola, e la
 *   pagina dice «ammesso, sessione nuova, tela 1920×1080, desktop GNOME» —
 *   oppure dice PERCHE' no, con una frase e non con un numero (`RCP.md` §8.2).
 *
 * ---------------------------------------------------------------------------
 * ⛔ I DUE ASCOLTATORI, CON LO STESSO NUMERO DI PORTA
 *
 * `RCP.md` §2.4: **7447**, UDP per HTTP/3 e WebTransport, TCP per il primo
 * caricamento della pagina.  ⚠ E le due cose sono INDIPENDENTI: WebTransport
 * non usa `Alt-Svc`, apre la sua connessione da se' (misura S1).  ⛔ Il ripiego
 * silenzioso su TCP dichiarato come pericolo in `PIANO.md` fase 1 non puo'
 * accadere — quella riga e' anteriore alla misura.
 *
 * ---------------------------------------------------------------------------
 * ⛔ UN SOLO FILO, E VA DETTO
 *
 * Tutto gira in un ciclo `poll` solo.  ⚠ La verifica PAM BLOCCA quel filo (vedi
 * `webtransport.c`), quindi la stretta di mano di un utente ritarda i pacchetti
 * di chiunque altro.  E' un ripiego dichiarato della fase 1: `SPECIFICHE.md`
 * §5.5 vuole dieci utenti insieme, e prima di allora la verifica va su un filo
 * a parte.
 */
#include "certificati.h"
#include "comando.h"
#include "pagina.h"
#include "rcp.h"
#include "registro.h"
#include "tls.h"
#include "trasporto.h"

#include <errno.h>
#include <poll.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <time.h>
#include <unistd.h>

#include <openssl/ssl.h>

#define PORTA_PREDEFINITA "7447" /* RCP.md §2.4 */

/* 1 per l'UDP, 1 per l'ascoltatore TCP, il resto per le connessioni TCP. */
#define MAX_POLL 64

static volatile sig_atomic_t si_ferma;

static void al_segnale(int s)
{
	(void)s;
	si_ferma = 1;
}

static void aiuto(const char *nome)
{
	fprintf(stderr,
	        "REMOTIX_V2 — il server (fase 1: il filo nudo)\n"
	        "\n"
	        "  %s [opzioni]\n"
	        "\n"
	        "  --indirizzo IND   su che cosa ascoltare (predefinito: 0.0.0.0)\n"
	        "  --nome NOME       il nome o l'indirizzo che va nel certificato\n"
	        "                    (predefinito: quello di --indirizzo, e se e'\n"
	        "                     0.0.0.0 va dichiarato: un subjectAltName\n"
	        "                     sbagliato fa comparire un avviso DIVERSO)\n"
	        "  --porta N         predefinito: %s  (RCP.md §2.4)\n"
	        "  --certificati DIR dove stanno i due certificati\n"
	        "  --pagina FILE     la pagina da servire in TCP\n"
	        "  --ban-file FILE   dove si conserva il ban degli indirizzi\n"
	        "                    (RCP.md §4.4-bis: sopravvive al riavvio)\n"
	        "                    ⚠ `--ban` e' lo stesso nome, tenuto perche' e'\n"
	        "                      quello che questo server usava prima\n"
	        "  --comando-socket PATH\n"
	        "                    il socket Unix 0600 del comando di sblocco:\n"
	        "                    «SBLOCCA <indirizzo>» oppure «PING».  Senza,\n"
	        "                    dal ban si esce solo con le 12 ore\n"
	        "  --parlantina      registro di dettaglio\n",
	        nome, PORTA_PREDEFINITA);
}

/* ⛔⭐ IL FILE DEL SERVIZIO PAM, GUARDATO ALL'AVVIO — rilievo B-11.
 *
 *     `SPECIFICHE.md` §4.2 vuole il servizio `remotix`.  Se
 *     `/etc/pam.d/remotix` non c'e', Linux-PAM ripiega sul servizio `other`,
 *     che su Debian e' `pam_deny`: **ogni** parola d'ordine giusta viene
 *     rifiutata, e quel che l'utente legge e' «utente o parola d'ordine non
 *     corretti» — cioe' una diagnosi che punta sulla parola d'ordine mentre il
 *     difetto e' un file mancante.
 *
 * ⚠ NON si rifiuta di partire: senza PAM il server non serve a niente, ma il
 *   ban di §4.4-bis, la pagina e i certificati funzionano lo stesso, e
 *   spegnere tutto metterebbe il rosso sull'imputato sbagliato.  ⛔ La riga
 *   pero' si scrive, ed e' la protezione che l'invariante I7 chiede: sta nel
 *   programma, non in una nota di installazione che si perde. */
static void guarda_il_servizio_pam(void)
{
	static const char *dove = "/etc/pam.d/remotix";
	struct stat st;
	if (stat(dove, &st) == 0) {
		registro_dice(REG_AVVIO,
		              "servizio PAM «remotix»: %s c'e' (SPECIFICHE.md §4.2)",
		              dove);
		return;
	}
	registro_dice(REG_AVVIO,
	              "⛔ %s NON C'E' (%s): PAM ripieghera' sul servizio «other», "
	              "che su Debian e' pam_deny — OGNI parola d'ordine giusta "
	              "verra' rifiutata e l'utente leggera' «utente o parola "
	              "d'ordine non corretti».  Si installa src/remotix.pam.",
	              dove, strerror(errno));
}

int main(int argc, char **argv)
{
	const char *indirizzo = "0.0.0.0";
	const char *nome = NULL;
	const char *porta = PORTA_PREDEFINITA;
	const char *dir_cert = "/var/lib/remotix/certificati";
	const char *file_html = "pagina.html";
	const char *file_ban = "/var/lib/remotix/ban";
	const char *socket_comando = NULL;
	certificati cert;
	SSL_CTX *ctx_quic = NULL, *ctx_pagina = NULL;
	trasporto *t = NULL;
	pagina *p = NULL;
	comando *k = NULL;
	time_t ultimo_controllo_cert;
	int esito = 1;

	for (int i = 1; i < argc; i++) {
		const char *a = argv[i];
		const char *v = (i + 1 < argc) ? argv[i + 1] : NULL;
		if (strcmp(a, "--indirizzo") == 0 && v)
			indirizzo = argv[++i];
		else if (strcmp(a, "--nome") == 0 && v)
			nome = argv[++i];
		else if (strcmp(a, "--porta") == 0 && v)
			porta = argv[++i];
		else if (strcmp(a, "--certificati") == 0 && v)
			dir_cert = argv[++i];
		else if (strcmp(a, "--pagina") == 0 && v)
			file_html = argv[++i];
		/* ⛔ DUE NOMI PER LA STESSA OPZIONE, E SI ACCETTANO TUTT'E DUE —
		 *    rilievo R12.9a, 10 agosto 2026 notte.  Questo server diceva
		 *    `--ban`; l'ospite dei banchi (`01-b3-rcp-innesta.py`) e i loro
		 *    script di lancio dicono `--ban-file`.  ⚠ Chi porta al prodotto la
		 *    riga di comando che i banchi usano otteneva `aiuto()` e uscita 2
		 *    — un fallimento chiaro, che e' il modo giusto di sbagliare, ma un
		 *    fallimento che nessuno dei due documenti spiegava.  Nessun `.md`
		 *    nomina l'uno o l'altro: finche' non lo fa, li si accetta
		 *    entrambi e l'aiuto dichiara quale dei due e' il nome buono. */
		else if ((strcmp(a, "--ban-file") == 0 || strcmp(a, "--ban") == 0) && v)
			file_ban = argv[++i];
		else if (strcmp(a, "--comando-socket") == 0 && v)
			socket_comando = argv[++i];
		else if (strcmp(a, "--parlantina") == 0)
			registro_parlantina(true);
		else if (strcmp(a, "--sblocca") == 0) {
			/* ⛔⭐ E QUESTA OPZIONE NON C'E' PIU', E NON SI TACE SUL PERCHE'
			 *     — rilievo R12.1, 10 agosto 2026 notte.
			 *
			 *     `remotix --sblocca IND` era un SECONDO PROCESSO: caricava il
			 *     file dei ban, toglieva la voce dalla tabella **del processo
			 *     nuovo**, riscriveva il file, stampava «era bannato, adesso
			 *     e' libero» e usciva **0**.  ⛔ Il processo che SERVE non
			 *     vedeva niente: la sua `tentativi[]` restava intatta, il
			 *     quarto tentativo riceveva ancora `TROPPI_TENTATIVI`, e al
			 *     primo ban successivo di chiunque altro `salva_ban()`
			 *     riscriveva il file dalla memoria stantia — **il ban tolto
			 *     tornava anche su disco**.
			 *
			 *     ⚠ Il danno non era che non funzionava: era che **usciva 0
			 *       dicendo che aveva funzionato**.
			 *
			 * ⛔ Un messaggio, e non `aiuto()`: chi ha in mano un comando che
			 *    per un giorno e' esistito deve leggere PERCHE' non c'e' piu',
			 *    o cerchera' l'errore di battitura. */
			fprintf(stderr,
			        "⛔ --sblocca non esiste piu', e non e' un cambio di nome.\n"
			        "   Il ban vive nella memoria del processo che serve: un "
			        "secondo processo puo' solo\n"
			        "   riscrivere il file, e il server continuerebbe a "
			        "rispondere TROPPI_TENTATIVI fino\n"
			        "   al riavvio — uscendo 0 come se avesse funzionato "
			        "(RCP.md §4.4-bis).\n"
			        "\n"
			        "   Si accende il server con --comando-socket PATH e si "
			        "sblocca cosi':\n"
			        "       python3 banchi/01-b8-sblocca.py --socket PATH "
			        "192.168.0.2\n"
			        "   oppure, senza strumenti:\n"
			        "       printf 'SBLOCCA 192.168.0.2\\n' | nc -U PATH\n");
			return 2;
		} else {
			aiuto(argv[0]);
			return 2;
		}
	}
	if (!nome)
		nome = indirizzo;

	if (!nome[0] || strcmp(nome, "0.0.0.0") == 0 || strcmp(nome, "::") == 0) {
		/* ⛔ `RCP.md` §4.1: «il certificato DEVE portare come
		 *    `subjectAltName` l'indirizzo su cui il server risponde».  Un
		 *    SAN `0.0.0.0` non combacia con NIENTE, e ⚠ «un browser che
		 *    trova un SAN che non combacia mostra un avviso DIVERSO, e
		 *    alcuni non offrono nemmeno il clic per proseguire».  Non si
		 *    indovina: si chiede. */
		fprintf(stderr,
		        "⛔ serve --nome: il certificato deve portare l'indirizzo su "
		        "cui il server risponde (RCP.md §4.1), e «%s» non e' un "
		        "indirizzo.\n",
		        nome);
		return 2;
	}

	signal(SIGINT, al_segnale);
	signal(SIGTERM, al_segnale);
	signal(SIGPIPE, SIG_IGN);

	registro_dice(REG_AVVIO, "REMOTIX_V2 — fase 1, il filo nudo");

	/* ⛔ §4.4-bis: «il ban sopravvive al riavvio», ed e' l'invariante I7 — la
	 *    protezione di un difetto noto sta nel programma, non in una riga di
	 *    configurazione che si puo' perdere. */
	{
		int n = rcp_ban_carica(file_ban, registro_ora_ms());
		if (n < 0) {
			/* ⛔ «zero ban» e «non ho potuto guardare» sono due fatti
			 *    diversi (`rcp.h`, `LEZIONI.md` §1.9 regola 1): il
			 *    secondo e' la protezione spenta con l'aria di non avere
			 *    niente da proteggere, cioe' l'invariante I7 rotta in
			 *    silenzio.  Non si parte. */
			registro_dice(REG_AVVIO,
			              "⛔ il file dei ban %s c'e' e NON si e' potuto "
			              "leggere: non e' «zero ban», e' la protezione di "
			              "§4.4-bis spenta.  Non si parte.",
			              file_ban);
			return 1;
		}
		registro_dice(REG_AVVIO, "ban: %s, %d indirizzi caricati", file_ban, n);
	}

	/* ⭐ «Come si esce: le 12 ore che passano, oppure un comando di sblocco sul
	 *    server — che chiede l'accesso alla macchina, cioe' l'unica chiave che
	 *    quel caso ammette» (`SPECIFICHE.md` §4.2, `RCP.md` §4.4-bis).  ⛔ E il
	 *    comando parla col processo VIVO, che e' l'unico che ha in mano la
	 *    tabella dei ban: vedi il riquadro di `comando.h`, rilievo R12.1.
	 *
	 * ⚠ `comando_apri()` restituisce NULL anche quando il socket non e' stato
	 *   chiesto, e in tutt'e due i casi scrive PERCHE': il server va avanti,
	 *   perche' senza comando la protezione di §4.4-bis c'e' ancora — si esce
	 *   solo con le dodici ore. */
	k = comando_apri(socket_comando);

	guarda_il_servizio_pam();

	if (!certificati_prepara(&cert, dir_cert, nome))
		goto fine;

	ctx_quic = tls_contesto_quic(cert.sessione_pem, cert.sessione_key);
	ctx_pagina = tls_contesto_pagina(cert.pagina_pem, cert.pagina_key);
	if (!ctx_quic || !ctx_pagina)
		goto fine;

	t = trasporto_apri(indirizzo, porta, ctx_quic);
	if (!t)
		goto fine;
	p = pagina_apri(indirizzo, porta, ctx_pagina, file_html, &cert);
	if (!p)
		goto fine;

	registro_dice(REG_AVVIO,
	              "⭐ pronto: https://%s:%s  —  la sessione WebTransport vive "
	              "su /rcp/1 (RCP.md §2.2)",
	              nome, porta);

	ultimo_controllo_cert = time(NULL);

	while (!si_ferma) {
		struct pollfd fds[MAX_POLL];
		size_t n = 0, npagina, ncomando;
		int attesa;

		fds[n].fd = trasporto_fd(t);
		fds[n].events = POLLIN;
		fds[n].revents = 0;
		n++;

		npagina = pagina_descrittori(p, fds + n, MAX_POLL - n);
		ncomando = comando_descrittori(k, fds + n + npagina,
		                               MAX_POLL - n - npagina);

		attesa = trasporto_attesa_ms(t);
		if (attesa < 0 || attesa > 1000)
			attesa = 1000;

		if (poll(fds, n + npagina + ncomando, attesa) < 0) {
			if (errno == EINTR)
				continue;
			registro_dice(REG_AVVIO, "⛔ poll: %s", strerror(errno));
			break;
		}

		if (fds[0].revents & POLLIN)
			trasporto_leggi(t);
		trasporto_scaduti(t);
		pagina_muovi(p, fds + 1, npagina);
		comando_muovi(k, fds + 1 + npagina, ncomando);

		/* ⛔ LA ROTAZIONE, e si guarda una volta al minuto invece che a
		 *    ogni giro: «prima che scada», non «quando e' scaduto»
		 *    (§4.1-bis).  ⚠ Un minuto e' abbondante per un margine di due
		 *    giorni, e non costa niente. */
		if (time(NULL) - ultimo_controllo_cert >= 60) {
			ultimo_controllo_cert = time(NULL);
			if (certificati_ruota_se_serve(&cert)) {
				SSL_CTX *nuovo =
					tls_contesto_quic(cert.sessione_pem, cert.sessione_key);
				if (nuovo) {
					/* ⚠ Le connessioni gia' aperte tengono il vecchio
					 *   contesto: TLS e' gia' fatto, e cambiarlo sotto
					 *   non ha senso.  ⛔ Le NUOVE prendono questo, e
					 *   la pagina pubblica gia' l'impronta nuova. */
					trasporto_contesto(t, nuovo);
					SSL_CTX_free(ctx_quic);
					ctx_quic = nuovo;
					registro_dice(REG_CERT,
					              "⭐ il contesto QUIC usa il certificato "
					              "ruotato; la pagina pubblica gia' la "
					              "nuova impronta e /impronta la serve");
				} else {
					registro_dice(REG_CERT,
					              "⛔ certificato ruotato ma il contesto "
					              "TLS non si rifa': le nuove sessioni "
					              "userebbero un certificato di cui la "
					              "pagina non pubblica l'impronta");
				}
			}
		}
	}

	registro_dice(REG_AVVIO, "chiusura richiesta: %zu connessioni QUIC vive",
	              trasporto_quante(t));

	/* ⛔⭐ E CHI CHIUDE LO DICE — §8.1, §8.2 motivo `0x0C SERVER_IN_CHIUSURA`.
	 *     Rilievo B-7, 10 agosto 2026 notte.
	 *
	 *     Prima di stanotte qui il ciclo usciva e `trasporto_chiudi()` liberava
	 *     tutto: nessun `CONGEDO`, nessun codice di chiusura, nemmeno un
	 *     `CONNECTION_CLOSE`.  Chi era collegato aspettava trenta secondi e
	 *     leggeva «errore di rete» — il difetto di `LEZIONI.md` §1.7 che §3.1
	 *     esiste per togliere, e qui il server non scriveva nemmeno «congedo».
	 *
	 * ⛔ E si ASPETTA che i byte escano, invece di contare i giri: la capsula di
	 *    §3.1 punto 3 matura mezzo secondo dopo che la coda si e' svuotata
	 *    (vedi `wt_batti`), quindi uscire subito sarebbe scrivere il congedo e
	 *    buttarlo.  ⚠ Ma l'attesa ha un fondo — due secondi — o un client che
	 *    non legge piu' terrebbe in piedi lo spegnimento del servizio.  ⛔ La
	 *    rinuncia si scrive: chi spegne deve poter distinguere «l'hanno saputo
	 *    tutti» da «non ho fatto in tempo». */
	{
		size_t restano = trasporto_congeda_tutte(
			t, RCP_SERVER_IN_CHIUSURA, "il server si sta spegnendo");
		int giri = 0;
		while (restano > 0 && giri < 200) {
			struct pollfd fds[MAX_POLL];
			int attesa = trasporto_attesa_ms(t);
			fds[0].fd = trasporto_fd(t);
			fds[0].events = POLLIN;
			fds[0].revents = 0;
			if (attesa < 0 || attesa > 10)
				attesa = 10;
			if (poll(fds, 1, attesa) > 0 && (fds[0].revents & POLLIN))
				trasporto_leggi(t);
			trasporto_scaduti(t);
			restano = trasporto_congeda_tutte(t, RCP_SERVER_IN_CHIUSURA,
			                                  "il server si sta spegnendo");
			giri++;
		}
		if (restano == 0)
			registro_dice(REG_AVVIO,
			              "⭐ congedo 0x0c mandato a tutte le sessioni e uscito "
			              "sul filo in %d giri (§8.1: mai con un silenzio)",
			              giri);
		else
			registro_dice(REG_AVVIO,
			              "⛔ %zu sessioni hanno ancora byte in coda dopo 2 s: "
			              "il congedo 0x0c e' stato scritto ma non e' detto che "
			              "sia uscito.  Si chiude lo stesso.",
			              restano);
	}
	esito = 0;

fine:
	comando_chiudi(k);
	pagina_chiudi(p);
	trasporto_chiudi(t);
	if (ctx_quic)
		SSL_CTX_free(ctx_quic);
	if (ctx_pagina)
		SSL_CTX_free(ctx_pagina);
	return esito;
}
