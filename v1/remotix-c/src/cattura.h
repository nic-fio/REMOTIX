/*
 * cattura — i pixel, letti dal nodo PipeWire che Mutter ha aperto.
 *
 * ⛔ LO STRIDE SI LEGGE DAL CHUNK DEL BUFFER, mai calcolato come
 *    `larghezza * 4`.  Il produttore allinea le righe come gli conviene, e
 *    dedurlo produce immagini oblique (§5.6 di SPECIFICA.md; vale anche per il
 *    riferimento, §11.4 di gnome-remote-desktop.md).
 *
 * ⛔ IL DMA-BUF SI CHIEDE IN DUE POSTI, e chi ne dichiara uno solo non lo
 *    ottiene: il campo `modifier` nel FORMATO (con `MANDATORY | DONT_FIXATE`) e
 *    il bit `SPA_DATA_DmaBuf` in `SPA_PARAM_Buffers`.  Dichiarandone uno solo la
 *    negoziazione riesce lo stesso e i buffer continuano ad arrivare in memoria
 *    ordinaria: nessun errore, nessuna riga di registro, e la copia zero
 *    semplicemente non c'e' (§7.3 di REFERENCE.md, misurato il 6 agosto).
 *
 *    E non si chiede se non c'e' chi lo sappia leggere: un consumatore che si
 *    aspetta un puntatore scarta ogni DMA-BUF in silenzio.  E' il senso di
 *    `su_dmabuf`, che e' l'interruttore, e di `cattura_dmabuf`, che lo gira a
 *    cattura viva quando il codec cambia idea.
 *
 * ⛔ LA CADENZA SI DICHIARA A ZERO, con un massimo a intervallo: significa
 *    «mandami un fotogramma quando cambia qualcosa, non a ritmo fisso», che e'
 *    esattamente il comportamento che serve a un desktop remoto.  Ne discende
 *    che su un desktop fermo NON ARRIVA NULLA — comportamento voluto, non
 *    guasto, ed e' la ragione per cui esiste R9.
 *
 * Il ciclo di PipeWire vive su un thread suo (`pw_thread_loop`): e' sincrono e
 * bloccante, e mescolarlo con qualunque altro ciclo significa bloccarsi a
 * vicenda.  Le due richiamate qui sotto vengono quindi chiamate DA QUEL THREAD:
 * chi le scrive non deve aspettare nulla al loro interno, e in particolare non
 * deve chiamare `cattura_ferma` da dentro `CatturaFine`.
 */
#pragma once

#include <glib.h>
#include <stdint.h>

typedef struct Cattura Cattura;

/* Un fotogramma appena arrivato.  I pixel sono BGRX a 32 bit e vivono solo per
 * la durata della chiamata: chi li vuole se li copia. */
/*
 * Il fotogramma consegnato come DMA-BUF: non c'e' un puntatore, c'e' un
 * descrittore di memoria che vive sulla scheda.
 *
 * ⛔ Il descrittore vale SOLO DENTRO la richiamata: appena si torna, il buffer
 *    torna a PipeWire.  Chi lo vuole conservare deve averne fatto qualcosa
 *    prima — che e' esattamente quel che fa il palco, importandolo sulla scheda.
 */
