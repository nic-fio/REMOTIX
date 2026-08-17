/*
 * suono — il suono della sessione: il sink virtuale e la cattura del monitor.
 *
 * ---------------------------------------------------------------------------
 * ⛔ NELLA SESSIONE NON C'E' NIENTE DA CATTURARE, e va creato
 *
 * `[M]` 5 agosto 2026 (v1, `REFERENCE.md` §7.5): nella sessione senza monitor,
 * con `pipewire`, `pipewire-pulse` e `wireplumber` tutti e tre attivi,
 * `wpctl status` mostra ZERO device, ZERO sink, ZERO source.  La macchina non ha
 * una scheda sonora, ed e' il caso NORMALE per un server (`SPECIFICHE.md` §11).
 *
 * Il riferimento qui non aiuta, e va detto: `gnome-remote-desktop` apre una
 * cattura sul monitor di ogni nodo con `media.class = Audio/Sink` che trova nel
 * registro di PipeWire, e un sink non lo crea mai.  ⛔ Con il suo codice, su
 * questa macchina, non arriverebbe un campione — e senza un errore da nessuna
 * parte, che e' la forma di guasto che `LEZIONI.md` §2.2 chiama per nome.
 *
 * ⇒ Il sink lo si crea: un nodo `support.null-audio-sink`, che diventa il
 *   predefinito perche' e' l'unico, e di cui si cattura il **monitor** — cioe'
 *   il mixaggio di quel che suonano tutte le applicazioni della sessione.
 *
 * ---------------------------------------------------------------------------
 * ⛔ IL SINK E' DELLA SESSIONE, LA CATTURA E' DELLA CONNESSIONE
 *
 * E' la stessa divisione del palco (invariante I4, `CODER.md` §2), e per la
 * stessa ragione.  Il dispositivo su cui le applicazioni suonano non puo'
 * comparire e sparire a ogni riconnessione: chi sta ascoltando qualcosa si
 * ritroverebbe il suono interrotto, e le applicazioni gia' aperte non
 * tornerebbero da sole sul dispositivo nuovo — PipeWire le lascia attaccate al
 * nodo che hanno scelto quando sono partite.  La cattura invece serve soltanto
 * mentre qualcuno ascolta: e' roba della connessione, e si accende e si spegne
 * quante volte serve.
 *
 * ⇒ `suono_apri()` monta il sink e lo TIENE per tutta la sessione;
 *   `suono_ascolto_avvia()` / `suono_ascolto_ferma()` sono della connessione.
 *
 * ---------------------------------------------------------------------------
 * ⛔ IL FORMATO E' FISSO, E NON E' UN'OPINIONE DI QUESTO FILE
 *
 * `RCP.md` §5.3: 48 000 Hz, 2 canali interlacciati, `s16`.  I due numeri stanno
 * in `audio.h` (`AUDIO_FREQUENZA`, `AUDIO_CANALI`) e da li' si prendono: chi li
 * riscrivesse qui creerebbe una seconda verita' sul formato, e il giorno in cui
 * le due divergessero il sintomo non sarebbe un errore — sarebbe **rumore a
 * fondo scala**, il difetto di v1 (`LEZIONI.md` §2.2).
 *
 * ⚠ In v1 la frequenza arrivava dal formato negoziato con il client RDP e
 *   questo modulo la riceveva come parametro.  In V2 non si negozia niente:
 *   `suono_ascolto_avvia()` non ha piu' ne' frequenza ne' canali.
 *
 * ---------------------------------------------------------------------------
 * ⛔⛔ E I BLOCCHI NON SI ACCUMULANO QUI — la scelta, con la ragione
 *
 * Il codificatore vuole blocchi di misura FISSA: 960 fotogrammi per Opus, 240
 * per PCM (`audio.h`, `RCP.md` §5.3).  PipeWire consegna quanti fotogrammi
 * vuole lui — con il quanto forzato a 256 ne consegna 256, che non e' ne' l'uno
 * ne' l'altro.  Qualcuno deve accumulare.  ⇒ **Non questo modulo**, e non e'
 * pigrizia:
 *
 *   1. ⛔ Chi consuma **deve** avere una coda propria, comunque.  Il richiamo
 *      gira sul thread di tempo reale (vedi sotto): dentro non si puo'
 *      codificare — `avcodec_send_frame` alloca — ne' scrivere su un socket.
 *      Quindi i campioni vanno copiati in una struttura che un ALTRO thread
 *      legge, e quella struttura e' per forza un anello con testa e coda: da un
 *      anello si tirano fuori 960 fotogrammi per costruzione, senza un secondo
 *      accumulatore.  Metterne uno qui vorrebbe dire **due memorie intermedie
 *      per lo stesso mestiere**, e `CODER.md` §1-bis: «ogni memoria intermedia
 *      che aggiungi compra fluidita' e vende risposta».
 *
 *   2. ⛔ Un accumulatore qui deciderebbe QUANDO il suono parte, e quella e' una
 *      decisione di chi spedisce, non di chi cattura.
 *
 *   3. ⚠ E il resto: allo spegnimento un accumulatore si ritroverebbe in mano
 *      fino a 959 fotogrammi che nessuno reclama, e li butterebbe in silenzio.
 *
 * ⇒ ⛔ **Il contratto e' quindi: `fotogrammi` VARIA a ogni richiamo, e chi
 *   ascolta non deve dare per scontato niente sul suo valore.**  La misura del
 *   blocco si chiede a `audio_cod_blocco()`, che e' il posto unico in cui vive.
 *
 * ---------------------------------------------------------------------------
 * ⛔ IL VOLUME: invariante I5, e una trappola misurata
 *
 * Il volume appartiene alla sessione e chi si collega lo trova al MASSIMO
 * (`SPECIFICHE.md` §10, `CODER.md` §2 I5).  ⚠ E il sink nasce con
 * `monitor.channel-volumes = true`, senza la quale il cursore del volume non
 * governa niente: `STUDI.md` §kde §10.5, `[M]` 8 agosto 2026.  La ragione
 * lunga, con la tabella dei numeri, sta accanto alla riga in `suono.c`.
 */
