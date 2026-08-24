/* audio.c — il codificatore del suono.  Le ragioni stanno in `audio.h`. */

#include "audio.h"

#include "registro.h"

#include <libavcodec/avcodec.h>
#include <libavutil/channel_layout.h>
#include <libavutil/opt.h>
#include <stdlib.h>
#include <string.h>

#define REG_AUDIO "audio"

/*
 * ⛔ Il bitrate di Opus, e il numero e' 🔸 DERIVATO — non deciso dall'utente.
 *
 * 96 kbit/s in stereo e' la banda a cui Opus e' trasparente per la musica
 * secondo la sua stessa documentazione `[S]`.  ⚠ Sulla sonda del 17 agosto un
 * blocco da 20 ms a questo bitrate misura **241-376 byte** su Chrome e
 * **309-439** su Firefox `[M]`: sta nel datagram con un margine largo, che e'
 * la ragione per cui non si e' scelto piu' alto.
 *
 * ⏳ Va messo a verbale in `DECISIONI.md` il giorno in cui l'utente lo sente:
 *    `SPECIFICHE.md` §10 il bitrate non lo nomina, e un numero senza una voce
 *    e' una decisione presa a meta' (`LEZIONI.md` §2.3-quater).
 */
#define AUDIO_OPUS_BITRATE 96000

/*
 * ⛔⭐⭐ IL SILENZIO NON SI SPEDISCE — cura della fase 9, 24 agosto 2026, e
 *       NASCE SPENTA (I6).
 *
 * `[M]` 24 agosto 2026, `banchi/09-b84-audio-silenzio.py`, porta 7972, binario
 * `b484d699…`: una sessione con **Opus** negoziato e il desktop FERMO consegna
 *
 *     50 datagram al secondo · **3 byte di carico ciascuno** · PICCO 0 su 32767
 *
 * cioe' **1,2 kbit/s** di suono vero.  ⛔ E sul filo quei 50 datagram costano
 * **589 kbit/s**, perche' ognuno si porta via un pacchetto INTERO da 1444 byte
 * (`webtransport.c`, `NGTCP2_WRITE_DATAGRAM_FLAG_PADDING`).  ⇒ Il **99,8 %** di
 * quel traffico e' riempimento, e paga la stessa finestra di congestione del
 * video.
 *
 * ⭐ E non c'e' niente da inventare per toglierlo.  `RCP.md` §6.3 mette
 *    l'`istante` dentro ogni datagram e chi riceve rimette i blocchi al loro
 *    posto ASSOLUTO.  ⇒ **Un blocco non spedito e' un buco, e un buco e'
 *    silenzio** — che e' esattamente quel che quel blocco conteneva.  Non si
 *    approssima niente: si smette di spedire lo zero.
 *
 * ⛔ E LA SOGLIA NON C'E', APPOSTA.  Si tace solo sul silenzio **digitale** —
 *    tutti i campioni esattamente `0` — perche' quello non e' un giudizio: e'
 *    l'unico caso in cui «spedito» e «non spedito» suonano IDENTICI.  Una
 *    soglia («sotto -60 dB») sarebbe una decisione sul suono dell'utente presa
 *    dal codice, cioe' precisamente la cosa che I6 vuole dietro un interruttore
 *    e che questa fase non ha misurato.
 *
 * ⚠ IL PREZZO, DICHIARATO — due voci, e sono la ragione per cui l'interruttore
 *   esiste invece di essere un'ovvieta':
 *     1. su Opus il primo blocco dopo un tratto di silenzio riparte con lo
 *        stato del codificatore lasciato PRIMA del tratto (qui il `pts` non
 *        avanza, apposta, o libavcodec vedrebbe un salto).  E' quel che la DTX
 *        di Opus fa da sempre; `[?]` inudibile, e da qui NON e' misurato;
 *     2. chi riceve vede un salto di `istante` e i suoi contatori lo contano
 *        come **`mancato`** — cioe' un numero che oggi vuol dire «perso»
 *        comincerebbe a voler dire anche «non c'era niente da mandare».
 *        ⛔ Il banco lo misura appaiato apposta, e lo dichiara.
 *
 * ⛔⛔ E L'INTERRUTTORE OGGI E' DI COMPILAZIONE, e va detto perche' non e' una
 *      scelta di comodo: il codificatore vive nel **figlio**, che e' un
 *      `execve` con l'ambiente **composto da zero** (`figlio.c`, il riquadro
 *      delle due cure della fase 9) — una `REMOTIX_...` non lo raggiunge, e non
 *      lascerebbe nemmeno una riga a dire che non e' arrivata.  L'unico canale
 *      che attraversa l'`exec` e' la coda di `argv`, e quella si scrive in
 *      `main.c` e in `figlio.c`, che **non sono di questo file**.
 *
 *      ⇒ Quel che serve, per chi possiede quei due file, e non e' scritto qui:
 *        · `main.c`   riconoscere `--audio-silenzio` accanto a `--parlantina`
 *                     (`:1020`) e tenerne un `bool`;
 *        · `figlio.c` metterlo in coda ad `argv` come fa con la parlantina
 *                     (`:1165`) e rileggerlo **per nome** in `figlio_vive()`
 *                     (`:5938`), chiamando `audio_silenzio_taci(true)`;
 *        · qui        non cambia niente: `audio_silenzio_taci()` c'e' gia'.
 */
