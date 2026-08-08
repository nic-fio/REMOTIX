/*
 * mutter — la sequenza obbligata che apre un monitor virtuale e il suo flusso.
 *
 * Si parla alle interfacce DIRETTE del compositore, non a `xdg-desktop-portal`:
 * il portale e' pensato per chi chiede il permesso a un utente seduto davanti
 * allo schermo, e in una sessione senza monitor quell'interazione non puo'
 * avvenire.  E' anche la via del riferimento (§5 di gnome-remote-desktop.md).
 *
 * ⛔ L'ORDINE NON AMMETTE PERMUTE, e ogni permuta la punisce con un errore
 *    diverso (§5.8 regola 1 di SPECIFICA.md, confermata dal riferimento):
 *
 *      1. RemoteDesktop.CreateSession        → percorso, e se ne legge SessionId
 *                                              SENZA avviarla
 *      2. ScreenCast.CreateSession           dichiarando `remote-desktop-session-id`
 *                                            e `disable-animations`
 *      3. RemoteDesktop.Session.Start        ← ADESSO, non prima
 *      4. ScreenCast.Session.RecordVirtual   → percorso del flusso
 *      5. Stream.Start                       ← il FLUSSO, non la sessione
 *
 *    - avviare il controllo prima del punto 2 →
 *      «Remote desktop session already started»: Mutter registra la cattura
 *      solo su un controllo non ancora partito;
 *    - avviare la cattura con `Session.Start` →
 *      «Must be started from remote desktop session».
 *
 *    E in chiusura vale lo stesso, all'inverso: `ScreenCast.Session.Stop` su una
 *    cattura associata risponde «Must be stopped from remote desktop session».
 *    Si chiude fermando il CONTROLLO, e la cattura lo segue.
 *
 * ⛔ IL NODO PIPEWIRE ARRIVA CON UN SEGNALE EMESSO DURANTE `Start`: bisogna
 *    mettersi in ascolto PRIMA di chiamarlo, o si aspetta per sempre un
 *    annuncio gia' passato (§5.6).
 *
 * LA MISURA NON SI DICHIARA QUI.  `RecordVirtual` non la prende: il monitor si
 * chiede, non si impone, e la risoluzione si concorda nella negoziazione
 * PipeWire — vedi `cattura.c`.  E' la base su cui poggera' la fase 6.
 *
 * LA SESSIONE VIVE QUANTO LA CONNESSIONE D-BUS di chi l'ha creata.  Qui si usa
 * quella condivisa di GLib, che vive quanto il processo: ne discende che le
 * sessioni vanno chiuse ESPLICITAMENTE, perche' nessuno lo fara' al posto
 * nostro e ogni rimontaggio lascerebbe a Mutter un monitor virtuale in piu'.
 *
 * La sessione di controllo si crea gia' adesso, benche' la fase 3 non comandi
 * nulla: e' il punto 1 della sequenza, senza il quale la cattura non si puo'
 * associare a niente e il puntatore della fase 4 non avrebbe dove muoversi.
 * Alla fase 4 restera' da innestarci `ConnectToEIS` — vedi la nota sulla scelta
 * di libei in `PIANO.md`.
 */
#pragma once

#include <glib.h>
#include <stdint.h>

typedef struct MutterSessione MutterSessione;

/* Esegue la sequenza per intero e restituisce la sessione pronta, con il nodo
 * PipeWire gia' annunciato. */
MutterSessione *mutter_apri(GError **sbaglio);

/* Il nodo PipeWire da cui leggere i fotogrammi. */
uint32_t mutter_nodo(const MutterSessione *sessione);

/* Il percorso D-Bus del flusso: e' l'indirizzo a cui la fase 4 muovera' il
 * puntatore, e la chiave con cui libei associa la regione dello schermo. */
const char *mutter_percorso_flusso(const MutterSessione *sessione);

/* L'identificativo della sessione di controllo, per chi dovra' parlarle. */
const char *mutter_percorso_controllo(const MutterSessione *sessione);

/*
 * Il descrittore aperto da `ConnectToEIS`: e' il canale su cui viaggiano
 * tastiera e mouse.  Vale -1 se il compositore non l'ha concesso, e in quel
 * caso la sessione resta di sola visione invece di non nascere: guardare senza
 * comandare e' meno di quel che si voleva, ma e' molto piu' di niente.
 *
 * La chiamata lo CONSEGNA: da qui in poi e' di chi l'ha preso, perche' libei
 * dichiara di prenderselo e di chiuderlo lui.  Due proprietari dello stesso
 * descrittore sono una doppia chiusura che si manifesta lontanissimo da qui.
 */
int mutter_prendi_fd_eis(MutterSessione *sessione);

/*
 * L'identificativo dichiarato a `RecordVirtual`.
 *
 * E' la chiave con cui si riconosce, fra le regioni che libei annuncia, quella
 * che corrisponde al nostro monitor virtuale — cioe' come si mette d'accordo il
 * puntatore con l'immagine.  Sostituisce il percorso D-Bus dello stream che i
 * metodi `Notify*` volevano.
 */
const char *mutter_mapping_id(const MutterSessione *sessione);

/* Ferma il controllo — e con lui la cattura — e libera tutto. */
void mutter_chiudi(MutterSessione *sessione);