#ifndef REMOTIX_SUONO_H
#define REMOTIX_SUONO_H

#include <stdbool.h>
#include <stdint.h>

typedef struct suono suono;

/*
 * I campioni catturati: interlacciati, `s16` nell'ordine della macchina, e
 * `fotogrammi` campioni PER CANALE (quindi `fotogrammi * AUDIO_CANALI` interi).
 *
 * ⛔⛔ GIRA SUL THREAD DI TEMPO REALE DI PIPEWIRE: qui si COPIA e si TORNA.
 *
 *     `[R]` `pipewire/stream.h:150` — con `PW_STREAM_FLAG_RT_PROCESS` questa
 *     richiamata «will be called from a realtime thread and it is not safe to
 *     call non-realtime functions such as doing file operations, blocking
 *     operations or any of the PipeWire functions that are not explicitly
 *     marked as being RT safe».
 *
 *     ⛔ E il danno non si ferma all'audio: chi ci scrive dentro una chiamata
 *     che aspetta — un lucchetto conteso, una scrittura su socket, una `malloc`
 *     sfortunata, **una riga di registro** — fa saltare il quanto a TUTTO il
 *     grafo PipeWire, cattura del desktop compresa.  Il sintomo non sarebbe
 *     «l'audio gracchia», sarebbe «il video ha degli scatti», e nessuno
 *     risalirebbe fin qui.
 *
 * ⚠ `campioni` vale solo per la durata del richiamo: al giro dopo PipeWire ci
 *   riscrive dentro.
 */
typedef void (*suono_campioni)(const int16_t *campioni, uint32_t fotogrammi, void *chi);

