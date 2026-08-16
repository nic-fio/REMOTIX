/*
 * cursore.h — LA CUCITURA della forma del cursore: da PipeWire al filo.
 *
 * ⛔ QUESTO FILE E' DEL COORDINATORE (vedi `input.h`, stessa ragione).
 *
 * Il difetto che questo modulo esiste per curare — `STUDI.md` §gnome §1.1 punto 6 e
 * §5.2, ed e' `[R]`: chiediamo a Mutter `cursor-mode=2`, cioe' «dammi il
 * cursore come METADATO invece che nei pixel», ⛔ ma NON chiediamo
 * `SPA_META_Cursor` ⇒ forma, posizione e punto attivo non arrivano affatto, e
 * `CURSORE_FORMA` (`RCP.md` §7.2) e' un canale senza sorgente.
 *
 * ⭐ E il verso e' quello giusto per noi: pixel puliti nell'immagine (cosi' non
 *    se ne vedono due, `SPECIFICHE.md` §7.1) E la forma in banda laterale, che
 *    e' esattamente cio' che serve al puntatore disegnato dal client.
 */
#ifndef REMOTIX_CURSORE_H
#define REMOTIX_CURSORE_H

#include <stdint.h>
#include <stddef.h>

/*
 * Una forma di cursore, come arriva dal metadato di PipeWire e come parte sul
 * filo.  ⛔ I limiti sono di `RCP.md` §5.5 e §7.2, e si fanno rispettare QUI:
 * chi manda un cursore piu' grande di 256 fa cadere la sessione dall'altra
 * parte per `ERRORE_PROTOCOLLO`.
 */
#define CURSORE_MAX_LATO 256

typedef struct {
	uint16_t larghezza;   /* 0 con altezza 0 = cursore NASCOSTO (§5.5)   */
	uint16_t altezza;
	int16_t  attivo_x;    /* il punto che «punta» ⛔ 0 se nascosto         */
	int16_t  attivo_y;
	uint32_t serie;       /* cresce a ogni cambio di forma; per non rimandare
	                       * la stessa immagine mille volte               */
	const uint8_t *immagine;  /* larghezza x altezza x 4, BGRA PREMOLTIPLICATO.
	                           * Vive fino al richiamo successivo: chi la vuole
	                           * tenere la copia.  NULL se nascosto.       */
} CursoreForma;

/*
 * La chiamata che `cattura.c` fa quando il metadato del cursore cambia dentro
 * un buffer PipeWire.  ⛔ `cattura.c` NON conosce il filo: passa di qui.
 * Ritorna 0 se la forma e' stata accettata, -1 se e' malformata (e allora si
 * DICHIARA nel registro, non si manda niente).
 */
typedef int (*CursoreArrivata)(void *chi, const CursoreForma *);

/*
 * ⛔ Perche' esiste un modulo e non una chiamata diretta: fra PipeWire e il
 *    filo c'e' del lavoro che non e' di nessuno dei due — riconoscere che la
 *    forma NON e' cambiata (il metadato arriva a ogni buffer), tagliare a 256,
 *    e distinguere «nascosto» da «non pervenuto».  Senza un posto suo, quel
 *    lavoro finisce meta' in `cattura.c` e meta' in `rcp.c`, che e' la forma
 *    del difetto della fase 3.
 */
typedef struct cursore Cursore;

Cursore *cursore_apri(CursoreArrivata quando_cambia, void *chi);

/*
 * Da chiamare con il metadato grezzo di PipeWire (`struct spa_meta_cursor`).
 * Ritorna 1 se la forma e' CAMBIATA (e allora `quando_cambia` e' gia' stata
 * chiamata), 0 se e' la stessa di prima, -1 se e' malformata.
 */
int cursore_metadato(Cursore *, const void *spa_meta_cursor, size_t dimensione);

void cursore_chiudi(Cursore *);

#endif /* REMOTIX_CURSORE_H */