/*
 * Una regione cambiata del fotogramma (SPA_META_VideoDamage).
 *
 * ⛔ E' UN'INFORMAZIONE SU QUANTO E' CAMBIATO, NON LA CONDIZIONE PER CUI IL
 *    BUFFER SI PUO' LEGGERE.  ⚠ Qui c'era scritto il contrario, e la misura lo
 *    ha smentito.  Diceva: «NON E' UN'OTTIMIZZAZIONE: e' quel che rende
 *    leggibile il buffer.  In zero-copy Mutter ricicla i propri buffer e vi
 *    ridipinge dentro SOLO la parte cambiata; fuori da quelle regioni ci sono i
 *    pixel del fotogramma che aveva usato quel buffer prima» (7 agosto 2026,
 *    R29 di REFERENCE.md).
 *
 *    `[M]` 12 agosto 2026 — F2.2, `fasi/rapporti/F2-2-cattura.md`.  NIC-OS,
 *    sessione GNOME headless (Mutter 48.7), strada MEMORIA, monitor virtuale
 *    1920x1080, scena «bandiera» con sette barre SMPTE: il danno e' PARZIALE su
 *    tutti e 410 i fotogrammi — il primo compreso — e le sette bande si leggono
 *    INTERE nel fotogramma di regime, coi valori RGB attesi banda per banda.
 *    ⇒ il buffer e' intero ANCHE quando il danno e' parziale.
 *
 *    `[R]` `gnome.md` §8.1, Mutter 48 riletto riga per riga, che lo diceva gia':
 *    blit dell'INTERO framebuffer, stack di clip svuotato deliberatamente, e la
 *    vista virtuale e' un `CoglOffscreen` persistente.  Le due strade — il
 *    codice letto e i pixel contati — concordano.
 *
 * ⛔ E LA POSTA ERA ALTA.  Se avesse avuto ragione il testo vecchio, la fase 2
 *    avrebbe consegnato mezzo desktop e meta' schermata gia' passata, SENZA UN
 *    ERRORE da nessuna parte; e la cura sarebbe stata una superficie di
 *    accumulo, che e' proprio quel che in v1 PEGGIORAVA le cose — copiavamo i
 *    rettangoli danneggiati da un buffer che era gia' intero (`gnome.md` §8.1).
 *
 * ⚠ A che cosa serve allora il danno: a sapere QUANTA parte e' stata ridipinta
 *   — cioe' quanto conviene ricodificare — e a distinguere «il produttore non
 *   dichiara il danno» da «il danno copriva tutto».  Si continua a chiederlo
 *   (`SPA_META_VideoDamage`), perche' non chiederlo significa non riceverlo.
 *
 * ⚠ `[?]` La misura e' della strada MEMORIA.  Sul DMA-BUF il codice letto dice
 *   la stessa cosa, ma nessuno l'ha ancora misurata: quando la fase 8 la
 *   percorrera', questo riquadro va riletto.
 */
typedef struct
{
	uint32_t x, y, larghezza, altezza;
} CatturaRegione;

/* `quante == 0` significa «il fotogramma vale tutto»: o il produttore non ha
 * dichiarato il danno, o il danno copriva tutto, o le regioni erano piu' di
 * quante se ne portano.  E' il caso sicuro, e costa solo una copia in piu'. */
typedef void (*CatturaDmabuf)(int fd, uint32_t offset, uint32_t passo, uint64_t modificatore,
                              uint32_t larghezza, uint32_t altezza, const CatturaRegione *danno,
                              guint quante, gpointer dati);

typedef void (*CatturaFotogramma)(const uint8_t *pixel, uint32_t passo, uint32_t larghezza,
                                  uint32_t altezza, gpointer dati);

/* Il flusso si e' staccato: o la sessione grafica e' finita — un «Esci» dal
 * menu di sistema — oppure Mutter l'ha fermato per conto suo. */
typedef void (*CatturaFine)(gpointer dati);

/*
 * Avvia la lettura dal nodo indicato, chiedendo la misura voluta.
 *
 * La misura si dichiara perche' si sta riprendendo un MONITOR VIRTUALE: non
 * esiste uno schermo da cui dedurla, ed e' il consumatore a dire quanto grande
 * lo vuole.  E' la base della risoluzione dinamica della fase 6.
 */
/*
 * `su_dmabuf` non e' facoltativa per comodita': e' l'interruttore.  Passandola
 * si dichiara di saper leggere i DMA-BUF, e solo allora la cattura li chiede al
 * compositore — chiederli senza saperli consumare significa scartare ogni
 * fotogramma in silenzio (§7.3 di REFERENCE.md).  Con NULL si resta in memoria
 * ordinaria.
 *
 * ⛔ `misura_negoziabile` sceglie fra le due FORME della proposta, e le due
 *    forme sono due compositori.
 *
 *    FALSO — rettangolo fisso: «voglio esattamente questa misura».  E' la forma
 *    di Mutter, dove il monitor virtuale si chiede e lui lo fa della misura
 *    chiesta.  Un intervallo APERTO qui sarebbe un difetto: Mutter sceglierebbe
 *    da se', e sceglie 1280×720 (§7.3 di REFERENCE.md).
 *
 *    VERO — intervallo: «la mia misura preferita e' questa, ma prendo la tua».
 *    E' la forma con cui KWin 6.8 fara' seguire allo stream la misura del
 *    consumatore (`kwin!7932`, unita il 29 luglio 2026 — ed e' il codice della
 *    nostra fase 6, `kde.md` §8.2).  Su Trixie il compositore risponde con la
 *    propria e noi la adottiamo, senza aspettare inutilmente una conferma che
 *    non arrivera' mai.
 */
