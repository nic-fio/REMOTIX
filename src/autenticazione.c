/*
 * autenticazione.c — PAM, e la guardia che parte da negato.
 *
 * ---------------------------------------------------------------------------
 * ⭐ DERIVATO DA `v1/remotix-c/src/autenticazione.c` (144 righe), CON DUE
 *    CAMBIAMENTI, E IL PRIMO E' QUELLO CHE `PIANO.md` FASE 1 CHIAMA
 *    «NON UN DETTAGLIO»:
 *
 * 1. ⛔ **E' CADUTO IL CONFRONTO CON L'UTENTE DEL PROCESSO.**  La versione di
 *    v1 chiamava `autenticazione_utente_atteso()` — il nome ricavato dall'uid
 *    EFFETTIVO — e rifiutava chiunque altro *prima* di interpellare PAM.  Era
 *    giusto in v1, dove il server girava dentro la sessione di una persona;
 *    ⛔ **contraddice il multi-tenant** di `SPECIFICHE.md` §5.5, dove il
 *    servizio e' di sistema e serve dieci utenti diversi.
 *
 *    ⚠ E il sintomo, per chi lo riusasse senza toglierlo, sarebbe un server
 *      che funziona **solo per chi lo ha avviato**, e per tutti gli altri dice
 *      «credenziali errate» — cioe' la diagnosi punta sulla password.  E'
 *      il rilievo B10 del banco.
 *
 * 2. Via glib: `gboolean` diventa `bool`.  Il modulo RCP non dipende da glib,
 *    e questa e' una dipendenza in meno da portarsi nel prodotto.
 *
 * ---------------------------------------------------------------------------
 * ⛔ LA GUARDIA PARTE DA NEGATO
 *
 * La regola di v1 che resta, e vale ancora: un server che valida «se ci sono
 * credenziali» non valida niente.  Qui l'esito parte da falso e solo un
 * `PAM_SUCCESS` su **tutt'e due** i passi lo apre.
 *
 * ⚠ E `pam_acct_mgmt` non e' un di piu': `pam_authenticate` dice «questa
 *   parola e' giusta», non «questo conto e' utilizzabile».  Un conto scaduto o
 *   bloccato passa il primo e non il secondo.
 *
 * ---------------------------------------------------------------------------
 * ⭐ E UN TERZO CAMBIAMENTO, DEL 10 AGOSTO 2026 NOTTE (rilievo B-11)
 *
 * 3. ⛔ **Il servizio PAM e' `remotix`, non `login`** — `SPECIFICHE.md` §4.2.
 *    Vedi il riquadro sopra `SERVIZIO_PAM`, il file `src/remotix.pam` che va
 *    installato in `/etc/pam.d/`, e il controllo che `main.c` fa all'avvio.
 *    ⚠ Insieme e' arrivata la distinzione fra «PAM ha rifiutato» e «PAM non ha
 *      potuto giudicare», che prima non c'era: erano lo stesso `false`.
 */
#include <security/pam_appl.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* ⛔ IL SERVIZIO PAM E' `remotix` — `SPECIFICHE.md` §4.2, prima riga:
 *    «PAM locale, servizio `remotix`, con il ban dell'indirizzo dopo tre
 *    tentativi falliti».
 *
 * ⛔ Qui c'era `login`, e la contraddizione con §4.2 stava in una riga —
 *    rilievo B-11, 10 agosto 2026 notte.  Il prezzo non era di forma: su Debian
 *    `/etc/pam.d/login` e' la pila della CONSOLE LOCALE, con `pam_securetty`,
 *    `pam_lastlog`, `pam_motd` e `pam_limits`, e un accesso di rete che passa
 *    di li' eredita politiche pensate per un'altra cosa.
 *
 * ⚠ E il file del servizio va INSTALLATO: `src/remotix.pam` in
 *   `/etc/pam.d/remotix`.  Senza, Linux-PAM ripiega sul servizio `other`, che
 *   su Debian e' `pam_deny` — cioe' **ogni** parola d'ordine giusta viene
 *   rifiutata, con il sintomo «utente o parola non corretti».  ⛔ E' per questo
 *   che il ripiego qui sotto NON e' silenzioso: `perche_no()` distingue «PAM
 *   dice che la parola e' sbagliata» da «PAM non ha potuto giudicare», e chi
 *   accende il server controlla il file all'avvio (`main.c`). */
#define SERVIZIO_PAM "remotix"

struct risposta {
	const char *parola;
};

