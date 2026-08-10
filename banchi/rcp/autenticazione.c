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
 */
#include <security/pam_appl.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

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

bool rcp_autentica(const char *utente, const char *parola)
{
	if (!utente || !*utente || !parola)
		return false;

	struct risposta r = {parola};
	struct pam_conv conv = {conversazione, &r};
	pam_handle_t *pam = NULL;

	/* Il servizio PAM: `login` c'e' su ogni Debian.  ⚠ Un servizio dedicato
	 * (`remotix`) sara' meglio nel prodotto — si potra' restringere — ma
	 * introdurlo qui vorrebbe dire che il banco prova un file che nel
	 * prodotto non c'e' ancora. */
	if (pam_start("login", utente, &conv, &pam) != PAM_SUCCESS)
		return false;

	bool ammesso = false;
	if (pam_authenticate(pam, 0) == PAM_SUCCESS &&
	    pam_acct_mgmt(pam, 0) == PAM_SUCCESS)
		ammesso = true;

	pam_end(pam, ammesso ? PAM_SUCCESS : PAM_AUTH_ERR);
	return ammesso;
}
