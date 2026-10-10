/*
 * autenticazione.c — PAM, and the guard that starts from denied.
 *
 * ---------------------------------------------------------------------------
 * ⭐ DERIVED FROM `fondamenta/remotix-c/src/autenticazione.c` (144 lines), WITH TWO
 *    CHANGES, AND THE FIRST IS THE ONE THAT `PIANO.md` PHASE 1 CALLS
 *    «NOT A DETAIL»:
 *
 * 1. ⛔ **THE COMPARISON WITH THE PROCESS USER HAS BEEN DROPPED.**  The v1
 *    version called `autenticazione_utente_atteso()` — the name derived from
 *    the EFFECTIVE uid — and refused anyone else *before* consulting PAM.  It
 *    was right in v1, where the server ran inside one person's session;
 *    ⛔ **it contradicts the multi-tenancy** of `SPECIFICHE.md` §5.5, where the
 *    service is a system one and serves ten different users.
 *
 *    ⚠ And the symptom, for whoever reused it without removing it, would be a
 *      server that works **only for whoever started it**, and says «wrong
 *      credentials» to everyone else — that is, the diagnosis points at the
 *      password.  It is finding B10 of the bench.
 *
 * 2. glib removed: `gboolean` becomes `bool`.  The RCP module does not depend
 *    on glib, and this is one dependency fewer to carry into the product.
 *
 * ---------------------------------------------------------------------------
 * ⛔ THE GUARD STARTS FROM DENIED
 *
 * The v1 rule that remains, and still holds: a server that validates «if there
 * are credentials» validates nothing.  Here the outcome starts from false and
 * only a `PAM_SUCCESS` on **both** steps opens it.
 *
 * ⚠ And `pam_acct_mgmt` is not an extra: `pam_authenticate` says «this
 *   password is right», not «this account is usable».  An expired or locked
 *   account passes the first and not the second.
 *
 * ---------------------------------------------------------------------------
 * ⭐ AND A THIRD CHANGE, FROM THE NIGHT OF 10 AUG 2026 (finding B-11)
 *
 * 3. ⛔ **The PAM service is `remotix`, not `login`** — `SPECIFICHE.md` §4.2.
 *    See the box above `SERVIZIO_PAM`, the file `src/remotix.pam` that must be
 *    installed in `/etc/pam.d/`, and the check `main.c` does at startup.
 *    ⚠ Together with it came the distinction between «PAM refused» and «PAM
 *      could not judge», which did not exist before: they were the same `false`.
 */
#include <security/pam_appl.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>

/* ⛔ THE PAM SERVICE IS `remotix` — `SPECIFICHE.md` §4.2, first line:
 *    «local PAM, service `remotix`, with the address ban after three failed
 *    attempts».
 *
 * ⛔ There used to be `login` here, and the contradiction with §4.2 lived in
 *    one line — finding B-11, night of 10 Aug 2026.  The price was not one of
 *    form: on Debian `/etc/pam.d/login` is the LOCAL CONSOLE stack, with
 *    `pam_securetty`, `pam_lastlog`, `pam_motd` and `pam_limits`, and a
 *    network login that goes through there inherits policies meant for
 *    something else.
 *
 * ⚠ And the service file must be INSTALLED: `src/remotix.pam` (or the one of
 *   the family: `.fedora`, `.suse`, `.arch`) in `/etc/pam.d/remotix` — on
 *   openSUSE in `/usr/lib/pam.d/remotix`.  Without it, Linux-PAM falls back to
 *   the `other` service, which on Fedora and Arch is `pam_deny` — that is,
 *   **every** right password is refused, with the symptom «user or password
 *   not correct» — and on Debian is a stack that is not ours.  ⛔ This is why
 *   the fallback below is NOT silent: `perche_no()` tells «PAM says the
 *   password is wrong» from «PAM could not judge», and whoever starts the
 *   server checks the file at startup (`main.c`). */
#define SERVIZIO_PAM "remotix"

bool rcp_autentica_da(const char *utente, const char *parola,
                      const char *rhost);

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
			/* the only question we answer: the password */
			/* ⚠ ⛔ THE FOURTH COPY OF THE PASSWORD, AND DECLARING IT IS ALL
			 *   THAT CAN BE DONE — finding B-13, night of 10 Aug 2026.
			 *
			 *   §4.4 says «it must be zeroed as soon as PAM has answered», and
			 *   `rcp.c` does it on all three copies that are ITS OWN (R9.8: the
			 *   local copy on every exit road, the tail of the accumulator
			 *   after the `memmove`, `s->acc` before freeing it).  ⛔ This
			 *   fourth copy is born here and is freed by **libpam**, not by
			 *   us: from the moment this function returns, the pointer belongs
			 *   to the module, and writing over it after it has freed it would
			 *   be a use-after-free — a real defect bought to cover a probable
			 *   one.
			 *
			 *   ⭐ Who zeroes, and where: Linux-PAM does it in `_pam_drop_reply()`
			 *      (`libpam/pam_misc.c`), which calls `_pam_overwrite()` on
			 *      every `resp` before `free()`.  ⛔ It is true TODAY and IN
			 *      THAT IMPLEMENTATION: whoever ports this file to another PAM
			 *      library has THIS line to reread, and that is the reason it
			 *      is written.  `[M]` measured on the night of 10 Aug 2026
			 *      (see the coder's report): after `pam_authenticate()` the
			 *      bytes are no longer there. */
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

