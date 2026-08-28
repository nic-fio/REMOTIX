/*
 * input — dal client al compositore, via libei.
 *
 * # Perche' libei e non i metodi `Notify*`
 *
 * Deciso il 4 agosto 2026 chiudendo la fase 3 (§5.8 di SPECIFICA.md).  Non
 * perche' i `Notify*` non funzionino — funzionavano, ed erano misurati — ma
 * perche' libei consegna quattro cose che loro non hanno, e la prima chiude una
 * questione aperta invece di rimandarla: la **disposizione di tastiera della
 * sessione**, lo **stato reale dei lucchetti**, un **punto di
 * sincronizzazione** (`ei_ping`) e le **regioni degli schermi**.
 *
 * # ⛔ Non si chiama mai libei dal ciclo del protocollo
 *
 * I gestori di FreeRDP girano dentro il ciclo della connessione.  Una chiamata
 * che aspetta li' dentro ferma quel ciclo e con esso la connessione intera.
 * Qui si **accoda e basta** — operazione che non attende mai — e un thread
 * separato svuota la coda parlando con il compositore.  E' la regola 3 di §5.8
 * di SPECIFICA.md, ed e' anche la forma del riferimento (§13.6 di
 * `gnome-remote-desktop.md`).
 *
 * Ne discende che **libei vive su un thread solo**: non e' una libreria a
 * prova di thread, e tutte le sue chiamate stanno dietro questa interfaccia.
 *
 * # Gli spostamenti del puntatore si accorpano
 *
 * Di una raffica conta dove il puntatore ARRIVA, non la strada che ha fatto. Si
 * scarta uno spostamento solo quando il successivo e' ancora uno spostamento:
 * se in mezzo c'e' un clic, la posizione conta eccome.
 */
#pragma once

#include <glib.h>
#include <stdint.h>

typedef struct Input Input;

/*
 * Prende in consegna il descrittore restituito da `ConnectToEIS` e avvia il
 * thread.  `mapping_id` e' quello dichiarato a `RecordVirtual`: e' la chiave
 * con cui si riconosce, fra le regioni che libei annuncia, quella che
 * corrisponde al nostro monitor virtuale.
 */
/*
 * `scatti_discreti` sceglie fra le due forme della rotella, e le due forme sono
 * due compositori: `ei_device_scroll_discrete(±120)` su KWin, che altrimenti
 * non produce **nessuno scatto**, e `ei_device_scroll_delta` su Mutter, dove il
 * `/120 → ×10` e' quel che e' stato misurato il 4 agosto.  Il perche' per esteso
 * sta accanto a `manda_scatti` in `input.c`.
 */
Input *input_avvia(int fd_eis, const char *mapping_id, gboolean scatti_discreti,
                   GError **sbaglio);
void input_ferma(Input *input);

/* La misura del desktop che il client sta guardando: serve a riscalare le
 * coordinate assolute sulla regione dello schermo. */
void input_misura(Input *input, uint32_t larghezza, uint32_t altezza);

/* Le cinque porte d'ingresso.  Si chiamano dal thread della connessione RDP,
 * accodano e ritornano subito. */
void input_tasto(Input *input, uint16_t flags, uint8_t scancode);
void input_tasto_unicode(Input *input, uint16_t flags, uint16_t carattere);
void input_mouse(Input *input, uint16_t flags, uint16_t x, uint16_t y);
void input_mouse_esteso(Input *input, uint16_t flags, uint16_t x, uint16_t y);
void input_sincronizza(Input *input, uint32_t flags);

/*
 * Rilascia tutto cio' che risulta premuto.
 *
 * Va chiamata a fine connessione **anche se in quel momento non c'e' piu' una
 * sessione a cui parlare**: e' il difetto trovato in prova il 2 agosto.  Lo
 * stato sporco si paga alla connessione SUCCESSIVA, dove il primo colpo su un
 * tasto che risulta ancora premuto viene ingoiato e la lettera non compare.
 */
void input_rilascia_tutto(Input *input);

/*
 * Lo stato VERO dei tasti a scatto, per i compositori che non lo mandano con
 * l'input.
 *
 * ⛔ Serve su KWin, dove `EI_EVENT_KEYBOARD_MODIFIERS` non arriva MAI
 *    (`kde.md` §7.2): senza questa porta, la riconciliazione di BlocMaiusc e
 *    BlocNum sarebbe codice scritto che non gira — che e' peggio di codice che
 *    manca, perche' nessuno va a cercarlo.
 *
 * Si chiama da un altro thread: accoda e ritorna.
 */
void input_lucchetti_veri(Input *input, gboolean maiusc, gboolean num);
