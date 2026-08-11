/*
 * webtransport.h — ⭐ LO STRATO WEBTRANSPORT, E RCP SOPRA.
 *
 * ---------------------------------------------------------------------------
 * ⛔ PERCHE' QUESTO FILE ESISTE
 *
 * `DECISIONI.md` §6.4: delle quattro candidate resta `ngtcp2`+`nghttp3`, e
 * ⛔ **nessuna delle due porta WebTransport lato server**.  Danno le fondamenta
 * — l'extended CONNECT di RFC 9220, i datagram, il Capsule Protocol — e non lo
 * strato di sopra.  Questo file E' lo strato di sopra, ed e' il collante che
 * §6.4 voleva conoscere prima di scegliere.
 *
 * I tre buchi che copre, che sono i tre punti che questo file tocca:
 *
 *   1. ⛔ **Non si puo' annunciare WebTransport.**  `nghttp3_settings` ha
 *      `enable_connect_protocol` e `h3_datagram` — le due che stanno negli RFC
 *      — e nient'altro; non c'e' nessun modo di mettere un'impostazione
 *      arbitraria sullo stream di controllo.  `SETTINGS_WT_MAX_SESSIONS`, che
 *      e' quel che i browser cercano, non passa di li'.  ⛔ Si riscrive il
 *      SETTINGS che nghttp3 sta scrivendo, mentre lo scrive.
 *
 *   2. ⛔ **Gli stream WebTransport vanno sottratti a nghttp3.**  Cominciano
 *      col tipo di frame `0x41` seguito dal numero della sessione, e nghttp3
 *      leggerebbe quel numero come una LUNGHEZZA.
 *
 *   3. ⛔ **E i byte che tornano indietro non hanno una strada.**  nghttp3 non
 *      conosce quegli stream, quindi non li mettera' mai fra i vettori da
 *      scrivere: la coda d'uscita e' nostra.
 *
 * ⚠ Nessuno dei tre e' un difetto di ngtcp2 o di nghttp3: fanno HTTP/3, e
 *   WebTransport non e' HTTP/3.
 *
 * ---------------------------------------------------------------------------
 * ⛔ IL PREZZO DICHIARATO, E VA RIPROVATO A OGNI AGGIORNAMENTO DI NGHTTP3
 *
 * Il punto 1 dipende dalla FORMA DEI BYTE che nghttp3 scrive, non da una sua
 * promessa d'API.  `DECISIONI.md` §6.4 lo dichiara: «va riprovato a ogni
 * aggiornamento di nghttp3».  La guardia sta in `riscrivi_impostazioni()`: se i
 * byte non sono quelli attesi non si riscrive niente, lo si dice nel registro,
 * e il server resta senza WebTransport — un guasto rumoroso invece che uno
 * stream di controllo sfasato.
 *
 * ---------------------------------------------------------------------------
 * ⭐ CHE COSA E' CAMBIATO PASSANDO DALL'INNESTO AL PRODOTTO
 *
 * L'innesto (`banchi/01-b2-ngtcp2-wt-innesta.py`) faceva scorrere il tempo di
 * RCP col **keep-alive di QUIC**, cioe' mettendo byte sul filo ogni 100 ms:
 * era l'unico orologio che un esempio ospite gli offrisse, e i suoi commenti lo
 * dichiarano — «un server vero armera' un proprio timer e non mettera' niente
 * sul filo».  ⭐ Qui il server e' nostro e il timer e' nostro: `wt_battito_ns()`
 * dice al ciclo quando ripassare, e per far scorrere il tempo di RCP sul filo
 * non va niente.  `RCP.md` §2.2 vieta un battito applicativo, e non ce n'e'
 * nemmeno l'ombra.
 *
 * ⛔⭐ E QUESTO RIQUADRO ERA MEZZO SBAGLIATO — rilievo B-2, corretto il 10
 *     agosto 2026 notte.  Presentava l'assenza TOTALE di byte sul filo come un
 *     miglioramento sull'innesto, citando §2.2.  ⛔ Ma §4.6 — riquadro R1.8,
 *     normativo — impone al server i **PING del trasporto** finche' aspetta le
 *     credenziali, e distingue esplicitamente le due cose: i PING «non portano
 *     informazione, non hanno una risposta da interpretare, e non creano una
 *     seconda verita' sul silenzio (§2.2)».  Il divieto di §2.2 NON li copre.
 *
 *     ⚠ Senza, i 60 secondi che §4.6 da' per digitare la parola d'ordine sono
 *       IRRAGGIUNGIBILI: al trentesimo scatta l'inattivita' di QUIC e la
 *       connessione muore in silenzio.  L'orologio nostro non basta perche' non
 *       mette un byte sul filo, e quello che uccide la connessione guarda i
 *       byte.  Vedi `regola_tienila_viva()` in `webtransport.c`.
 */
