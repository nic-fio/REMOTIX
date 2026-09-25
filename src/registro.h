/*
 * registro.h — le righe che il server scrive, e l'unico posto che le scrive.
 *
 * ---------------------------------------------------------------------------
 * ⛔ PERCHE' UN MODULO E NON UNA `printf`
 *
 * `CODER.md` §6: «dichiarare i ripieghi e le degradazioni nel registro, perche'
 * il revisore possa distinguere un comportamento voluto da uno accidentale».
 * Un registro sparso in venti `fprintf(stderr, ...)` non ha ne' un istante ne'
 * un'area, e le due cose sono quel che rende una riga leggibile a chi cerca un
 * difetto sei ore dopo.
 *
 * ⛔ E B13.2 GUARDA DENTRO QUESTO FILE: «che la parola d'ordine non sia in
 *    nessun registro».  Passare da un solo imbuto e' quel che rende la verifica
 *    possibile — con venti punti di stampa, «non c'e'» sarebbe una speranza.
 */
#ifndef REMOTIX_REGISTRO_H
#define REMOTIX_REGISTRO_H

#include <stdbool.h>
#include <stdint.h>

/* L'area che scrive la riga.  Serve a leggere il registro per colonna quando
 * il trasporto e il protocollo parlano insieme. */
#define REG_AVVIO "avvio"
#define REG_QUIC "quic"
#define REG_WT "wt"
#define REG_RCP "rcp"
#define REG_PAGINA "pagina"
#define REG_CERT "cert"
/* ⭐ Le due aree della fase 2, innestate il 12 agosto 2026 dal montaggio.
 * ⚠ `REG_SESSIONE` stava in testa a `src/sessione.h` con accanto la nota che lo
 *   dichiarava provvisorio, perche' quel file e' nato prima di entrare nel
 *   `Makefile` (`P2-1-sessione.md` §6.2 chiede questa riga). */
#define REG_SESSIONE "sessione"
#define REG_VIDEO "video"
/* ⭐ L'area della fase 10 (25 agosto 2026): il budget di composizione.  ⚠ Ha
 *   un'area sua e non `avvio` perche' scrive in tre momenti diversi — la riga
 *   del valore in vigore, il verdetto su chi bussa, e il rifiuto — e chi cerca
 *   *«perche' quell'utente e' stato respinto»* deve poter leggere una colonna
 *   sola invece di setacciare `wt` e `figlio`. */
#define REG_BUDGET "budget"

/* ⭐ Le quattro funzioni che scrivono sono MACRO sopra quattro `_in`: la
 *    macro ci mette `__FILE__` e `__LINE__`, che vanno nel journal come
 *    `CODE_FILE`/`CODE_LINE` (fase 16 §12).  ⚠ Sulla riga di `stderr` non
 *    compaiono: quella resta byte per byte com'era. */
void registro_dice_in(const char *file, int linea, const char *area,
                      const char *fmt, ...)
	__attribute__((format(printf, 4, 5)));
#define registro_dice(...) registro_dice_in(__FILE__, __LINE__, __VA_ARGS__)

/* Le righe di dettaglio del trasporto: molte, e utili solo quando si sta
 * cercando qualcosa.  Spente di serie. */
void registro_parlantina(bool acceso);
bool registro_parla_molto(void);
void registro_dettaglio_in(const char *file, int linea, const char *area,
                           const char *fmt, ...)
	__attribute__((format(printf, 4, 5)));
#define registro_dettaglio(...) \
	registro_dettaglio_in(__FILE__, __LINE__, __VA_ARGS__)

/*
 * ---------------------------------------------------------------------------
 * ⭐⭐ IL JOURNAL DI SISTEMA — fase 16 §12, 25 settembre 2026.
 *
 * Con `--journal` ogni riga va ANCHE al journal di systemd, col protocollo
 * nativo (un datagramma `CHIAVE=valore` su `/run/systemd/journal/socket`,
 * senza libsystemd), con i campi che servono a filtrare:
 *
 *      MESSAGE            la riga senza l'ora (l'ora la mette il journal)
 *      PRIORITY           3 se il corpo comincia con ⛔, 4 con ⚠, 7 per la
 *                         parlantina, 6 tutto il resto
 *      SYSLOG_IDENTIFIER  remotix        (⇒ `journalctl -t remotix`)
 *      REMOTIX_AREA       l'area         (⇒ `REMOTIX_AREA=rcp`)
 *      REMOTIX_INQUILINO  l'identita', solo se la riga ne ha una
 *      CODE_FILE/LINE     chi l'ha scritta
 *
 * ⛔ La riga su `stderr` NON cambia e NON si spegne: il journal si AGGIUNGE.
 *    I banchi leggono il file, e un journal che non risponde (pieno, fermo,
 *    assente in un contenitore) non deve costare nemmeno una riga.  ⇒ Un
 *    `sendmsg` non bloccante per riga, e se fallisce si tace.
 * ⚠ Non attraversa l'`exec`: il figlio la riceve come `--journal` nella sua
 *   riga di comando, come `--parlantina` (`figlio.c`, `diventa_ed_esegui()`).
 * ⚠ E il figlio, dopo `pam_systemd`, sta nello scope della SESSIONE e non
 *   nell'unita' del server: ⇒ `journalctl -t remotix`, non solo `-u`.
 *
 * Torna false se il socket non si apre (e allora il journal resta spento).
 */
