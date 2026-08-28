#include "altoparlante.h"

#include <freerdp/channels/rdpsnd.h>
#include <freerdp/codec/audio.h>
#include <freerdp/server/rdpsnd.h>
#include <string.h>

#include "registro.h"

/*
 * La coda: mezzo secondo abbondante di stereo a 48 kHz.
 *
 * Piu' corta e un ciclo che si ferma per un ridimensionamento — che dura circa
 * mezzo secondo, misurato in fase 6 — produrrebbe un buco nel suono ogni volta
 * che si trascina il bordo della finestra.  Piu' lunga e si accumulerebbe un
 * ritardo che nessuno vuole sentire.
 */
#define ANELLO_BYTE (256 * 1024)

/*
 * ⛔ QUANTO AUDIO IN UN PDU — ed e' la misura che decide se il suono si sente o
 *    scoppietta.  Non e' un dettaglio di efficienza.
 *
 * Il client di FreeRDP butta un blocco quando la sua coda supera
 * `2 * durata_del_blocco + latenza` (`rdpsnd_detect_overrun`, lato client): la
 * tolleranza e' proporzionale alla DURATA DEL BLOCCO CHE STA RICEVENDO.  Un
 * blocco da 5 ms si porta dietro una tolleranza di 10 ms, e viene buttato quasi
 * sempre — mentre uno da 50 ms ne ha 100.
 *
 * Misurato il 5 agosto 2026 col registro del client: su sei secondi di tono,
 * 132 blocchi da 32 ms passavano e **35 blocchi da 5 ms venivano buttati**, uno
 * per uno, con «Buffer overrun pending 27 ms dropping 5 ms».  I blocchi corti
 * nascevano quando il ciclo si svegliava presto — un riscontro, un tasto — e
 * spediva quel poco che c'era nell'anello.
 *
 * Quindi: MAI UN BLOCCO PARZIALE.  E' anche la regola di xrdp, che accumula in
 * un buffer da `g_bbuf_size` (8 192 byte per il PCM) e spedisce solo quando e'
 * pieno (`sound_send_wave_data`); ed e' quel che faceva `SendSamples` di
 * FreeRDP, che accumulava fino a `latency` millisecondi prima di comporre un
 * `WAVE2`.  Passando a `SendSamples2` (R24) quella funzione se n'e' andata, e
 * va rifatta qui.
 */
#define BLOCCO_MS 50

/*
 * Il tetto, per quando si e' in ritardo: se il ciclo si e' fermato e nell'anello
 * si e' accumulato piu' di un blocco, si manda un blocco PIU' GRANDE invece di
 * due di fila.  Due di fila il client li rifiuterebbe — il secondo arriva
 * quando la sua coda e' ancora piena del primo — mentre uno grande porta con se'
 * una tolleranza grande, che e' esattamente quel che serve per recuperare.
 */
#define BLOCCO_MAX_MS 200

/*
 * Oltre questo ritardo nell'anello non si recupera piu' spedendo: si butta il
 * passato e si riparte dal presente.  E' la stessa scelta di xrdp, che quando i
 * riscontri dicono che il client e' rimasto indietro di 250 ms taglia il blocco
 * a un quarto e lo riempie di silenzio (`sound_send_wave_data`), invece di
 * lasciar crescere il ritardo.
 */
#define RITARDO_MASSIMO_MS 500

/*
 * ⛔ QUANTO SILENZIO SI SPEDISCE PRIMA DI TACERE.
 *
 * Il silenzio non si spedisce (si veda piu' sotto), ma smettere al primo blocco
 * muto costa uno STRAPPO a ogni ripresa: il client resta a secco, e quando il
 * suono torna riparte da fermo.  Su un tono continuo non si nota; su una voce,
 * che di pause ne ha una ogni due parole, e' proprio il difetto che si sente.
 *
 * Mezzo secondo di zeri copre le pause del parlato e della musica e costa
 * 88 KB — contro il 1,4 Mbit/s che costerebbe non tacere mai.  Si tace solo
 * quando la sessione e' muta davvero.
 */
#define CODA_SILENZIO_MS 500

/* Il piu' grande blocco possibile: 200 ms a 48 kHz, stereo, 16 bit. */
#define BLOCCO_MAX_BYTE (48u * BLOCCO_MAX_MS * 2u * 2u)

/* Non piu' di un lamento al secondo quando la coda trabocca: se il ciclo e'
 * fermo, il registro non deve diventare il secondo problema. */
#define LAMENTO_OGNI_US (1000 * 1000)

/*
 * La versione del canale da cui esiste il PDU `WAVE2`.
 *
 * Sta scritta a mano perche' FreeRDP la tiene in `rdpsnd_common.h`, che e'
 * privato del canale e non viene installato: la costante pubblica non c'e'.
 * Il valore e' quello di `CHANNEL_VERSION_WIN_8` [R, FreeRDP 3.15,
 * channels/rdpsnd/common/rdpsnd_common.h], ed e' anche la soglia che FreeRDP
 * stessa usa per scegliere fra `WAVE` e `WAVE2`.
 */
#define VERSIONE_WAVE2 0x08

struct Altoparlante
{
	RdpsndServerContext *ctx;
	gboolean avviato;
	uint32_t canale;
	gboolean canale_negato;