static int conversazione(int n, const struct pam_message **domande,
                         struct pam_response **risposte, void *dati)
{
	struct risposta *r = (struct risposta *)dati;
	if (n <= 0 || n > 16)
		return PAM_CONV_ERR;
	struct pam_response *out = (struct pam_response *)calloc((size_t)n, sizeof *out);
	if (!out)
		return PAM_BUF_ERR;
	for (int i = 0; i < n; i++) {
		switch (domande[i]->msg_style) {
		case PAM_PROMPT_ECHO_OFF:
			/* la sola domanda a cui rispondiamo: la parola d'ordine */
			/* ⚠ ⛔ LA QUARTA COPIA DELLA PAROLA D'ORDINE, E DICHIARARLA E'
			 *   TUTTO QUEL CHE SI PUO' FARE — rilievo B-13, 10 agosto 2026
			 *   notte.
			 *
			 *   §4.4 dice «va azzerata appena PAM ha risposto», e `rcp.c` lo
			 *   fa su tutte e tre le copie che sono SUE (R9.8: la copia locale
			 *   su ogni strada d'uscita, la coda dell'accumulo dopo il
			 *   `memmove`, `s->acc` prima di liberarlo).  ⛔ Questa quarta
			 *   copia nasce qui e la libera **libpam**, non noi: dal momento
			 *   in cui questa funzione ritorna, il puntatore appartiene al
			 *   modulo, e scriverci sopra dopo che l'ha liberato sarebbe un
			 *   accesso a memoria liberata — un difetto vero comprato per
			 *   coprirne uno probabile.
			 *
			 *   ⭐ Chi azzera, e dove: Linux-PAM lo fa in `_pam_drop_reply()`
			 *      (`libpam/pam_misc.c`), che chiama `_pam_overwrite()` su
			 *      ogni `resp` prima di `free()`.  ⛔ E' vero OGGI e IN
			 *      QUELL'IMPLEMENTAZIONE: chi porta questo file su un'altra
			 *      libreria PAM ha QUESTA riga da rileggere, ed e' la ragione
			 *      per cui e' scritta.  `[M]` misurato il 10 agosto 2026 notte
			 *      (vedi il rapporto del coder): dopo `pam_authenticate()` i
			 *      byte non ci sono piu'. */
			out[i].resp = strdup(r->parola ? r->parola : "");
			if (!out[i].resp) {
				free(out);
				return PAM_BUF_ERR;
			}
			break;
		case PAM_PROMPT_ECHO_ON:
		case PAM_ERROR_MSG:
		case PAM_TEXT_INFO:
		default:
			out[i].resp = NULL;
			break;
		}
		out[i].resp_retcode = 0;
	}
	*risposte = out;
	return PAM_SUCCESS;
}

/* ⛔⭐ «PAM DICE CHE LA PAROLA E' SBAGLIATA» E «PAM NON HA POTUTO GIUDICARE»
 *     SONO DUE FATTI DIVERSI — `LEZIONI.md` §1.9 regola 1, e la faccia comune
 *     di «vuoto» e «proibito».
 *
 *     Per il protocollo l'esito e' uno solo — la guardia parte da negato, e
 *     `RESPINTO(0x07)` e' quel che il client riceve in tutt'e due i casi, come
 *     dev'essere: dire all'esterno «il tuo conto e' bloccato» invece di
 *     «credenziali errate» e' un oracolo.  ⛔ Ma nel REGISTRO DEL SERVER i due
 *     fatti si scrivono diversi, o un `/etc/pam.d/remotix` mancante somiglia
 *     in tutto a mille parole d'ordine sbagliate — e chi diagnostica cerca
 *     nella parola d'ordine per ore.
 *
 * ⚠ Si scrive su `stderr` e non con `registro.h`: questo file e' montato su
 *   DUE ospiti (il prodotto e l'innesto di `banchi/01-b3-rcp-innesta.py`), e
 *   solo uno dei due ha il nostro registro.  `stderr` ce l'hanno tutti e due,
 *   ed e' dove tutt'e due scrivono. */
static void perche_no(const char *utente, const char *passo, pam_handle_t *pam,
                      int rv)
{
	if (rv == PAM_AUTH_ERR || rv == PAM_USER_UNKNOWN ||
	    rv == PAM_PERM_DENIED || rv == PAM_CRED_INSUFFICIENT ||
	    rv == PAM_ACCT_EXPIRED || rv == PAM_NEW_AUTHTOK_REQD ||
	    rv == PAM_MAXTRIES) {
		fprintf(stderr,
		        "RCP: PAM ha RIFIUTATO l'utente «%s» in %s: %s (servizio "
		        "«%s»)\n",
		        utente, passo, pam_strerror(pam, rv), SERVIZIO_PAM);
	} else {
		fprintf(stderr,
		        "RCP: ⛔ PAM NON HA POTUTO GIUDICARE l'utente «%s» in %s: %s "
		        "(servizio «%s») — NON e' «parola sbagliata».  Se manca "
		        "/etc/pam.d/%s, Linux-PAM ripiega su «other» e su Debian "
		        "«other» e' pam_deny: ogni parola giusta viene rifiutata.\n",
		        utente, passo, pam_strerror(pam, rv), SERVIZIO_PAM,
		        SERVIZIO_PAM);
	}
	fflush(stderr);
}

bool rcp_autentica(const char *utente, const char *parola)
{
	if (!utente || !*utente || !parola)
		return false;

	struct risposta r = {parola};
	struct pam_conv conv = {conversazione, &r};
	pam_handle_t *pam = NULL;
	int rv;

	rv = pam_start(SERVIZIO_PAM, utente, &conv, &pam);
	if (rv != PAM_SUCCESS) {
		fprintf(stderr,
		        "RCP: ⛔ pam_start(«%s») e' fallito (%d): nessuna "
		        "autenticazione e' stata nemmeno tentata\n",
		        SERVIZIO_PAM, rv);
		fflush(stderr);
		return false;
	}

	bool ammesso = false;
	rv = pam_authenticate(pam, 0);
	if (rv != PAM_SUCCESS) {
		perche_no(utente, "pam_authenticate", pam, rv);
	} else {
		/* ⚠ `pam_acct_mgmt` non e' un di piu': `pam_authenticate` dice
		 *   «questa parola e' giusta», non «questo conto e' utilizzabile». */
		rv = pam_acct_mgmt(pam, 0);
		if (rv != PAM_SUCCESS)
			perche_no(utente, "pam_acct_mgmt", pam, rv);
		else
			ammesso = true;
	}

	pam_end(pam, ammesso ? PAM_SUCCESS : PAM_AUTH_ERR);
	return ammesso;
}