/*
 * Monta il sink virtuale nella sessione, e lo porta al massimo.
 *
 * ⛔ Torna NULL e scrive il perche' nel registro (`CODER.md` §4.2: un ripiego
 *    si dichiara).  Il nodo muore con questo oggetto — `object.linger = false` —
 *    perche' appartiene alla sessione servita e non alla macchina: lasciarlo
 *    dietro vorrebbe dire che un REMOTIX riavviato ne trova due.
 */
suono *suono_apri(void);
void suono_chiudi(suono *s);

/*
 * Accende la cattura del monitor del sink.
 *
 * ⛔ Il formato e' quello di §5.3 e non si passa: 48 000 Hz, 2 canali, `s16`.
 *    Se PipeWire ne negoziasse un altro la consegna si SPEGNE e lo si dichiara,
 *    invece di leggere i campioni alla cieca — leggere `f32` come `s16` non
 *    produce un errore, produce un'onda quadra a fondo scala che al banco
 *    sembra «audio che arriva» e all'orecchio e' un ronzio (`[M]` 5 ago 2026).
 *
 * ⚠ Una sola cattura per volta: la seconda torna `false` e lo dice.
 */
bool suono_ascolto_avvia(suono *s, suono_campioni su_campioni, void *chi);

/*
 * Spegne la cattura, e ASPETTA che il thread di tempo reale abbia finito.
 *
 * ⛔ Deve aspettare: `su_campioni` porta il puntatore della connessione, e chi
 *    torna di qui e' autorizzato a liberarlo.  Un fotogramma lasciato a meta'
 *    strada sarebbe un segfault dentro un thread che non ha il nostro nome.
 *    Come si aspetta davvero — e perche' il lucchetto del ciclo NON basta — sta
 *    scritto accanto alla funzione in `suono.c`.
 */
void suono_ascolto_ferma(suono *s);

/* Il nodo del sink, per il registro e per la diagnosi.  0 = non c'e' (piu'). */
uint32_t suono_nodo(const suono *s);

/*
 * Il volume del sink al massimo, e non zittito — invariante I5.
 *
 * Si chiama alla creazione, all'avvio della cattura e A OGNI COLLEGAMENTO.
 * `[decisione dell'utente, 8 agosto 2026]` Il livello lo porta il server dentro
 * i campioni, quindi un cursore lasciato in basso e' uno stato che il client non
 * puo' ne' vedere ne' spiegare: chi si collega da un altro apparecchio tre
 * giorni dopo sente piano e va a cercare il guasto nella rete, nel
 * codificatore, ovunque tranne li'.  E' successo davvero, a noi.
 *
 * ⚠ Si puo' chiamare da qualunque thread: prende il lucchetto del ciclo.
 */
void suono_volume_massimo(suono *s);

/*
 * ⭐ LE DUE FUNZIONI IN PIU' RISPETTO A v1, e la ragione e' una sola.
 *
 * ⛔ v1 stampava dal thread di tempo reale — «primo blocco di suono dalla
 *    sessione: %u fotogrammi» stava dentro `su_processo`.  Una riga di registro
 *    e' una `vsnprintf` piu' una `write`: e' esattamente la chiamata che
 *    aspetta di cui sopra.  ⇒ Qui il thread di tempo reale **non scrive niente**
 *    e si limita a contare; quel che v1 stampava, qui si CHIEDE da fuori.
 *
 * ⚠ E serve, non e' ornamento: `CODER.md` §3.10 — «una lettura negata non e' una
 *   lettura che dice zero».  Senza questi due, «non si sente niente» ha almeno
 *   quattro cause con la stessa faccia: nessuno suona, il flusso e' morto, il
 *   formato e' stato rifiutato, il volume e' a zero.  Con questi due, le prime
 *   tre si distinguono in una riga.
 */
bool suono_ascolto_vivo(const suono *s);
void suono_conti(const suono *s, uint64_t *blocchi, uint64_t *fotogrammi, uint64_t *scartati);

#endif
