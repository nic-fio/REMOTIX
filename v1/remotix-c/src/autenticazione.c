#include "autenticazione.h"

#include <pwd.h>
#include <security/pam_appl.h>
#include <string.h>
#include <sys/types.h>
#include <unistd.h>

#include "registro.h"

#define SERVIZIO_PAM "remotix"

const char *autenticazione_utente_atteso(void)
{
	static char *atteso;
	static gsize una_volta;

	if (g_once_init_enter(&una_volta))
	{
		/* Dall'uid EFFETTIVO, non da $USER: quando il server e' avviato con
		 * `sudo -u` o da un'unita' systemd, $USER puo' parlare di qualcun
		 * altro (§3.4). */
		const struct passwd *voce = getpwuid(geteuid());
		atteso = voce && voce->pw_name ? g_strdup(voce->pw_name) : NULL;
		g_once_init_leave(&una_volta, 1);
	}
	return atteso;
}

typedef struct
{
	const char *parola;
} DatiConversazione;

static int conversazione(int n, const struct pam_message **messaggi,
                         struct pam_response **risposte, void *dati_utente)
{
	DatiConversazione *dati = dati_utente;
	struct pam_response *r;

	if (n <= 0 || n > 32)
		return PAM_CONV_ERR;

	r = calloc((size_t) n, sizeof *r);
	if (!r)
		return PAM_BUF_ERR;

	for (int i = 0; i < n; i++)
	{
		switch (messaggi[i]->msg_style)
		{
			case PAM_PROMPT_ECHO_OFF:
			case PAM_PROMPT_ECHO_ON:
				r[i].resp = strdup(dati->parola ? dati->parola : "");
				if (!r[i].resp)
				{
					for (int k = 0; k < i; k++)
						free(r[k].resp);
					free(r);
					return PAM_BUF_ERR;
				}
				break;
			case PAM_ERROR_MSG:
				avviso("PAM: %s", messaggi[i]->msg ? messaggi[i]->msg : "");
				break;
			case PAM_TEXT_INFO:
				diagnostica("PAM: %s", messaggi[i]->msg ? messaggi[i]->msg : "");
				break;
			default:
				break;
		}
	}

	*risposte = r;
	return PAM_SUCCESS;
}

gboolean autenticazione_verifica(const char *utente, const char *dominio, const char *parola)
{
	const char *atteso = autenticazione_utente_atteso();
	DatiConversazione dati = { .parola = parola };
	struct pam_conv conv = { conversazione, &dati };
	pam_handle_t *pam = NULL;
	int esito;

	if (!atteso)
	{
		errore("non so di chi sia la sessione che servo: rifiuto");
		return FALSE;
	}

	if (!utente || !*utente)
	{
		/* R14 in pratica: il client non ha mandato credenziali.  Non e' un
		 * caso da trattare con indulgenza, e' il caso da cui la regola nasce. */
		avviso("rifiutato: il client non ha mandato alcun nome utente (atteso «%s»)", atteso);
		return FALSE;
	}

	/* Il confronto viene PRIMA di PAM: PAM direbbe «credenziale buona» anche a
	 * un altro utente della macchina, che si troverebbe dentro la sessione di
	 * questo.  Sul rifiuto si scrivono ENTRAMBI i nomi, perche' «ho sbagliato
	 * utente» e «qualcuno sta provando a entrare» si distinguono solo cosi'. */
	if (g_strcmp0(utente, atteso) != 0)
	{
		avviso("rifiutato: arrivato «%s», atteso «%s»", utente, atteso);
		return FALSE;
	}

	if (dominio && *dominio)
		diagnostica("dominio dichiarato dal client, ignorato: «%s»", dominio);

	/*
	 * Password assente e password sbagliata sono due guasti diversi e vanno
	 * distinti nel registro, perche' portano a rimedi opposti.
	 *
	 * Senza NLA il client puo' collegarsi SENZA che nessuno gli chieda nulla e
	 * mandare una password vuota — mstsc lo fa quando non ha credenziali
	 * salvate per quell'host.  Da fuori il sintomo e' identico a una password
	 * sbagliata: «connessione rifiutata».  Ed e' successo davvero il 4 agosto,
	 * costando all'utente due prove a vuoto.
	 */
	if (!parola || !*parola)
		avviso("«%s» si e' collegato SENZA password: senza NLA il client puo' non chiederla, "
		       "e va digitata nel client prima di collegarsi",
		       utente);

	esito = pam_start(SERVIZIO_PAM, utente, &conv, &pam);
	if (esito != PAM_SUCCESS)
	{
		errore("pam_start fallita: %s", pam_strerror(pam, esito));
		return FALSE;
	}

	esito = pam_authenticate(pam, PAM_DISALLOW_NULL_AUTHTOK);
	if (esito == PAM_SUCCESS)
		esito = pam_acct_mgmt(pam, PAM_DISALLOW_NULL_AUTHTOK);

	if (esito != PAM_SUCCESS)
		avviso("rifiutato «%s»: %s", utente, pam_strerror(pam, esito));

	pam_end(pam, esito);
	return esito == PAM_SUCCESS;
}
