/*
 * uscita — chi si accorge che la sessione se ne sta andando, e lo sa SUBITO.
 *
 * # Il difetto che questo modulo toglie
 *
 * Senza, REMOTIX viene a sapere di un «Esci» per ultimo: se ne accorge quando
 * muore il flusso di cattura, cioe' quando GNOME ha FINITO di smontare la
 * sessione.  Misurato dal telefono: fra il tocco su «Log Out» e quel momento
 * passano **5,1 secondi**, e in tutti e cinque il client resta fermo
 * sull'ultimo fotogramma — che, non avendo piu' finestre aperte, e' uno sfondo
 * pulito, cioe' **visivamente identico a un desktop vivo**.
 *
 * Da qui il difetto segnalato dall'utente il 3 agosto: «la connessione sembra
 * restare viva».  Non era un'impressione: era esattamente cio' che il client
 * aveva motivo di credere, perche' nessuno gli aveva detto il contrario e
 * l'immagine diceva il contrario.
 *
 * # Come si sa in tempo
 *
 * Registrandosi con `gnome-session` come fa una qualunque applicazione
 * (`RegisterClient`).  Da quel momento il gestore di sessione manda **a noi**,
 * di persona, i segnali dell'uscita.  Misurato nella VM:
 *
 *   | logout richiesto  |                                                  |
 *   | QueryEndSession   | +9 ms  — la DOMANDA: qualcuno si oppone?         |
 *   | EndSession        | +16 ms — la DECISIONE: si esce                   |
 *   | Stop              | +20 ms                                           |
 *   | morte della cattura | +324 ms  (qui ce ne accorgevamo prima)         |
 *
 * ⛔ CI SI AGGANCIA A `EndSession`, NON A `QueryEndSession`.  La seconda e' una
 *    domanda a cui un inibitore puo' ancora rispondere di no — un programma con
 *    modifiche non salvate ne ha il diritto — e in quel caso GNOME annulla
 *    l'uscita.  Chi si aggancia alla domanda butta fuori l'utente per un logout
 *    che poi non avviene.
 *
 * ⛔ LA REGOLA DELL'OSTAGGIO: si risponde SEMPRE, e si risponde PER PRIMO, da un
 *    percorso che non puo' fermarsi ad aspettare nient'altro.  Un client
 *    registrato che non riscontra i segnali **blocca l'uscita dell'utente**:
 *    `gnome-session` aspetta lui, la sessione resta in piedi, e sullo schermo
 *    non c'e' niente che lo spieghi.  Non e' un timore: e' successo in prova,
 *    con una spia che rispondeva alla domanda ma non alla decisione, e la
 *    sessione e' rimasta in ostaggio finche' quella spia non e' scaduta, mezzo
 *    minuto dopo.
 *
 * # Se gnome-session non ci vuole
 *
 * Si prosegue senza, dichiarandolo nel registro, e si resta col comportamento
 * di prima: dell'uscita ci si accorge alla morte della cattura, cinque secondi
 * dopo.  E' peggio, ma e' cio' che c'era, e non e' un motivo per non servire
 * nessuno.
 */
#pragma once

#include <glib.h>

#include "compositore.h"

typedef struct Uscita Uscita;

/*
 * Chiamata quando la sessione ha deciso di uscire.
 *
 * Gira sul thread di questo modulo, DOPO che il riscontro e' partito.  Chi la
 * scrive non deve fare nulla che possa attendere: e' il percorso che deve
 * essere veloce, ed e' tutto il motivo per cui il modulo esiste.
 */
typedef void (*UscitaAnnuncio)(gpointer dati);

Uscita *uscita_avvia(UscitaAnnuncio su_uscita, gpointer dati, TipoCompositore tipo);
void uscita_ferma(Uscita *uscita);