	/*
	 * Il formato della SORGENTE, cioe' di quel che si consegna a `SendSamples`.
	 *
	 * E' una copia esatta del formato scelto dal client: PCM a PCM, stessi
	 * hertz e stessi canali, quindi FreeRDP non converte niente e non si dipende
	 * da quali ricampionatori sia stata compilata.  A ricampionare — se serve —
	 * e' PipeWire, fra il monitor del sink e la nostra cattura.
	 *
	 * Vive QUI e non nel contesto perche' `rdpsnd_server_context_free` non lo
	 * libera: il contesto ne tiene solo il puntatore.
	 */
	AUDIO_FORMAT sorgente;
	gint pronto; /* atomico: il formato e' stato scelto */
	uint32_t frequenza;
	uint32_t canali;
	uint32_t byte_per_fotogramma;
	/* Le tre misure del ritmo, in byte, calcolate quando si sa il formato. */
	gsize blocco_byte;   /* il minimo che si spedisce: sotto, si aspetta */
	gsize blocco_max;    /* il massimo in un solo PDU, per recuperare */
	gsize ritardo_max;   /* oltre, si butta il passato */
	/* L'indice, nell'elenco del client, del formato scelto: va in ogni PDU. */
	UINT16 indice_formato;
	/* Vero quando si spedisce con `SendSamples2`, cioe' saltando il DSP di
	 * FreeRDP.  Si veda il commento in `altoparlante_passo`. */
	gboolean senza_dsp;

	GMutex lucchetto;
	uint8_t *anello;
	/* Il blocco che si sta componendo per il canale.  Sta qui e non sulla pila
	 * perche' con i 200 ms del tetto sarebbero quarantamila byte a ogni giro del
	 * ciclo. */
	uint8_t *blocco;
	gsize inizio; /* primo byte pieno */
	gsize quanti; /* byte pieni */
	guint64 spediti;
	guint64 blocchi; /* quanti PDU: e' il numero che dice se il ritmo e' sano */
	guint64 scartati;
	guint64 taciuti;
	/* Quanti byte di silenzio di fila si sono gia' spediti.  Oltre la coda si
	 * tace, e si riparte a contare al primo suono. */
	gsize silenzio_byte;
	gsize coda_silenzio; /* la coda, in byte, del formato negoziato */
	/* Atomico e non sotto lucchetto: lo incrementa il thread del canale e lo
	 * legge quello della connessione, e per un contatore non serve altro. */
	gint riscontrati;

	/*
	 * ⛔ IL VIAGGIO DEI RISCONTRI, che e' l'unica cosa che sappiamo dell'altro
	 *    capo.
	 *
	 * La nostra coda dice se il CICLO e' in ritardo; non dice niente se a
	 * riempirsi e' la coda del canale o il buffer del client — rete lenta invece
	 * che ciclo lento.  Il ritardo fra «spedito il blocco n» e «il client
	 * riscontra il blocco n» invece lo dice, ed e' il segnale con cui xrdp
	 * regola il suo flusso (§8.3.1 di xrdp-funzionalita.md).
	 *
	 * Qui si MISURA soltanto, e si scrive nel registro accanto agli altri numeri
	 * grezzi: regolare su un numero che non si e' mai guardato sarebbe indovinare.
	 *
	 * L'istante si scrive dal thread della connessione e si legge da quello del
	 * canale, sotto lo stesso lucchetto della coda: sono due letture corte.
	 * Un blocco riscontrato due volte — i client di FreeRDP lo fanno — conta una
	 * volta sola, perche' l'istante si azzera al primo.
	 */
	gint64 istante_blocco[256];
	guint riscontri_misurati;
	gint64 ritardo_somma_us;
	gint64 ritardo_min_us;
	gint64 ritardo_max_us;
	gint64 ultimo_lamento_us;
	gint64 ultimo_riassunto_us;
};

/* ------------------------------------------------------------------ *
 * La scelta del formato
 * ------------------------------------------------------------------ */
/*
 * Quanto ci piace un formato offerto dal client.  Zero significa «non lo so
 * produrre».
 *
 * Si accetta il solo PCM a 16 bit, ed e' una scelta con una misura dietro: ne'
 * mstsc ne' RDM hanno mai dichiarato AAC o Opus (§1.5 di REFERENCE.md), quindi
 * il resto sarebbe codice scritto per nessuno finche' la questione n.8 non dice
 * altro.  Fra i PCM si preferisce lo stereo, e poi la frequenza piu' vicina a
 * 44 100 — che e' quella che i client offrono sempre.
 */
static guint punteggio(const AUDIO_FORMAT *formato)
{
	guint punti;

	if (formato->wFormatTag != WAVE_FORMAT_PCM)
		return 0;
	if (formato->wBitsPerSample != 16)
		return 0;
	if (formato->nChannels != 1 && formato->nChannels != 2)
		return 0;
	if (formato->nSamplesPerSec < 8000 || formato->nSamplesPerSec > 48000)
		return 0;

	punti = formato->nChannels == 2 ? 1000 : 100;
	if (formato->nSamplesPerSec == 44100)
		punti += 500;
	else if (formato->nSamplesPerSec == 48000)
		punti += 400;
	else
		punti += formato->nSamplesPerSec / 1000;
	return punti;
}

