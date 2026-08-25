/*
 * sentinella.h — chi guarda le sessioni grafiche LOCALI, e per conto di chi.
 *
 * ---------------------------------------------------------------------------
 * ⛔ IL MESTIERE, in una riga
 *
 * `SPECIFICHE.md` §5.1 promette quattro comportamenti, e due di essi non hanno
 * mai avuto nessuno che li facesse:
 *
 *   · l'utente ha una sessione grafica LOCALE e ne apre una remota
 *       ⇒ la remota e' RIFIUTATA, motivo `0x05 GIA_ATTIVA_LOCALE`;
 *   · l'utente ha una remota viva e apre una LOCALE
 *       ⇒ ⛔ la LOCALE VINCE: la remota viene chiusa, `0x04 SESSIONE_LOCALE_PREVALSA`.
 *
 * ⛔ I due codici stanno in `rcp.h` dal 9 agosto 2026 e **nessuna riga di
 *    nessun `.c` li spediva**: e' la stessa forma di guasto del rilievo B-7
 *    (`RCP_SERVER_IN_CHIUSURA` definito e senza emittente), dove chi era
 *    collegato aspettava i trenta secondi del silenzio e leggeva «errore di
 *    rete».  Questo file e' l'emittente che mancava.
 *
 * ---------------------------------------------------------------------------
 * ⛔⛔ CHE COS'E' UNA «SESSIONE GRAFICA LOCALE» — e la stesura ovvia e' SBAGLIATA
 *
 * Il criterio che viene in mente e' *«`Type` grafico e `Remote = false`»*.
 * ⛔ Con quello ci rifiuteremmo da soli, e il primo giorno.
 *
 * `[R]` **Noi non chiamiamo `pam_set_item(PAM_RHOST, …)` da nessuna parte** —
 * `autenticazione.c` fa `pam_start` e basta — quindi `pam_systemd` crea le
 * NOSTRE sessioni senza host remoto, e logind le segna `Remote=no`.  Una
 * sessione nostra passerebbe per locale, e il secondo utente che si collega
 * verrebbe respinto con `0x05` da se' stesso.
 *
 * ⭐ **Il discrimine e' il SEAT, non `Remote`.**  Una sessione locale sta su un
 *    seat (`seat0`): ci sono uno schermo, una tastiera e un mouse veri attaccati
 *    a quella macchina.  La nostra headless un seat non ce l'ha — ed e' la
 *    STESSA proprieta' su cui Mutter decide `is_headless()` (`DECISIONI.md`
 *    §4.3-bis).  ⇒ Le due cose stanno in piedi insieme: il giorno in cui la
 *    nostra sessione avesse un seat, perderemmo l'headless **e** ci
 *    rifiuteremmo da soli, e il registro direbbe tutt'e due le cose.
 *
 * ⚠ `Remote` si guarda lo stesso, come seconda cintura: quando `PAM_RHOST`
 *   sara' impostato (fase 5, `FASI.md` §05-la-sessione §1.4) diventera' vero per
 *   le nostre, e allora due criteri indipendenti diranno la stessa cosa.
 *
 * ---------------------------------------------------------------------------
 * ⚠ PERCHE' SINCRONO, e non un thread come in v1
 *
 * v1 (`v1/remotix-c/src/sentinella.c`, 307 righe) teneva un `GMainLoop` in un
 * thread suo, con `SessionNew`/`SessionRemoved`.  ⛔ Li' il server girava DENTRO
 * la sessione di UNA persona e la domanda era «c'e' una locale?»; qui il server
 * e' di sistema e la domanda e' «c'e' una locale **di quest'utente**?», che si
 * pone in due momenti soli:
 *
 *   · quando qualcuno ATTACCA        — una volta per sessione, il costo non si vede;
 *   · mentre qualcuno E' attaccato   — un ripasso ogni paio di secondi.
 *
 * ⇒ Una chiamata sincrona con un'attesa CORTA costa meno di un thread e di un
 *   mutex, e non aggiunge un secondo filo a un programma che ne ha uno solo per
 *   scelta.  ⛔ Ma l'attesa corta e' obbligatoria: questo ciclo `poll` e' lo
 *   stesso che consegna i fotogrammi, e `LEZIONI.md` §6.2-bis dice che
 *   *un'attesa che protegge un anello e' un ritardo per tutti gli altri*.
 */