#ifndef AUDIO_SILENZIO_PREDEFINITO
#define AUDIO_SILENZIO_PREDEFINITO 0
#endif

static bool audio_taci_silenzio = AUDIO_SILENZIO_PREDEFINITO;

void audio_silenzio_taci(bool si)
{
	audio_taci_silenzio = si;
}

bool audio_silenzio_acceso(void)
{
	return audio_taci_silenzio;
}

struct audio_cod {
	uint8_t codec; /* 1 = Opus, 2 = PCM */
	uint32_t blocco;
	uint64_t entrati, usciti;
	uint64_t taciuti; /* blocchi di silenzio digitale NON spediti (I6) */

	/* solo per Opus */
	AVCodecContext *ctx;
	AVFrame *frame;
	AVPacket *pkt;
	int64_t pts;
	bool eagain_detto;
};

static bool opus_apri(audio_cod *c)
{
	const AVCodec *cod;
	int e;

	/* ⛔ Si chiede l'encoder PER NOME, e non si accetta un sostituto.
	 *    `CODER.md` §3.9: «un componente che sceglie in autonomia produce due
	 *    misure diverse sotto la stessa etichetta».  ⚠ `avcodec_find_encoder`
	 *    con `AV_CODEC_ID_OPUS` potrebbe restituire l'encoder NATIVO di
	 *    FFmpeg, che e' dichiarato **sperimentale** e non e' quel che la sonda
	 *    ha misurato. */
	cod = avcodec_find_encoder_by_name("libopus");
	if (!cod) {
		registro_dice(REG_AUDIO,
		              "⛔ l'encoder «libopus» non c'e' in questa libavcodec.  "
		              "⚠ Non si ripiega su PCM da qui: il codec e' negoziato "
		              "(§4.3), e spedire PCM a chi aspetta Opus produce RUMORE "
		              "invece di un errore");
		return false;
	}

	c->ctx = avcodec_alloc_context3(cod);
	if (!c->ctx)
		return false;

	c->ctx->sample_rate = AUDIO_FREQUENZA;
	c->ctx->sample_fmt = AV_SAMPLE_FMT_S16;
	c->ctx->bit_rate = AUDIO_OPUS_BITRATE;
	av_channel_layout_default(&c->ctx->ch_layout, AUDIO_CANALI);
	/* 20 ms per pacchetto, che e' quel che §5.3 impone e non quel che
	 * l'encoder sceglierebbe se nessuno glielo dicesse. */
	av_opt_set(c->ctx->priv_data, "frame_duration", "20", 0);
	av_opt_set(c->ctx->priv_data, "application", "audio", 0);

	e = avcodec_open2(c->ctx, cod, NULL);
	if (e < 0) {
		char m[128];
		av_strerror(e, m, sizeof m);
		registro_dice(REG_AUDIO, "⛔ avcodec_open2(libopus): %s", m);
		return false;
	}

	/* ⛔ E si VERIFICA che abbia obbedito, invece di crederci.  Se l'encoder
	 *    scegliesse un `frame_size` diverso dai 960 di §5.3, i blocchi che gli
	 *    diamo sarebbero della misura sbagliata e il suono uscirebbe storto
	 *    **senza un errore da nessuna parte**. */
	if (c->ctx->frame_size != AUDIO_BLOCCO_OPUS) {
		registro_dice(REG_AUDIO,
		              "⛔ libopus ha scelto blocchi da %d fotogrammi, e §5.3 ne "
		              "vuole %d (20 ms).  Non si adatta in silenzio: si dichiara",
		              c->ctx->frame_size, AUDIO_BLOCCO_OPUS);
		return false;
	}

	c->frame = av_frame_alloc();
	c->pkt = av_packet_alloc();
	if (!c->frame || !c->pkt)
		return false;
	c->frame->format = AV_SAMPLE_FMT_S16;
	c->frame->sample_rate = AUDIO_FREQUENZA;
	c->frame->nb_samples = AUDIO_BLOCCO_OPUS;
	av_channel_layout_default(&c->frame->ch_layout, AUDIO_CANALI);
	if (av_frame_get_buffer(c->frame, 0) < 0)
		return false;

	registro_dice(REG_AUDIO,
	              "⭐ Opus aperto: 48 000 Hz, 2 canali, blocchi da %d fotogrammi "
	              "(20 ms), %d bit/s — encoder «libopus» di libavcodec",
	              c->ctx->frame_size, (int)AUDIO_OPUS_BITRATE);
	return true;
}

