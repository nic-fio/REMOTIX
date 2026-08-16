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

#include "aiutante.h"

#include <nghttp3/nghttp3.h>
#include <ngtcp2/ngtcp2.h>

typedef struct wt wt;

/* ⭐ `aiuto` e' l'aiutante di PAM (`DECISIONI.md` §1.10): uno solo per tutto il
 * server, e questo strato lo riceve senza possederlo.  ⚠ NULL e' lecito e vuol
 * dire «verifica sincrona», cioe' il ripiego dichiarato — il server funziona
 * lo stesso, con il filo che si ferma. */
wt *wt_nuovo(ngtcp2_conn *conn, ngtcp2_ccerr *ultimo_errore,
             const char *provenienza, aiutante *aiuto);

/* ⭐ Il verdetto di PAM che rientra dall'aiutante.  ⛔ `true` se questa
 * connessione era quella che aspettava quella pratica: chi chiama lo passa a
 * tutte, e una sola lo prende. */
bool wt_verdetto(wt *w, uint64_t pratica, bool ammesso);
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

/* ⛔⭐ §5.3 — «il client e' ancora li'».  La chiama `trasporto.c` dopo ogni
 *     pacchetto che ngtcp2 ha ACCETTATO, ed e' l'unica cosa che si muove quando
 *     l'utente guarda e non tocca niente. */
void wt_segno_di_vita(wt *w, ngtcp2_tstamp ts);

/* ⛔ §8.1 — chi chiude DEVE mandare `CONGEDO` col motivo e ripeterlo nel codice
 * della chiusura, «mai con un silenzio».  La chiama il trasporto quando il
 * server si spegne: `RCP_SERVER_IN_CHIUSURA` (§8.2, `0x0C`).  Rilievo B-7. */
void wt_congeda(wt *w, uint8_t motivo, const char *dettaglio);

/* ⛔ «Ha ancora qualcosa da dire?» — serve a chi spegne il server per sapere
 * quando ha finito di far uscire i congedi, invece di contare i giri. */
bool wt_ha_da_dire(const wt *w);
/* ⛔ Perche' ha ancora da dire: «capsula non matura» e «coda non vuota» sono
 *    due guasti diversi, e allo spegnimento avevano la stessa faccia. */
const char *wt_perche_ha_da_dire(const wt *w);

/* ⭐⭐ FASE 3 — IL CICLO DEI FOTOGRAMMI, E DOVE PASSA IL CONFINE.
 *
 * ⛔ QUI C'ERA `wt_video_deposita()`, ED E' STATO TOLTO.  Depositava UN
 *    fotogramma per codec, **di processo**, marcato chiave per costruzione, e
 *    questo strato lo spediva una volta sola per sessione (`bool video_fatto`).
 *    Tre difetti in una funzione, e tutt'e tre della fase 3: il deposito di
 *    processo consegnava a una sessione i pixel di un altro utente (`[M]` 12
 *    agosto 2026, invariante I3); il `chiave = true` per costruzione sarebbe
 *    diventato **una bugia sul filo** appena i delta fossero esistiti (§6.2,
 *    campo `tipo`); e il `bool` fermava il ciclo al primo fotogramma.
 *
 * ⇒ Adesso i fotogrammi ARRIVANO, uno dopo l'altro, dal figlio dell'utente che
 *   li cattura e li codifica (`figlio.h`), e `main.c` li gira qui.
 *
 * ⛔ `utente` NON e' un'etichetta: e' l'invariante I3 sul filo.  Il fotogramma
 *    va **solo** alle sessioni che PAM ha ammesso per quell'utente, e il
 *    confronto si fa qui perche' qui si sa chi e' ciascuna sessione.
 *
 * `codec` e' quello di `RCP.md` §4.3/§6.2 — **1 = HEVC, 2 = AV1**, gli stessi
 * numeri e non una traduzione.  `chiave` e' il tipo VERO letto dal flusso dal
 * codificatore, non una supposizione: §6.2 lo scrive nel campo `tipo`.
 * `istante_us` e' l'orologio MONOTONO del server alla cattura (§6.2): non e'
 * un'ora, e il client non lo confronta col proprio.  `input` e' §7.3.
 *
 * ⚠ I byte si COPIANO dentro la coda di ciascuna sessione: chi cattura puo'
 *   liberare il suo buffer subito dopo. */
/* ⭐⭐ FASE 4 — LA FORMA DEL CURSORE A CHI GUARDA (`RCP.md` §7.2).
 *
 * ⚠ La gemella di `wt_video_diffondi()`, e per la stessa ragione: la forma
 *   nasce nel figlio di UN utente, e va a tutte le sessioni di QUELL'utente —
 *   che possono essere piu' d'una (I4: il palco e' della sessione, non della
 *   connessione).
 * ⛔ `0x0` con `immagine` NULL = cursore nascosto, e si spedisce: e' l'unico
 *    modo che il client ha di sapere che il puntatore e' sparito. */