#ifndef REMOTIX_SENTINELLA_H
#define REMOTIX_SENTINELLA_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

typedef struct sentinella sentinella;

/* Apre il collegamento al bus di SISTEMA (logind non sta su quello di
 * sessione).  ⛔ Restituisce NULL se il bus non c'e': e allora la regola di §5.1
 * NON e' in vigore, e chi chiama lo scrive nel registro invece di proseguire
 * come se niente fosse. */
sentinella *sentinella_apri(void);

void sentinella_chiudi(sentinella *s);

/*
 * «Quest'utente ha una sessione grafica LOCALE, adesso?»
 *
 * `descrizione` — se non NULL — riceve di che sessione si tratta, per il
 * registro del server: id, tipo e seat.  ⛔ Non finisce mai nel corpo di un
 * congedo (§8.2).
 *
 * ⚠ Un errore di logind risponde `false`, e scrive una riga: «non lo so» e «non
 *   c'e'» sono due fatti diversi, e chiudere fuori tutti perche' logind non
 *   risponde punirebbe chi non ha sbagliato niente (invariante I1).
 */
bool sentinella_locale(sentinella *s, const char *utente, char *descrizione,
                       size_t quanto);

/*
 * ⭐⭐⭐ «QUALI DI QUESTI UTENTI HANNO UNA SESSIONE GRAFICA LOCALE?» — UNA
 *       DOMANDA SOLA PER TUTTI, e nasce da un difetto MISURATO.
 *
 * ⛔⛔ IL DIFETTO CHE QUESTA FUNZIONE ESISTE PER TOGLIERE — rilievo P4 di
 *      `fasi/10-multi-tenant-e-il-budget.md` §8.2, misurato in §6.13.
 *
 *      Il ripasso di §5.1 (`wt_sorveglia_locali()`) chiamava `sentinella_locale()`
 *      **una volta per inquilino attaccato**, e ogni chiamata e' un giro
 *      SINCRONO su D-Bus dentro lo stesso `poll` che consegna i fotogrammi.
 *      `[M]` 25 agosto 2026: le chiamate per ripasso sono **1 · 3 · 5 · 7** a
 *      N = 1/3/5/7 — lineari negli inquilini — e a governare il danno e' il
 *      PRODOTTO `P = N × D`, dove D e' quanto ci mette logind.
 *      ⛔ La frontiera si restringe come **1/N** e taglia i **300 ms** che
 *         `ATTESA_MS` qui sotto si concede gia' a ~4 inquilini: a **N=7 con
 *         D=286 ms** ogni desktop crolla a **1,3 fotogrammi/s con un p95 di due
 *         secondi**, ⛔⛔ *e non viene scritta una riga*, perche' non si stacca
 *         nessuno.  Il degrado SILENZIOSO, che per `CODER.md` §1-bis pesa piu'
 *         dei fotogrammi.
 *
 * ⭐⭐ E LA CURA STA NEI NUMERI, non nell'eleganza — `[M]` §6.13:
 *
 *      · `ListSessions` costa **2,4-2,6 ms** e ⛔ **NON cresce col numero di
 *        sessioni di logind** (da 63 a 72 la mediana SCENDE, pendenza −34,6 µs
 *        a sessione).  ⇒ Il costo non e' nella chiamata: e' nel FARLA N VOLTE.
 *      · `ListSessions` restituisce **TUTTE** le sessioni della macchina.
 *        ⇒ Una sola risposta contiene gia' quella di ogni inquilino.
 *
 *      ⇒ Il costo passa da `N × D` a **`D`**, ed e' un cambiamento di forma, non
 *        una mitigazione: non c'e' nessuna cache da far scadere e nessun giro a
 *        turno da tarare — cose che avrebbero aggiunto una seconda verita' sul
 *        «adesso» (`LEZIONI.md` §1.9) per un difetto che si chiude alla radice.
 *
 * ⚠ IL COSTO CHE RESTA, dichiarato: le sessioni con un SEAT vanno aperte una per
 *   una (`GetAll` sulle proprieta') per sapere se sono grafiche.  ⛔ Ma quelle
 *   sono le sessioni **locali della macchina** — su una macchina headless sono
 *   zero, e sono comunque indipendenti dal numero dei nostri inquilini.  ⇒ Il
 *   termine che cresceva con N e' sparito; questo non c'era mai.
 *
 * `utenti`   — i nomi da cercare, `quanti` in tutto.  ⚠ Possono ripetersi: la
 *              risposta e' per POSIZIONE, cosi' chi chiama non deve deduplicare.
 * `locale`   — un vettore di `quanti` booleani, riempito da questa funzione.
 * `quali`    — se non NULL, `quanti` fette da `larghezza` byte l'una, ciascuna
 *              con la descrizione della sessione trovata (per il REGISTRO:
 *              §8.2 vieta di dire al client i fatti delle sessioni altrui).
 *
 * ⛔ Ritorna quanti ne ha trovati con una locale.  ⚠ Se logind non risponde,
 *    ritorna 0 e mette tutto a `false` — «non lo so» si tratta come «non c'e'»,
 *    che e' l'unica scelta che non punisce chi non ha sbagliato niente
 *    (invariante I1), ed e' la stessa che fa `sentinella_locale()`.
 */
