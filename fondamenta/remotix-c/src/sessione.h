/*
 * sessione — la sessione grafica: REMOTIX la avvia, non si limita a trovarla.
 *
 * Perche' (§5.9-bis di SPECIFICA.md): dopo un «Esci» dal menu di sistema non
 * c'e' piu' niente da mostrare, e al primo avvio della macchina non c'e' alcun
 * gestore di accesso grafico che apra una sessione — e non deve esserci, ne
 * aprirebbe una LOCALE che confligge con le regole di §3.4.
 *
 * Due regole pagate care, entrambe codificate qui:
 *
 *   - L'AMBIENTE SI COMPONE, NON SI EREDITA.  Chi avvia la sessione le regala
 *     tutto il proprio ambiente, comprese le variabili che non c'entrano
 *     nulla, e da li' la sessione lo ridistribuisce al gestore systemd
 *     dell'utente e all'attivazione D-Bus, dove SOPRAVVIVE al compositore.  Una
 *     `LC_ALL=C` arrivata per sbaglio da una shell SSH ha impedito a TUTTE le
 *     applicazioni di aprirsi, e il sintomo non diceva «manca una variabile»:
 *     diceva «le applicazioni non partono».
 *   - LA VITALITA' SI ACCERTA SENZA INTERPRETARE LA RISPOSTA.  Si guarda solo
 *     che la risposta ARRIVI.  Dichiarare il tipo di ritorno di
 *     `GetCurrentState` significa che la vitalita' della sessione dipende
 *     dall'esattezza di quella dichiarazione, e la prima stesura in Rust
 *     falliva cosi': la sessione era partita e REMOTIX la dava per morta.
 *     Anche `Ping` e `Introspect` non valgono, perche' rispondono pure a ciclo
 *     principale fermo: li serve la libreria D-Bus per conto proprio (§5.6).
 */
#pragma once

#include <gio/gio.h>
#include <glib.h>
#include <stdint.h>

#include "compositore.h"

/*
 * L'UNICO modo lecito di prendere il bus di sessione.
 *
 * ⛔ Non si chiama mai `g_bus_get_sync(G_BUS_TYPE_SESSION, ...)` direttamente.
 *
 * GIO, sulla connessione al bus di SESSIONE, tiene acceso «exit-on-close»: se
 * il bus si chiude, la libreria chiama `raise(SIGTERM)` per conto nostro.  Al
 * logout `dbus.service` dell'utente si ferma, e REMOTIX moriva li' — non
 * ucciso da systemd ne' da nessun altro, ma da se stesso, dentro un gestore di
 * segnale GObject emesso dal ciclo principale.  La pila che lo dimostra e' del
 * 4 agosto 2026.  Per il bus di SISTEMA il difetto non esiste: quello resta.
 *
 * Restituisce un riferimento nuovo (la connessione e' comunque una sola per
 * tutto il processo, quindi spegnere l'interruttore una volta basta: lo si fa
 * qui ogni volta perche' costi nulla e non dipenda dall'ordine delle chiamate).
 */
GDBusConnection *sessione_bus(GError **sbaglio);

/*
 * Come si avvia una sessione senza monitor, per famiglia di compositore.
 *
 * In tutti e due i casi il comando e' la parte FACILE: quel che decide se il
 * compositore parte senza schermo e' la sovrascrittura dell'`ExecStart` della
 * sua unita' — su GNOME quella della Shell, su KDE quella di `kwin_wayland`.
 *
 * ⛔ E LA DIFFERENZA E' CHE SU KDE QUELLA SOVRASCRITTURA LA SCRIVIAMO NOI, A
 *    OGNI AVVIO.  Vive in `$XDG_RUNTIME_DIR/systemd/user.control`, cioe' in un
 *    filesystem che si azzera al riavvio — ed e' un bene, perche' porta dentro
 *    **la misura del desktop**, che e' quella del primo client che si collega.
 *    E' la decisione dell'utente dell'8 agosto 2026 presa alla lettera: misura
 *    fissa alla connessione.
 */
#define SESSIONE_COMANDO_GNOME "exec gnome-session --session=gnome"
#define SESSIONE_COMANDO_KDE "exec startplasma-wayland"

const char *sessione_comando_predefinito(TipoCompositore tipo);

/* Vero se c'e' un compositore che risponde. */
gboolean sessione_viva(void);

/* Si assicura che ci sia una sessione grafica, avviandola se manca.
 * `avviata` (facoltativo) dice se l'ha dovuta avviare. */
/*
 * `larghezza` e `altezza` servono solo dove il compositore vuole saperle
 * all'avvio, cioe' su KDE: finiscono nel `--width/--height` del drop-in.  Su
 * GNOME non si usano — la' il monitor si chiede a compositore gia' avviato.
 *
 * ⚠ Valgono per la sessione che si AVVIA.  Se una sessione c'e' gia', la sua
 *   misura e' quella che aveva, e nessuno la cambia: su KWin un output virtuale
 *   non si ridimensiona (`kde.md` §8.1).
 */
gboolean sessione_assicura(const char *comando, TipoCompositore tipo, uint32_t larghezza,
                           uint32_t altezza, gboolean *avviata, GError **sbaglio);

/*
 * Termina la sessione grafica.  Restituisce TRUE se c'era e ora non c'e' piu'.
 *
 * # Perche' esiste
 *
 * Perche' «la sessione locale vince» (§3.4) non significa soltanto staccare il
 * client: se il compositore remoto restasse in piedi, l'utente che si siede
 * davanti alla macchina avrebbe **due sessioni grafiche a proprio nome** sullo
 * stesso `$XDG_RUNTIME_DIR`, e la seconda troverebbe il nome D-Bus
 * `org.gnome.Shell` gia' occupato.  Il difetto si vedrebbe dove nessuno lo
 * cerca: sulla sessione LOCALE che non parte.
 *
 * # Prima si chiede, poi si insiste
 *
 * `Logout(1)` e' l'uscita ordinata senza domande: le applicazioni ricevono
 * l'avviso e possono salvare.  Ma puo' anche non succedere nulla — un programma
 * con modifiche non salvate ha il diritto di INIBIRE l'uscita — e a quel punto
 * resterebbero le due sessioni che si sta cercando di evitare.  Dopo dieci
 * secondi si insiste, **dichiarandolo nel registro**: e' una perdita possibile
 * di lavoro non salvato, e chi legge deve poterla ricostruire.
 *
 * ⛔ E IL SECONDO PASSO E' DIVERSO SUI DUE COMPOSITORI.  Su GNOME e' `Logout(2)`.
 *    Su KDE **`Logout(2)` non esiste** [✗]: la via ordinata e'
 *    `org.kde.Shutdown.logout()`, e la forzatura e'
 *    `StopUnit("plasma-workspace.target", "fail")` — che e' quel che fa
 *    `plasma-shutdown` alla fine (`kde.md` §6.5).
 *
 * ⚠ E su KDE la via ordinata puo' ANNULLARSI DA SOLA: dopo dieci secondi KWin
 *   mostra una notifica con «Cancel Logout» / «Log Out Anyway» e, se nessuno
 *   risponde, aspetta fino a DUE MINUTI (`kwin/src/sm.cpp:422-508`).  In una
 *   sessione non presidiata nessuno risponde mai — ed e' il motivo per cui il
 *   secondo passo qui non e' un lusso ma la strada normale.
 */
gboolean sessione_termina(TipoCompositore tipo, GError **sbaglio);
