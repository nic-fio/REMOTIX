/*
 * altoparlante — l'audio in uscita verso il client (MS-RDPEA).
 *
 * Sta sul canale DINAMICO `AUDIO_PLAYBACK_DVC` e non sullo statico `rdpsnd`, e
 * la scelta ha due ragioni misurate, non estetiche:
 *
 *   1. e' quello con cui il riferimento ha negoziato PCM sia con mstsc sia con
 *      RDM — le due righe «[RDP.AUDIO_PLAYBACK] Client Formats: [AAC: false,
 *      Opus: false, PCM: true]» di §1.2 e §1.7 di REFERENCE.md vengono da li';
 *   2. non compete con gli altri canali statici (§14.1 di protocollo-rdp.md).
 *
 * # ⛔ PERCHE' C'E' UNA CODA IN MEZZO
 *
 * I campioni arrivano dal thread di PipeWire, in tempo reale, ogni pochi
 * millisecondi.  Spedirli da li' significherebbe chiamare `WTSVirtualChannelWrite`
 * — che alloca e prende lucchetti — dentro un percorso in cui il ritardo lo paga
 * tutto il grafo audio, cattura del desktop compresa.
 *
 * Quindi qui si accoda e basta, e a svuotare e' il ciclo della connessione, lo
 * stesso che spedisce i fotogrammi.  Ne discendono due cose buone:
 *
 *   - `SendSamples` viene chiamata sempre dallo stesso thread, come tutto il
 *     resto del protocollo;
 *   - i byte dell'audio finiscono dentro la finestra della misura di banda
 *     (R19), che e' esattamente dove devono stare: sul filo ci passano davvero.
 *
 * Quando la coda si riempie — il ciclo e' fermo, la rete e' strozzata — si
 * BUTTANO I CAMPIONI PIU' VECCHI, non i piu' nuovi, e lo si dice nel registro.
 * Il suono in ritardo non serve a nessuno, e una coda che cresce all'infinito
 * finirebbe per mangiare la memoria del server per riprodurre un rumore di
 * mezzo minuto fa.
 *
 * # ⛔ E PERCHE' NON SI USA `SendSamples`
 *
 * Perche' passa dal DSP di FreeRDP, e il DSP di FreeRDP RIBALTA IL SEGNO di
 * ogni campione PCM a 16 bit: manda il nostro PCM con segno al codificatore
 * FFmpeg `AV_CODEC_ID_PCM_U16LE`, che e' senza segno.  Il client lo rilegge con
 * segno e sente rumore a fondo scala.  E' costato la questione aperta n.10, ed
 * e' misurato in `REFERENCE.md` R24.
 *
 * Si usa quindi `SendSamples2`, che scrive i byte come sono.  Non e' un
 * aggiramento: la sorgente E' il formato scelto dal client, e non c'e' nulla da
 * convertire.
 *
 * # ⛔ E ALLORA IL RITMO LO DOBBIAMO FARE NOI
 *
 * `SendSamples` accumulava fino a `latency` millisecondi prima di comporre un
 * PDU; `SendSamples2` spedisce quel che gli si da'.  Senza qualcuno che tenga il
 * ritmo, la dimensione dei blocchi diventa quella del CICLO — che si sveglia
 * anche per un tasto o per un riscontro — e il client BUTTA i blocchi corti: la
 * sua tolleranza e' `2 x durata del blocco`.
 *
 * Quindi qui si spedisce **un blocco intero per giro, mai parziale, mai due di
 * fila**, come fa xrdp con `g_bbuf_size`.  Le misure e il perche' stanno accanto
 * a `BLOCCO_MS` nel corpo, e in `REFERENCE.md` R25.
 */
#pragma once

#include <freerdp/freerdp.h>
#include <glib.h>
#include <stdint.h>
#include <winpr/wtsapi.h>

typedef struct Altoparlante Altoparlante;

/*
 * Apre il canale e manda i formati del server.
 *
 * ⛔ R21 — `Initialize` E' `Start`: apre il canale e spedisce subito i formati.
 *    Non c'e' un `Open` da chiamare dopo, e siccome il canale e' dinamico va
 *    aperto solo a `drdynvc` in stato READY, come EGFX e DISP.
 */
Altoparlante *altoparlante_apri(HANDLE vcm, rdpContext *contesto);

/*
 * Chiude il canale e libera tutto.
 *
 * ⛔ PRIMA DI CHIAMARLA VA SPENTA LA CATTURA (`suono_ascolto_ferma`): finche' e'
 *    accesa, il thread di PipeWire accoda campioni qui dentro.
 */
void altoparlante_chiudi(Altoparlante *altoparlante);

/* L'identificativo del canale dinamico, per riconoscerne l'esito di creazione. */
uint32_t altoparlante_canale(const Altoparlante *altoparlante);

/* Il client ha risposto alla creazione del canale: se ha detto di no, si spegne
 * tutto invece di accodare campioni per nessuno. */
void altoparlante_esito_canale(Altoparlante *altoparlante, int esito);

/*
 * Vero quando il client ha scelto un formato, e allora dice quale.
 *
 * E' il momento in cui si sa a che frequenza catturare: prima di qui una
 * cattura non saprebbe che formato chiedere, e `SendSamples` scarterebbe tutto
 * in silenzio (R21).
 */
gboolean altoparlante_formato(Altoparlante *altoparlante, uint32_t *frequenza, uint32_t *canali);

/*
 * I campioni dalla sessione.  Ha la forma di `SuonoCampioni`, e gira sul thread
 * di PipeWire: accoda e torna.
 */
void altoparlante_campioni(const int16_t *campioni, uint32_t fotogrammi, gpointer dati);

/* Un passo dal ciclo della connessione: svuota la coda sul canale. */
void altoparlante_passo(Altoparlante *altoparlante);

/*
 * I tre numeri che raccontano l'audio: fotogrammi spediti, fotogrammi buttati
 * perche' la coda era piena, e BLOCCHI RISCONTRATI dal client.
 *
 * Il terzo e' l'unico che dica qualcosa sull'altro capo: «spediti» conta quel
 * che abbiamo scritto, e un canale che il client ignora produce lo stesso
 * numero di uno che funziona.
 */
void altoparlante_conti(const Altoparlante *altoparlante, guint64 *spediti, guint64 *scartati,
                        guint64 *riscontrati, guint64 *taciuti);
