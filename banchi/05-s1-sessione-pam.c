/*
 * 05-s1-sessione-pam.c — ⭐ L'ESPERIMENTO: una sessione grafica che nasce
 * DENTRO una sessione logind aperta da PAM.
 *
 *   sudo ./05-s1-sessione-pam <utente> [avvia|stato|ferma]
 *
 * ---------------------------------------------------------------------------
 * ⛔ LA TESI CHE PROVA, e perche' si prova PRIMA di toccare il prodotto
 *
 * `[M]` 15 agosto 2026, sera.  Dopo il riavvio della macchina il desktop remoto
 * non compare piu', e il registro dice tre cose in fila:
 *
 *     sessione  nessun compositore sul bus: la sessione non c'e'
 *     figlio    «SESSIONE MORTA»: guardo e non tocco — far NASCERE una
 *               sessione e' del login vero, non di qui
 *     mutter    Couldn't get class for session '0': No such device or address
 *               Failed to setup: Failed to find any matching session
 *
 * ⛔ L'ultima riga e' la causa, e non e' d'ambiente: `sd_pid_get_session()`
 *    risponde **ENXIO** — cioe' *«questo processo non sta in nessuna sessione
 *    logind»*.  Sotto il gestore d'utente acceso dal **linger** il processo sta
 *    in `user@<uid>.service`, che e' uno **scope di classe `manager`**, non una
 *    sessione: `/run/user/<uid>` e il bus ci sono, ⛔ ma una sessione no.
 *
 * ⇒ Prima del riavvio funzionava perche' la sessione di `prova` era stata
 *   avviata **da un accesso vero** (14 agosto), che una sessione logind la crea.
 *   Il riavvio se l'e' portata via, e nessuno la rifa'.
 *
 * ⭐ LA TESI: se la sessione grafica nasce dentro una sessione logind aperta da
 *    `pam_open_session` — **senza seat**, `Type=wayland`, `Class=user` — allora
 *    Mutter parte, ed e' **headless per costruzione** invece che per accidente
 *    (`DECISIONI.md` §4.3-bis).
 *
 * ⚠ E se la tesi regge, la cura nel prodotto e' una sola riga di mandato:
 *   `figlio.c:2428` dice *«far nascere una sessione e' del login vero, non di
 *   questo mandato»* — ⛔ alla fase 5 quel mandato **e' questo**, perche'
 *   `PIANO.md` alla fase 5 scrive «Produce: **PAM per intero**».
 *
 * ---------------------------------------------------------------------------
 * COME SI COSTRUISCE
 *
 *   cc -O2 -g -std=gnu11 -Wall -Wextra -o 05-s1-sessione-pam \
 *      05-s1-sessione-pam.c -lpam
 */
#include <errno.h>
#include <grp.h>
#include <pwd.h>
#include <security/pam_appl.h>
#include <signal.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

#define SERVIZIO "remotix"
#define COMANDO "exec gnome-session --session=gnome"

static int muta(int n, const struct pam_message **m, struct pam_response **r,
                void *d)
{
	(void)n;
	(void)m;
	(void)d;
	*r = NULL;
	return PAM_CONV_ERR;
}