/* ⛔⭐ «PAM SAYS THE PASSWORD IS WRONG» AND «PAM COULD NOT JUDGE» ARE TWO
 *     DIFFERENT FACTS — `LEZIONI.md` §1.9 rule 1, and the common face of
 *     «empty» and «forbidden».
 *
 *     For the protocol the outcome is one only — the guard starts from denied,
 *     and `RESPINTO(0x07)` is what the client receives in both cases, as it
 *     must be: telling the outside «your account is locked» instead of «wrong
 *     credentials» is an oracle.  ⛔ But in the SERVER LOG the two facts are
 *     written differently, or a missing `/etc/pam.d/remotix` looks in every
 *     way like a thousand wrong passwords — and whoever diagnoses searches the
 *     password for hours.
 *
 * ⚠ It is written on `stderr` and not with `registro.h`: this file is mounted
 *   on TWO hosts (the product and the graft of `banchi/01-b3-rcp-innesta.py`),
 *   and only one of the two has our log.  Both have `stderr`, and it is where
 *   both write. */
static void perche_no(const char *utente, const char *passo, pam_handle_t *pam,
                      int rv)
{
	if (rv == PAM_AUTH_ERR || rv == PAM_USER_UNKNOWN ||
	    rv == PAM_PERM_DENIED || rv == PAM_CRED_INSUFFICIENT ||
	    rv == PAM_ACCT_EXPIRED || rv == PAM_NEW_AUTHTOK_REQD ||
	    rv == PAM_MAXTRIES) {
		fprintf(stderr,
		        "RCP: PAM REFUSED user «%s» in %s: %s (service "
		        "«%s»)\n",
		        utente, passo, pam_strerror(pam, rv), SERVIZIO_PAM);
	} else {
		fprintf(stderr,
		        "RCP: ⛔ PAM COULD NOT JUDGE user «%s» in %s: %s "
		        "(service «%s») — it is NOT «wrong password».  Check that "
		        "/etc/pam.d/%s (or /usr/lib/pam.d/%s on openSUSE) and "
		        "/etc/remotix/utenti-negati exist: without the first Linux-PAM "
		        "falls back to «other» (pam_deny on Fedora and Arch), without the "
		        "second pam_listfile refuses everyone.\n",
		        utente, passo, pam_strerror(pam, rv), SERVIZIO_PAM,
		        SERVIZIO_PAM, SERVIZIO_PAM);
	}
	fflush(stderr);
}

/* ⭐ PHASE 17 T6 — THE CLIENT'S ADDRESS, AS sshd GIVES IT (DECISIONI §10.18).
 *
 * `provenienza` is the form of `trasporto.c`, `[address]:port` (brackets
 * for IPv4 too).  PAM gets the BARE address, like sshd's `PAM_RHOST` with
 * `UseDNS no` (its default): no brackets, no port, and an IPv4 mapped into
 * IPv6 (`::ffff:1.2.3.4`, the dual-stack socket) goes back to `1.2.3.4`,
 * as sshd's `ipv64_normalise_mapped()` does.
 * ⇒ `pam_faillock` records the address instead of «SVC remotix», `pam_unix`
 *   writes `rhost=…` in the journal, `pam_access` has the host, and logind
 *   marks the session with `RemoteHost`.
 * Returns false (and `fuori` empty) if the form is not the expected one: no
 * `PAM_RHOST` is preferred to an invented one. */
bool rcp_rhost_da_provenienza(const char *provenienza, char *fuori, size_t cap)
{
	const char *a, *c;
	size_t n;

	if (!fuori || cap == 0)
		return false;
	fuori[0] = 0;
	if (!provenienza || provenienza[0] != '[')
		return false;
	a = provenienza + 1;
	c = strchr(a, ']');
	if (!c || c == a)
		return false;
	n = (size_t)(c - a);
	if (n > 7 && strncasecmp(a, "::ffff:", 7) == 0 && memchr(a + 7, '.', n - 7)) {
		a += 7;
		n -= 7;
	}
	if (n >= cap)
		return false;
	memcpy(fuori, a, n);
	fuori[n] = 0;
	return true;
}

bool rcp_autentica(const char *utente, const char *parola)
{
	return rcp_autentica_da(utente, parola, NULL);
}

bool rcp_autentica_da(const char *utente, const char *parola,
                      const char *rhost)
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
		        "RCP: ⛔ pam_start(«%s») failed (%d): no "
		        "authentication was even attempted\n",
		        SERVIZIO_PAM, rv);
		fflush(stderr);
		return false;
	}

	/* ⭐ Like sshd (`auth-pam.c`, `sshpam_init`): `PAM_RHOST` = the client's
	 *    address and `PAM_TTY` = the service name («ssh» for it) — modules
	 *    like `pam_time` want a tty, and before the session there is no real
	 *    one.  sshd does not set `PAM_RUSER`, and neither do we. */
	if (rhost && rhost[0])
		pam_set_item(pam, PAM_RHOST, rhost);
	pam_set_item(pam, PAM_TTY, SERVIZIO_PAM);

	bool ammesso = false;
	rv = pam_authenticate(pam, 0);
	if (rv != PAM_SUCCESS) {
		perche_no(utente, "pam_authenticate", pam, rv);
	} else {
		/* ⚠ `pam_acct_mgmt` is not an extra: `pam_authenticate` says
		 *   «this password is right», not «this account is usable». */
		rv = pam_acct_mgmt(pam, 0);
		if (rv != PAM_SUCCESS)
			perche_no(utente, "pam_acct_mgmt", pam, rv);
		else
			ammesso = true;
	}

	pam_end(pam, ammesso ? PAM_SUCCESS : PAM_AUTH_ERR);
	return ammesso;
}