/*
 * Che cosa il client dichiara di saper decodificare.
 *
 * ⛔ QUESTO NON CHIUDE LA QUESTIONE n.8 (l'AAC serve a qualcuno?), e conviene
 *    dirlo qui perche' il registro sembra rispondere e non risponde: il client
 *    replica con il SOTTOINSIEME dei formati che gli abbiamo offerto noi.
 *    Offrendo solo PCM, «AAC no» significa soltanto che non gliel'abbiamo
 *    chiesto.  Per rispondere davvero bisogna ANNUNCIARE l'AAC e guardare se
 *    qualcuno lo sceglie — ed e' la voce 3 della fase 8, non questa.
 *
 * Si scrive a livello «informazione» e non «diagnostica» apposta: quando un
 * giorno l'audio non si sentira' su un client, la prima domanda sara' «che cosa
 * aveva dichiarato», e deve stare nel registro di una sessione normale.
 */
static void racconta_formati(const RdpsndServerContext *ctx)
{
	gboolean aac = FALSE, opus = FALSE, pcm = FALSE;
	GString *elenco = g_string_new(NULL);

	for (UINT16 i = 0; i < ctx->num_client_formats; i++)
	{
		const AUDIO_FORMAT *f = &ctx->client_formats[i];

		switch (f->wFormatTag)
		{
			case WAVE_FORMAT_PCM:
				pcm = TRUE;
				break;
			case 0xA106: /* WAVE_FORMAT_AAC_MS */
				aac = TRUE;
				break;
			case 0x704F: /* WAVE_FORMAT_OPUS   */
				opus = TRUE;
				break;
			default:
				break;
		}
		g_string_append_printf(elenco, "%s0x%04X %u Hz %u ch %u bit", i ? ", " : "", f->wFormatTag,
		                       f->nSamplesPerSec, f->nChannels, f->wBitsPerSample);
	}

	informazione("formati audio del client: %u — AAC %s, Opus %s, PCM %s", ctx->num_client_formats,
	             aac ? "SI" : "no", opus ? "SI" : "no", pcm ? "SI" : "no");
	diagnostica("formati audio, uno per uno: %s", elenco->str);
	g_string_free(elenco, TRUE);
}

/*
 * Il client e' pronto.
 *
 * ⛔ GIRA SUL THREAD DEL CANALE, e arriva col Quality Mode PDU, non con i
 *    formati (R21).  Qui si sceglie il formato e si dichiara la sorgente; ad
 *    accendere la cattura sara' il ciclo della connessione, che se ne accorge
 *    guardando `altoparlante_formato` — perche' aprire un flusso PipeWire da
 *    dentro una richiamata di FreeRDP significherebbe far aspettare il canale.
 */
