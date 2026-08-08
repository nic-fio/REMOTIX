/*
 * palco — cattura e monitor virtuale, montati una volta e tenuti in piedi.
 *
 * # R9: l'ultimo fotogramma si conserva e si rispedisce
 *
 * Mutter manda un fotogramma SOLO quando qualcosa cambia.  Un fotogramma
 * arrivato prima che il client abbia finito di negoziare non si puo' disegnare,
 * e su un desktop fermo non ne arrivera' un altro: il client resta nero a tempo
 * indeterminato.  Il difetto e' insidioso perche' SI CORREGGE DA SE' appena
 * qualcuno muove qualcosa, quindi in prova sembra un ritardo d'avvio.
 *
 * Qui l'ultimo fotogramma vive in un posto solo, sempre disponibile, e ogni
 * connessione tiene il conto di quale ha gia' visto: chi arriva trova subito
 * qualcosa da disegnare.
 *
 * # R10: dopo un rimontaggio si aspetta il ridisegno
 *
 * Quando il monitor virtuale cambia misura, Mutter manda un fotogramma SUBITO,
 * prima che GNOME abbia ridisegnato: lo sfondo e' ancora quello della misura
 * vecchia e il resto e' vuoto.  Misurato in PNG fuori dalla catena RDP, ne manda
 * due — il primo con il solo colore di fondo, il secondo completo — e poi tace.
 * Con R9 quell'immagine parziale RESTA.  Si aspetta quindi il silenzio, ma
 * fidandosene solo dopo il secondo fotogramma: il silenzio fra il primo e il
 * secondo e' esattamente dove cadeva la prima stesura di questa attesa.
 *
 * # Perche' il palco appartiene al SERVER e non alla connessione
 *
 * Perche' smontarlo alla disconnessione lascia Mutter con ZERO schermi, e da
 * li' `libmutter` va in asserzione fallita
 * (`meta_workspace_get_work_area_for_monitor: logical_monitor != NULL`), le
 * applicazioni aperte perdono la connessione Wayland con «Error 71 (Protocol
 * error)» e quelle nuove non hanno dove aprirsi.  E' la questione aperta n.5 di
 * `SPECIFICA.md`, gia' colta sul fatto il 3 agosto.
 *
 * Fase 5 lo prevede come proprio contenuto — «il palco appartiene alla
 * sessione, non alla connessione» — ma anticiparlo qui non e' zelo: la prova
 * della fase 3 e' «il desktop vero SUI TRE CLIENT», cioe' tre connessioni una
 * dopo l'altra, che e' precisamente la sequenza che quel difetto rovina.  In
 * dote arriva anche il riaggancio: chi si ricollega alla stessa misura ritrova
 * il desktop com'era, senza rifare la cattura.
 */
#pragma once

#include <glib.h>
#include <libavutil/frame.h>
#include <stdint.h>

#include "appunti.h"
#include "compositore.h"
#include "immagine.h"
#include "input.h"
#include "suono.h"

typedef struct Palco Palco;

typedef enum
{
	PALCO_NUOVO,  /* c'e' un fotogramma piu' recente, ed e' stato copiato */
	PALCO_NIENTE, /* il desktop e' fermo: condizione NORMALE, non un guasto */
	PALCO_FINITA, /* la cattura si e' chiusa: la sessione grafica non c'e' piu' */
} EsitoPalco;

Palco *palco_nuovo(TipoCompositore tipo);
void palco_libera(Palco *palco);

/*
 * La misura VERA del palco montato, che puo' non essere quella chiesta.
 *
 * ⛔ VA LETTA DOPO OGNI `palco_assicura` E OGNI `palco_ridimensiona`, e non e'
 *    prudenza: su KWin la misura la decide il compositore (`compositore.h`), e
 *    una tela grafica dichiarata al client con la misura CHIESTA invece che con
 *    quella servita produce un desktop che copre una parte della superficie —
 *    senza alcun errore, e con il resto grigio.  E' il sintomo che il 3 agosto
 *    2026 costo' una caccia e una questione aperta.
 *
 * Zero significa «non c'e' nessun palco».
 */
