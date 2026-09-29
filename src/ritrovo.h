/*
 * ritrovo.h — ⭐ FASE 17, T7: I DESKTOP REMOTIX VIVI CHE NESSUN FIGLIO TIENE.
 *
 * ---------------------------------------------------------------------------
 * ⛔ PERCHE' ESISTE, CON LA MISURA ACCANTO
 *
 * `[M]` T2, 29 set 2026 (`fasi/17-l-installatore.md` §5.2): fermare il servizio
 * **non uccide i desktop**.  Muoiono padre, aiutante PAM e figlio; il palco,
 * nato con `setsid --fork` (`sessione.c`, `avvia()`), sta fuori dall'unita' e
 * sopravvive coi suoi programmi.  ⛔ Ma il padre nuovo ripartiva con
 * «inquilini=0»: quei desktop non li contava nessuno — ne' il tetto delle
 * sessioni, ne' il budget, ne' l'orologio dell'abbandono — e al primo utente
 * nuovo senza i gruppi della scheda `loginctl terminate-user` li avrebbe
 * potuti buttare giu'.  E' il caso di xrdp: sessioni vive che nessuno ritrova.
 *
 * ---------------------------------------------------------------------------
 * ⭐ IL CRITERIO — uno per tutti i desktop, niente eccezioni per compositore
 *
 *   1. una sessione **logind** col servizio PAM `remotix` (`Service=remotix`:
 *      la apre il figlio con `pam_start("remotix", …)`), in QUALUNQUE stato —
 *      `[M]` T2: e' «closing» 24 ms dopo la nascita, perche' il figlio fa
 *      `pam_end` senza `pam_close_session`, e resta cosi' finche' ha processi;
 *   2. nella sua scope, un processo dell'utente che e' **capo della propria
 *      sessione di processi** (pid = sid) e il cui padre **non** sta nella
 *      stessa scope.  E' la firma di `setsid --fork`, cioe' di come il prodotto
 *      avvia il palco su TUTTI i desktop.  `[M]` T2, dopo lo stop:
 *      `gnome-session-binary` (GNOME), `startplasma-wayland` (KDE), `labwc`
 *      (XFCE, LXQt), tutti con pid = sid e padre 1.  ⚠ Un terminale aperto nel
 *      desktop fa capo di sessione la sua shell, ma suo padre (il terminale)
 *      sta nella scope: non si confonde.
 *
 * ⚠ Non si usa il bus di sessione dell'utente: il padre e' root e root non ci
 *   si collega (`figlio.h`, §1.10-bis).  E non si usano file scritti dal
 *   figlio: i desktop nati col binario di PRIMA (l'aggiornamento) non li
 *   avrebbero.  logind e `/proc` li ha ogni versione.
 */
#ifndef REMOTIX_RITROVO_H
#define REMOTIX_RITROVO_H

#include <stdbool.h>
#include <stddef.h>
#include <sys/types.h>

/* Il servizio PAM che il figlio apre: `pam_start("remotix", …)`. */
#define RITROVO_SERVIZIO_PAM "remotix"

typedef struct {
	char utente[257];
	uid_t uid;
	char sessione[32]; /* l'id logind della sessione che contiene il palco */
	pid_t palco;       /* il capo del palco (pid = sid) */
	char comm[20];     /* il suo nome, per il registro */
	unsigned sessioni; /* quante sessioni logind `remotix` ha l'utente */
} RitrovoDesktop;

/*
 * Cerca i desktop REMOTIX vivi: al piu' `cap`, UNO per utente.  Torna quanti
 * ne ha scritti, o -1 se logind non ha risposto (il perche' in `perche`).
 * ⚠ Chiamate sincrone a logind (300 ms di tetto ciascuna) e una lettura di
 *   `/proc`: si chiama all'avvio e ogni tanto, non a ogni giro del ciclo.
 */
int ritrovo_cerca(RitrovoDesktop *v, int cap, char *perche, size_t quanto);

/*
 * L'utente `uid` ha un desktop REMOTIX vivo?  1 si' (e `d`, se non NULL, lo
 * descrive) · 0 no · -1 non lo so (logind muto).  ⛔ Chi deve decidere se
 * buttare giu' qualcosa tratta -1 come «si'».
 */
int ritrovo_vivo(uid_t uid, RitrovoDesktop *d);

#endif
