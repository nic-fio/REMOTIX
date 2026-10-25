/*
 * authentication.c — PAM, and the guard that starts from denied.
 *
 * ---------------------------------------------------------------------------
 * ⭐ DERIVED FROM `fondamenta/remotix-c/src/autenticazione.c` (144 lines), WITH TWO
 *    CHANGES, AND THE FIRST IS THE ONE THAT `PLAN.md` PHASE 1 CALLS
 *    «NOT A DETAIL»:
 *
 * 1. ⛔ **THE COMPARISON WITH THE PROCESS USER HAS BEEN DROPPED.**  The v1
 *    version called `autenticazione_utente_atteso()` — the name derived from
 *    the EFFECTIVE uid — and refused anyone else *before* consulting PAM.  It
 *    was right in v1, where the server ran inside one person's session;
 *    ⛔ **it contradicts the multi-tenancy** of `SPECS.md` §5.5, where the
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
 * 3. ⛔ **The PAM service is `remotix`, not `login`** — `SPECS.md` §4.2.
 *    See the box above `SERVICE_PAM`, the file `src/remotix.pam` that must be
 *    installed in `/etc/pam.d/`, and the check `main.c` does at startup.
 *    ⚠ Together with it came the distinction between «PAM refused» and «PAM
 *      could not judge», which did not exist before: they were the same `false`.
 */
#include <pwd.h>
#include <security/pam_appl.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>

/* ⛔ THE PAM SERVICE IS `remotix` — `SPECS.md` §4.2, first line:
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
 *   the fallback below is NOT silent: `why_no()` tells «PAM says the
 *   password is wrong» from «PAM could not judge», and whoever starts the
 *   server checks the file at startup (`main.c`). */
#define SERVICE_PAM "remotix"

bool rcp_authenticate_from(const char *user, const char *password,
                      const char *rhost);
int rcp_authenticate_judged(const char *user, const char *password,
                            const char *rhost);

/* ⭐ `rcp_authenticate_judged()`'s three answers — the byte the PAM helper's
 *    grandchild writes (`helper.c`, `struct response.outcome`). */
#define RCP_PAM_REFUSED 0
#define RCP_PAM_ADMITTED 1
#define RCP_PAM_REFUSED_LOCKED 2

/* ⛔⭐ «REFUSED WHILE `pam_faillock` HAD THE ACCOUNT LOCKED» — `DECISIONS.md`
 *     §11.47 B (the user, 15 Oct 2026).  While the account is locked,
 *     `pam_faillock preauth` refuses even the RIGHT password, with an ordinary
 *     `PAM_AUTH_ERR` (no `PAM_MAXTRIES`), and `rcp.c` counted it towards the
 *     12-hour ban of the owner's own address.
 *
 *     How the lock is recognised: `pam_faillock preauth` — and only it, and only
 *     when the account IS locked — says through the conversation, BEFORE any
 *     module asks the password, «The account is locked due to N failed logins.»
 *     (`pam_info`, `PAM_TEXT_INFO`).  `[M]` 15 Oct 2026, Arch (pam 1.7.3,
 *     pambase 20260616), our `remotix.pam.arch`: locked ⇒ the right password
 *     and a wrong one both give `PAM_AUTH_ERR` with that line then «(10
 *     minutes left to unlock)» then «Password: »; not locked ⇒ only
 *     «Password: »; unknown user ⇒ `PAM_USER_UNKNOWN`, no line.
 *   ⇒ «locked» = that line seen before the password prompt AND
 *     `pam_authenticate` = `PAM_AUTH_ERR`.  It is PAM's own judgement, not
 *     ours, and the client cannot write in our conversation.
 *   ⚠ The text is matched in English: this program never calls `setlocale()`,
 *     so `pam_faillock`'s gettext answers in the «C» locale.  A translation,
 *     or `silent` in `faillock.conf` / on the module line (Fedora's authselect
 *     writes it), means no line ⇒ RCP_PAM_REFUSED, counted as before: the
 *     failure of this detection is the old behaviour, never a free guess.
 *   ⚠ «Before the prompt» matters: a stack that asks the password FIRST (a
 *     `sufficient pam_unix` above `preauth`) could still admit a right
 *     password while «locked», so its no is an ordinary no. */
#define FAILLOCK_LOCKED "The account is locked due to "

struct response {
	const char *password;
	bool prompted;    /* the password was asked */
	bool locked_seen; /* pam_faillock's «locked» line, before the prompt */
};

