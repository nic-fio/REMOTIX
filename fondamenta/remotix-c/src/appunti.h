/*
 * appunti — la clipboard della SESSIONE, quella di Mutter.
 *
 * L'altra meta' — il canale `cliprdr` verso il client — sta in `scambio.c`.  La
 * divisione e' la stessa di `input.c`/`tastiera.c` e di `suono.c`/`altoparlante.c`:
 * di qua si parla al compositore, di la' si parla al protocollo, e la
 * traduzione fra i due mondi avviene in un posto solo.
 *
 * # La clipboard sta sulla sessione RemoteDesktop, non su un servizio a parte
 *
 * Mutter la espone sulla STESSA sessione che il palco ha gia' aperto per la
 * cattura e per l'input (`org.gnome.Mutter.RemoteDesktop.Session`): sei metodi e
 * due segnali.  Chi non ha una sessione di controllo non ha appunti, e per
 * questo l'oggetto nasce insieme al palco.
 *
 *   EnableClipboard    ci mette in gioco: da qui in poi arrivano i due segnali
 *   SetSelection       «il CLIENT ha copiato roba di questi tipi»
 *   SelectionRead      «dammi quel che la SESSIONE ha copiato»      → fd
 *   SelectionWrite     «ecco quel che il CLIENT aveva copiato»      → fd
 *   SelectionWriteDone chiude il trasferimento, riuscito o no
 *
 *   SelectionOwnerChanged   qualcuno nella sessione ha copiato qualcosa
 *   SelectionTransfer       la sessione vuole incollare roba del client
 *
 * # ⛔ IL SEGNALE DI RITORNO VA RICONOSCIUTO, o si gira in tondo
 *
 * `SelectionOwnerChanged` arriva ANCHE dopo una nostra `SetSelection`, con
 * `session-is-owner` a vero.  Trattarlo come una copia nuova significa
 * annunciare al client quel che il client ci ha appena annunciato — e da li' i
 * due lati si rincorrono.  E' la stessa forma dell'eco del ridimensionamento
 * (R10-bis), in un protocollo diverso.
 *
 * # I due segnali arrivano su un THREAD NOSTRO
 *
 * GDBus consegna i segnali al contesto predefinito del thread che ha
 * sottoscritto, e nessuno dei thread di REMOTIX fa girare un ciclo GLib: il
 * ciclo della connessione aspetta descrittori di FreeRDP, quello di PipeWire e'
 * suo.  Quindi qui si apre un contesto privato e lo si fa girare su un thread
 * dedicato — la stessa soluzione dell'attesa del nodo in `mutter.c`, resa
 * permanente.
 */
#pragma once

#include <gio/gio.h>
#include <glib.h>

#include "compositore.h"

typedef struct Appunti Appunti;

/*
 * La sessione ha copiato qualcosa, e i tipi sono questi (elenco terminato da
 * NULL, valido solo dentro la chiamata).
 *
 * Gira sul thread degli appunti: si traduca e si accodi, senza aspettare.
 */
typedef void (*AppuntiSuOfferta)(const char *const *mime, gpointer dati);

/*
 * La sessione vuole incollare qualcosa che ha il CLIENT: si chieda al client, e
 * quando la risposta arriva si chiami `appunti_rispondi` con questo `serial`.
 *
 * ⛔ VA RISPOSTO SEMPRE, anche fallendo: un `SelectionTransfer` lasciato senza
 *    risposta lascia l'applicazione che sta incollando in attesa a tempo
 *    indeterminato — e quel che l'utente vede e' un desktop che si e' piantato.
 */
typedef void (*AppuntiSuRichiesta)(const char *mime, guint32 serial, gpointer dati);

/*
 * Accende gli appunti sulla sessione di controllo indicata, e li accende UNA
 * VOLTA PER SESSIONE.
 *
 * ⛔ NON SI SPENGONO MAI, ed e' un difetto di Mutter, non una nostra pigrizia.
 *
 *    `handle_disable_clipboard` (Mutter 48.7, `meta-remote-desktop-session.c`)
 *    stacca il proprio gestore di «owner-changed» e azzera la sorgente, ma
 *    NON rimette a falso `is_clipboard_enabled`.  Da li' in poi la clipboard e'
 *    morta a meta': i segnali non arrivano piu', e un `EnableClipboard` per
 *    riaverli viene rifiutato con «Already enabled».  Chi spegne alla
 *    disconnessione si ritrova, alla connessione dopo, appunti che non
 *    funzionano piu' per il resto della sessione.  Misurato il 5 agosto 2026.
 */
/*
 * ⭐ E SU KWIN LA CLIPBOARD NON STA SU NESSUNA SESSIONE.
 *
 *    Il portale RemoteDesktop di KDE dichiara `clipboard_enabled: false`
 *    (`remotedesktop.cpp:264`): la via di Mutter — gli appunti appesi alla
 *    sessione di controllo — **non ha equivalente**, e non serve.  Si prende
 *    `zwlr_data_control_manager_v1`, che non e' dietro alcun permesso
 *    (`kde.md` §9), con una connessione Wayland propria.
 *
 *    Da cui i due parametri che valgono per uno solo dei due: `bus` e
 *    `percorso_controllo` servono a Mutter e su KWin si passano NULL.
 */
Appunti *appunti_apri(TipoCompositore tipo, GDBusConnection *bus, const char *percorso_controllo,
                      GError **sbaglio);
void appunti_chiudi(Appunti *appunti);

/*
 * L'ultimo elenco di tipi che la SESSIONE ha annunciato, o NULL.
 *
 * ⛔ E' QUI CHE CHI SI RICOLLEGA RITROVA GLI APPUNTI.
 *    `SelectionOwnerChanged` arriva solo quando il proprietario CAMBIA, e a una
 *    riconnessione non cambia niente: senza questa memoria, il client nuovo non
 *    saprebbe mai che c'e' gia' qualcosa da incollare.  La memoria sta QUI, e
 *    non nel canale, proprio perche' deve sopravvivere alla connessione — come
 *    tutto il resto del palco.
 *
 * Restituisce una copia, da liberare con `g_strfreev`.
 */
GStrv appunti_ultimi_tipi(Appunti *appunti);

/* Chi ascolta i due segnali.  Con richiamate a NULL si smette di ascoltare, e
 * la chiamata ASPETTA che nessuna richiamata sia in corso. */
void appunti_ascolta(Appunti *appunti, AppuntiSuOfferta su_offerta,
                     AppuntiSuRichiesta su_richiesta, gpointer dati);

/* «Il client ha copiato roba di questi tipi»: da adesso la sessione puo'
 * chiederla, e la chiedera' con `SelectionTransfer`. */
gboolean appunti_offri(Appunti *appunti, const char *const *mime, GError **sbaglio);

/*
 * Legge quel che la SESSIONE ha copiato, nel tipo chiesto.
 *
 * ⛔ ASPETTA: apre un descrittore e lo legge fino alla fine.  Va chiamata da un
 *    thread che puo' permetterselo — mai dal ciclo della connessione.
 */
GBytes *appunti_leggi(Appunti *appunti, const char *mime, GError **sbaglio);

/*
 * Risponde a una richiesta della sessione.  Con `dati` NULL dichiara di non
 * avere quel che era stato chiesto, che e' comunque una risposta.
 *
 * ⛔ ASPETTA, come `appunti_leggi`, e per lo stesso motivo.
 */
void appunti_rispondi(Appunti *appunti, guint32 serial, GBytes *dati);
