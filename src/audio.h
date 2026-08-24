/*
 * audio — il codificatore del suono: Opus, con PCM come base.
 *
 * ---------------------------------------------------------------------------
 * ⛔ IL FORMATO NON SI NEGOZIA, E NON E' UN'OPINIONE DI QUESTO FILE
 *
 * `RCP.md` §5.3 lo fissa, e la ragione e' scritta li': «"Opus, con PCM come
 * base" dice il codec e non dice il formato, e due implementazioni che
 * scelgono due frequenze diverse producono un rumore che sembra un difetto di
 * rete».
 *
 *   frequenza   48 000 Hz, sempre, per entrambi i codec
 *   canali      2, interlacciati
 *   Opus        un pacchetto per datagram, blocchi da 20 ms   (960 fotogrammi)
 *   PCM         s16 LITTLE-endian, 5 ms per datagram          (240 fotogrammi)
 *
 * ⛔ I 5 ms del PCM non sono una scelta di comodo: sono `RCP.md` §5.3 dopo il
 *    rilievo R1.1, «il piu' grave della revisione del 9 agosto».  A 20 ms il
 *    PCM farebbe 3852 byte, e un datagram QUIC non e' frammentabile.
 *    ⭐ `[M]` 17 agosto 2026 (`banchi/07-b40`): il datagram vero e' **1024
 *    byte su Chrome 151**, quindi i 972 del PCM ci stanno per 52 byte — e a
 *    20 ms non ci starebbero per un fattore quattro.
 *
 * ⛔ E il little-endian del PCM e' l'unica eccezione all'ordine di rete di §6,
 *    dichiarata: sono un carico utile, come i byte di HEVC, non un campo di
 *    protocollo.  ⚠ Un banco che lo legga big-endian non vede un errore: vede
 *    RUMORE A FONDO SCALA, che e' il difetto di v1 (`LEZIONI.md` §2.2), e
 *    `banchi/07-b40` lo innesta apposta come controllo positivo.
 *
 * ---------------------------------------------------------------------------
 * ⭐ PERCHE' OPUS PASSA DA `libavcodec` E NON DA `libopus`
 *
 * `[M]` 17 agosto 2026, sulla macchina di prova: `libavcodec` 61.19.101 e' gia'
 * collegato a `libopus.so.0`, e dichiara l'encoder `libopus`.  ⇒ Il `Makefile`
 * NON cambia e non si aggiunge un pacchetto a due ambienti di costruzione (il
 * contenitore del portatile e il `devroot` del server), dove `opus.pc` non c'e'.
 *
 * ⚠ Il prezzo, dichiarato: si paga l'allocazione di un `AVPacket` per blocco,
 *   cioe' 50 al secondo.  E' meno del prezzo di una dipendenza che va
 *   installata due volte e ricordata per sempre (`LEZIONI.md` §2.5-bis).
 */
#pragma once

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

/* §5.3, e valgono per tutt'e due i codec. */
#define AUDIO_FREQUENZA 48000
#define AUDIO_CANALI 2

/* Quanti fotogrammi (campioni per canale) sta in un blocco, per codec. */
#define AUDIO_BLOCCO_OPUS 960 /* 20 ms */
#define AUDIO_BLOCCO_PCM 240  /*  5 ms */

typedef struct audio_cod audio_cod;

/*
 * Apre il codificatore per il codec NEGOZIATO.
 *
 * `codec` 1 = Opus, 2 = PCM — i numeri di `RCP.md` §6.3, non quelli del video.
 *
 * ⛔ Torna NULL e scrive nel registro se il codec non c'e': `CODER.md` §4.2 —
 *    un ripiego si dichiara.  ⚠ E NON si ripiega su PCM da soli: la scelta del
 *    codec e' della negoziazione (§4.3), e un server che spedisse PCM dove il
 *    client aspetta Opus produrrebbe rumore invece di un errore.
 */
audio_cod *audio_cod_apri(uint8_t codec);
void audio_cod_chiudi(audio_cod *c);

/* Quanti fotogrammi vuole un blocco di questo codificatore. */
uint32_t audio_cod_blocco(const audio_cod *c);