static void su_attivato(RdpsndServerContext *ctx)
{
	Altoparlante *altoparlante = ctx->data;
	const AUDIO_FORMAT *scelto = NULL;
	UINT16 indice = 0;
	guint migliore = 0;

	racconta_formati(ctx);

	for (UINT16 i = 0; i < ctx->num_client_formats; i++)
	{
		guint punti = punteggio(&ctx->client_formats[i]);

		if (punti > migliore)
		{
			migliore = punti;
			indice = i;
			scelto = &ctx->client_formats[i];
		}
	}

	if (!scelto)
	{
		avviso("nessun formato audio in comune con il client: la sessione resta muta");
		return;
	}

	/* La sorgente e' il formato scelto, identico: cosi' non c'e' nulla da
	 * convertire.  `cbSize` e `data` si azzerano — sono la coda variabile del
	 * formato, e di quella il client non ci ha dato la proprieta'. */
	altoparlante->sorgente = *scelto;
	altoparlante->sorgente.cbSize = 0;
	altoparlante->sorgente.data = NULL;

	ctx->src_format = &altoparlante->sorgente;
	/* Serve solo al percorso `SendSamples`, che non usiamo (R24); si dichiara
	 * lo stesso, perche' se un giorno ci si ricadesse dentro deve trovare un
	 * valore sensato invece dei cinquanta di FreeRDP presi per caso. */
	ctx->latency = BLOCCO_MS;
	if (ctx->SelectFormat(ctx, indice) != CHANNEL_RC_OK)
	{
		errore("il formato audio %u non e' stato accettato dal canale", indice);
		return;
	}

	/*
	 * Il volume si dichiara: un client a cui il server non dice niente parte con
	 * quello che si e' scelto da solo, e non e' detto che sia «tutto e basta».
	 *
	 * ⚠ NON E' QUESTA la correzione della distorsione del 5 agosto, per quanto
	 *   ci sia stata attribuita per mezza giornata: quella era il DSP di FreeRDP
	 *   che ribaltava il segno dei campioni, e si corregge in
	 *   `altoparlante_passo`.  La riga resta perche' e' giusta lo stesso, ma
	 *   attribuirle un merito che non ha e' il modo di riaprire la stessa caccia
	 *   fra sei mesi.
	 */
	if (ctx->SetVolume(ctx, 0xFFFF, 0xFFFF) != CHANNEL_RC_OK)
		avviso("volume audio non dichiarato: il client usera' il proprio");

	altoparlante->frequenza = scelto->nSamplesPerSec;
	altoparlante->canali = scelto->nChannels;
	altoparlante->byte_per_fotogramma = 2u * scelto->nChannels;
	altoparlante->indice_formato = indice;

	/* Le misure del ritmo, in byte, adesso che si sa a che velocita' scorre il
	 * suono.  L'arrotondamento al fotogramma intero e' quello che impedisce a un
	 * canale di scambiarsi con l'altro. */
	{
		gsize al_millisecondo = (gsize) scelto->nSamplesPerSec * altoparlante->byte_per_fotogramma
		                        / 1000u;

		altoparlante->blocco_byte = al_millisecondo * BLOCCO_MS;
		altoparlante->blocco_max = MIN((gsize) BLOCCO_MAX_BYTE, al_millisecondo * BLOCCO_MAX_MS);
		altoparlante->ritardo_max = al_millisecondo * RITARDO_MASSIMO_MS;
		altoparlante->coda_silenzio = al_millisecondo * CODA_SILENZIO_MS;
		altoparlante->blocco_byte -= altoparlante->blocco_byte % altoparlante->byte_per_fotogramma;
		altoparlante->blocco_max -= altoparlante->blocco_max % altoparlante->byte_per_fotogramma;
	}

	/*
	 * Si spedisce senza DSP se il client capisce il `WAVE2`, cioe' sempre, per i
	 * tre client di riferimento.  La soglia e' la stessa che usa FreeRDP per
	 * scegliere fra `WAVE` e `WAVE2`, quindi qui non si sta indovinando: sotto la
	 * soglia `SendSamples2` rifiuterebbe con `ERROR_INTERNAL_ERROR`.
	 */
	altoparlante->senza_dsp = ctx->clientVersion >= VERSIONE_WAVE2;

	informazione("audio negoziato: PCM %u Hz, %u canali, 16 bit (formato %u di %u), "
	             "versione del canale %u — %s",
	             scelto->nSamplesPerSec, scelto->nChannels, indice, ctx->num_client_formats,
	             ctx->clientVersion,
	             altoparlante->senza_dsp ? "WAVE2 senza DSP" : "WAVE con il DSP di FreeRDP");

	if (!altoparlante->senza_dsp)
		avviso("il client e' troppo vecchio per il WAVE2: i campioni passano dal DSP di "
		       "FreeRDP, che sul PCM a 16 bit ribalta il segno — il suono sara' rumore");

	/* Ultimo, e con la barriera che l'atomica porta con se': chi legge `pronto`
	 * vero deve trovare gia' scritti frequenza, canali e byte per fotogramma. */
	g_atomic_int_set(&altoparlante->pronto, 1);
}

/*
 * Il client ha riscontrato un blocco.
 *
 * ⛔ E' LA SOLA PROVA CHE L'AUDIO E' ARRIVATO DALL'ALTRA PARTE, ed e' il motivo
 *    per cui si contano.  Dal lato server, «spediti» significa soltanto «messi
 *    in coda e scritti»: un canale che il client ignora produce lo stesso
 *    numero di un canale che funziona.  I riscontri no — quelli li manda lui.
 *
 * Gira sul thread del canale: qui si conta, e basta.
 */
static UINT su_blocco_riscontrato(RdpsndServerContext *ctx, BYTE blocco, UINT16 orario)
{
	Altoparlante *altoparlante = ctx->data;
	gint64 partito;

	g_atomic_int_inc(&altoparlante->riscontrati);

	/* Il viaggio del blocco, se e' il PRIMO riscontro che ne arriva. */
	g_mutex_lock(&altoparlante->lucchetto);
	partito = altoparlante->istante_blocco[blocco];
	if (partito > 0)
	{
		gint64 viaggio = g_get_monotonic_time() - partito;

		altoparlante->istante_blocco[blocco] = 0;
		altoparlante->riscontri_misurati++;
		altoparlante->ritardo_somma_us += viaggio;
		if (viaggio > altoparlante->ritardo_max_us)
			altoparlante->ritardo_max_us = viaggio;
		if (altoparlante->ritardo_min_us == 0 || viaggio < altoparlante->ritardo_min_us)
			altoparlante->ritardo_min_us = viaggio;
	}
	g_mutex_unlock(&altoparlante->lucchetto);

	traccia("blocco audio %u riscontrato dal client", blocco);
	return CHANNEL_RC_OK;
}

static BOOL su_canale_assegnato(RdpsndServerContext *ctx, UINT32 id_canale)
{
	Altoparlante *altoparlante = ctx->data;

	altoparlante->canale = id_canale;
	diagnostica("canale audio: identificativo %u", id_canale);
	return TRUE;
}

/* ------------------------------------------------------------------ *
 * Ciclo di vita
 * ------------------------------------------------------------------ */