#ifndef REMOTIX_WEBTRANSPORT_H
#define REMOTIX_WEBTRANSPORT_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#include <nghttp3/nghttp3.h>
#include <ngtcp2/ngtcp2.h>

typedef struct wt wt;

wt *wt_nuovo(ngtcp2_conn *conn, ngtcp2_ccerr *ultimo_errore,
             const char *provenienza);
void wt_libera(wt *w);

/* Le chiamate che il trasporto gira qui.  Restituiscono 0 o un errore di
 * ngtcp2 (negativo) da propagare. */
int wt_app_pronta(wt *w); /* la chiave d'applicazione e' pronta: si apre HTTP/3 */
int wt_ricevi_stream(wt *w, uint32_t flags, int64_t stream_id,
                     const uint8_t *dati, size_t len);
int wt_stream_chiuso(wt *w, int64_t stream_id, uint64_t codice, bool con_codice);
int wt_stream_reset(wt *w, int64_t stream_id);
int wt_stream_stop_sending(wt *w, int64_t stream_id);
int wt_ack_stream_data(wt *w, int64_t stream_id, uint64_t len);
int wt_estendi_max_stream_data(wt *w, int64_t stream_id);
int wt_estendi_max_streams_bidi(wt *w, uint64_t max_streams);

/* ⭐ Scrive UN pacchetto: e' il punto in cui lo strato WebTransport fa le due
 * cose che nghttp3 non sa fare.  La chiama il richiamo che il trasporto passa a
 * `ngtcp2_conn_write_aggregate_pkt2`.
 *
 * ⛔ E il `wt *` glielo passa il trasporto, non ngtcp2: il `user_data` di quel
 *    richiamo e' quello della CONNESSIONE, non il nostro.  ⚠ Prendere l'uno per
 *    l'altro compila senza una parola — sono due `void *` — e produce un server
 *    che apre HTTP/3 e poi muore alla prima scrittura con
 *    `ERR_CALLBACK_FAILURE`, cioe' un sintomo che non nomina nessuno dei due
 *    puntatori.  `[M]` 10 agosto 2026, prima accensione contro il cliente di
 *    prova. */
ngtcp2_ssize wt_scrivi(wt *w, ngtcp2_path *path, ngtcp2_pkt_info *pi,
                       uint8_t *dest, size_t destlen, ngtcp2_tstamp ts);

/* ⭐ IL NOSTRO OROLOGIO, al posto del keep-alive dell'innesto.
 * Restituisce l'istante (nella scala di ngtcp2, nanosecondi) in cui questo
 * strato vuole essere richiamato, o UINT64_MAX se non gli serve. */
ngtcp2_tstamp wt_battito_ns(const wt *w);
/* Fa scorrere il tempo di RCP e matura la chiusura rimandata.  Da chiamare
 * quando `wt_battito_ns()` e' passato. */
void wt_batti(wt *w, ngtcp2_tstamp ts);

/* ⛔ §8.1 — chi chiude DEVE mandare `CONGEDO` col motivo e ripeterlo nel codice
 * della chiusura, «mai con un silenzio».  La chiama il trasporto quando il
 * server si spegne: `RCP_SERVER_IN_CHIUSURA` (§8.2, `0x0C`).  Rilievo B-7. */
void wt_congeda(wt *w, uint8_t motivo, const char *dettaglio);

/* ⛔ «Ha ancora qualcosa da dire?» — serve a chi spegne il server per sapere
 * quando ha finito di far uscire i congedi, invece di contare i giri. */
bool wt_ha_da_dire(const wt *w);

/* Per il registro e per i banchi. */
const char *wt_stato_rcp(const wt *w);

#endif
