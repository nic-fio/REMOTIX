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

void registro_dice(const char *area, const char *fmt, ...)
	__attribute__((format(printf, 2, 3)));

/* Le righe di dettaglio del trasporto: molte, e utili solo quando si sta
 * cercando qualcosa.  Spente di serie. */
void registro_parlantina(bool acceso);
bool registro_parla_molto(void);
void registro_dettaglio(const char *area, const char *fmt, ...)
	__attribute__((format(printf, 2, 3)));

/* Millisecondi da un orologio monotono — l'ora che RCP vuole. */
uint64_t registro_ora_ms(void);

#endif