audio_cod *audio_cod_apri(uint8_t codec)
{
	audio_cod *c = calloc(1, sizeof *c);
	if (!c)
		return NULL;
	c->codec = codec;

	/* ⛔ L'interruttore si DICHIARA anche quando e' spento: «la cura non c'e'»
	 *    e «la cura c'e' e non ha fatto niente» devono avere due righe diverse
	 *    (`CODER.md` §3.10).  ⚠ E' la riga su cui il banco appaiato controlla
	 *    di aver davvero acceso due bracci diversi. */
	registro_dice(REG_AUDIO,
	              "cura del silenzio digitale (I6): %s",
	              audio_taci_silenzio
	                  ? "⭐ ACCESA — i blocchi tutti a zero non si spediscono"
	                  : "spenta (predefinito) — si spedisce anche il silenzio");

	if (codec == 2) {
		c->blocco = AUDIO_BLOCCO_PCM;
		registro_dice(REG_AUDIO,
		              "⭐ PCM aperto: 48 000 Hz, 2 canali, s16 little-endian, "
		              "blocchi da %u fotogrammi (5 ms) = %u byte (§5.3)",
		              c->blocco, c->blocco * AUDIO_CANALI * 2u);
		return c;
	}
	if (codec == 1) {
		c->blocco = AUDIO_BLOCCO_OPUS;
		if (!opus_apri(c)) {
			audio_cod_chiudi(c);
			return NULL;
		}
		return c;
	}

	registro_dice(REG_AUDIO,
	              "⛔ codec audio %u sconosciuto: RCP/1 ne definisce due, "
	              "1 = Opus e 2 = PCM (§6.3)",
	              codec);
	free(c);
	return NULL;
}