void palco_misura(Palco *palco, uint32_t *larghezza, uint32_t *altezza);

/* Chi possiede schermo e input, riconosciuto all'avvio.  Serve a chi deve
 * avviare o chiudere la SESSIONE, che si fa in modi diversi sui due. */
TipoCompositore palco_compositore(Palco *palco);

/*
 * Assicura che ci sia un palco della misura chiesta.
 *
 * Tre casi, in ordine di fortuna:
 *
 *   - c'e' gia' ed e' della misura giusta: non si tocca nulla, ed e' il
 *     riaggancio — il desktop ricompare all'istante, con le finestre dov'erano;
 *   - c'e' ma di un'altra misura: si RIDIMENSIONA, non si rimonta.  Fino alla
 *     fase 5 qui si smontava, e smontare lascia Mutter con zero schermi (§7.3
 *     di REFERENCE.md);
 *   - non c'e', o la sua cattura si e' chiusa: si monta da capo.
 */
gboolean palco_assicura(Palco *palco, uint32_t larghezza, uint32_t altezza,
                        uint32_t fotogrammi_al_secondo, GError **sbaglio);

/*
 * Cambia la misura del palco SENZA smontarlo, ed e' il cuore della fase 6.
 *
 * ⛔ NON DEVE RIFARE LA CATTURA.  Rifarla significa rifare anche il controllo —
 *    una cattura nuova non si registra su un controllo gia' avviato (§7.3 di
 *    REFERENCE.md) — e quindi i dispositivi virtuali di libei, con il conto dei
 *    tasti premuti che se ne va e Android che riavvia il decodificatore due
 *    volte invece di una.  E' il prezzo pagato in §5.8 di SPECIFICA.md, e la
 *    fase 6 esiste anche per non pagarlo piu'.
 *
 * Se la misura chiesta e' quella corrente non fa nulla e dice di si': e' il
 * caso del `MONITOR_LAYOUT` che il client Android manda subito dopo essersi
 * collegato, che ripete la misura del Client Core Data.
 *
 * Se `pw_stream_update_params` non riesce, si RIPIEGA sul rimontaggio completo
 * dichiarandolo nel registro («ripiego»): una sessione degradata e' meglio di
 * una sessione ferma (§2 di SPECIFICA.md), ma resta un ripiego, e nel banco
 * della fase 6 la sua comparsa e' un guasto.
 */
gboolean palco_ridimensiona(Palco *palco, uint32_t larghezza, uint32_t altezza,
                            uint32_t fotogrammi_al_secondo, GError **sbaglio);

/*
 * Copia nella tela l'ultimo fotogramma, se e' piu' recente di quello che il
 * chiamante ha gia' visto.  `visto` va inizializzato a 0 e viene aggiornato.
 */
EsitoPalco palco_preleva(Palco *palco, Immagine *tela, guint64 *visto);

/*
 * Le due porte del percorso a copia zero.
 *
 * `palco_superfici` dice se il palco sta lavorando sulla scheda — e con che
 * contesto va aperto il codificatore; `palco_preleva_superficie` consegna
 * l'ultimo fotogramma gia' convertito e gia' allineato, come riferimento nuovo
 * da liberare con `av_frame_free`.
 *
 * Quando la prima restituisce NULL vale il percorso di sempre, con la tela in
 * memoria: e' cosi' che si serve un client che vuole RemoteFX Progressive, il
 * cui codificatore i pixel li vuole in CPU.
 */
AVBufferRef *palco_superfici(Palco *palco);
EsitoPalco palco_preleva_superficie(Palco *palco, AVFrame **fuori, guint64 *visto);

