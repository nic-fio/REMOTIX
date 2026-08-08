/*
 * suono — il suono della sessione: il sink virtuale e la cattura del monitor.
 *
 * # ⛔ NELLA SESSIONE NON C'E' NIENTE DA CATTURARE, e va creato
 *
 * Misurato il 5 agosto 2026 (§7.5 di REFERENCE.md): nella sessione senza
 * monitor, con `pipewire`, `pipewire-pulse` e `wireplumber` tutti attivi,
 * `wpctl status` mostra ZERO device, ZERO sink, ZERO source.  La macchina non ha
 * una scheda sonora, ed e' il caso normale per un server (§6.2 di SPECIFICA.md).
 *
 * Il riferimento qui non aiuta e va detto: `gnome-remote-desktop` apre una
 * cattura sul monitor di ogni nodo con `media.class = Audio/Sink` che trova nel
 * registro PipeWire, e un sink non lo crea mai.  Con il suo codice, su questa
 * macchina, non arriverebbe un campione — e senza un errore da nessuna parte.
 *
 * Quindi il sink lo si crea: un nodo `support.null-audio-sink`, che diventa il
 * predefinito perche' e' l'unico, e di cui si cattura il MONITOR — cioe' il
 * mixaggio di quel che suonano tutte le applicazioni.
 *
 * # Il sink e' della SESSIONE, la cattura e' della CONNESSIONE
 *
 * E' la stessa divisione del palco, per la stessa ragione.  Il dispositivo audio
 * su cui le applicazioni suonano non puo' comparire e sparire a ogni
 * riconnessione: chi sta ascoltando qualcosa si ritroverebbe il suono
 * interrotto, e le applicazioni gia' aperte non tornerebbero da sole sul
 * dispositivo nuovo.  La cattura invece serve solo mentre qualcuno ascolta, e la
 * sua frequenza dipende dal formato che il CLIENT ha negoziato: e' roba della
 * connessione.
 *
 * Da cui: `suono_apri` monta il sink e lo tiene, `suono_ascolto_avvia` e
 * `suono_ascolto_ferma` accendono e spengono la cattura quante volte serve.
 */
#pragma once

#include <glib.h>
#include <stdint.h>

typedef struct Suono Suono;

/*
 * I campioni catturati, interlacciati, a 16 bit con segno.
 *
 * ⛔ GIRA SUL THREAD DI PIPEWIRE, e in tempo reale: qui si copia e si torna.
 *    Chi ci scrive dentro una chiamata che aspetta — un lucchetto contesissimo,
 *    una scrittura su socket — non ferma soltanto l'audio: fa saltare il quanto
 *    a tutto il grafo PipeWire, cattura del desktop compresa.
 */
typedef void (*SuonoCampioni)(const int16_t *campioni, uint32_t fotogrammi, gpointer dati);

/* Monta il sink virtuale nella sessione.  Il nodo muore con questo oggetto. */
Suono *suono_apri(GError **sbaglio);
void suono_chiudi(Suono *suono);

/*
 * Accende la cattura del monitor, nel formato che il client ha negoziato.
 *
 * La frequenza e i canali sono quelli scelti sul canale audio: si cattura
 * direttamente in quel formato e PipeWire ricampiona per conto suo, cosi' fra
 * il monitor e il filo non resta nessuna conversione da fare — ed e' anche il
 * modo di non dipendere da quali ricampionatori sia stata compilata FreeRDP.
 */
gboolean suono_ascolto_avvia(Suono *suono, uint32_t frequenza, uint32_t canali,
                             SuonoCampioni su_campioni, gpointer dati, GError **sbaglio);

/*
 * Spegne la cattura, e ASPETTA che il thread di PipeWire abbia finito.
 *
 * Deve aspettare: `su_campioni` porta il puntatore della connessione, e chi
 * torna da qui e' autorizzato a liberarla.  Lasciare un fotogramma a meta'
 * strada significherebbe un segfault dentro un thread che non ha il nostro nome.
 */
void suono_ascolto_ferma(Suono *suono);

/* Il nodo del sink, per il registro e per la diagnosi. */
uint32_t suono_nodo(const Suono *suono);

/*
 * Il volume del sink al massimo, e non zittito.
 *
 * Si chiama alla creazione e A OGNI COLLEGAMENTO, ed e' una decisione
 * dell'utente dell'8 agosto 2026: il livello lo porta il server dentro i
 * campioni, quindi un cursore lasciato in basso e' uno stato che il client non
 * puo' vedere ne' spiegare.  La regola che ne esce e' semplice da ricordare —
 * **ci si collega e il volume e' al massimo** — e se lo si abbassa, resta
 * abbassato finche' si resta collegati.
 */
void suono_volume_massimo(Suono *suono);
