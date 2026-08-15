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
 *   sara' impostato (fase 5, `fasi/05-la-sessione.md` §1.4) diventera' vero per
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

/* Quante chiamate sono state fatte, e la piu' lenta in millisecondi — il numero
 * che dice se la scelta «sincrona» regge.  ⛔ Sta qui e non in un commento:
 * `CODER.md` §6 vuole che un ripiego si possa MISURARE, non credere. */
void sentinella_conti(const sentinella *s, uint64_t *chiamate,
                      uint64_t *peggior_ms);

#endif