Altoparlante *altoparlante_apri(HANDLE vcm, rdpContext *contesto)
{
	Altoparlante *altoparlante = g_new0(Altoparlante, 1);
	AUDIO_FORMAT *nostri;

	g_mutex_init(&altoparlante->lucchetto);
	altoparlante->anello = g_malloc(ANELLO_BYTE);
	altoparlante->blocco = g_malloc(BLOCCO_MAX_BYTE);

	altoparlante->ctx = rdpsnd_server_context_new(vcm);
	if (!altoparlante->ctx)
	{
		errore("rdpsnd_server_context_new fallita");
		goto guasto;
	}

	altoparlante->ctx->data = altoparlante;
	altoparlante->ctx->rdpcontext = contesto;
	altoparlante->ctx->Activated = su_attivato;
	altoparlante->ctx->ChannelIdAssigned = su_canale_assegnato;
	altoparlante->ctx->ConfirmBlock = su_blocco_riscontrato;
	altoparlante->ctx->use_dynamic_virtual_channel = TRUE;
	altoparlante->ctx->latency = BLOCCO_MS;

	/*
	 * I formati che il server dichiara di saper produrre.
	 *
	 * L'elenco DELIMITA la risposta del client, che risponde con quelli che sa
	 * decodificare fra questi: dichiararne uno solo significherebbe scoprire
	 * troppo tardi che quel client non lo vuole.  Si allocano con
	 * `audio_formats_new` perche' e' `free()` a liberarli dentro FreeRDP.
	 */
	nostri = audio_formats_new(3);
	if (!nostri)
	{
		errore("formati audio non allocati");
		goto guasto;
	}
	{
		static const UINT32 frequenze[3] = { 48000, 44100, 22050 };

		for (gsize i = 0; i < 3; i++)
		{
			nostri[i].wFormatTag = WAVE_FORMAT_PCM;
			nostri[i].nChannels = 2;
			nostri[i].nSamplesPerSec = frequenze[i];
			nostri[i].wBitsPerSample = 16;
			nostri[i].nBlockAlign = 4; /* canali x byte per campione */
			nostri[i].nAvgBytesPerSec = frequenze[i] * 4;
			nostri[i].cbSize = 0;
			nostri[i].data = NULL;
		}
	}
	altoparlante->ctx->server_formats = nostri;
	altoparlante->ctx->num_server_formats = 3;

	/* R21 — questa apre il canale E manda i formati: non c'e' altro da
	 * chiamare.  Con TRUE si prende un thread suo, che e' quello su cui
	 * arrivera' `Activated`. */
	if (altoparlante->ctx->Initialize(altoparlante->ctx, TRUE) != CHANNEL_RC_OK)
	{
		errore("apertura del canale audio fallita");
		goto guasto;
	}
	altoparlante->avviato = TRUE;
	diagnostica("canale audio aperto, aspetto che il client dichiari i formati");
	return altoparlante;

guasto:
	altoparlante_chiudi(altoparlante);
	return NULL;
}

void altoparlante_chiudi(Altoparlante *altoparlante)
{
	if (!altoparlante)
		return;

	/* `rdpsnd_server_context_free` ferma il thread del canale e lo aspetta:
	 * dopo di qui nessuna richiamata puo' piu' toccarci. */
	if (altoparlante->ctx)
		rdpsnd_server_context_free(altoparlante->ctx);

	g_mutex_clear(&altoparlante->lucchetto);
	g_free(altoparlante->anello);
	g_free(altoparlante->blocco);
	g_free(altoparlante);
}

uint32_t altoparlante_canale(const Altoparlante *altoparlante)
{
	return altoparlante ? altoparlante->canale : 0;
}

void altoparlante_esito_canale(Altoparlante *altoparlante, int esito)
{
	if (!altoparlante)
		return;
	if (esito >= 0)
		return;

	/*
	 * Il client non ha voluto il canale.  Non e' un guasto: e' una sessione
	 * senza suono, cioe' quel che REMOTIX faceva fino alla fase 7.  Si degrada
	 * e si dichiara (§2 di SPECIFICA.md).
	 */
	avviso("il client non ha aperto il canale audio (esito %d): niente suono per questa sessione",
	       esito);
	altoparlante->canale_negato = TRUE;
	g_atomic_int_set(&altoparlante->pronto, 0);
}

gboolean altoparlante_formato(Altoparlante *altoparlante, uint32_t *frequenza, uint32_t *canali)
{
	if (!altoparlante || !g_atomic_int_get(&altoparlante->pronto))
		return FALSE;
	if (frequenza)
		*frequenza = altoparlante->frequenza;
	if (canali)
		*canali = altoparlante->canali;
	return TRUE;
}

/* ------------------------------------------------------------------ *
 * La coda
 * ------------------------------------------------------------------ */
