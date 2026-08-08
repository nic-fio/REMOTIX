/*
 * tastiera — le conversioni esatte, e il conto di cio' che e' premuto.
 *
 * ⛔ SI TIENE IL CONTO DEI TASTI PREMUTI, e si scartano la pressione ripetuta e
 *    il rilascio non appaiato: il compositore rifiuta entrambi con
 *    «Invalid key event», e i client mandano regolarmente l'uno e l'altra — il
 *    rilascio quando riprendono il fuoco, la pressione ripetuta finche' il
 *    tasto resta giu'.  La ripetizione la genera il compositore per conto suo.
 *
 * ⛔ A FINE CONNESSIONE SI RILASCIA TUTTO, anche se non c'e' piu' una sessione
 *    a cui parlare.  Trattando il rilascio come un evento qualsiasi lo si
 *    butterebbe, e alla connessione successiva il primo colpo su un tasto che
 *    risulta ancora premuto verrebbe ingoiato: l'utente scrive e la prima
 *    lettera non compare.  [M, 2 agosto]
 *
 * IL PERCORSO UNICODE NON E' UN RIPIEGO: su Android e' la strada principale,
 * perche' una tastiera software non manda posizioni fisiche ma testo (§6.1 di
 * REFERENCE.md).  Tradurlo richiede di sapere QUALE tasto fisico produce quel
 * simbolo nella disposizione della sessione — ed e' precisamente cio' che
 * libei consegna e i metodi `Notify*` non davano.
 */
#pragma once

#include <glib.h>
#include <stdint.h>

typedef struct Tastiera Tastiera;

Tastiera *tastiera_nuova(void);
void tastiera_libera(Tastiera *tastiera);

/* La disposizione della sessione, come arriva da `ei_device_keyboard_get_keymap`.
 * Senza, il percorso Unicode non puo' funzionare. */
gboolean tastiera_keymap(Tastiera *tastiera, const char *xkb, gsize lunghezza);
gboolean tastiera_ha_keymap(const Tastiera *tastiera);

/* Il gruppo XKB attivo, letto da `EI_EVENT_KEYBOARD_MODIFIERS`. */
void tastiera_gruppo(Tastiera *tastiera, uint32_t gruppo);

/*
 * scancode RDP → codice evdev, con la catena esatta di §6.1 di REFERENCE.md.
 * Le posizioni fisiche restano posizioni fisiche: il simbolo lo decide la
 * disposizione configurata dentro la sessione.
 */
gboolean tastiera_evdev(uint16_t flags, uint8_t scancode, uint32_t *evdev);

/*
 * Il tasto Pausa arriva come sequenza di quattro eventi
 * — Ctrl↓(E1) → BlocNum↓ → Ctrl↑(E1) → BlocNum↑ — e serve una macchina a
 * quattro stati per riconoscerla.  Il flag E1 serve solo a disambiguare: la
 * sequenza e' riconoscibile anche senza.
 */
typedef enum
{
	PAUSA_ESTRANEO, /* non fa parte della sequenza: si tratti normalmente */
	PAUSA_INGOIA,   /* fa parte della sequenza, e non va inoltrato */
	PAUSA_EMETTI,   /* la sequenza si e' chiusa: si emette Pausa */
} EsitoPausa;

EsitoPausa tastiera_pausa(Tastiera *tastiera, uint16_t flags, uint8_t scancode,
                          gboolean premuto);

/* Registra pressione o rilascio.  FALSE significa **scartare l'evento**. */
gboolean tastiera_registra(Tastiera *tastiera, uint32_t evdev, gboolean premuto);

/*
 * Un carattere Unicode → il tasto fisico che lo produce nella disposizione
 * della sessione, più i modificatori da tenere premuti mentre lo si preme
 * (Maiusc per il livello 1, AltGr per il 2, entrambi per il 3).
 *
 * `modificatori` deve avere spazio per TASTIERA_MODIFICATORI_MAX voci.
 */
#define TASTIERA_MODIFICATORI_MAX 2

gboolean tastiera_unicode_premi(Tastiera *tastiera, uint32_t codepoint, uint32_t *evdev,
                                uint32_t *modificatori, guint *n_modificatori);

/* Il rilascio dello stesso carattere: restituisce cio' che era stato premuto. */
gboolean tastiera_unicode_rilascia(Tastiera *tastiera, uint32_t codepoint, uint32_t *evdev,
                                   uint32_t *modificatori, guint *n_modificatori);

/*
 * Che cosa è rimasto premuto, e azzera le tabelle.
 * Restituisce un array di `uint32_t` (codici evdev) che il chiamante libera.
 */
GArray *tastiera_svuota(Tastiera *tastiera);

/*
 * Legge lo stato reale dei due tasti a scatto dalla maschera che libei
 * consegna in `EI_EVENT_KEYBOARD_MODIFIERS`.
 *
 * Serve alla riconciliazione: non esiste un modo di IMPORRE lo stato di un
 * lucchetto, si può solo premere il tasto quando quello che il client dichiara
 * non corrisponde a quello che c'è.  Con i metodi `Notify*` lo stato reale non
 * si leggeva affatto e si partiva dal presupposto «tutti spenti».
 */
gboolean tastiera_lucchetti(const Tastiera *tastiera, uint32_t bloccati, gboolean *maiuscole,
                            gboolean *numeri);

/* Codici evdev che servono anche fuori di qui. */
#define TASTIERA_EVDEV_PAUSA 119
#define TASTIERA_EVDEV_BLOCMAIUSC 58
#define TASTIERA_EVDEV_BLOCNUM 69
