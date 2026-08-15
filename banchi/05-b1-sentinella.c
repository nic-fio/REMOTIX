/*
 * 05-b1-sentinella.c — IL BANCO DEL GUARDIANO DELLE SESSIONI LOCALI,
 * `SPECIFICHE.md` §5.1, motivi `0x04` e `0x05`.
 *
 *   sudo ./05-b1-sentinella <utente-di-prova>
 *
 * ---------------------------------------------------------------------------
 * ⛔ PERCHE' QUESTO BANCO NON E' UN BANCO DI RETE, E VUOLE ROOT
 *
 * La regola di §5.1 attraversa quattro cose — il browser, il filo, `rcp.c` e
 * logind — ⛔ ma quella che decide e' **una domanda sola**: *«quest'utente ha
 * una sessione grafica LOCALE?»*.  `CODER.md` §3.6: quando la catena e' gia'
 * ristretta, si chiama la sola funzione sospetta su un ingresso noto.
 *
 * ⛔ E l'ingresso noto qui NON si puo' fingere, ed e' il punto di tutto: una
 *    sessione logind finta non prova niente, perche' il difetto che si teme sta
 *    proprio in **come logind descrive una sessione vera**.  ⇒ Il banco le
 *    sessioni le CREA, con lo stesso PAM che usa il figlio del server, e per
 *    questo vuole root.
 *
 * ---------------------------------------------------------------------------
 * ⛔⛔ IL DIFETTO CHE QUESTO BANCO ESISTE PER PRENDERE — e non e' `0x05`
 *
 * `0x05` («c'e' gia' una locale ⇒ rifiuta») e' facile: basta guardare.  ⛔ Il
 * difetto vero e' il suo rovescio, ed e' quello che rende il prodotto
 * **inutilizzabile invece che permissivo**:
 *
 *   `[R]` noi non chiamiamo `pam_set_item(PAM_RHOST, …)`, quindi le NOSTRE
 *   sessioni risultano `Remote=no` — cioe' **identiche a una locale**, se il
 *   criterio e' `Remote`.  ⇒ Il primo utente che si collega verrebbe respinto
 *   con `0x05` **dalla sua stessa sessione**, e il messaggio direbbe una cosa
 *   vera in un modo che non aiuta nessuno.
 *
 * ⇒ Il caso 2 e' quello che conta: una sessione fatta **come la nostra** non
 *   deve contare.  Un banco che provasse solo il caso 3 sarebbe verde con il
 *   difetto vivo — la forma che `LEZIONI.md` chiama «una prova verde col
 *   difetto vivo».
 *
 * ---------------------------------------------------------------------------
 * ⛔ L'ATTESO SI DICHIARA PRIMA (regola B0.4 di `LEZIONI.md`).
 *
 *   | caso | la scena                                    | atteso |
 *   |------|---------------------------------------------|--------|
 *   |  1   | nessuna sessione dell'utente                 | falso  |
 *   |  2   | una sessione COME LA NOSTRA (senza seat)     | falso  |
 *   |  3   | una sessione LOCALE (seat0, wayland)         | VERO   |
 *   |  4   | chiusa la locale, resta solo la nostra       | falso  |
 *   |  5   | un ALTRO utente ha la locale                  | falso  |
 *   |  6   | l'utente e' alla consolle, ma in TESTO        | falso  |
 *
 * ⭐ Il caso 5 e' il multi-tenant di `DECISIONI.md` §4.6-quater: il guardiano
 *    discrimina **per utente**, e la macchina di prova lo smaschera da sola
 *    (`nicfio` locale, `prova` remoto).
 *
 * ---------------------------------------------------------------------------
 * COME SI COSTRUISCE
 *
 *   cc -O2 -g -std=gnu11 -Wall -Wextra $(pkg-config --cflags gio-2.0) \
 *      -o 05-b1-sentinella 05-b1-sentinella.c ../src/sentinella.c \
 *      ../src/registro.c $(pkg-config --libs gio-2.0) -lpam
 */
#include "../src/sentinella.h"

#include <security/pam_appl.h>
#include <stdarg.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <signal.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

/* ⚠ Il servizio PAM del prodotto: si usa QUELLO, non uno finto.  Un banco che
 *   aprisse una sessione con `pam_permit` proverebbe la propria configurazione,
 *   non la nostra. */
#define SERVIZIO "remotix"

static int casi_falliti;
static int casi_fatti;

static int conversazione_muta(int n, const struct pam_message **m,
                              struct pam_response **r, void *dati)
{
	/* `pam_open_session` non chiede niente; se chiedesse, il banco deve
	 * fallire in modo rumoroso invece di rispondere a caso. */
	(void)n;
	(void)m;
	(void)dati;
	*r = NULL;
	return PAM_CONV_ERR;
}

