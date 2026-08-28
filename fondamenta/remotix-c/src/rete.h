/*
 * rete — quanto e' lontano il client, quanto ne digerisce, e quanto se ne puo'
 * spedire.
 *
 * Due cose che stanno insieme perche' la seconda si ricava dalla prima:
 *
 *   la MISURA      RTT e banda, con il meccanismo di autodetect di
 *                  MS-RDPBCGR 2.2.14 (§16 di protocollo-rdp.md);
 *   il REGOLATORE  quanti fotogrammi non riscontrati si tollerano prima di
 *                  smettere di produrre, con la soglia ricavata dall'RTT
 *                  (§10.2 di gnome-remote-desktop.md).
 *
 * # Perche' non si usano i campi che FreeRDP calcola gia'
 *
 * `rdpAutoDetect` tiene `netCharAverageRTT` e `netCharBaseRTT`, e li aggiorna da
 * se' a ogni risposta.  Sono inservibili, e non per una sfumatura:
 * `autodetect_recv_rtt_measure_response` calcola il round trip come
 * «adesso meno `rttMeasureStartTime`», dove quel campo e' l'istante dell'ULTIMA
 * richiesta spedita — non di quella a cui il client sta rispondendo.  Con una
 * sola sonda in volo per volta il conto tornerebbe; con la cadenza a 70 ms e una
 * rete lenta le sonde si accavallano sempre, e il numero misurerebbe il tempo
 * fra due sonde invece del ritardo del collegamento.
 *
 * Qui ogni sonda si annota con il suo numero di sequenza e il suo istante di
 * partenza, e la risposta si accoppia per numero.  E' quel che fa anche il
 * riferimento, per la stessa ragione.
 *
 * # ⛔ I riscontri arrivano su un ALTRO thread
 *
 * `rdpgfx_server_context_new` mette `priv->ownThread = TRUE`: il canale EGFX si
 * legge da un thread suo, e `FrameAcknowledge` — cioe' `rete_riscontro` — gira
 * la'.  Tutto il resto (le sonde, l'invio, il passo) gira sul thread della
 * connessione.  Da qui il lucchetto: senza, il conto dei fotogrammi in volo si
 * corromperebbe proprio quando la rete e' carica, che e' l'unico momento in cui
 * serve.
 *
 * # Il prerequisito, e chi lo controlla
 *
 * §16 di protocollo-rdp.md: la misura vale solo se il client ha dichiarato
 * `RNS_UD_CS_SUPPORT_NETCHAR_AUTODETECT`.  Non serve controllarlo a mano —
 * `gcc.c:1096` di FreeRDP spegne `FreeRDP_NetworkAutoDetect` da se' quando legge
 * un Client Core Data che non lo porta.  Chi non lo dichiara non si misura, e si
 * serve con la soglia prudente.
 */
#pragma once

#include <freerdp/freerdp.h>
#include <glib.h>
#include <stdint.h>

typedef struct Rete Rete;

/*
 * Va costruita PRIMA di `peer->Initialize`.
 *
 * ⛔ Non piu' tardi, e non in `PostConnect`: l'autodetect alla connessione
 *    (`CONNECT_TIME_AUTO_DETECT_REQUEST`, §16) sta nella macchina a stati fra le
 *    impostazioni riservate e le licenze, cioe' PRIMA che `PostConnect` venga
 *    chiamata (`peer.c:756` contro `peer.c:927`).  Ganci messi dopo perdono la
 *    prima misura, che e' l'unica disponibile quando si disegna il primo
 *    fotogramma.
 *
 * `fingi_sospensione` serve al BANCO, e non e' una comodita': il caso
 * `queueDepth == 0xFFFFFFFF` e' quello in cui un regolatore scritto male si
 * ferma per sempre, e nessuno dei tre client di riferimento lo produce a
 * comando.  Con questa accesa, dopo un centinaio di fotogrammi la misura si
 * comporta come se il client avesse appena chiesto di non riceverne piu' — cioe'
 * mentre ci sono fotogrammi in volo e il regolatore puo' essere strozzato, che
 * e' il momento pericoloso.
 */
Rete *rete_nuova(rdpContext *contesto, uint32_t fotogrammi_al_secondo,
                 gboolean fingi_sospensione);
void rete_libera(Rete *rete);

/* Un passo, a ogni giro del ciclo della connessione: spedisce una sonda se e'
 * ora, e ogni tanto scrive nel registro come sta andando. */
void rete_passo(Rete *rete);

/*
 * Il regolatore: c'e' posto per un altro fotogramma?
 *
 * Va chiesto PRIMA di prelevare dal palco.  Prelevare e poi rinunciare
 * consumerebbe il fotogramma senza spedirlo, e su un desktop fermo non ne
 * arriverebbe un altro (R9).
 */
gboolean rete_c_e_posto(Rete *rete);

/*
 * Attorno all'invio, sul thread della connessione.
 *
 * `rete_fotogramma_parte` riceve la dimensione del fotogramma gia' codificato:
 * la misura di banda si aggancia solo a quelli grossi (§16 — sotto i 10 KB il
 * risultato e' rumore).  `rete_fotogramma_partito` conta il fotogramma fra
 * quelli in volo.
 */
void rete_fotogramma_parte(Rete *rete, uint32_t byte_fotogramma);
void rete_fotogramma_partito(Rete *rete);

/*
 * ⛔ LA MISURA DI BANDA SI STRINGE ATTORNO ALLO SVUOTAMENTO DELLA CODA DEI
 *    CANALI, NON ATTORNO ALL'INVIO DEL FOTOGRAMMA.  Misurato il 5 agosto 2026.
 *
 * `WTSVirtualChannelWrite` su un canale dinamico non scrive niente sul socket:
 * accoda con `wts_queue_send_item`, e i byte partono quando il ciclo chiama
 * `WTSVirtualChannelManagerCheckFileDescriptor`.  I PDU di autodetect invece
 * vanno DRITTI sul filo (`rdp_send_message_channel_pdu`).  Mandare Start e Stop
 * attorno a `SurfaceFrameCommand` significa quindi mandarli entrambi PRIMA del
 * fotogramma: al banco il client rispondeva «10 byte in 0 ms», cioe' aveva
 * contato solo il PDU di Stop.
 *
 * Vanno chiamate una prima e una dopo lo svuotamento, dal ciclo della
 * connessione, e solo quando lo svuotamento avviene davvero.
 */
void rete_banda_apre(Rete *rete);
void rete_banda_chiude(Rete *rete);

/*
 * Dal gancio `FrameAcknowledge` — che gira sul thread di EGFX.
 *
 * `profondita_coda` vale `0xFFFFFFFF` quando il client smette di riscontrare
 * (§5 di REFERENCE.md): da quel momento il regolatore non ha piu' niente da
 * contare e deve togliersi di mezzo, altrimenti aspetta per sempre riscontri che
 * non arriveranno.
 */
void rete_riscontro(Rete *rete, uint32_t id_fotogramma, uint32_t profondita_coda,
                    uint32_t totale_decodificati);

/* Per il registro e per chi deve decidere: -1 se non c'e' ancora una misura. */
gint64 rete_rtt_us(Rete *rete);
uint32_t rete_banda_kbit(Rete *rete);

