/*
 * superficie — il fotogramma che non passa dalla CPU.
 *
 * Prende il DMA-BUF che Mutter consegna a PipeWire e lo porta al codificatore
 * senza copiarlo: lo importa come superficie della scheda, lo converte in NV12
 * e lo depone dentro una superficie della misura ALLINEATA.  Quel che prima
 * costava due copie in memoria, una conversione di colore e un caricamento —
 * misurati il 6 agosto: 12,5 ms la sola conversione — qui e' un passo solo,
 * sulla scheda.
 *
 * # Perche' esiste come oggetto a se'
 *
 * Perche' e' il **contesto delle superfici** a legare cattura e codificatore:
 * un codificatore di libavcodec accetta soltanto fotogrammi che vengono dal
 * contesto con cui e' stato aperto.  Il convertitore lo crea, il codificatore
 * ci si apre sopra, e cosi' il fotogramma non viene mai copiato fra i due.
 *
 * Il convertitore appartiene quindi al PALCO — vive quanto la cattura, cioe'
 * quanto la sessione — e il codificatore, che appartiene alla connessione, ci
 * si aggancia quando nasce.
 *
 * # Il riempimento del bordo, che e' il motivo per cui qui c'e' un grafo
 *
 * R4 vuole il flusso H.264 largo un multiplo di 16 e alto un multiplo di 64,
 * col bordo in eccesso RIEMPITO e non tagliato.  La conversione della scheda
 * (`scale_vaapi`) sa cambiare formato e misura, ma **non sa deporre
 * un'immagine dentro una piu' grande**: chiedendole la misura allineata
 * allungherebbe l'immagine invece di riempirle attorno.
 *
 * Si compone quindi sopra una superficie gia' allineata e gia' nera, creata
 * una volta sola: `overlay_vaapi` la usa come sfondo e ci deposita sopra il
 * desktop all'angolo (0,0).  Un solo passaggio sulla scheda, e il bordo resta
 * quello che il client non guarda mai.
 */
#pragma once

#include <glib.h>
#include <libavutil/frame.h>
#include <stdint.h>

typedef struct Superficie Superficie;

/*
 * Una regione cambiata, in coordinate del desktop.
 *
 * ⛔ SENZA DI QUESTE IL FOTOGRAMMA NON SI PUO' LEGGERE.  Il DMA-BUF che Mutter
 *    presta non e' un fotogramma intero: e' il buffer di qualche giro fa con
 *    ridipinta dentro la sola parte cambiata.  R29 di REFERENCE.md.
 */
typedef struct
{
	uint32_t x, y, larghezza, altezza;
} SuperficieRegione;

/*
 * Apre il convertitore per una misura data.
 *
 * `larghezza`/`altezza` sono quelle del desktop; le allineate sono quelle del
 * flusso H.264 (R4).  Restituisce NULL — senza errore, con una spiegazione nel
 * registro — se la scheda non c'e' o non sa fare quel che serve: chi chiama
 * deve poter continuare sul percorso in CPU, perche' degradare e' meglio che
 * fallire (§2 di SPECIFICA.md).
 */
Superficie *superficie_nuova(uint32_t larghezza, uint32_t altezza,
                             uint32_t larghezza_allineata, uint32_t altezza_allineata);
void superficie_libera(Superficie *sup);

/*
 * Importa un DMA-BUF e ne restituisce il fotogramma NV12 allineato.
 *
 * Il fotogramma restituito e' un riferimento NUOVO, da liberare con
 * `av_frame_free`: il chiamante puo' tenerlo quanto vuole — ed e' proprio
 * quello che serve a R9, perche' l'ultimo fotogramma va conservato e
 * rispedito.  Il DMA-BUF invece **non viene trattenuto**: finita questa
 * chiamata, chi l'ha consegnato puo' riaccodarlo subito.
 *
 * ⛔ Va chiamata dal thread che ha in mano il fotogramma di PipeWire, e non
 *    dura quanto una codifica: e' una conversione sola, misurata in pochi
 *    millisecondi.  Ma sta comunque su un thread di tempo reale, quindi non ci
 *    si aggiungono attese.
 */
AVFrame *superficie_importa(Superficie *sup, int fd, uint32_t offset, uint32_t passo,
                            uint64_t modificatore, uint32_t larghezza, uint32_t altezza,
                            const SuperficieRegione *danno, guint quante);

/*
 * Il contesto delle superfici in uscita, con cui aprire il codificatore.
 *
 * ⛔ Il codificatore DEVE essere aperto su questo, o rifiutera' i fotogrammi
 *    con «invalid argument» — e sarebbe l'unico sintomo.
 */
AVBufferRef *superficie_contesto(Superficie *sup);

/* La misura allineata con cui il convertitore e' stato aperto: il codificatore
 * dev'essere della stessa, e il chiamante lo verifica invece di ricordarselo. */
void superficie_misura(const Superficie *sup, uint32_t *larghezza_allineata,
                       uint32_t *altezza_allineata);
