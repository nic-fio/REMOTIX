/*
 * tastiera.h — LA CUCITURA fra una LETTERA e le POSIZIONI che la producono.
 *
 * ⛔ QUESTO FILE E' DEL COORDINATORE (vedi `input.h`, stessa ragione).
 *
 * Il problema, in una riga (`SPECIFICHE.md` §7.3): sul filo le lettere
 * viaggiano come lettere, ma un compositore Wayland non accetta lettere —
 * accetta POSIZIONI, e decide lui che lettera sia guardando la disposizione.
 * ⇒ Qualcuno deve fare il giro all'incontrario: «per far uscire la e' con
 *   questa disposizione, quale tasto premo, e con quali modificatori?».
 *
 * ⚠ La macchina da scrivere: il filo porta la LETTERA stampata, `libei` vuole
 *   il MARTELLETTO da battere.  Questo file trova il martelletto.
 */
#ifndef REMOTIX_TASTIERA_H
#define REMOTIX_TASTIERA_H

#include <stdint.h>
#include <stddef.h>

typedef struct tastiera Tastiera;

/*
 * Apre la disposizione della sessione con `xkbcommon`.  `disposizione` e' la
 * stringa negoziata all'attacco (`RCP.md` §4.5, `DECISIONI.md` §5-bis.7): per
 * esempio "it" o "us".  NULL = quella in vigore nella sessione.
 *
 * ⛔ Ritorna NULL e riempie `*errore` se la disposizione non si carica.  ⛔ NON
 *    si ripiega su "us" in silenzio: sarebbe il ripiego silenzioso che
 *    `CODER.md` §4.2 vieta, e il sintomo sarebbe «scrive le lettere sbagliate».
 */
Tastiera *tastiera_apri(const char *disposizione, char **errore);

/*
 * ⛔⛔ E QUESTA E' LA STRADA BUONA — aggiunta il 14 agosto 2026, e non e' un
 *      di piu': e' la correzione di un difetto del contratto, sollevata
 *      dall'anello che lo attuava e accolta.
 *
 * La firma qui sopra poggia su un presupposto che nessuno aveva misurato: che
 * la disposizione che compiliamo NOI sia la stessa con cui il compositore
 * interpretera' i codici che gli mandiamo.  ⛔ E' fragile dalla parte peggiore,
 * perche' **la disposizione della sessione non la scegliamo noi: la sceglie
 * GNOME, e `libei` ce la CONSEGNA** col dispositivo tastiera.
 *
 * Il danno, in concreto — sessione `it`, client che ha negoziato `us`, l'utente
 * scrive `[`:
 *
 *     su `us`   `[` sta sul tasto 26, da solo
 *     su `it`   sul tasto 26 c'e' la `è`, e `[` vuole l'AltGr
 *
 * ⇒ Mandiamo 26 e sullo schermo compare **`è`**.  ⛔ Non un carattere mancante:
 *   **un carattere DIVERSO** — esattamente cio' che `RCP.md` §7.3 vieta.  E
 *   nessuno collegherebbe mai il sintomo alla disposizione.
 *
 * ⚠ E rende falsa una riga che credevamo vera: `DECISIONI.md` §5-bis.7 dice che
 *   la degradazione e' morbida — «una disposizione vecchia non produce mai
 *   caratteri sbagliati».  ⛔ E' vero SOLO usando la keymap della sessione.
 *
 * ⭐ E v1 lo faceva gia' cosi' (`v1/remotix-c/src/tastiera.c:69`): e' l'unico
 *    pezzo di v1 che il primo contratto di V2 non aveva ripreso.
 *
 * `testo`/`lunghezza` sono la keymap che `libei` porta col dispositivo tastiera
 * (`ei_device_keyboard_get_keymap`, `XKB_KEYMAP_FORMAT_TEXT_V1`).
 * `negoziata` e' il nome dichiarato dal client in `ATTACCA` (`RCP.md` §4.5), o
 * NULL.  ⛔ Se non combacia con quella della sessione si usa **quella della
 * sessione** — e' la verita', e con l'altra uscirebbero lettere sbagliate — e
 * il ripiego si DICHIARA nel registro (`CODER.md` §4.2).
 *
 * ⛔ Da chiamare a OGNI `DEVICE_ADDED`, non una volta all'avvio: `STUDI.md` §gnome §9
 *    misura che un cambio di keymap distrugge e ricrea il dispositivo tastiera,
 *    e il vecchio smette di funzionare **senza errore**.
 */
Tastiera *tastiera_apri_da_keymap(const char *testo, size_t lunghezza,
                                  const char *negoziata, char **errore);

/* Quante posizioni al massimo servono per una lettera (con i modificatori). */
#define TASTIERA_MAX_POSIZIONI 4

/*
 * ⛔ La domanda a cui questo modulo esiste per rispondere.
 *
 * Cerca, in tutta la disposizione, un tasto che con qualche combinazione di
 * modificatori produca `carattere`.
 *
 *   ritorna  1  producibile: `codici[0..n)` sono i codici EVDEV da premere in
 *               ordine (i modificatori prima, il tasto per ultimo) e si
 *               rilasciano all'incontrario; `*n` e' quanti sono;
 *   ritorna  0  ⛔ NON producibile con questa disposizione — e' il caso che
 *               `RCP.md` §7.3 obbliga a scrivere nel registro senza mandare
 *               niente.  Il banco della fase lo esercita di proposito, con una
 *               sessione dalla disposizione sbagliata;
 *   ritorna -1  errore.
 *
 * ⚠ Maiusc e AltGr NON sono comandi: servono a FARE la lettera, e stanno qui
 *   dentro (`SPECIFICHE.md` §7.3).  Ctrl, Alt e Super non passano mai da qui:
 *   quelli viaggiano gia' come posizione sul filo.
 */
int tastiera_posizioni_per(Tastiera *, uint32_t carattere,
                           uint16_t codici[TASTIERA_MAX_POSIZIONI], size_t *n);

/*
 * Il nome della disposizione effettivamente in vigore, per il registro e per
 * la risposta al client.  Mai NULL dopo un'apertura riuscita.
 */
const char *tastiera_disposizione(Tastiera *);

void tastiera_chiudi(Tastiera *);

#endif /* REMOTIX_TASTIERA_H */
