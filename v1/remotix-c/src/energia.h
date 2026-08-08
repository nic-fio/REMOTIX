/*
 * energia — impedire alla sessione di spegnersi da sola.
 *
 * ⛔ SU KDE UNA SESSIONE REMOTA SI SPEGNE LO SCHERMO DA SOLA DOPO DIECI MINUTI,
 *    e si blocca dopo cinque.  Sono due predefiniti, non due guasti:
 *
 *      - powerdevil ha «spegni lo schermo dopo 10 minuti» ACCESO per difetto
 *        (`powerdevilsettingsdefaults.cpp:61-80`), e non dipende dalla cura di
 *        logind di §3.4-bis di `SPECIFICA.md`;
 *      - `kscreenlockerrc [Daemon] Autolock` vale **true** con `Timeout=5`
 *        (`kscreenlockersettings.kcfg:8-18`).
 *
 *    Chi si collega e resta a guardare un desktop fermo se li prende tutti e
 *    due.  (`kde.md` §10.2)
 *
 * ⛔ E L'ORDINE FRA I DUE NON E' INDIFFERENTE: **a blocco attivo powerdevil
 *    ignora le inibizioni** (`powerdevilpolicyagent.cpp:509`).  Spegnere il
 *    locker non e' quindi una comodita' che si aggiunge a questa inibizione: e'
 *    la sua PRECONDIZIONE, e si ottiene con `kwin_wayland --no-lockscreen` —
 *    cioe' nel drop-in che scrive `sessione.c`, non qui.
 *
 * La via giusta e' `AddInhibition(types=4)`, dove 4 e' `ChangeScreenSettings` e
 * **implica** `InterruptSession` (`powerdevilpolicyagent.cpp:737-745`).  La via
 * freedesktop (`org.freedesktop.PowerManagement.Inhibit`) mappa **solo** su
 * `InterruptSession` e **non ferma lo schermo**: sembra la stessa cosa e non lo
 * e'.
 *
 * Nessun controllo di permesso, effetto dopo cinque secondi, e si rilascia da
 * se' alla caduta del nostro nome sul bus — quindi anche se il processo muore
 * male non resta niente appeso.
 */
#pragma once

#include <glib.h>

#include "compositore.h"

typedef struct Energia Energia;

/*
 * Chiede al gestore dell'energia di non spegnere lo schermo.
 *
 * Su Mutter non fa niente e restituisce NULL: la' la cura e' quella di §3.4-bis
 * di `SPECIFICA.md` — `sleep.conf` e polkit — che vale identica su KDE per la
 * sospensione, ma non copre lo spegnimento dello schermo.
 *
 * Non fallisce in modo utile al chiamante: se non riesce lo dice nel registro e
 * si prosegue.  Un desktop che dopo dieci minuti si oscura e' molto piu' di
 * nessun desktop (§2 di `SPECIFICA.md`).
 */
Energia *energia_inibisci(TipoCompositore tipo);

void energia_rilascia(Energia *energia);