bool registro_journal(bool acceso);
bool registro_nel_journal(void);

/*
 * ⛔⛔ I TASTI NEL REGISTRO — fase 16 §12: «le battute si registrano come
 *      "tasto", mai come carattere».  Un codice evdev E' un carattere, a meno
 *      della disposizione: una fila di `codice evdev 30, 48, 46` e' una parola.
 *
 * ⭐ Tranne i modificatori (Ctrl, Maiusc, Alt, Meta, BlocMaiusc): non dicono
 *    niente di quel che si scrive, e sono proprio quelli che restano giu' e
 *    rendono il desktop inservibile (`RCP.md` §11) — chi indaga ha bisogno
 *    di sapere QUALE.  ⇒ Questa e' la sola domanda che un chiamante deve fare
 *    prima di scrivere un codice di tasto; la risposta sta in un posto solo.
 */
bool registro_tasto_dicibile(unsigned codice_evdev);

/*
 * ---------------------------------------------------------------------------
 * ⛔⛔ DI CHI E' LA RIGA — 25 agosto 2026, rilievo R10-A4, `fasi/10-…md` §6.7.
 *
 * ⛔ IL DIFETTO, MISURATO e non dedotto: con **quattro** sessioni GNOME vere
 *    (57 121 righe, 90 s a regime) solo il **4,2 %** delle righe di DIAGNOSI
 *    diceva di chi parlava; `fotogramma-spedito`, `ciclo-cattura` e
 *    `audio-blocchi` — le tre famiglie piu' grosse — **0,0 %**.  Spenta una
 *    scena su quattro, si *vedeva* che una serie si era fermata 2 volte su 4,
 *    ⛔ ma il registro diceva un NOME **0 volte su 4** — e chi provava a
 *    indovinarlo sbagliava **96 volte su 100**, cioe' mandava a guardare **il
 *    desktop di un altro**.
 *
 * ⭐ L'identita' arriva da due strade, e sono due perche' i processi sono di
 *    due specie — e' l'intera ragione del disegno:
 *
 *      · `registro_identita()` — ⭐ la mette il processo che serve **UNA**
 *        sessione sola: il figlio, che conosce il proprio utente fin
 *        dall'`exec` (`figlio.c`, `argv[2]`).  ⇒ Da li' in poi **ogni** riga di
 *        quel processo la porta, comprese quelle di `codificatore.c` e di
 *        `audio.c`, che di sessioni non sanno niente.
 *      · `registro_dice_di()` — ⭐ la porta la SINGOLA riga, nel processo che
 *        serve **tutte** le sessioni insieme: il padre.  Li' un'identita' di
 *        processo direbbe sempre la stessa cosa, cioe' niente.
 *
 * ⭐ E l'identita' si compone in UN POSTO SOLO (`registro.c`, `riga()`), non
 *    dal chiamante: due punti che scrivono la parentesi la scrivono diversa, e
 *    un lettore che ne trovasse due in testa alla stessa riga non saprebbe piu'
 *    dove comincia il corpo.
 *
 * ⚠ E CHI NON SA TACE: una riga senza identita' esce **senza parentesi**, non
 *   con una parentesi vuota o col nome del vicino.  `[M]` §6.7: il
 *   classificatore che indovina sbaglia il 96,4 % delle volte, quello prudente
 *   che si astiene sbaglia lo **0 %**.  ⇒ «non lo so» e' un esito, e si scrive
 *   non scrivendo.
 *
 * ⛔ 48 e' il tetto: la parentesi sta in testa al CORPO della riga, e un
 *    identificatore lungo mangerebbe il messaggio.  Chi e' piu' lungo viene
 *    tagliato.
 */
#define REG_IDENTITA_MAX 48

/* L'identita' di QUESTO processo, da qui alla fine.  `NULL` o "" la toglie.
 * ⚠ Non attraversa l'`exec`: e' una statica del processo, e il figlio la rimette
 *   appena letto il proprio `argv`. */
void registro_identita(const char *chi);

/* La riga di UNA sessione, scritta da un processo che ne serve molte.
 * ⚠ `chi` NULL o "" ⇒ vale l'identita' di processo; se non c'e' nemmeno quella,
 *   la riga esce muta, che e' la verita'. */
void registro_dice_di_in(const char *file, int linea, const char *area,
                         const char *chi, const char *fmt, ...)
	__attribute__((format(printf, 5, 6)));
#define registro_dice_di(...) \
	registro_dice_di_in(__FILE__, __LINE__, __VA_ARGS__)
void registro_dettaglio_di_in(const char *file, int linea, const char *area,
                              const char *chi, const char *fmt, ...)
	__attribute__((format(printf, 5, 6)));
#define registro_dettaglio_di(...) \
	registro_dettaglio_di_in(__FILE__, __LINE__, __VA_ARGS__)

/* Millisecondi da un orologio monotono — l'ora che RCP vuole. */
uint64_t registro_ora_ms(void);

#endif