Cattura *cattura_avvia(uint32_t nodo, uint32_t larghezza, uint32_t altezza,
                       uint32_t fotogrammi_al_secondo, gboolean misura_negoziabile,
                       CatturaFotogramma su_fotogramma, CatturaDmabuf su_dmabuf,
                       CatturaFine su_fine, gpointer dati, GError **sbaglio);

/* La misura davvero negoziata, che puo' non essere quella chiesta. */
void cattura_misura_negoziata(const Cattura *cattura, uint32_t *larghezza, uint32_t *altezza);

/*
 * Chiede a Mutter una misura nuova SENZA rifare la cattura.
 *
 * ⛔ E' la correzione che toglie il prezzo pagato in §5.8 di SPECIFICA.md.  Fino
 *    alla fase 5 un cambio di risoluzione smontava e rimontava il palco; ma una
 *    cattura nuova non si registra su un controllo gia' avviato (§7.3 di
 *    REFERENCE.md), quindi rifaceva anche il CONTROLLO — e con lui i dispositivi
 *    virtuali di libei, perdendo lo stato dei tasti premuti e obbligando GNOME a
 *    ricostruire il monitor virtuale da zero.
 *
 *    Il riferimento dimostra che non serve: `pw_stream_update_params` con la
 *    misura nuova basta, Mutter riconfigura il monitor virtuale e risponde con
 *    un `param_changed` (§11.3 di gnome-remote-desktop.md).
 *
 * Si aspetta la CONFERMA, non un silenzio: e' la forma giusta di R10, dove il
 * riferimento sostituisce un'attesa a tempo con un evento.
 *
 * ⛔ E LA CONFERMA SI RESTITUISCE INVECE DI GIUDICARLA QUI.  La misura
 *    confermata puo' essere diversa da quella chiesta, e le due risposte
 *    corrette sono opposte: su Mutter e' un guasto — il desktop coprirebbe mezza
 *    superficie — su KWin e' la risposta normale, perche' la misura la decide
 *    lui.  A saperlo e' il palco, che sa con quale compositore sta parlando; qui
 *    si riporta il fatto.
 */
gboolean cattura_ridimensiona(Cattura *cattura, uint32_t larghezza, uint32_t altezza,
                              uint32_t fotogrammi_al_secondo, uint32_t *confermata_larghezza,
                              uint32_t *confermata_altezza, GError **sbaglio);

/*
 * Cambia la STRADA dei pixel a cattura viva: dalla scheda alla memoria e
 * ritorno.
 *
 * ⛔ SERVE PERCHE' I DUE CODEC NON VOGLIONO LA STESSA COSA.  AVC420 si codifica
 *    in GPU e il fotogramma non deve mai passare dalla CPU; RemoteFX
 *    Progressive e' un codec a wavelet, gira in CPU, e i pixel li vuole li'.
 *    Quale dei due si spedisce lo si sa solo al `CapsAdvertise`, cioe' DOPO che
 *    il palco e' montato: senza questa chiamata, un client Android che si
 *    collegasse con la copia zero accesa non vedrebbe niente — e non un errore,
 *    proprio niente.
 *
 * Si passa per la stessa porta del ridimensionamento (`pw_stream_update_params`)
 * e per la stessa ragione: rifare la cattura significherebbe rifare il
 * controllo, e con lui i dispositivi virtuali di libei (§7.3 di REFERENCE.md).
 *
 * La misura si ripete perche' la proposta la porta con se': e' quella corrente
 * del palco, non un cambio.  Se la modalita' chiesta e' gia' quella in corso
 * non fa nulla e dice di si'.
 */
gboolean cattura_dmabuf(Cattura *cattura, gboolean vuole, uint32_t larghezza, uint32_t altezza,
                        uint32_t fotogrammi_al_secondo, GError **sbaglio);

void cattura_ferma(Cattura *cattura);
