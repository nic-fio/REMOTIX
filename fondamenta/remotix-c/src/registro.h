/*
 * registro — messaggi diagnostici con livelli.
 *
 * Il livello `traccia` annota ogni evento di input, tasto per tasto: e' a
 * tutti gli effetti un registratore di battitura, password comprese.  Sta a
 * `traccia` e non a `diagnostica` apposta, ed e' il motivo per cui i due
 * livelli sono distinti (§5.8 di SPECIFICA.md).
 */
#pragma once

#include <glib.h>

typedef enum
{
	REGISTRO_ERRORE = 0,
	REGISTRO_AVVISO,
	REGISTRO_INFORMAZIONE,
	REGISTRO_DIAGNOSTICA,
	REGISTRO_TRACCIA,
} LivelloRegistro;

/* Installa il gestore dei messaggi.  Va chiamata una volta sola, all'avvio. */
void registro_avvia(LivelloRegistro livello);

/* Converte un nome («informazione», «diagnostica», …) nel livello
 * corrispondente.  Restituisce FALSE se il nome non e' riconosciuto. */
gboolean registro_livello_da_nome(const char *nome, LivelloRegistro *fuori);

/* L'elenco dei nomi accettati, per i messaggi d'aiuto. */
const char *registro_nomi_livelli(void);

LivelloRegistro registro_livello(void);

void registro_scrivi(LivelloRegistro livello, const char *formato, ...) G_GNUC_PRINTF(2, 3);

#define errore(...)       registro_scrivi(REGISTRO_ERRORE, __VA_ARGS__)
#define avviso(...)       registro_scrivi(REGISTRO_AVVISO, __VA_ARGS__)
#define informazione(...) registro_scrivi(REGISTRO_INFORMAZIONE, __VA_ARGS__)
#define diagnostica(...)  registro_scrivi(REGISTRO_DIAGNOSTICA, __VA_ARGS__)
#define traccia(...)      registro_scrivi(REGISTRO_TRACCIA, __VA_ARGS__)

/*
 * Manda nel nostro registro anche quel che dice libavcodec.
 *
 * Non e' un di piu': quelle librerie spiegano i propri rifiuti a voce — «DRM
 * PRIME mapping not supported», «no usable entrypoint» — e senza questo aggancio
 * al chiamante arriva soltanto un numero negativo.  Il 6 agosto un `-22` ha
 * fatto perdere due giri di prove, e la spiegazione era li' dentro.
 */
void registro_aggancia_libav(void);
