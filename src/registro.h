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

void registro_dice(const char *area, const char *fmt, ...)
	__attribute__((format(printf, 2, 3)));

/* Le righe di dettaglio del trasporto: molte, e utili solo quando si sta
 * cercando qualcosa.  Spente di serie. */
void registro_parlantina(bool acceso);
bool registro_parla_molto(void);
void registro_dettaglio(const char *area, const char *fmt, ...)
	__attribute__((format(printf, 2, 3)));

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
void registro_dice_di(const char *area, const char *chi, const char *fmt, ...)
	__attribute__((format(printf, 3, 4)));
void registro_dettaglio_di(const char *area, const char *chi, const char *fmt,
                           ...)
	__attribute__((format(printf, 3, 4)));

/* Millisecondi da un orologio monotono — l'ora che RCP vuole. */
uint64_t registro_ora_ms(void);

#endif