void altoparlante_campioni(const int16_t *campioni, uint32_t fotogrammi, gpointer dati)
{
	Altoparlante *altoparlante = dati;
	const uint8_t *sorgente = (const uint8_t *) campioni;
	/* Non si chiama `byte`: WinPR ha un typedef con quel nome, e -Wshadow lo
	 * segnala giustamente. */
	gsize quanti_byte;
	gsize scrivi;

	if (!altoparlante || !g_atomic_int_get(&altoparlante->pronto) || fotogrammi == 0)
		return;

	quanti_byte = (gsize) fotogrammi * altoparlante->byte_per_fotogramma;

	g_mutex_lock(&altoparlante->lucchetto);

	/* Un blocco piu' grande dell'intera coda: se ne tiene la CODA, cioe' la
	 * parte piu' recente.  Non succede con i quanti di PipeWire, ma un ramo che
	 * scrive oltre la fine dell'anello non e' una cosa da lasciare in giro. */
	if (quanti_byte > ANELLO_BYTE)
	{
		sorgente += quanti_byte - ANELLO_BYTE;
		altoparlante->scartati += (quanti_byte - ANELLO_BYTE) / altoparlante->byte_per_fotogramma;
		quanti_byte = ANELLO_BYTE;
	}

	/* Si buttano i PIU' VECCHI: il suono in ritardo non serve a nessuno. */
	if (altoparlante->quanti + quanti_byte > ANELLO_BYTE)
	{
		gsize troppi = altoparlante->quanti + quanti_byte - ANELLO_BYTE;
		gint64 adesso = g_get_monotonic_time();

		altoparlante->inizio = (altoparlante->inizio + troppi) % ANELLO_BYTE;
		altoparlante->quanti -= troppi;
		altoparlante->scartati += troppi / altoparlante->byte_per_fotogramma;

		if (adesso - altoparlante->ultimo_lamento_us > LAMENTO_OGNI_US)
		{
			altoparlante->ultimo_lamento_us = adesso;
			avviso("coda audio piena: buttati %" G_GUINT64_FORMAT
			       " fotogrammi in tutto — il ciclo non svuota abbastanza in fretta",
			       altoparlante->scartati);
		}
	}

	scrivi = (altoparlante->inizio + altoparlante->quanti) % ANELLO_BYTE;
	{
		gsize fino_in_fondo = MIN(quanti_byte, (gsize) ANELLO_BYTE - scrivi);

		memcpy(altoparlante->anello + scrivi, sorgente, fino_in_fondo);
		if (quanti_byte > fino_in_fondo)
			memcpy(altoparlante->anello, sorgente + fino_in_fondo, quanti_byte - fino_in_fondo);
	}
	altoparlante->quanti += quanti_byte;

	g_mutex_unlock(&altoparlante->lucchetto);
}

/*
 * Silenzio digitale: tutti zeri.
 *
 * Il confronto e' esatto e non a soglia, ed e' voluto: quel che arriva da un
 * sink virtuale a riposo sono zeri veri, mentre un suono molto piano e' roba
 * dell'utente e va spedita.  Una soglia trasformerebbe la correzione di un
 * difetto in una censura.
 */
static gboolean muto(const uint8_t *blocco, gsize quanti)
{
	const int16_t *campioni = (const int16_t *) blocco;

	for (gsize i = 0; i < quanti / sizeof(int16_t); i++)
	{
		if (campioni[i] != 0)
			return FALSE;
	}
	return TRUE;
}

/*
 * Il riassunto periodico, e ha lo stesso scopo di quello della rete: dice i
 * numeri GREZZI accanto al risultato, perche' e' il loro rapporto a distinguere
 * un canale che funziona da uno che gira a vuoto.  Spediti senza riscontri
 * significa che il client non ascolta; coda sempre piena significa che il ciclo
 * non svuota.
 */
static void riassumi(Altoparlante *altoparlante)
{
	gint64 adesso = g_get_monotonic_time();
	gsize in_coda;
	guint misurati;
	double medio_ms = 0.0, min_ms = 0.0, max_ms = 0.0;

	if (adesso - altoparlante->ultimo_riassunto_us < 5 * G_USEC_PER_SEC)
		return;
	altoparlante->ultimo_riassunto_us = adesso;

	g_mutex_lock(&altoparlante->lucchetto);
	in_coda = altoparlante->quanti;
	/* Il viaggio dei riscontri si racconta a finestre di cinque secondi, e poi
	 * si azzera: una media da inizio sessione nasconderebbe proprio le raffiche
	 * che si stanno cercando. */
	misurati = altoparlante->riscontri_misurati;
	if (misurati > 0)
	{
		medio_ms = (double) altoparlante->ritardo_somma_us / misurati / 1000.0;
		min_ms = altoparlante->ritardo_min_us / 1000.0;
		max_ms = altoparlante->ritardo_max_us / 1000.0;
	}
	altoparlante->riscontri_misurati = 0;
	altoparlante->ritardo_somma_us = 0;
	altoparlante->ritardo_min_us = 0;
	altoparlante->ritardo_max_us = 0;
	g_mutex_unlock(&altoparlante->lucchetto);

	/* ⚠ Il testo di questa riga lo LEGGE il banco (`prove/fase8.sh`): «N blocchi
	 *   riscontrati» e «N di silenzio taciuto» sono ganci, non prosa.  Cambiarli
	 *   non rompe niente che si veda — il banco riporta zero e accusa il server
	 *   di un difetto che non ha.  Costato un giro, il 5 agosto 2026. */
	diagnostica("audio: %" G_GUINT64_FORMAT " fotogrammi in %" G_GUINT64_FORMAT
	            " blocchi spediti, %d blocchi riscontrati dal client, %" G_GUINT64_FORMAT
	            " di silenzio taciuto, %" G_GUINT64_FORMAT " buttati, in coda %" G_GSIZE_FORMAT
	            " byte",
	            altoparlante->spediti, altoparlante->blocchi,
	            g_atomic_int_get(&altoparlante->riscontrati), altoparlante->taciuti,
	            altoparlante->scartati, in_coda);

	/*
	 * ⛔ IL NUMERO CHE PARLA DELLA RETE, e va letto insieme agli altri.
	 *
	 * Un viaggio breve e regolare dice che il client sta al passo.  Un MASSIMO
	 * molto piu' grande della media dice che ogni tanto resta indietro — ed e'
	 * la forma che ha il micro-stutter quando non nasce da noi.  Xrdp regola
	 * proprio su questo scarto: media corrente contro la migliore mai vista
	 * (§8.3.1 di xrdp-funzionalita.md).
	 */
	if (misurati > 0)
		diagnostica("audio, viaggio dei riscontri su %u blocchi: minimo %.0f ms, medio %.0f ms, "
		            "MASSIMO %.0f ms",
		            misurati, min_ms, medio_ms, max_ms);
}

