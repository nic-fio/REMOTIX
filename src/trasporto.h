/*
 * trasporto.h — L'ASCOLTATORE UDP: QUIC, e le connessioni che ci vivono sopra.
 *
 * ---------------------------------------------------------------------------
 * ⛔ IL PRIMO DEI DUE ASCOLTATORI (`RCP.md` §2.4)
 *
 * «7447, e sono DUE ascoltatori con lo stesso numero: UDP per HTTP/3 e
 * WebTransport, TCP per il primo caricamento della pagina.»  Questo file e'
 * l'UDP; `pagina.h` e' il TCP.
 *
 * ⚠ E le due cose sono INDIPENDENTI — misura S1, `RCP.md` §2.4: WebTransport
 *   non usa `Alt-Svc` affatto, apre la sua connessione da se'.  ⛔ Il ripiego
 *   silenzioso su TCP che il piano dichiarava come pericolo NON PUO' accadere,
 *   perche' non c'e' nessun ripiego da fare.  Chi legge `PIANO.md` fase 1
 *   trovera' ancora scritto «e l'annuncio `Alt-Svc` che li lega»: quella riga e'
 *   anteriore alla misura, e `RCP.md` §2.4 la corregge con un ⛔.
 *
 * ---------------------------------------------------------------------------
 * ⛔ I PARAMETRI DI TRASPORTO CHE SONO NORMATIVI, E DOVE STANNO
 *
 * `RCP.md` §2.2 e §2.3 impongono al SERVER — non al client, che e' un browser e
 * i suoi parametri li sceglie lui:
 *
 *   max_idle_timeout          30 s, imposto dal server (§2.2)
 *   datagram                  abilitati (§2.2) — e senza il parametro di
 *                             trasporto, annunciare SETTINGS_H3_DATAGRAM=1 e'
 *                             un errore di protocollo
 *   almeno 16 stream uni      DISPONIBILI IN OGNI MOMENTO al client (§2.3): il
 *                             loro esempio ne concede 3, e con quel credito il
 *                             client non aprirebbe nemmeno lo stream di input —
 *                             il sintomo sarebbe «il desktop non risponde».
 *                             ⛔ Se ne concedono **19**: i tre unidirezionali di
 *                             HTTP/3 (controllo + i due di QPACK) sono aperti
 *                             dal primo secondo e non si chiudono mai, quindi
 *                             16 come TOTALE erano 13 come disponibilita'
 *                             (rilievo B-12)
 *   niente 0-RTT              (§2.3) — sta in `tls.c`, dove si spegne
 *   migrazione non disabilitata (§2.3) — non si tocca `disable_active_migration`
 */
#ifndef REMOTIX_TRASPORTO_H
#define REMOTIX_TRASPORTO_H

#include <openssl/ssl.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

typedef struct trasporto trasporto;

/* Apre il socket UDP e prepara la pila.  `porta` e' la stessa del TCP. */
trasporto *trasporto_apri(const char *indirizzo, const char *porta, SSL_CTX *ctx);
void trasporto_chiudi(trasporto *t);

int trasporto_fd(const trasporto *t);

/* ⛔ Dopo una rotazione del certificato di sessione il contesto TLS cambia: le
 * connessioni gia' aperte tengono il loro, le nuove prendono questo.  Chi non
 * lo rifa' serve per quattordici giorni un certificato di cui la pagina non
 * pubblica piu' l'impronta. */
void trasporto_contesto(trasporto *t, SSL_CTX *ctx);

/* Il socket e' leggibile: si legge tutto quel che c'e'. */
void trasporto_leggi(trasporto *t);

/* Si scrive quel che c'e' da scrivere su tutte le connessioni. */
void trasporto_scrivi(trasporto *t);

/* Millisecondi da adesso al primo timer che scade, o -1 se non ce n'e'.
 * ⛔ Non e' «zero se non ce n'e'»: zero significa «adesso», e confondere i due
 *    fa girare il ciclo a vuoto bruciando una CPU. */
int trasporto_attesa_ms(const trasporto *t);

/* Fa scadere i timer maturi (di QUIC e nostri) e riscrive. */
void trasporto_scaduti(trasporto *t);

/* Quante connessioni sono vive.  Per il registro. */
size_t trasporto_quante(const trasporto *t);

/* ⛔ §8.1 — «mai con un silenzio»: manda `CONGEDO` col motivo a tutte le
 * sessioni vive e chiude ciascuna col codice del motivo (§3.1 punto 3).  La
 * chiama chi spegne il server, con `RCP_SERVER_IN_CHIUSURA` (§8.2, `0x0C`).
 *
 * ⭐ Restituisce quante connessioni hanno ancora byte da far uscire: chi spegne
 *    fa girare il ciclo finche' non e' zero (o finche' non scade la sua
 *    pazienza), perche' «consegnato a ngtcp2» non e' «uscito sul filo». */
const char *trasporto_perche_restano(const trasporto *t);
size_t trasporto_congeda_tutte(trasporto *t, uint8_t motivo, const char *perche);

#endif
