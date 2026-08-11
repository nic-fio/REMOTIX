/*
 * pagina.h — L'ASCOLTATORE TCP: il secondo mestiere del server.
 *
 * ---------------------------------------------------------------------------
 * ⛔ IL SECONDO DEI DUE ASCOLTATORI, CON LO STESSO NUMERO DI PORTA
 *
 * `RCP.md` §2.4: «7447, e sono DUE ascoltatori con lo stesso numero: UDP per
 * HTTP/3 e WebTransport, TCP per il primo caricamento della pagina».  ⚠ «Il TCP
 * serve solo a consegnare la pagina, e le basta HTTP/1.1.  Da li' in poi il
 * browser apre la sessione WebTransport per conto suo, sull'UDP.»
 *
 * ---------------------------------------------------------------------------
 * ⛔ E COME LA PAGINA VIENE SERVITA E' UN VINCOLO DI PRODOTTO
 *
 * `SPECIFICHE.md` §11.5: va consegnata **isolata fra origini** — le due
 * intestazioni che il browser pretende per dare alla pagina i cronometri a
 * piena risoluzione e la memoria condivisa.  ⚠ «Non e' una taratura del banco:
 * cambia come il server serve OGNI risorsa della pagina, e deciderlo dopo
 * significa riscrivere il modo in cui la pagina e' confezionata.»
 *
 * Le intestazioni, e la terza che le due implicano:
 *
 *   Cross-Origin-Opener-Policy: same-origin
 *   Cross-Origin-Embedder-Policy: require-corp
 *   Cross-Origin-Resource-Policy: same-origin   ← su OGNI risorsa
 *
 * ⛔ La terza non e' un di piu': con `require-corp` il browser rifiuta ogni
 *    sotto-risorsa che non la dichiari, e il sintomo non nomina l'isolamento —
 *    la risorsa semplicemente non si carica.  E' precisamente il «cambia come
 *    il server serve ogni risorsa» che §11.5 dichiara.
 *
 * ---------------------------------------------------------------------------
 * ⛔ E DUE COSE CHE LA PAGINA PORTA, E NESSUN'ALTRA STRADA PUO' PORTARE
 *
 *   1. **l'impronta del certificato di SESSIONE**, scritta dentro la pagina
 *      (`RCP.md` §4.1-bis, `serverCertificateHashes`): e' il nostro modello di
 *      fiducia, ed e' il server stesso a servire la pagina proprio per poterci
 *      scrivere l'impronta corrente;
 *
 *   2. **l'endpoint da cui la pagina ritira l'impronta aggiornata** (`/impronta`).
 *      ⛔ «Una scheda lasciata aperta due settimane tiene l'impronta di un
 *      certificato che nel frattempo e' stato ruotato: alla riconnessione il
 *      browser rifiuta, e il sintomo e' *non si collega piu' e non dice
 *      perche'*.»  ⛔ E NON passa da RCP: la sessione non e' ancora aperta,
 *      quindi non c'e' un canale su cui chiedere.
 *
 * ---------------------------------------------------------------------------
 * ⛔ E CHI E' BANNATO VEDE LA PAGINA LO STESSO
 *
 * `SPECIFICHE.md` §4.2: «la pagina si carica lo stesso e dice che i tentativi
 * sono esauriti.  ⛔ Mai un silenzio: chi e' bannato per errore e' quasi sempre
 * il proprietario».
 */
#ifndef REMOTIX_PAGINA_H
#define REMOTIX_PAGINA_H

#include "certificati.h"

#include <openssl/ssl.h>
#include <poll.h>
#include <stdbool.h>
#include <stddef.h>

typedef struct pagina pagina;

pagina *pagina_apri(const char *indirizzo, const char *porta, SSL_CTX *ctx,
                    const char *file_html, const certificati *cert);
void pagina_chiudi(pagina *p);

void pagina_contesto(pagina *p, SSL_CTX *ctx);

/* I descrittori da sorvegliare.  Ne restituisce quanti ne ha messi. */
size_t pagina_descrittori(pagina *p, struct pollfd *dove, size_t cap);
/* Da chiamare dopo la `poll`, con lo stesso vettore. */
void pagina_muovi(pagina *p, struct pollfd *dove, size_t quanti);

#endif