/*
 * Apre una sessione logind come farebbe chi accede, e la tiene aperta.
 * `seat` NULL ⇒ nessun seat: e' la forma della NOSTRA sessione headless.
 *
 * ---------------------------------------------------------------------------
 * ⛔⛔ SI BIFORCA, E NON E' UN DETTAGLIO DI STILE — [M] 15 agosto 2026
 *
 * La prima stesura apriva tutte le sessioni dallo STESSO processo, e il caso 3
 * era rosso: logind ne creava **una sola**.  ⛔ Il motivo e' che una sessione ha
 * un processo GUIDA, e a chi ne chiede una seconda dallo stesso guida logind
 * restituisce quella che ha gia' — senza errore.
 *
 * ⇒ Ogni sessione vuole il suo processo, ⭐ e cosi' il banco somiglia alla
 *   realta' invece di allontanarsene: nel prodotto ogni sessione ha il suo
 *   figlio, ed e' esattamente per questo che `figlio.c` fa `fork` prima di PAM.
 */
struct sessione_finta {
	pid_t pid;
	int tubo; /* il figlio ci scrive un byte quando la sessione c'e' */
};

static volatile sig_atomic_t si_chiude;

static void al_termine(int s)
{
	(void)s;
	si_chiude = 1;
}

static struct sessione_finta sessione_apri(const char *utente, const char *seat,
                                           int vt, const char *tipo)
{
	struct sessione_finta f = { -1, -1 };
	struct pam_conv conv = { conversazione_muta, NULL };
	pam_handle_t *pam = NULL;
	int tubo[2];
	char riga[128];
	char pronto = 0;
	int rv;

	if (pipe(tubo) != 0)
		return f;

	f.pid = fork();
	if (f.pid < 0) {
		close(tubo[0]);
		close(tubo[1]);
		return f;
	}

	if (f.pid == 0) {
		close(tubo[0]);
		signal(SIGTERM, al_termine);

		rv = pam_start(SERVIZIO, utente, &conv, &pam);
		if (rv != PAM_SUCCESS)
			_exit(3);

		/* ⛔ `pam_systemd` legge il seat e il tipo dall'AMBIENTE PAM, non dai
		 *    parametri: e' esattamente la leva con cui il banco costruisce le
		 *    due scene che deve distinguere. */
		/* ⛔ OGNI SESSIONE VUOLE LA SUA CONSOLE VIRTUALE — [M] 15 agosto 2026.
		 *
		 *    Con `XDG_VTNR=1` per tutte, logind creava la PRIMA e rifiutava le
		 *    successive **in silenzio**: `pam_systemd` e' `optional`, quindi PAM
		 *    tornava `SUCCESS` e il banco credeva di avere una scena che non
		 *    c'era.  ⇒ Il caso 6 era verde perche' vuoto — la forma «prova verde
		 *    col difetto vivo», dentro il banco stesso. */
		if (seat) {
			snprintf(riga, sizeof riga, "XDG_SEAT=%s", seat);
			pam_putenv(pam, riga);
			snprintf(riga, sizeof riga, "XDG_VTNR=%d", vt);
			pam_putenv(pam, riga);
		}
		snprintf(riga, sizeof riga, "XDG_SESSION_TYPE=%s", tipo);
		pam_putenv(pam, riga);
		pam_putenv(pam, "XDG_SESSION_CLASS=user");

		if (pam_open_session(pam, PAM_SILENT) != PAM_SUCCESS) {
			pam_end(pam, PAM_SESSION_ERR);
			_exit(4);
		}

		pronto = 1;
		if (write(tubo[1], &pronto, 1) != 1)
			_exit(5);

		while (!si_chiude)
			pause();

		pam_close_session(pam, PAM_SILENT);
		pam_end(pam, PAM_SUCCESS);
		_exit(0);
	}

	close(tubo[1]);
	/* ⛔ Si ASPETTA il byte: senza, il caso girerebbe mentre la sessione sta
	 *    ancora nascendo, e il rosso sarebbe una corsa invece di un fatto. */
	if (read(tubo[0], &pronto, 1) != 1 || !pronto) {
		printf("   ⛔ la sessione finta non e' nata\n");
		close(tubo[0]);
		waitpid(f.pid, NULL, 0);
		f.pid = -1;
		return f;
	}
	f.tubo = tubo[0];
	return f;
}

static void sessione_chiudi(struct sessione_finta *f)
{
	if (!f || f->pid <= 0)
		return;
	kill(f->pid, SIGTERM);
	waitpid(f->pid, NULL, 0);
	if (f->tubo >= 0)
		close(f->tubo);
	f->pid = -1;
	f->tubo = -1;
	/* ⚠ logind toglie la sessione quando il processo guida se ne va, e non e'
	 *   istantaneo: senza questa pausa il caso successivo leggerebbe uno stato
	 *   che sta cambiando — e un banco che corre contro il sistema misura la
	 *   propria fretta. */
	usleep(400 * 1000);
}

/*
 * ⛔ IL DUMP NON E' VERBOSITA': e' la differenza fra «il caso 3 e' rosso» e «il
 *    caso 3 e' rosso PERCHE' logind non ha dato il seat».  Un banco che dice
 *    solo il colore fa ricominciare la caccia da capo (`LEZIONI.md` §6.2-ter).
 */