static int conversation(int n, const struct pam_message **questions,
                         struct pam_response **replies, void *data)
{
	struct response *r = (struct response *)data;
	if (n <= 0 || n > 16)
		return PAM_CONV_ERR;
	struct pam_response *out = (struct pam_response *)calloc((size_t)n, sizeof *out);
	if (!out)
		return PAM_BUF_ERR;
	for (int i = 0; i < n; i++) {
		switch (questions[i]->msg_style) {
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
			r->prompted = true;
			out[i].resp = strdup(r->password ? r->password : "");
			if (!out[i].resp) {
				free(out);
				return PAM_BUF_ERR;
			}
			break;
		case PAM_ERROR_MSG:
		case PAM_TEXT_INFO:
			/* ⭐ §11.47 B: only noted (box at `FAILLOCK_LOCKED`) */
			if (!r->prompted && questions[i]->msg &&
			    strncmp(questions[i]->msg, FAILLOCK_LOCKED,
			            sizeof FAILLOCK_LOCKED - 1) == 0)
				r->locked_seen = true;
			out[i].resp = NULL;
			break;
		case PAM_PROMPT_ECHO_ON:
		default:
			out[i].resp = NULL;
			break;
		}
		out[i].resp_retcode = 0;
	}
	*replies = out;
	return PAM_SUCCESS;
}

/* ⛔⭐ «PAM SAYS THE PASSWORD IS WRONG» AND «PAM COULD NOT JUDGE» ARE TWO
 *     DIFFERENT FACTS — `LESSONS.md` §1.9 rule 1, and the common face of
 *     «empty» and «forbidden».
 *
 *     For the protocol the outcome is one only — the guard starts from denied,
 *     and `REJECTED(0x07)` is what the client receives in both cases, as it
 *     must be: telling the outside «your account is locked» instead of «wrong
 *     credentials» is an oracle.  ⛔ But in the SERVER LOG the two facts are
 *     written differently, or a missing `/etc/pam.d/remotix` looks in every
 *     way like a thousand wrong passwords — and whoever diagnoses searches the
 *     password for hours.
 *
 * ⚠ It is written on `stderr` and not with `log.h`: this file is mounted
 *   on TWO hosts (the product and the graft of `benches/01-b3-graft-rcp.py`),
 *   and only one of the two has our log.  Both have `stderr`, and it is where
 *   both write. */
/* ⛔ R3 (audit of 25 Oct 2026): the NAME that goes to the log.  `why_no()` wrote the raw name the client typed: someone who types the
 *    password in the user field left it in clear in a file that is kept, and control characters (a newline, an escape) went through
 *    untouched — this line does not pass `log.c`'s cleaning.  The rule of the 1.5 (DECISIONS §11.1, §4.4-bis D) is that a name that is
 *    not a user of this machine never reaches a log.  So:
 *      · a user of this machine (`getpwnam_r`)  → `user «name»`, control characters turned into «?», at most 64 bytes;
 *      · anything else                          → `unknown user [a1b2c3]`, the 6 hex of the HMAC the SERVER computed (`rcp_log_tag()`
 *        of rcp.c, under its `log-secret`) and handed down in the environment of this process as REMOTIX_PAM_LOG_TAG by the helper
 *        that forks us (`helper.c`).  ⚠ This file cannot ask rcp.c itself: the helper is the same binary re-executed with a fresh
 *        memory image (the secret is not loaded there, and it is not for this process to read the secret file), and this file is
 *        also mounted on the graft of `benches/01-b3-graft-rcp.py`.  No tag (root side, bench, graft) → `unknown user [??????]`:
 *        the name still never leaves. */
static void name_for_log(const char *user, char *out, size_t cap)
{
	struct passwd pw, *res = NULL;
	char spare[2048];

	if (user && *user && getpwnam_r(user, &pw, spare, sizeof spare, &res) == 0 && res) {
		size_t j = 0;
		const char *p = "user «";
		snprintf(out, cap, "%s", p);
		j = strlen(out);
		for (size_t i = 0; user[i] && i < 64 && j + 4 < cap; i++) {
			unsigned char c = (unsigned char)user[i];
			out[j++] = (c < 0x20 || c == 0x7f) ? '?' : (char)c;
		}
		out[j] = 0;
		snprintf(out + j, cap - j, "»");
		return;
	}
	{
		const char *t = getenv("REMOTIX_PAM_LOG_TAG");
		bool ok = t && strlen(t) == 6;
		for (size_t i = 0; ok && i < 6; i++)
			ok = (t[i] >= '0' && t[i] <= '9') || (t[i] >= 'a' && t[i] <= 'f');
		snprintf(out, cap, "unknown user [%s]", ok ? t : "??????");
	}
}