void wt_cursore_diffondi(const char *utente, uint16_t larghezza,
                         uint16_t altezza, int16_t attivo_x, int16_t attivo_y,
                         const uint8_t *immagine, size_t byte);

void wt_video_diffondi(const char *utente, uint8_t codec, bool chiave,
                       const uint8_t *dati, size_t byte, uint32_t larghezza,
                       uint32_t altezza, uint64_t istante_us, uint32_t input);

/* ⛔⭐ LA CUCITURA CHE MANCAVA — il punto 4 della fase 3.
 *
 *     `rcp_video_serve_chiave()` era LETTA e non serviva a niente, perche'
 *     `codificatore_chiedi_chiave()` non aveva **nessun chiamante nel
 *     prodotto**: un `RICHIEDI_CHIAVE` del client accendeva un `bool` e non
 *     produceva nessuna chiave.  Con `chiavi_ogni = 0` (GOP infinito) dopo la
 *     prima chiave non ne arrivava **mai piu' una**, e lo schermo restava fermo.
 *
 * ⇒ Il palco sta in un altro processo, e questo e' il gancio che attraversa il
 *   confine.  Lo chiama questo strato quando:
 *     · una sessione arriva a `SESSIONE` e il codec e' negoziato
 *       ⇒ `acceso = true`, `chiave = true` (§5.2: il primo DEVE essere chiave);
 *     · §5.2 vuole una chiave (richiesta dal client, delta abbandonato, tela
 *       cambiata) ⇒ `chiave = true`;
 *     · l'ultima sessione di quell'utente se ne va ⇒ `codec = 0`, cioe'
 *       «smetti di catturare».  ⚠ Il palco (I4) resta in piedi: si ferma solo
 *       il ciclo dei fotogrammi. */
typedef void (*wt_video_richiesta)(void *ctx, const char *utente, uint8_t codec,
                                   bool chiave);
void wt_video_gancio(wt_video_richiesta f, void *ctx);

/* ⭐⭐ FASE 4 — IL PONTE DELL'INPUT, e attraversa un confine di PROCESSO.
 *
 * ⛔ Chi sa che l'utente ha premuto: `rcp.c`, che ha convalidato il messaggio
 *    di `RCP.md` §7.3.  Chi sa a quale sessione appartiene: questo modulo.
 *    ⛔ Chi puo' davvero iniettarlo: il **figlio**, che gira come l'utente ed
 *    e' l'unico ad avere la sessione grafica — cioe' un altro processo.
 *    `main.c` fa da ponte perche' e' l'unico che conosce tutt'e due i lati.
 *
 * ⚠ `true` vuol dire «consegnato al palco», NON «il compositore l'ha preso»:
 *   la risposta non torna indietro dal confine di processo.  ⭐ Chi conta quel
 *   che il compositore ha preso davvero e' il figlio, che lo timbra sul
 *   fotogramma (§6.2, campo `input`) — ed e' l'unico posto in cui quel numero
 *   e' la verita' invece di una promessa.
 *
 * `azione` sono i `FIGLI_INPUT_*` di `figlio.h`. */
typedef bool (*wt_input_richiesta)(void *ctx, const char *utente, uint32_t id,
                                   uint8_t azione, uint16_t codice, int premuto,
                                   int32_t a, int32_t b);
void wt_input_gancio(wt_input_richiesta f, void *ctx);

/* ⭐⭐ IL PONTE DELLA TELA — `RCP.md` §7.1, `DECISIONI.md` §5.0-sexies.
 *
 * ⛔ E' SEPARATO DA QUELLO DELL'INPUT, e non per simmetria: un input e' un gesto
 *    gia' convalidato che si inietta e si dimentica, e il suo esito non serve a
 *    nessuno sul filo.  Questa e' una richiesta di **riconfigurare il palco** la
 *    cui risposta arriva **da un'altra parte** — con un fotogramma, decine di
 *    millisecondi dopo o mai — e che il client sta aspettando (§7.1: «a ogni
 *    `ADATTA_TELA` il server DEVE rispondere con un `TELA`»).
 *
 * ⚠ `true` = la domanda e' partita verso il figlio.  ⛔ NON «la tela e'
 *   cambiata»: quello lo dira' `rcp_tela_concessa()`, quando i pixel arrivano
 *   alla misura nuova. */
typedef bool (*wt_ritela_richiesta)(void *ctx, const char *utente,
                                    uint32_t larghezza, uint32_t altezza);
void wt_ritela_gancio(wt_ritela_richiesta f, void *ctx);

