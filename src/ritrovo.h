/*
 * ritrovo.h — ⭐ PHASE 17, T7: LIVE REMOTIX DESKTOPS THAT NO CHILD HOLDS.
 *
 * ---------------------------------------------------------------------------
 * ⛔ WHY IT EXISTS, WITH THE MEASUREMENT NEXT TO IT
 *
 * `[M]` T2, 29 Sep 2026 (`fasi/17-l-installatore.md` §5.2): stopping the service
 * **does not kill the desktops**.  Parent, PAM helper and child die; the stage,
 * born with `setsid --fork` (`sessione.c`, `avvia()`), lives outside the unit and
 * survives with its programs.  ⛔ But the new parent restarted with
 * «inquilini=0»: nobody counted those desktops — neither the session cap,
 * nor the budget, nor the abandonment clock — and the first new user
 * without the card groups could have had them knocked down by
 * `loginctl terminate-user`.  It is the xrdp case: live sessions nobody finds again.
 *
 * ---------------------------------------------------------------------------
 * ⭐ THE CRITERION — one for all desktops, no per-compositor exceptions
 *
 *   1. a **logind** session with the PAM service `remotix` (`Service=remotix`:
 *      the child opens it with `pam_start("remotix", …)`), in ANY state —
 *      `[M]` T2: it is «closing» 24 ms after birth, because the child calls
 *      `pam_end` without `pam_close_session`, and it stays so while it has processes;
 *   2. in its scope, a process of the user that is **leader of its own
 *      process session** (pid = sid) and whose parent is **not** in the
 *      same scope.  It is the signature of `setsid --fork`, that is of how the product
 *      starts the stage on ALL desktops.  `[M]` T2, after the stop:
 *      `gnome-session-binary` (GNOME), `startplasma-wayland` (KDE), `labwc`
 *      (XFCE, LXQt), all with pid = sid and parent 1.  ⚠ A terminal opened in the
 *      desktop makes its shell a session leader, but its parent (the terminal)
 *      is in the scope: no confusion.
 *
 * ⚠ The user's session bus is not used: the parent is root and root cannot
 *   join it (`figlio.h`, §1.10-bis).  Nor are files written by the
 *   child used: desktops born with the PREVIOUS binary (the upgrade) would not
 *   have them.  Every version has logind and `/proc`.
 */
#ifndef REMOTIX_RITROVO_H
#define REMOTIX_RITROVO_H

#include <stdbool.h>
#include <stddef.h>
#include <sys/types.h>

/* The PAM service the child opens: `pam_start("remotix", …)`. */
#define RITROVO_SERVIZIO_PAM "remotix"

typedef struct {
	char utente[257];
	uid_t uid;
	char sessione[32]; /* the logind id of the session that contains the stage */
	pid_t palco;       /* the leader of the stage (pid = sid) */
	char comm[20];     /* its name, for the log */
	unsigned sessioni; /* how many `remotix` logind sessions the user has */
} RitrovoDesktop;

/*
 * Looks for live REMOTIX desktops: at most `cap`, ONE per user.  Returns how many
 * it wrote, or -1 if logind did not answer (the reason in `perche`).
 * ⚠ Synchronous calls to logind (300 ms ceiling each) and a read of
 *   `/proc`: it is called at startup and now and then, not at every loop turn.
 */
int ritrovo_cerca(RitrovoDesktop *v, int cap, char *perche, size_t quanto);

/*
 * Does user `uid` have a live REMOTIX desktop?  1 yes (and `d`, if not NULL,
 * describes it) · 0 no · -1 unknown (logind silent).  ⛔ Whoever must decide whether
 * to knock something down treats -1 as «yes».
 */
int ritrovo_vivo(uid_t uid, RitrovoDesktop *d);

#endif
