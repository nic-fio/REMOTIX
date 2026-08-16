/*
 * comando.h — ⛔⭐ IL COMANDO DI SBLOCCO DI `RCP.md` §4.4-bis.
 *
 * ---------------------------------------------------------------------------
 * ⛔ PERCHE' UN SOCKET DI CONTROLLO, E NON UN'OPZIONE SULLA RIGA DI COMANDO
 *
 * §4.4-bis vuole «un comando di sblocco sul server», «la via d'uscita di chi si
 * banna dal proprio telefono», che «chiede l'unica chiave che quel caso ammette
 * — l'accesso alla macchina», e che scriva nel registro ogni sblocco
 * distinguendo un ban tolto da un ban mai scattato.  Le forme possibili sono
 * tre e due non reggono:
 *
 *   ⛔ un SECONDO PROCESSO con un'opzione (`remotix --sblocca X`) — **non
 *      funziona**, e il modo in cui non funziona e' silenzioso: il ban vive
 *      nella memoria del processo che serve (`rcp.c`, `static … tentativi[]`),
 *      e un secondo processo puo' solo riscrivere il file.  Il server
 *      continuerebbe a rispondere `TROPPI_TENTATIVI` fino al riavvio, e ⛔ il
 *      primo `salva_ban()` — cioe' il primo ban di chiunque altro —
 *      riscriverebbe il file rimettendoci dentro il ban appena tolto.  ⚠ E chi
 *      ha dato il comando lo ha visto **uscire con zero**;
 *   ⛔ un SEGNALE — non porta un indirizzo, e soprattutto non ha una risposta:
 *      §4.4-bis vuole che «non era bannato» e «l'ho tolto» si distinguano, e un
 *      segnale consegnato dice solo che e' stato consegnato;
 *   ⭐ un SOCKET DI CONTROLLO — porta l'indirizzo, agisce sul processo VIVO
 *      (memoria e file nella stessa riga, per mano di `rcp_sblocca()`), e
 *      **risponde**, quindi le due risposte esistono davvero.  La chiave che
 *      chiede e' un file con permessi `0600` nel filesystem della macchina,
 *      cioe' esattamente «l'accesso alla macchina» — e non aggiunge nessuna
 *      superficie raggiungibile dalla rete: un socket di dominio Unix non ha un
 *      indirizzo IP.
 *
 * ⛔ Fino al 10 agosto 2026 notte questo file non c'era e `main.c` implementava
 *    la PRIMA forma, quella che non funziona: rilievo R12.1 della revisione
 *    delle cuciture, e l'analisi per esteso e' scritta — dalla mano che ha
 *    innestato l'ospite del banco — in `banchi/01-b3-rcp-innesta.py`.
 *
 * ---------------------------------------------------------------------------
 * ⛔ IL PROTOCOLLO E' UNA RIGA, E SI LEGGE SENZA STRUMENTI
 *
 *     SBLOCCA <indirizzo>  →  TOLTO <chiave>        il ban c'era e non c'e' piu'
 *                          →  NON-BANNATO <chiave>  non c'era niente da togliere
 *     PING                 →  PONG                  «il comando esiste?», e non
 *                                                   tocca niente
 *     (altro)              →  NON-CAPITO <riga>
 *
 * ⭐ `PING` non e' un ornamento: e' il denominatore della regola B0.3 di
 *    `FASI.md` §01-filo-nudo.  Un banco che chiama lo sblocco fra una prova e
 *    l'altra deve poter dire «il comando c'era e ha risposto», o «il ban non e'
 *    scattato» e «lo sblocco non e' mai arrivato a nessuno» hanno lo stesso
 *    aspetto.
 *
 * ⭐ E' lo stesso protocollo, byte per byte, che parla `banchi/01-b8-sblocca.py`
 *    — che e' lo strumento di B0.3 e non un pezzo di B8.  Averne due sarebbe
 *    stata la forma E2 di `REVIEWER.md`: due comportamenti sotto la stessa
 *    etichetta.
 *
 * ---------------------------------------------------------------------------
 * ⛔⭐ E `PING` DICE «QUALCUNO RISPONDE», NON «RISPONDE QUELLO GIUSTO»
 *
 * *Constatato l'11 agosto 2026, la prima volta che qualcuno ha puntato
 * `01-b8-sblocca.py` a un server diverso da quello che aveva il ban.*
 *
 * Su questa macchina i server sono **due** — l'innesto `bsslserver` sulla 7447
 * e questo prodotto sulla 7448 — e ciascuno ha il suo socket.  ⛔ Chi sbaglia
 * socket riceve `PONG` e poi `NON-BANNATO`, cioe' le due risposte piu'
 * rassicuranti del protocollo, mentre il ban che voleva togliere e' vivo
 * nell'altro processo.  E' la faccia nuova del terzo esito: **ho parlato con un
 * server, ma non con QUELLO** — e a differenza delle altre tre (socket assente,
 * nessuno in ascolto, permesso negato) questa **risponde**, quindi non si vede.
 *
 * ⛔ NON SI E' AGGIUNTO NESSUN VERBO, e la ragione va scritta perche' e' la
 *    tentazione ovvia.  Un `CHI` → `SONO remotix <pid>` avrebbe messo l'identita'
 *    **dentro il protocollo**, e li' due cose vanno storte insieme:
 *
 *      1. `RCP.md` §4.4-bis e `FASI.md` §01-filo-nudo B0.3 promettono che i due
 *         server parlino lo stesso protocollo **byte per byte**.  Un verbo che
 *         capisce uno solo dei due lo rompe, ed e' la forma E2 di `REVIEWER.md`
 *         proprio nel punto che questo riquadro esiste per non ripetere;
 *      2. ⛔ e chi risponderebbe a `CHI` sarebbe il server: cioe' si chiederebbe
 *         l'identita' **all'indiziato**.  `CODER.md` §3.7 dice l'opposto — *«non
 *         si deduce il mittente: lo si chiede al nucleo»*.
 *
 * ⭐ La strada giusta e' fuori dal protocollo e non costa una riga a questo
 *    file: un socket di dominio Unix porta con se' le credenziali di chi
 *    ascolta, e `getsockopt(SO_PEERCRED)` le consegna a chi si collega — pid,
 *    uid, gid, dal kernel.  Da li' `/proc/<pid>/comm` dice `remotix` oppure
 *    `bsslserver`.  Lo fa `01-b8-sblocca.py`, che stampa sempre chi ha risposto
 *    e sa pretenderlo (`--pretendi-chi`, `--pretendi-pid`).
 *
 * ⚠ E l'altra meta' del ban — il **file** che sopravvive al riavvio — questo
 *   modulo non la sa guardare: `rcp_sblocca()` chiama `salva_ban(NULL, …)`, che
 *   con la sessione a `NULL` tace su ogni guasto, e `percorso_ban` e' `static`
 *   dentro `rcp.c`.  ⛔ Quindi qui non si dichiara mai che il file sia stato
 *   scritto: si dice che e' stato **chiesto**.  Chi misura lo guarda da fuori —
 *   `01-b8-sblocca.py --ban-file`, che lo legge prima e dopo.  ⭐ La cura vera
 *   sarebbe in `rcp.c`: `rcp_sblocca()` deve poter dire se il file l'ha scritto.
 */
#ifndef REMOTIX_COMANDO_H
#define REMOTIX_COMANDO_H

#include <poll.h>
#include <stddef.h>

typedef struct comando comando;

/* Apre il socket.  ⛔ Restituisce NULL su qualunque guasto, e lo SCRIVE: senza
 * il comando di sblocco la protezione di §4.4-bis c'e' ancora — si esce solo
 * con le dodici ore — quindi chi accende il server va avanti, ma la meta'
 * mancante si deve leggere nel registro. */
comando *comando_apri(const char *percorso);
void comando_chiudi(comando *k);

/* Come `pagina_*`: si mette il descrittore nel `poll` e si muove quel che si e'
 * mosso. */
size_t comando_descrittori(comando *k, struct pollfd *dove, size_t cap);
void comando_muovi(comando *k, struct pollfd *dove, size_t quanti);

#endif