/* ⭐⭐ §5.1 — IL GUARDIANO DELLE SESSIONI GRAFICHE LOCALI, e serve a DUE cose
 *     che sembrano una sola e non lo sono:
 *
 *   · ⛔ chi **arriva** e ha gia' una locale ⇒ rifiutato, `0x05 GIA_ATTIVA_LOCALE`
 *     — la domanda la fa `rcp.c` una volta, all'`ATTACCA`;
 *   · ⛔ chi **c'e' gia'** e apre una locale ⇒ la locale VINCE e la remota cade,
 *     `0x04 SESSIONE_LOCALE_PREVALSA` — e questa nessuno la chiede: va
 *     **sorvegliata**, ed e' `wt_sorveglia_locali()`.
 *
 * ⚠ I due codici stanno in `rcp.h` dal 9 agosto 2026 e fino al 15 **nessuna
 *   riga di nessun `.c` li spediva** (rilievo B-7, la stessa forma).
 *
 * `quale` — se non NULL — riceve di che sessione si tratta, **per il registro
 * del server**: §8.2 non permette di dire al client i fatti delle sessioni
 * altrui, e infatti nel corpo del congedo non ci finisce. */
typedef bool (*wt_locale_richiesta)(void *ctx, const char *utente, char *quale,
                                    size_t quanto);
void wt_locale_gancio(wt_locale_richiesta f, void *ctx);

/* Il ripasso: per ogni sessione attaccata chiede al guardiano se quell'utente
 * ha aperto una sessione grafica locale, e in tal caso la congeda con `0x04`.
 * Restituisce quante ne ha congedate.  ⚠ Senza il gancio non fa niente e non si
 * lamenta: la lamentela l'ha gia' fatta `rcp.c` all'attacco, una volta sola. */
size_t wt_sorveglia_locali(void);

/* ⭐⭐ §7.6 — «L'UTENTE HA CHIESTO DI USCIRE», e non e' il congedo.
 *
 * ⛔ Il congedo lascia la sessione viva (I4); questo la FINISCE, e con lei si
 *    chiudono i programmi dell'utente.  Chi lo riceve deve terminare la
 *    sessione grafica di QUELL'utente — il nome lo mette questo modulo, che sa
 *    chi PAM ha ammesso su quella connessione, e non viene dal filo (I3). */
typedef void (*wt_termina_richiesta)(void *ctx, const char *utente);
void wt_termina_gancio(wt_termina_richiesta f, void *ctx);

/* Congeda tutte le sessioni di un utente, saltando `tranne` (che di solito e'
 * quella che ha appena chiesto, gia' congedata da `rcp.c`).  Restituisce
 * quante.  ⛔ Serve a §7.6: la sessione grafica e' UNA (I2), quindi chi la
 * guardasse da un secondo dispositivo resterebbe con uno schermo fermo per
 * sempre. */
size_t wt_congeda_utente(const char *utente, uint8_t motivo, const char *dettaglio,
                         const wt *tranne);

/* ⭐ §7.1 — «il palco non c'e' ANCORA»: rimanda il fondo dei tre secondi sulle
 * sessioni di quell'utente che stanno aspettando proprio quella misura.  ⛔ Non
 * manda niente sul filo: sposta una scadenza, e toglie al padre una deduzione
 * (`LEZIONI.md` §7.5). */
void wt_tela_rimanda(const char *utente, uint32_t voluta_l, uint32_t voluta_a);

/* ⭐⭐ E LA RISPOSTA RIENTRA DI QUI — §7.1.  La manda il figlio (`FiglioTela`) e
 *     `main.c` la porta fin qui, perche' e' questo modulo che sa quali sessioni
 *     sono di quell'utente.
 *
 * ⛔ `avuta_l == 0` = il palco non ce l'ha fatta ⇒ `TELA(NON_ORA)` subito,
 *    invece dei tre secondi del fondo di §7.1. */
void wt_tela_dal_palco(const char *utente, uint32_t voluta_l, uint32_t voluta_a,
                       uint32_t avuta_l, uint32_t avuta_a);

/* ⛔ Il palco di quell'utente non c'e' piu': la sua misura si dimentica.
 * ⚠ «Non lo so» e «era 1920x1080» sono due fatti diversi, e il secondo — quando
 *   e' falso — fa concedere al ri-attacco una tela che nessun fotogramma avra'. */
void wt_palco_dimentica(const char *utente);

/* ⛔ «Qualcuno di questo utente sta ancora guardando?»  Serve a decidere se
 *    spegnere il palco, e la risposta si CHIEDE all'elenco delle sessioni vive
 *    invece di tenersi un contatore a parte: due copie dello stesso insieme
 *    divergono, e quella che sbaglia lascia il palco acceso per sempre. */
bool wt_video_qualcuno_guarda(const char *utente, uint8_t *codec);

/* I quattro numeri del video di una sessione, per il registro e per i banchi.
 * ⛔ Insieme, sempre: «zero abbandonati» detto da solo non distingue una linea
 *    che porta da un canale che non ha mai spedito niente. */
void wt_video_conti(const wt *w, uint32_t *diffusi, uint32_t *saltati,
                    uint32_t *spediti, uint32_t *abbandonati);

/* Per il registro e per i banchi. */
const char *wt_stato_rcp(const wt *w);

#endif
