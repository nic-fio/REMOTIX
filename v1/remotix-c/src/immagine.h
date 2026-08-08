/*
 * immagine — la tela allineata che il codificatore comprime.
 *
 * Dalla fase 3 ci finisce dentro il DESKTOP VERO, copiato dal fotogramma di
 * PipeWire; la scena sintetica resta disponibile con `--immagine-di-prova`, e
 * non e' un residuo: e' lo strumento che isola il protocollo dalla cattura.  La
 * lezione di §5.4 di SPECIFICA.md — se qualcosa non si vede, il sospetto deve
 * cadere su UNA cosa sola — vale ogni volta che si tocca la pipeline, non solo
 * alla fase 2.
 *
 * La scena sintetica serve a giudicare a occhio tre cose che il protocollo puo'
 * sbagliare senza dare errori (§8 di REFERENCE.md):
 *
 *   - la GEOMETRIA: una cornice di un pixel sui bordi esatti e quattro angoli
 *     etichettati.  Se l'immagine e' spostata, tagliata o allineata male, la
 *     cornice non torna — ed e' il sintomo di R4, R5 e R6;
 *   - la SCALA: una griglia da 100 px con le coordinate scritte sopra;
 *   - il MOVIMENTO: un orologio al millesimo e una barra che scorre.  Se i
 *     fotogrammi non arrivano, l'orologio si ferma; se arrivano e non si
 *     disegnano, resta nero (ed e' la differenza fra 1-5 e 6-7 di §8.1).
 *
 * Il buffer e' BGRX a 32 bit, lo stesso formato che PipeWire consegna: cosi' il
 * codificatore non e' cambiato quando l'immagine e' diventata vera.
 *
 * Il buffer e' ALLINEATO (R4): larghezza multipla di 16, altezza di 64.  Il
 * bordo in eccesso viene RIEMPITO replicando l'ultima riga e l'ultima colonna,
 * non tagliato — il desktop resta della misura chiesta dal client.
 */
#pragma once

#include <glib.h>
#include <stdint.h>

typedef struct Immagine Immagine;

Immagine *immagine_nuova(uint32_t larghezza, uint32_t altezza);
void immagine_libera(Immagine *immagine);

/* Ridisegna la scena sintetica.  `millisecondi` e' il tempo da mostrare
 * sull'orologio. */
void immagine_disegna(Immagine *immagine, int64_t millisecondi);

/*
 * Copia dentro la tela un fotogramma catturato dal desktop.
 *
 * `passo` e' lo stride del produttore e NON e' `larghezza * 4`: PipeWire
 * allinea le righe come gli conviene, e dedurlo produce immagini oblique.
 *
 * Se il fotogramma e' piu' piccolo della tela — non deve succedere, ma succede
 * se Mutter negozia una misura diversa da quella chiesta — la parte scoperta si
 * riempie di grigio invece di lasciarci l'immagine di prima: una banda grigia
 * si diagnostica, un'immagine vecchia a meta' no.
 */
void immagine_copia_fotogramma(Immagine *immagine, const uint8_t *pixel, uint32_t passo,
                               uint32_t larghezza, uint32_t altezza);

/*
 * L'allineamento di R4, come funzioni pure: larghezza a 16, altezza a 64.
 *
 * Le usa anche il palco, che deve creare le superfici della scheda della stessa
 * misura della tela — e due punti che calcolano la stessa cosa a modo loro sono
 * due punti che un giorno divergono.
 */
uint32_t immagine_allinea_larghezza(uint32_t larghezza);
uint32_t immagine_allinea_altezza(uint32_t altezza);

const uint8_t *immagine_pixel(const Immagine *immagine);
uint32_t immagine_passo(const Immagine *immagine);
uint32_t immagine_larghezza(const Immagine *immagine);
uint32_t immagine_altezza(const Immagine *immagine);
uint32_t immagine_larghezza_allineata(const Immagine *immagine);
uint32_t immagine_altezza_allineata(const Immagine *immagine);
