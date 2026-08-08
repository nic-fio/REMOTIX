/*
 * scambio — gli appunti sul filo: il canale `cliprdr` (MS-RDPECLIP).
 *
 * L'altra meta' — la clipboard della sessione — sta in `appunti.c`.  Qui si
 * parla il protocollo e si traducono i formati; la' si parla a Mutter.
 *
 * # I due versi, e sono simmetrici solo in apparenza
 *
 *   la SESSIONE copia          → `SelectionOwnerChanged` → si annuncia al client
 *                                un `FORMAT_LIST`
 *   il client incolla          → `FORMAT_DATA_REQUEST`   → `SelectionRead`, si
 *                                converte, si risponde
 *
 *   il CLIENT copia            → `FORMAT_LIST`           → `SetSelection` verso
 *                                la sessione
 *   la sessione incolla        → `SelectionTransfer`     → `FORMAT_DATA_REQUEST`
 *                                al client, e quando risponde si consegna
 *
 * Il secondo verso ha una difficolta' che il primo non ha: la richiesta della
 * sessione e la risposta del client arrivano su DUE thread diversi e in due
 * momenti diversi, quindi la richiesta va tenuta da parte con il suo `serial`
 * finche' la risposta non arriva — e se non arriva mai, va risposto lo stesso
 * (l'applicazione che incolla sta aspettando).
 *
 * # ⛔ R22 — il canale ha bisogno del SUO thread
 *
 * `cliprdr_server_context_new` accende `autoInitializationSequence`, ma la
 * sequenza — capacita' piu' `MONITOR_READY` — la esegue una funzione statica
 * chiamata SOLO dal thread di `Start`.  Chi apre il canale e lo pompa dal
 * proprio ciclo si ritrova un canale aperto su cui non succede niente, e il
 * client che aspetta per sempre un `MONITOR_READY` che nessuno manda.
 *
 * # Che cosa si scambia, e che cosa no
 *
 * Testo e immagini, come dice la fase 8 del piano.  I FILE no: sono un progetto
 * a sé, con un filesystem virtuale FUSE (1591 righe nel riferimento), e stanno
 * nell'ultima voce di quella fase, non in questa.
 */
#pragma once

#include <freerdp/freerdp.h>
#include <glib.h>
#include <winpr/wtsapi.h>

#include "palco.h"

typedef struct Scambio Scambio;

/*
 * Apre il canale STATICO `cliprdr` e avvia la sequenza iniziale.
 *
 * Va chiamata solo se il client ha unito il canale — si controlla con
 * `WTSVirtualChannelManagerIsChannelJoined`, come per DRDYNVC — altrimenti
 * `WTSVirtualChannelOpen` fallisce e basta.
 *
 * Si riceve il PALCO e non gli appunti, per la regola di `palco.h`: la sessione
 * puo' finire mentre una connessione sta ancora scambiando, e il puntatore va
 * ripreso ogni volta.  L'unica eccezione — dentro le richiamate della sessione,
 * dove gli appunti sono vivi per costruzione — e' spiegata in `scambio.c`, e
 * c'e' un motivo preciso per cui la' NON si puo' riprendere il puntatore.
 */
Scambio *scambio_apri(HANDLE vcm, rdpContext *contesto, Palco *palco);

/*
 * Chiude il canale e smette di ascoltare la sessione.
 *
 * ⛔ Aspetta il thread del canale: dopo di qui nessuna richiamata puo' piu'
 *    toccare ne' questo oggetto ne' gli appunti della sessione.
 */
void scambio_chiudi(Scambio *scambio);

/* Quanti trasferimenti sono andati nei due versi, per il registro e per il
 * banco: senza questi numeri «gli appunti funzionano» non e' verificabile. */
void scambio_conti(const Scambio *scambio, guint *verso_client, guint *verso_sessione);