void audio_cod_chiudi(audio_cod *c)
{
	if (!c)
		return;
	/* ⛔⭐ IL CONTO DELLA CURA SI SCRIVE ALLA CHIUSURA, ED E' L'UNICO ISTANTE IN
	 *     CUI E' COMPLETO (`CODER.md` §3.10).  ⚠ La riga di dentro esce alla
	 *     prima e poi una ogni mille: chi legge solo quella sa dire «almeno N»,
	 *     non «N» — e un banco che confondesse le due cose scriverebbe un
	 *     numero che sembra misurato.  ⭐ E si scrive **con dentro gli zero**:
	 *     «la cura era spenta» e «la cura era accesa e non ha taciuto niente»
	 *     sono due fatti diversi, ed e' la differenza su cui la scena col tono
	 *     si giudica. */
	registro_dice(REG_AUDIO,
	              "conto della cura del silenzio (I6 %s): %llu blocchi taciuti "
	              "su %llu entrati, %llu usciti sul filo — codec %u",
	              audio_taci_silenzio ? "ACCESA" : "spenta",
	              (unsigned long long)c->taciuti,
	              (unsigned long long)c->entrati,
	              (unsigned long long)c->usciti, c->codec);
	if (c->pkt)
		av_packet_free(&c->pkt);
	if (c->frame)
		av_frame_free(&c->frame);
	if (c->ctx)
		avcodec_free_context(&c->ctx);
	free(c);
}

uint32_t audio_cod_blocco(const audio_cod *c)
{
	return c ? c->blocco : 0;
}

/* ⛔ Il PCM si scrive LITTLE-endian a mano, non con una `memcpy`.
 *
 *    Una `memcpy` darebbe l'ordine della macchina: giusto su x86, silenziosamente
 *    sbagliato su un ARM big-endian — e il sintomo non e' un errore, e' rumore a
 *    fondo scala.  ⚠ Costa due righe e toglie di mezzo un difetto che si
 *    manifesterebbe solo sull'unica macchina dove nessuno lo prova. */
static void pcm_scrivi(const int16_t *campioni, uint32_t fotogrammi, uint8_t *fuori)
{
	uint32_t n = fotogrammi * AUDIO_CANALI;
	for (uint32_t i = 0; i < n; i++) {
		uint16_t v = (uint16_t)campioni[i];
		fuori[i * 2] = (uint8_t)(v & 0xFF);
		fuori[i * 2 + 1] = (uint8_t)(v >> 8);
	}
}

/* ⛔ Silenzio DIGITALE: tutti i campioni esattamente zero, senza soglie.  ⚠ Il
 *    giro costa `blocco * 2` confronti su interi — 480 per un blocco PCM, 1920
 *    per uno di Opus, cinquanta volte al secondo — ed e' meno lavoro della
 *    `memcpy` che il codificatore fa subito dopo.  ⭐ E si esce al PRIMO
 *    campione diverso da zero: sul suono vero il costo e' una lettura. */
static bool tutto_zero(const int16_t *campioni, uint32_t fotogrammi)
{
	uint32_t n = fotogrammi * AUDIO_CANALI;
	for (uint32_t i = 0; i < n; i++)
		if (campioni[i] != 0)
			return false;
	return true;
}

