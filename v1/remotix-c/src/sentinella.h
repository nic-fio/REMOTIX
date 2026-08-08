/*
 * sentinella — c'e' una sessione grafica LOCALE del nostro utente?
 *
 * # Perche' la domanda conta
 *
 * Due sessioni grafiche dello stesso utente condividono `$XDG_RUNTIME_DIR`, il
 * gestore systemd dell'utente, il bus di sessione, l'agente delle chiavi e i
 * portali.  Il guasto che ne segue non si presenta come «due sessioni»: si
 * presenta come **applicazioni che non partono**, e si cerca dappertutto tranne
 * che dove sta.  Da qui la regola di §3.4 di SPECIFICA.md: la sessione locale
 * vince, e chi arriva da lontano resta fuori.
 *
 * # Che cosa conta come «grafica locale»
 *
 * Quattro condizioni insieme, piu' una negativa, lette da `systemd-logind`:
 *
 *   | User   | il nostro uid           | le sessioni altrui non ci riguardano   |
 *   | Seat   | non vuoto               | un seat e' hardware vero               |
 *   | Type   | wayland, x11, mir       | `tty` e' testuale e DEVE poter convivere |
 *   | Class  | user                    | esclude greeter, lock-screen, manager  |
 *   | Remote | falso                   | una X11 inoltrata non e' qualcuno davanti |
 *
 * ⛔ LE SESSIONI TESTUALI CONVIVONO LIBERAMENTE, ed e' essenziale: REMOTIX
 *    stesso gira dentro una sessione SSH, e con la regola scritta male —
 *    «esiste una sessione dell'utente, quindi rifiuto» — non si collegherebbe
 *    nessuno, mai.  Per la stessa ragione la propria sessione si esclude anche
 *    per identificatore: il giorno in cui si contasse, il sintomo sarebbe
 *    «rifiuta sempre tutti» e non farebbe sospettare la causa.
 *
 * ⛔ IL SEGNALE DA SOLO NON BASTA: il `Type` di una sessione cambia DOPO la
 *    nascita — chi la registra la promuove a grafica in un secondo momento —
 *    quindi un `SessionNew` letto troppo presto la mostra ancora testuale.
 *    Serve anche un ripasso periodico: una manciata di chiamate al minuto, e
 *    nessuna finestra cieca.
 *
 * ⛔ CHI INTERROGA NON FA I/O.  La risposta va data nell'istante in cui arriva
 *    una connessione; interrogare D-Bus li' significherebbe far aspettare ogni
 *    client per una risposta che quasi sempre e' «no».
 *
 * # Se logind non c'e'
 *
 * Si prosegue SENZA la regola, dichiarandolo nel registro.  L'alternativa —
 * rifiutare tutti — trasformerebbe un bus non raggiungibile in un server
 * inaccessibile senza spiegazione; e chi non ha logind non ha nemmeno il modo
 * di aprire la sessione locale che si sta temendo.
 */
#pragma once

#include <glib.h>

typedef struct Sentinella Sentinella;

/*
 * Chiamata quando lo stato cambia, sul thread della sentinella.
 * `descrizione` vale solo quando `presente` e' vero.
 */
typedef void (*SentinellaCambio)(gboolean presente, const char *descrizione, gpointer dati);

/*
 * Prepara la sentinella e fa SUBITO il primo controllo, prima di tornare: se la
 * macchina ha gia' una sessione grafica locale all'avvio, non deve esistere una
 * finestra iniziale in cui si entra lo stesso.
 */
Sentinella *sentinella_avvia(SentinellaCambio su_cambio, gpointer dati);

/* Lettura senza I/O: lo stato lo tiene aggiornato il thread. */
gboolean sentinella_locale_presente(Sentinella *sentinella, char *descrizione, gsize quanto);

void sentinella_ferma(Sentinella *sentinella);