static void mostra_sessioni(void)
{
	printf("   ── che cosa dice logind ──\n");
	fflush(stdout);
	if (system("loginctl list-sessions --no-legend | while read id uid u seat rest; do "
	           "printf '   %s ' \"$id\"; "
	           "loginctl show-session $id -p Name -p Type -p Class -p Remote -p Seat -p State "
	           "| tr '\\n' ' '; echo; done") != 0)
		printf("   (loginctl non ha risposto)\n");
}

static void caso(sentinella *s, int n, const char *scena, const char *utente,
                 bool atteso)
{
	char quale[160];
	bool avuto;

	casi_fatti++;
	avuto = sentinella_locale(s, utente, quale, sizeof quale);
	printf("caso %d — %s\n", n, scena);
	printf("   atteso: %-5s  avuto: %-5s  %s\n", atteso ? "VERO" : "falso",
	       avuto ? "VERO" : "falso", avuto ? quale : "(nessuna)");
	if (avuto != atteso) {
		casi_falliti++;
		printf("   ⛔ ROSSO\n");
		mostra_sessioni();
	} else {
		printf("   ✅ verde\n");
		/* ⚠ Con `BANCO_DUMP=1` si guarda anche il verde: un caso verde perche'
		 *   la scena non e' stata costruita e' la forma «prova verde col difetto
		 *   vivo», e senza guardare non si distingue da un verde vero. */
		if (getenv("BANCO_DUMP"))
			mostra_sessioni();
	}
}

int main(int argc, char **argv)
{
	const char *utente = argc > 1 ? argv[1] : "prova";
	const char *altro = argc > 2 ? argv[2] : "provaa1";
	sentinella *s;
	struct sessione_finta nostra = { -1, -1 }, locale = { -1, -1 },
	                     altrui = { -1, -1 }, seduto = { -1, -1 };

	if (geteuid() != 0) {
		fprintf(stderr, "⛔ questo banco crea sessioni logind: vuole root\n");
		return 2;
	}

	s = sentinella_apri();
	if (!s) {
		fprintf(stderr, "⛔ logind non raggiungibile: il banco non puo' dire "
		                "niente, e non dice «verde»\n");
		return 2;
	}

	printf("── il guardiano delle sessioni locali — §5.1, utente «%s» ──\n\n",
	       utente);

	caso(s, 1, "nessuna sessione grafica dell'utente", utente, false);

	/* ⭐ LA SCENA CHE CONTA: una sessione fatta come la nostra — nessun seat. */
	nostra = sessione_apri(utente, NULL, 0, "wayland");
	if (nostra.pid < 0)
		goto fine;
	caso(s, 2, "una sessione COME LA NOSTRA (wayland, SENZA seat)", utente,
	     false);

	locale = sessione_apri(utente, "seat0", 1, "wayland");
	if (locale.pid < 0)
		goto fine;
	caso(s, 3, "e adesso anche una LOCALE (wayland su seat0)", utente, true);

	sessione_chiudi(&locale);
	caso(s, 4, "chiusa la locale, resta solo la nostra", utente, false);

	/* ⭐ Il multi-tenant di §4.6-quater: la locale e' di UN ALTRO. */
	altrui = sessione_apri(altro, "seat0", 2, "wayland");
	if (altrui.pid < 0)
		goto fine;
	caso(s, 5, "la locale e' di un ALTRO utente", utente, false);

	/* ⭐⭐ E QUESTO CASO L'HA TROVATO LA CERTIFICAZIONE, non chi ha scritto il
	 *     banco: innestando il guasto «il tipo grafico non si guarda piu'»
	 *     nessun caso diventava rosso, ⇒ nessun caso esercitava quel controllo.
	 *
	 * ⛔ Ed e' un caso del PRODOTTO, non un riempitivo: `SPECIFICHE.md` §5.1
	 *    dice che un utente puo' avere **innumerevoli sessioni testuali** e che
	 *    testuali e grafiche **convivono**.  ⇒ Chi si e' seduto alla consolle e
	 *    ha fatto un accesso di TESTO non ha una sessione grafica, e la remota
	 *    deve entrare lo stesso. */
	seduto = sessione_apri(utente, "seat0", 3, "tty");
	if (seduto.pid < 0)
		goto fine;
	caso(s, 6, "l'utente e' alla consolle ma in una sessione di TESTO", utente,
	     false);

fine:
	sessione_chiudi(&seduto);
	sessione_chiudi(&altrui);
	sessione_chiudi(&locale);
	sessione_chiudi(&nostra);
	sentinella_chiudi(s);

	printf("\n── %d casi, %d rossi ──\n", casi_fatti, casi_falliti);
	if (casi_fatti < 6)
		printf("⛔ non tutti i casi sono stati eseguiti: il banco NON e' "
		       "verde, e' incompleto\n");
	return (casi_falliti || casi_fatti < 6) ? 1 : 0;
}