bool audio_cod_passa(audio_cod *c, const int16_t *campioni, uint8_t *fuori,
                     size_t *quanti)
{
	int e;

	if (!c || !campioni || !fuori || !quanti)
		return false;
	c->entrati++;

	/* ⛔⭐ LA CURA DEL SILENZIO — spenta di suo, e il riquadro sta in cima.
	 *
	 * ⚠ Si torna `false` **prima** del codificatore, ed e' quel che
	 *   `audio.h` promette gia': *«Torna `false` quando non c'e' niente da
	 *   spedire.  Il chiamante non manda niente e va avanti»*.  ⇒ Nessun
	 *   chiamante cambia, e l'`istante` di §6.3 continua ad avanzare da solo
	 *   in `figlio.c` — che e' quel che rende il buco un silenzio al posto
	 *   giusto invece di uno spostamento di tutto quel che segue.
	 *
	 * ⛔ E il `pts` di Opus NON si sposta: libavcodec vedrebbe un salto, e un
	 *    salto e' una cosa che non abbiamo misurato.  Qui il codificatore
	 *    semplicemente non vede quei blocchi. */
	if (audio_taci_silenzio && tutto_zero(campioni, c->blocco)) {
		c->taciuti++;
		/* ⚠ Con un fondo, o un desktop muto riempirebbe il registro invece di
		 *   raccontarlo: la prima e poi una ogni mille (20 s di Opus, 5 di PCM). */
		if (c->taciuti == 1 || c->taciuti % 1000 == 0)
			registro_dice(REG_AUDIO,
			              "⭐ silenzio DIGITALE: %llu blocchi non spediti su "
			              "%llu entrati (I6, cura accesa).  ⚠ Chi riceve vedra' "
			              "un salto di `istante` e lo contera' fra i «mancati»: "
			              "e' un buco VOLUTO, non una perdita",
			              (unsigned long long)c->taciuti,
			              (unsigned long long)c->entrati);
		return false;
	}

	if (c->codec == 2) {
		size_t n = (size_t)c->blocco * AUDIO_CANALI * 2;
		if (n > AUDIO_FUORI_MAX)
			return false;
		pcm_scrivi(campioni, c->blocco, fuori);
		*quanti = n;
		c->usciti++;
		return true;
	}

	if (av_frame_make_writable(c->frame) < 0)
		return false;
	memcpy(c->frame->data[0], campioni,
	       (size_t)AUDIO_BLOCCO_OPUS * AUDIO_CANALI * sizeof(int16_t));
	c->frame->pts = c->pts;
	c->pts += AUDIO_BLOCCO_OPUS;

	e = avcodec_send_frame(c->ctx, c->frame);
	if (e < 0) {
		char m[128];
		av_strerror(e, m, sizeof m);
		registro_dice(REG_AUDIO, "⛔ avcodec_send_frame: %s", m);
		return false;
	}

	e = avcodec_receive_packet(c->ctx, c->pkt);
	if (e == AVERROR(EAGAIN)) {
		/* ⛔ RAMO MISURATO E MAI PERCORSO — `[M]` 17 agosto 2026,
		 *    `banchi/07-b44`: 1000 blocchi dentro, 1000 pacchetti fuori, zero
		 *    EAGAIN.  ⚠ Resta perche' l'API lo ammette, ⭐ ma adesso SI VEDE
		 *    se si percorre: prima tornava `false` in silenzio, e allora
		 *    «Opus accumula» sarebbe stato indistinguibile da «il blocco non
		 *    e' arrivato».  E se un giorno si percorresse, l'`istante` di §6.3
		 *    non apparterrebbe piu' al blocco che parte. */
		if (!c->eagain_detto) {
			c->eagain_detto = true;
			registro_dice(REG_AUDIO,
			              "⛔ libopus ha trattenuto un blocco (EAGAIN) — e "
			              "`banchi/07-b44` dice che non succede mai.  ⚠ Da qui "
			              "in poi l'`istante` di §6.3 puo' non essere quello "
			              "del blocco spedito");
		}
		return false;
	}
	if (e < 0) {
		char m[128];
		av_strerror(e, m, sizeof m);
		registro_dice(REG_AUDIO, "⛔ avcodec_receive_packet: %s", m);
		return false;
	}

	if ((size_t)c->pkt->size > AUDIO_FUORI_MAX) {
		/* ⛔ Non si tronca un pacchetto Opus: un pacchetto monco non e' un
		 *    suono peggiore, e' un pacchetto che il decodificatore rifiuta. */
		registro_dice(REG_AUDIO,
		              "⛔ pacchetto Opus di %d byte, oltre il tetto di %d — "
		              "buttato invece che troncato",
		              c->pkt->size, AUDIO_FUORI_MAX);
		av_packet_unref(c->pkt);
		return false;
	}
	memcpy(fuori, c->pkt->data, (size_t)c->pkt->size);
	*quanti = (size_t)c->pkt->size;
	av_packet_unref(c->pkt);
	c->usciti++;
	return true;
}

void audio_cod_conti(const audio_cod *c, uint64_t *entrati, uint64_t *usciti)
{
	if (entrati)
		*entrati = c ? c->entrati : 0;
	if (usciti)
		*usciti = c ? c->usciti : 0;
}

/* ⛔ Il terzo numero sta a parte e NON dentro `audio_cod_conti()`: quella
 *    funzione ha gia' un chiamante (`webtransport.c:6891`) e cambiarle la
 *    firma vorrebbe dire toccare un file che non e' di questo modulo. */
uint64_t audio_cod_taciuti(const audio_cod *c)
{
	return c ? c->taciuti : 0;
}