/*
 * Un blocco di campioni entra, un blocco pronto per il datagram esce.
 *
 * `campioni`  esattamente `audio_cod_blocco()` fotogrammi, interlacciati, s16
 *             nell'ordine della macchina.
 * `fuori`     almeno `AUDIO_FUORI_MAX` byte.
 *
 * ⛔⛔ QUESTO PARAGRAFO E' STATO RISCRITTO SU UNA MISURA — 17 agosto 2026,
 *      rilievo 7 della revisione avversariale, chiuso da `banchi/07-b44`.
 *
 *      Diceva: *«Torna `false` quando non c'e' niente da spedire, e NON e' un
 *      errore: Opus puo' non produrre un pacchetto per ogni blocco offerto»*.
 *      ⛔ **E' FALSO per la nostra configurazione**, e la falsita' non era
 *      innocua: `RCP.md` §6.3 vuole nell'`istante` il tempo del **primo
 *      campione del blocco**, e se il codificatore accumulasse davvero, il
 *      pacchetto che esce porterebbe l'istante di un blocco DIVERSO da quello
 *      che contiene — sbagliato di 20 ms, per sempre.
 *
 *      `[M]` 1000 blocchi entrati, **1000 pacchetti usciti**, **zero EAGAIN**:
 *      `libopus` a 20 ms fissi e' UNO PER UNO.  ⇒ L'`istante` appartiene al
 *      blocco che parte, e il ramo `EAGAIN` qui sotto **non si percorre**.
 *      Resta perche' l'API di libavcodec lo ammette, non perche' succeda.
 *
 * ⚠⚠ E LA MISURA HA TROVATO UN'ALTRA COSA, che nessuno aveva dichiarato: il
 *     `pre-skip` di Opus.  `[M]` `initial_padding = 312 campioni`, e il `pts`
 *     dei pacchetti esce **sfasato di -312 campioni = -6,50 ms**, COSTANTE su
 *     tutti e mille.
 *     ⭐ Non e' un difetto e non deriva: e' l'anticipo che l'algoritmo si
 *     prende, e il **decodificatore lo toglie da se'** — end-to-end si
 *     cancella.  E non tocca l'ordinamento di §6.3, che confronta istanti fra
 *     loro e non con un orologio esterno.
 *     ⛔ Ma va scritto: un'implementazione che un giorno usasse questi istanti
 *     per sincronizzare l'audio col video troverebbe 6,5 ms che nessun
 *     documento spiega — ed e' la forma d'errore che questo progetto paga di
 *     piu' (`LEZIONI.md` §2.2).
 *
 * ⛔ Torna `false` quando non c'e' niente da spedire.  Il chiamante non manda
 *    niente e va avanti — un blocco vuoto spedito e' un blocco che il client
 *    conta e non sente.
 */
#define AUDIO_FUORI_MAX 1200
bool audio_cod_passa(audio_cod *c, const int16_t *campioni, uint8_t *fuori,
                     size_t *quanti);

/* I due numeri del codificatore, per il registro: blocchi entrati e usciti. */
void audio_cod_conti(const audio_cod *c, uint64_t *entrati, uint64_t *usciti);

/*
 * ⛔⭐ LA CURA DEL SILENZIO DIGITALE — fase 9, e NASCE SPENTA (I6).
 *
 * Accesa, un blocco in cui **tutti** i campioni sono esattamente zero non
 * diventa un datagram: `audio_cod_passa()` torna `false`, il chiamante non
 * manda niente, e chi riceve — che mette i blocchi al loro `istante` assoluto
 * (§6.3) — trova un buco.  ⭐ Un buco e' silenzio, cioe' quel che il blocco
 * conteneva: non e' un'approssimazione, e' il non spedire lo zero.
 *
 * `[M]` 24 agosto 2026, `banchi/09-b84`: a desktop fermo e Opus negoziato sono
 * **50 datagram al secondo da 3 byte** che si portano via **589 kbit/s** di
 * pacchetti riempiti, cioe' il 99,8 % di riempimento — e la stessa finestra di
 * congestione del video.
 *
 * ⚠ Il prezzo, e la ragione dell'interruttore, stanno nel riquadro in cima ad
 *   `audio.c`.  ⛔ E l'interruttore oggi e' **di compilazione**
 *   (`-DAUDIO_SILENZIO_PREDEFINITO=1`) perche' il codificatore vive nel figlio,
 *   che non eredita l'ambiente: la riga di comando che manca si scrive in
 *   `main.c` e in `figlio.c`, ed e' descritta li'.
 */
void audio_silenzio_taci(bool si);
bool audio_silenzio_acceso(void);

/* Quanti blocchi la cura ha taciuto.  ⛔ Sta a parte da `audio_cod_conti()`:
 *    quella ha gia' un chiamante e la sua firma non e' di questo modulo. */
uint64_t audio_cod_taciuti(const audio_cod *c);