static void why_no(const char *user, const char *step, pam_handle_t *pam,
                      int rv, bool locked)
{
	char who[160];

	name_for_log(user, who, sizeof who);
	if (rv == PAM_AUTH_ERR || rv == PAM_USER_UNKNOWN ||
	    rv == PAM_PERM_DENIED || rv == PAM_CRED_INSUFFICIENT ||
	    rv == PAM_ACCT_EXPIRED || rv == PAM_NEW_AUTHTOK_REQD ||
	    rv == PAM_MAXTRIES) {
		fprintf(stderr,
		        "RCP: PAM REFUSED %s in %s: %s (service "
		        "«%s»)%s\n",
		        who, step, pam_strerror(pam, rv), SERVICE_PAM,
		        locked ? " — pam_faillock had the account LOCKED (it said "
		                 "so before the password was asked): even the right "
		                 "password is refused until it unlocks, or until "
		                 "`faillock --user <name> --reset` (DECISIONS.md §11.47)"
		               : "");
	} else {
		fprintf(stderr,
		        "RCP: ⛔ PAM COULD NOT JUDGE %s in %s: %s "
		        "(service «%s») — it is NOT «wrong password».  Check that "
		        "/etc/pam.d/%s (or /usr/lib/pam.d/%s on openSUSE) and "
		        "/etc/remotix/denied-users exist: without the first Linux-PAM "
		        "falls back to «other» (pam_deny on Fedora and Arch), without the "
		        "second pam_listfile refuses everyone.\n",
		        who, step, pam_strerror(pam, rv), SERVICE_PAM,
		        SERVICE_PAM, SERVICE_PAM);
	}
	fflush(stderr);
}

/* ⭐ PHASE 17 T6 — THE CLIENT'S ADDRESS, AS sshd GIVES IT (DECISIONI §10.18).
 *
 * `provenance` is the form of `transport.c`, `[address]:port` (brackets
 * for IPv4 too).  PAM gets the BARE address, like sshd's `PAM_RHOST` with
 * `UseDNS no` (its default): no brackets, no port, and an IPv4 mapped into
 * IPv6 (`::ffff:1.2.3.4`, the dual-stack socket) goes back to `1.2.3.4`,
 * as sshd's `ipv64_normalise_mapped()` does.
 * ⇒ `pam_faillock` records the address instead of «SVC remotix», `pam_unix`
 *   writes `rhost=…` in the journal, `pam_access` has the host, and logind
 *   marks the session with `RemoteHost`.
 * Returns false (and `report` empty) if the form is not the expected one: no
 * `PAM_RHOST` is preferred to an invented one. */
bool rcp_rhost_from_provenance(const char *provenance, char *report, size_t cap)
{
	const char *a, *c;
	size_t n;

	if (!report || cap == 0)
		return false;
	report[0] = 0;
	if (!provenance || provenance[0] != '[')
		return false;
	a = provenance + 1;
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
	memcpy(report, a, n);
	report[n] = 0;
	return true;
}

bool rcp_authenticate(const char *user, const char *password)
{
	return rcp_authenticate_from(user, password, NULL);
}

bool rcp_authenticate_from(const char *user, const char *password,
                      const char *rhost)
{
	return rcp_authenticate_judged(user, password, rhost) == RCP_PAM_ADMITTED;
}

int rcp_authenticate_judged(const char *user, const char *password,
                            const char *rhost)
{
	if (!user || !*user || !password)
		return RCP_PAM_REFUSED;

	struct response r = {password, false, false};
	struct pam_conv conv = {conversation, &r};
	pam_handle_t *pam = NULL;
	int rv;

	rv = pam_start(SERVICE_PAM, user, &conv, &pam);
	if (rv != PAM_SUCCESS) {
		fprintf(stderr,
		        "RCP: ⛔ pam_start(«%s») failed (%d): no "
		        "authentication was even attempted\n",
		        SERVICE_PAM, rv);
		fflush(stderr);
		return RCP_PAM_REFUSED;
	}

	/* ⭐ Like sshd (`auth-pam.c`, `sshpam_init`): `PAM_RHOST` = the client's
	 *    address and `PAM_TTY` = the service name («ssh» for it) — modules
	 *    like `pam_time` want a tty, and before the session there is no real
	 *    one.  sshd does not set `PAM_RUSER`, and neither do we. */
	if (rhost && rhost[0])
		pam_set_item(pam, PAM_RHOST, rhost);
	pam_set_item(pam, PAM_TTY, SERVICE_PAM);

	bool admitted = false;
	bool locked = false;
	rv = pam_authenticate(pam, 0);
	if (rv != PAM_SUCCESS) {
		locked = rv == PAM_AUTH_ERR && r.locked_seen;
		why_no(user, "pam_authenticate", pam, rv, locked);
	} else {
		/* ⚠ `pam_acct_mgmt` is not an extra: `pam_authenticate` says
		 *   «this password is right», not «this account is usable». */
		rv = pam_acct_mgmt(pam, 0);
		if (rv != PAM_SUCCESS)
			why_no(user, "pam_acct_mgmt", pam, rv, false);
		else
			admitted = true;
	}

	pam_end(pam, admitted ? PAM_SUCCESS : PAM_AUTH_ERR);
	return admitted ? RCP_PAM_ADMITTED
	                : locked ? RCP_PAM_REFUSED_LOCKED : RCP_PAM_REFUSED;
}