size_t sentinella_locali(sentinella *s, const char *const *utenti, size_t quanti,
                         bool *locale, char *quali, size_t larghezza);

/*
 * ⭐ «LO SPEGNIMENTO E' DAVVERO VIETATO?» — `DECISIONI.md` §4.7, la verifica che
 * l'invariante I7 pretende: le tre cinture sono righe di configurazione, e una
 * protezione che vive in un file va **verificata**, non creduta.
 *
 * Chiede a logind `CanPowerOff`/`CanReboot`/`CanSuspend`/`CanHibernate` e
 * pretende **`no`** da tutte e quattro.  ⛔ «challenge» NON basta: mostra la
 * voce nel menu invece di toglierla.
 *
 * ⛔⛔ LA CHIAMA IL FIGLIO, MAI IL SERVER: `[M]` root si sente rispondere «yes»
 *     perche' logind guarda `CAP_SYS_BOOT` prima di polkit.
 */
bool sentinella_spegnimento_vietato(sentinella *s, char *dettaglio, size_t quanto);

/*
 * ⭐ «LA MIA SESSIONE E' SENZA SEAT?» — `DECISIONI.md` §4.3-bis, misura M2.
 *
 * Senza seat Mutter e' **headless**, ed e' l'unica forma in cui il blocca-schermo
 * di GNOME non ci revoca cattura e input.  ⚠ Dal 15 agosto 2026 la sessione
 * nasce senza seat **per costruzione** (`figlio.c`, passo 2-bis) — ⛔ ma
 * «scritto» non e' «in vigore» (`REVIEWER.md` E1), e questa e' la riga che lo
 * verifica DOPO l'avvio.
 *
 * `false` anche quando non c'e' nessuna sessione: e' un caso PEGGIORE, non
 * migliore, e `quale` lo dice.
 */
bool sentinella_senza_seat(sentinella *s, char *quale, size_t quanto);

/* Quante chiamate sono state fatte, e la piu' lenta in millisecondi — il numero
 * che dice se la scelta «sincrona» regge.  ⛔ Sta qui e non in un commento:
 * `CODER.md` §6 vuole che un ripiego si possa MISURARE, non credere.
 *
 * ⛔⛔ E FINO AL 25 AGOSTO 2026 NON LA CHIAMAVA NESSUNO — rilievo di contorno di
 *      §6.13.  Il contatore c'era, l'intestazione dichiarava perche' c'era, e
 *      **nel registro non finiva niente**: la scelta «sincrona» si poteva
 *      credere, non rimisurare.  E' la forma E1 del `REVIEWER.md` — uno
 *      strumento che esiste e non parla e' peggio di uno strumento che manca,
 *      perche' chi legge il codice crede che la misura ci sia.
 *  ⇒ Da oggi la chiama `main.c`, che scrive **una riga al minuto** con questi
 *    due numeri accanto al numero degli inquilini serviti: e' il conto con cui
 *    la cura di §8.2 P4 si potra' **rifiutare** invece che ricordare. */
void sentinella_conti(const sentinella *s, uint64_t *chiamate,
                      uint64_t *peggior_ms);

#endif