int main(int argc, char **argv)
{
	const char *utente = argc > 1 ? argv[1] : "prova";
	struct pam_conv conv = { muta, NULL };
	pam_handle_t *pam = NULL;
	struct passwd *pw;
	char **ambiente_pam;
	char riga[256];
	pid_t figlio;
	int rv;

	if (geteuid() != 0) {
		fprintf(stderr, "⛔ vuole root: apre una sessione PAM\n");
		return 2;
	}
	pw = getpwnam(utente);
	if (!pw) {
		fprintf(stderr, "⛔ utente «%s» sconosciuto\n", utente);
		return 2;
	}

	rv = pam_start(SERVIZIO, utente, &conv, &pam);
	if (rv != PAM_SUCCESS) {
		fprintf(stderr, "⛔ pam_start: %s\n", pam_strerror(NULL, rv));
		return 1;
	}

	/*
	 * ⛔⭐ LE TRE COSE CHE SI DICONO A `pam_systemd`, e ciascuna ha un perche'.
	 *
	 *   · `XDG_SESSION_TYPE=wayland` — l'unita' della Shell porta
	 *     `ConditionEnvironment=XDG_SESSION_TYPE=wayland`: senza, il compositore
	 *     **non viene avviato affatto** (`sessione.c`, misurato il 12 agosto);
	 *   · `XDG_SESSION_CLASS=user` — `manager` e' quel che il linger produce, ed
	 *     e' proprio la classe che NON basta a Mutter;
	 *   · ⛔ **nessun `XDG_SEAT`, e non e' una dimenticanza**: e' la condizione
	 *     di `is_headless()`.  Una sessione senza seat e' headless per
	 *     costruzione, ed e' l'unica forma in cui il blocca-schermo di GNOME non
	 *     ci revoca cattura e input (`DECISIONI.md` §4.3-bis).
	 *
	 * ⚠ E `PAM_RHOST`: logind segna la sessione `Remote=yes`.  ⭐ Ripaga due
	 *   volte — e' la seconda cintura del guardiano di §5.1 (`sentinella.c`), e
	 *   fa comparire la provenienza nei registri di sistema (`last`).
	 */
	pam_putenv(pam, "XDG_SESSION_TYPE=wayland");
	pam_putenv(pam, "XDG_SESSION_CLASS=user");
	pam_set_item(pam, PAM_RHOST, "remotix");
	pam_set_item(pam, PAM_TTY, "remotix");

	rv = pam_open_session(pam, PAM_SILENT);
	if (rv != PAM_SUCCESS) {
		fprintf(stderr, "⛔ pam_open_session: %s\n", pam_strerror(pam, rv));
		pam_end(pam, rv);
		return 1;
	}
	printf("✅ sessione PAM aperta per «%s»\n", utente);

	/* ⭐ E QUI STA IL GUADAGNO CHE L'UTENTE AVEVA INDICATO: le variabili non si
	 *    inventano piu' — le mette `pam_systemd`, e si LEGGONO.  `XDG_SESSION_ID`
	 *    e `XDG_RUNTIME_DIR` compresi. */
	ambiente_pam = pam_getenvlist(pam);
	printf("── quel che PAM ha messo nell'ambiente ──\n");
	for (int i = 0; ambiente_pam && ambiente_pam[i]; i++)
		printf("   %s\n", ambiente_pam[i]);

	figlio = fork();
	if (figlio < 0) {
		perror("fork");
		return 1;
	}

	if (figlio == 0) {
		char *envp[24];
		int ne = 0;
		static char e_home[256], e_user[128], e_log[128], e_path[256],
			e_shell[16], e_run[128], e_bus[160], e_desk[64], e_sdesk[64],
			e_tipo[64], e_lang[64];

		if (initgroups(utente, pw->pw_gid) != 0 || setgid(pw->pw_gid) != 0 ||
		    setuid(pw->pw_uid) != 0)
			_exit(30);

		snprintf(e_home, sizeof e_home, "HOME=%s", pw->pw_dir);
		snprintf(e_user, sizeof e_user, "USER=%s", pw->pw_name);
		snprintf(e_log, sizeof e_log, "LOGNAME=%s", pw->pw_name);
		snprintf(e_path, sizeof e_path, "PATH=/usr/local/bin:/usr/bin:/bin");
		snprintf(e_shell, sizeof e_shell, "SHELL=");
		snprintf(e_run, sizeof e_run, "XDG_RUNTIME_DIR=/run/user/%ld",
		         (long)pw->pw_uid);
		snprintf(e_bus, sizeof e_bus,
		         "DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/%ld/bus",
		         (long)pw->pw_uid);
		snprintf(e_desk, sizeof e_desk, "XDG_CURRENT_DESKTOP=GNOME");
		snprintf(e_sdesk, sizeof e_sdesk, "XDG_SESSION_DESKTOP=gnome");
		snprintf(e_tipo, sizeof e_tipo, "XDG_SESSION_TYPE=wayland");
		snprintf(e_lang, sizeof e_lang, "LANG=C.UTF-8");

		envp[ne++] = e_home;
		envp[ne++] = e_user;
		envp[ne++] = e_log;
		envp[ne++] = e_path;
		envp[ne++] = e_shell;
		envp[ne++] = e_run;
		envp[ne++] = e_bus;
		envp[ne++] = e_desk;
		envp[ne++] = e_sdesk;
		envp[ne++] = e_tipo;
		envp[ne++] = e_lang;

		/* ⭐ E quel che PAM ha aggiunto si porta dietro: XDG_SESSION_ID e' li'
		 *    dentro, ed e' esattamente quel che a Mutter mancava. */
		for (int i = 0; ambiente_pam && ambiente_pam[i] && ne < 22; i++)
			if (strncmp(ambiente_pam[i], "XDG_SESSION_ID=", 15) == 0 ||
			    strncmp(ambiente_pam[i], "XDG_SEAT=", 9) == 0 ||
			    strncmp(ambiente_pam[i], "XDG_VTNR=", 9) == 0)
				envp[ne++] = ambiente_pam[i];
		envp[ne] = NULL;

		snprintf(riga, sizeof riga,
		         "exec >>/run/user/%ld/05-s1.log 2>&1; " COMANDO,
		         (long)pw->pw_uid);
		{
			char *a[] = { "sh", "-c", riga, NULL };
			if (chdir(pw->pw_dir) != 0)
				_exit(31);
			execve("/bin/sh", a, envp);
		}
		_exit(32);
	}

	printf("⭐ sessione grafica avviata, pid %ld — il suo registro va in "
	       "/run/user/%ld/05-s1.log\n",
	       (long)figlio, (long)pw->pw_uid);
	printf("⚠ questo processo RESTA VIVO: e' il guida della sessione logind, e "
	       "se muore logind se la porta via.\n");

	/* ⛔ Non si chiude la sessione PAM e non si esce: il processo che ha
	 *    chiamato `pam_open_session` e' il GUIDA della sessione logind.  E' la
	 *    stessa ragione per cui nel prodotto a farlo dovra' essere il FIGLIO,
	 *    che vive quanto la sessione. */
	for (;;)
		pause();
}