/*
 * Dichiara che una connessione ha bisogno dei pixel IN CPU, o che non ne ha
 * piu' bisogno.
 *
 * ⛔ E' quel che rende servibile un client Android mentre la copia zero e'
 *    accesa.  Il palco che lavora sulla scheda non ha pixel in memoria, e
 *    RemoteFX Progressive — il codec di Android — li vuole li'.  Quale codec si
 *    spedisce lo si sa al `CapsAdvertise`, cioe' DOPO che il palco e' montato:
 *    senza questa chiamata quel client vedrebbe uno schermo fermo, e non un
 *    errore.
 *
 * Si conta, non si commuta: le richieste possono sovrapporsi, e si torna sulla
 * scheda solo quando l'ultima e' stata lasciata.  Ogni connessione deve
 * chiamarla con TRUE una volta sola e con FALSE una volta sola — chi si
 * dimentica il secondo giro lascia il palco in memoria per sempre.
 *
 * Non fallisce mai in modo utile al chiamante — se la rinegoziazione con Mutter
 * non riesce lo dice nel registro e si tiene la strada che ha: un desktop
 * servito peggio e' meglio di una connessione rifiutata (§2 di SPECIFICA.md).
 */
void palco_pixel_in_cpu(Palco *palco, gboolean servono);

/* Smonta tutto.  Si usa allo spegnimento, non alla disconnessione. */
void palco_smonta(Palco *palco);

/*
 * Il canale di input verso il compositore, o NULL se la sessione e' di sola
 * visione.
 *
 * Appartiene al palco per lo stesso motivo per cui gli appartiene la cattura:
 * i dispositivi virtuali vivono quanto la sessione di controllo, e quella nasce
 * e muore col monitor virtuale.  Chi si collega li trova gia' pronti.
 *
 * ⛔ VA PRESO E LASCIATO, non semplicemente letto, e non e' cerimonia: il palco
 *    si smonta da un thread — la sessione esce, compare una sessione locale —
 *    mentre le connessioni stanno ancora inoltrando tasti.  Leggere il
 *    puntatore e usarlo dopo significa usare memoria liberata, e il sintomo e'
 *    un segfault dentro glib in un thread «remotix-peer», cioe' lontanissimo
 *    dalla causa.  Misurato il 4 agosto, due volte, in `dmesg`.
 *
 *    Fra `prendi` e `lascia` lo smontaggio ASPETTA.  Chi sta in mezzo non deve
 *    quindi fare nulla di lungo: accodare un evento, e basta.
 */
Input *palco_input_prendi(Palco *palco);
void palco_input_lascia(Palco *palco);

/*
 * Il sink audio della sessione, o NULL se non c'e'.
 *
 * ⛔ VALE PAROLA PER PAROLA QUEL CHE E' SCRITTO SOPRA PER L'INPUT: si prende e
 *    si lascia, e il puntatore NON si tiene da parte fra una chiamata e l'altra.
 *    La sessione puo' finire mentre una connessione sta ascoltando, e chi avesse
 *    conservato il puntatore chiuderebbe una cattura che non esiste piu'.
 */
Suono *palco_suono_prendi(Palco *palco);
void palco_suono_lascia(Palco *palco);

/*
 * Gli appunti della sessione, o NULL se Mutter non li ha concessi.
 *
 * Valgono le stesse due righe dell'input e del suono: si prende, si usa, si
 * lascia, e il puntatore non si conserva.
 *
 * ⛔ CON UNA ECCEZIONE, e sta scritta in `scambio.c`: chi gira DENTRO una
 *    richiamata degli appunti non deve prendere questo lucchetto, perche' lo
 *    smontaggio lo tiene gia' in scrittura mentre aspetta proprio quella
 *    richiamata.  Li' il puntatore e' vivo per costruzione.
 */
Appunti *palco_appunti_prendi(Palco *palco);
void palco_appunti_lascia(Palco *palco);

/*
 * Arma la spia dei fotogrammi: i prossimi `quanti` finiscono su disco, nella
 * cartella indicata da REMOTIX_FOTO, su qualunque strada il palco stia
 * lavorando — memoria (PPM) o scheda (PGM del piano Y).
 *
 * La chiama il gestore di SIGUSR1: il difetto da fotografare non ha un istante
 * prevedibile, e armarla sul ridimensionamento copriva il solo istante che si
 * sapeva predire.
 */
void palco_spia_arma(guint quanti);

/*
 * Fotografa la superficie come la riceve il CODIFICATORE — l'altro capo del
 * passaggio di mano.  Non fa niente se la spia non e' armata.
 */
void palco_spia_superficie(Palco *palco, AVFrame *superficie);