/*
 * ⛔ UN SOLO BLOCCO PER GIRO, E MAI PARZIALE.
 *
 * Le due regole vengono dalla stessa misura (si veda `BLOCCO_MS`): il client
 * butta i blocchi corti, e butta anche il secondo di due spediti di fila —
 * perche' quando arriva la sua coda e' ancora piena del primo.  Non e' una
 * limitazione: il suono arriva in tempo reale, quindi un blocco da 50 ms si
 * riempie ogni 50 ms, e il ciclo passa di qui ogni 33.  Chi ha da spedire due
 * blocchi e' in ritardo, e allora ne spedisce UNO PIU' GRANDE.
 */
void altoparlante_passo(Altoparlante *altoparlante)
{
	if (!altoparlante || !g_atomic_int_get(&altoparlante->pronto))
		return;

	riassumi(altoparlante);

	while (TRUE)
	{
		uint8_t *blocco = altoparlante->blocco;
		gsize presi = 0;
		uint32_t fotogrammi;
		UINT16 orario;
		UINT esito;

		g_mutex_lock(&altoparlante->lucchetto);

		/* Non c'e' un blocco intero: si aspetta il prossimo giro.  E' QUI che si
		 * evita di spedire i cinque millisecondi che il client rifiuterebbe. */
		if (altoparlante->quanti < altoparlante->blocco_byte)
		{
			g_mutex_unlock(&altoparlante->lucchetto);
			return;
		}

		/*
		 * Troppo indietro: si butta il passato e si riparte dal presente.
		 * Spedirlo non servirebbe — il client lo rifiuterebbe comunque — e
		 * intanto il ritardo fra quel che si vede e quel che si sente crescerebbe
		 * senza tornare piu' indietro.
		 */
		if (altoparlante->quanti > altoparlante->ritardo_max)
		{
			gsize troppi = altoparlante->quanti - altoparlante->blocco_max;
			gint64 adesso = g_get_monotonic_time();

			altoparlante->inizio = (altoparlante->inizio + troppi) % ANELLO_BYTE;
			altoparlante->quanti -= troppi;
			altoparlante->scartati += troppi / altoparlante->byte_per_fotogramma;

			if (adesso - altoparlante->ultimo_lamento_us > LAMENTO_OGNI_US)
			{
				altoparlante->ultimo_lamento_us = adesso;
				avviso("audio in ritardo di oltre %d ms: butto il passato e riparto dal presente "
				       "(%" G_GUINT64_FORMAT " fotogrammi buttati in tutto)",
				       RITARDO_MASSIMO_MS, altoparlante->scartati);
			}
		}

		presi = MIN(altoparlante->quanti, altoparlante->blocco_max);
		/* Solo fotogrammi interi: mezzo campione spedito sarebbe un canale
		 * scambiato con l'altro da li' in avanti. */
		presi -= presi % altoparlante->byte_per_fotogramma;
		{
			gsize fino_in_fondo = MIN(presi, (gsize) ANELLO_BYTE - altoparlante->inizio);

			memcpy(blocco, altoparlante->anello + altoparlante->inizio, fino_in_fondo);
			if (presi > fino_in_fondo)
				memcpy(blocco + fino_in_fondo, altoparlante->anello, presi - fino_in_fondo);
			altoparlante->inizio = (altoparlante->inizio + presi) % ANELLO_BYTE;
			altoparlante->quanti -= presi;
		}
		g_mutex_unlock(&altoparlante->lucchetto);

		fotogrammi = (uint32_t) (presi / altoparlante->byte_per_fotogramma);

		/*
		 * Lo specchio del banco: con `REMOTIX_SUONO_COPIA=<file>` si scrive su
		 * disco esattamente quel che si consegna al canale.
		 *
		 * Serve a rispondere alla sola domanda che conta quando l'audio arriva
		 * sbagliato — «lo mandiamo storto noi, o si storce dopo?» — e senza di
		 * essa il sospetto resta diviso fra tre strati che non si vedono.
		 */
		{
			const char *copia = g_getenv("REMOTIX_SUONO_COPIA");

			if (copia && *copia)
			{
				FILE *f = fopen(copia, "ab");

				if (f)
				{
					fwrite(blocco, 1, presi, f);
					fclose(f);
				}
			}
		}

		/*
		 * ⛔ IL SILENZIO NON SI SPEDISCE, e questa non e' un'ottimizzazione: e'
		 *    la correzione di un difetto che il banco ha trovato al primo giro.
		 *
		 * Il monitor di un sink virtuale NON TACE MAI.  Il nodo ha un suo
		 * orologio e produce campioni comunque, anche quando nessuna
		 * applicazione sta suonando: senza questo controllo REMOTIX spediva
		 * 220 000 fotogrammi ogni cinque secondi — cioe' 1,4 Mbit/s, il 14% del
		 * budget di §3.1 di SPECIFICA.md — di zeri, per tutta la durata della
		 * sessione. [M, 5 agosto 2026]
		 *
		 * ⚠ Ma non si smette al primo blocco muto, e questa e' la correzione del
		 *   5 agosto sera: si spedisce silenzio per CODA_SILENZIO_MS, e solo dopo
		 *   si tace.  Smettere subito costava uno strappo a ogni ripresa — misurato
		 *   sulle giunture fra due toni, e sul parlato sarebbe a ogni pausa.
		 */
		if (muto(blocco, presi))
		{
			if (altoparlante->silenzio_byte >= altoparlante->coda_silenzio)
			{
				altoparlante->taciuti += fotogrammi;
				continue;
			}
			altoparlante->silenzio_byte += presi;
		}
		else
		{
			altoparlante->silenzio_byte = 0;
		}
		/* Il marcatore temporale del protocollo e' a 16 bit e in millisecondi:
		 * gira ogni 65 secondi, ed e' previsto che giri. */
		orario = (UINT16) (g_get_monotonic_time() / 1000);

		/*
		 * ⛔ SI SPEDISCE CON `SendSamples2`, CHE NON PASSA DAL DSP DI FreeRDP.
		 *    E' la correzione della questione n.10 — «l'audio esce come rumore su
		 *    tutti e tre i client» — e la ragione va scritta per intero, perche'
		 *    la riga qui sotto sembra una scelta di gusto e non lo e'.
		 *
		 * `SendSamples` fa passare i campioni da `freerdp_dsp_encode`.  Su una
		 * FreeRDP compilata con `WITH_DSP_FFMPEG=ON` — cioe' quella di Debian,
		 * cioe' la nostra — quella funzione manda il PCM a 16 bit al
		 * codificatore FFmpeg `AV_CODEC_ID_PCM_U16LE`: il PCM a 16 bit di RDP e'
		 * CON SEGNO, quello di FFmpeg e' SENZA, e la conversione somma 0x8000 a
		 * ogni campione, cioe' ne ribalta il bit di segno.
		 *
		 * Misurato con `banco-b/spia-dsp.c`, che chiama la sola `freerdp_dsp_encode`
		 * su un seno noto: dentro picco 2999 e rms 2121, fuori picco 32768 e rms
		 * 30872, e 8820 campioni su 8820 sono l'originale con il segno ribaltato.
		 * All'orecchio e' esattamente quel che si sentiva: rumore a fondo scala
		 * che segue la frequenza giusta. [M, 5 agosto 2026]
		 *
		 * `SendSamples2` scrive un `WAVE2` con i byte cosi' come sono
		 * (`encoded = TRUE`), e per noi non e' un aggiramento: la sorgente E' il
		 * formato scelto dal client, quindi non c'e' niente da convertire e il
		 * DSP era comunque di troppo.  Il prezzo e' che la spezzettatura la
		 * facciamo noi — ma la facevamo gia', qui sopra, con l'anello.
		 */
		if (altoparlante->senza_dsp)
			esito = altoparlante->ctx->SendSamples2(altoparlante->ctx,
			                                        altoparlante->indice_formato, blocco, presi,
			                                        orario, (UINT32) orario);
		else
			esito = altoparlante->ctx->SendSamples(altoparlante->ctx, blocco, fotogrammi, orario);

		if (esito != CHANNEL_RC_OK)
		{
			/*
			 * Non e' un motivo per chiudere la connessione: il video vale piu'
			 * dell'audio, e un canale audio che si lamenta non deve portarsi
			 * dietro il desktop.  Si spegne il suono e si dichiara.
			 */
			avviso("invio dei campioni fallito: spengo l'audio per questa sessione");
			g_atomic_int_set(&altoparlante->pronto, 0);
			return;
		}
		altoparlante->spediti += fotogrammi;
		altoparlante->blocchi++;

		/*
		 * Si annota l'istante di partenza sotto il numero del blocco appena
		 * spedito.  `block_no` e' gia' stato incrementato da FreeRDP, quindi il
		 * blocco che se n'e' andato porta il numero precedente.
		 */
		g_mutex_lock(&altoparlante->lucchetto);
		altoparlante->istante_blocco[(altoparlante->ctx->block_no + 255) % 256] =
		    g_get_monotonic_time();
		g_mutex_unlock(&altoparlante->lucchetto);
		/* Uno per giro: il resto aspetta il prossimo, e in tempo reale non c'e'
		 * resto. */
		return;
	}
}

void altoparlante_conti(const Altoparlante *altoparlante, guint64 *spediti, guint64 *scartati,
                        guint64 *riscontrati, guint64 *taciuti)
{
	if (!altoparlante)
		return;
	if (spediti)
		*spediti = altoparlante->spediti;
	if (scartati)
		*scartati = altoparlante->scartati;
	if (riscontrati)
		*riscontrati = (guint64) g_atomic_int_get(&altoparlante->riscontrati);
	if (taciuti)
		*taciuti = altoparlante->taciuti;
}
