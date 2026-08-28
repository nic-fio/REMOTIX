#include "rete.h"

#include <freerdp/autodetect.h>
#include <freerdp/channels/rdpgfx.h>

#include "registro.h"

/*
 * Le due cadenze delle sonde, dal riferimento (§10.1 di
 * gnome-remote-desktop.md, e §16 di protocollo-rdp.md).
 *
 * Alta quando la pipeline grafica sta lavorando — li' l'RTT serve subito, ed e'
 * quello che decide quanti fotogrammi si possono tenere in volo.  Bassa a
 * riposo: un desktop fermo non ha niente da regolare, e una sonda ogni 70 ms
 * per ore sarebbe traffico speso per niente.
 */
#define CADENZA_ALTA_MS  70
#define CADENZA_BASSA_MS 700

/* «Sta lavorando» = ha spedito un fotogramma nell'ultimo secondo. */
#define ATTIVITA_US (1000 * 1000)

/* La finestra su cui si fa la media dell'RTT.  Mezzo secondo: abbastanza da
 * smussare il singolo pacchetto sfortunato, poco da seguire una rete che
 * peggiora. */
#define FINESTRA_RTT_US (500 * 1000)

/*
 * Sotto i 10 KB la misura di banda e' rumore (§16).
 *
 * Il conto e' immediato: il client misura il tempo con `GetTickCount64`, cioe'
 * a millisecondi interi.  Un fotogramma da 2 KB su una rete qualunque parte e
 * arriva dentro lo stesso millisecondo, il tempo trascorso risulta zero, e la
 * banda stimata diventa un numero senza senso.
 */
#define BANDA_MINIMA_BYTE (10 * 1024)

/* Non si informa il client piu' di una volta al secondo. */
#define NETCHAR_OGNI_US (1000 * 1000)

/* Quanto spesso il registro racconta come sta andando. */
#define RIASSUNTO_OGNI_US (2000 * 1000)

/*
 * Il numero di sequenza ZERO e' riservato alla misura di banda.
 *
 * Non e' una convenzione del protocollo ma del riferimento, e conviene
 * copiarla: la banda ha una misura sola per volta, quindi le basta un numero
 * fisso, e tenerlo fuori dai numeri delle sonde evita di dover distinguere «la
 * risposta a quale cosa» quando arrivano insieme.
 */
#define NUMERO_BANDA 0

/*
 * Quante sonde si tollerano senza risposta prima di dichiarare che il client
 * non risponde piu'.
 *
 * Il riferimento usa 16384, che a 70 ms sono venti minuti: una soglia che non
 * scatta mai serve solo a non traboccare.  Qui bastano poche decine — a
 * cadenza alta sono un paio di secondi di silenzio — perche' la tabella e' un
 * anello e non una hash: se trabocca, si perde l'accoppiamento e la misura
 * dell'RTT diventa una bugia invece che un buco.
 */
#define SONDE_MASSIME 48

/* I campioni nella finestra: a 70 ms in mezzo secondo sono otto. Trentadue e'
 * gia' quattro volte il necessario. */
#define CAMPIONI_MASSIMI 32

/* La soglia non scende mai sotto due: sotto, si spedirebbe un fotogramma per
 * volta anche su una rete perfetta, e la latenza del disegno diventerebbe un
 * round trip pieno. */
#define SOGLIA_MINIMA 2

/* Si riprende a produrre quando i non riscontrati scendono a questo. */
#define SOGLIA_RIPRESA 1

/* Dopo quanti fotogrammi il banco finge che il client abbia sospeso i
 * riscontri.  Cento a trenta al secondo sono poco piu' di tre secondi: la
 * sessione e' gia' a regime, e ci sono fotogrammi in volo. */
#define FOTOGRAMMI_PRIMA_DELLA_FINTA 100

typedef struct
{
	uint16_t numero;
	gint64 partita_us;
} Sonda;

typedef struct
{
	gint64 rtt_us;
	gint64 quando_us;
} Campione;

typedef enum
{
	BANDA_FERMA,
	BANDA_DA_APRIRE,       /* c'e' un fotogramma grosso in coda, non ancora sul filo */
	BANDA_ATTESA_STOP,     /* «Start» spedito, la coda si sta svuotando              */
	BANDA_ATTESA_RISULTATI /* «Stop» spedito, il client deve rispondere              */
} StatoBanda;

struct Rete
{
	rdpContext *contesto;
	rdpAutoDetect *autodetect;
	uint32_t fotogrammi_al_secondo;

	GMutex lucchetto;

	gboolean detto_se_attiva;

	/* Le sonde partite e non ancora tornate, in ordine di partenza. */
	Sonda sonde[SONDE_MASSIME];
	guint prima_sonda, quante_sonde;
	uint16_t prossimo_numero;
	gint64 ultima_sonda_us;
	gboolean cadenza_alta;

	/* I round trip dentro la finestra. */
	Campione campioni[CAMPIONI_MASSIMI];
	guint primo_campione, quanti_campioni;
	gint64 rtt_medio_us; /* -1 finche' non c'e' un campione */
	gint64 rtt_base_us;

	StatoBanda stato_banda;
	uint32_t banda_kbit;
	/*
	 * QUANDO e' stata presa, e non solo quanto vale.
	 *
	 * ⛔ Il valore puo' essere vecchio di ordini di grandezza: la misura si
	 *    aggancia ai soli fotogrammi >= 10 KB (§16), e da quando il
	 *    codificatore lavora in VBR (R31) un desktop fermo ne produce da poche
	 *    centinaia di byte — quindi la misura non riparte e l'ultimo numero
	 *    resta li'.  Misurato il 7 agosto 2026: con il collegamento strozzato a
	 *    100 kbit/s, `banda_kbit` diceva ancora 220 136.
	 *
	 *    Chi decide qualcosa sulla banda deve poter chiedere «e di quando e'?».
	 */
	gint64 ultimo_netchar_us;

	/* Il regolatore. */
	guint64 spediti;
	gint in_volo;
	uint32_t soglia;
	gboolean strozzato;
	gboolean riscontri_sospesi;
	gboolean sospensione_detta;
	gboolean fingi_sospensione;

	gint64 ultimo_fotogramma_us;
	gint64 ultimo_riassunto_us;
};

/* ------------------------------------------------------------------ *
 * Le sonde: partenza, accoppiamento, media
 * ------------------------------------------------------------------ */

/* Il prossimo numero libero, saltando quello riservato alla banda.  Va chiamato
 * col lucchetto in mano. */
static uint16_t numero_nuovo(Rete *rete)
{
	uint16_t numero = rete->prossimo_numero;

	if (numero == NUMERO_BANDA)
		numero = 1;
	rete->prossimo_numero = (uint16_t) (numero + 1);
	return numero;
}

/* Annota una sonda in partenza.  Col lucchetto.  Restituisce FALSE se la
 * tabella e' piena, cioe' se il client ha smesso di rispondere. */
static gboolean annota_sonda(Rete *rete, uint16_t numero, gint64 adesso)
{
	guint posto;

	if (rete->quante_sonde >= SONDE_MASSIME)
		return FALSE;

	posto = (rete->prima_sonda + rete->quante_sonde) % SONDE_MASSIME;
	rete->sonde[posto].numero = numero;
	rete->sonde[posto].partita_us = adesso;
	rete->quante_sonde++;
	return TRUE;
}

/*
 * Ritrova la sonda che porta questo numero e restituisce quando era partita.
 *
 * Tutte quelle piu' vecchie si buttano: se la risposta alla terza e' arrivata,
 * la prima e la seconda non arriveranno mai piu' — il client risponde in ordine.
 * Tenerle vorrebbe dire far traboccare la tabella su una rete che perde
 * qualcosa, cioe' proprio dove la misura serve.  Col lucchetto.
 */
static gboolean ritrova_sonda(Rete *rete, uint16_t numero, gint64 *partita_us)
{
	for (guint j = 0; j < rete->quante_sonde; j++)
	{
		guint posto = (rete->prima_sonda + j) % SONDE_MASSIME;

		if (rete->sonde[posto].numero != numero)
			continue;

		*partita_us = rete->sonde[posto].partita_us;
		rete->prima_sonda = (rete->prima_sonda + j + 1) % SONDE_MASSIME;
		rete->quante_sonde -= j + 1;
		return TRUE;
	}
	return FALSE;
}

/* Aggiunge un campione e ricalcola media e minimo sulla finestra.  Col
 * lucchetto. */
static void aggiungi_campione(Rete *rete, gint64 rtt_us, gint64 adesso)
{
	gint64 somma = 0;
	guint contati = 0;
	guint posto;

	if (rete->quanti_campioni == CAMPIONI_MASSIMI)
	{
		rete->primo_campione = (rete->primo_campione + 1) % CAMPIONI_MASSIMI;
		rete->quanti_campioni--;
	}
	posto = (rete->primo_campione + rete->quanti_campioni) % CAMPIONI_MASSIMI;
	rete->campioni[posto].rtt_us = rtt_us;
	rete->campioni[posto].quando_us = adesso;
	rete->quanti_campioni++;

	/* I vecchi escono dalla finestra. */
	while (rete->quanti_campioni > 0 &&
	       adesso - rete->campioni[rete->primo_campione].quando_us >= FINESTRA_RTT_US)
	{
		rete->primo_campione = (rete->primo_campione + 1) % CAMPIONI_MASSIMI;
		rete->quanti_campioni--;
	}

	rete->rtt_base_us = G_MAXINT64;
	for (guint j = 0; j < rete->quanti_campioni; j++)
	{
		const Campione *c = &rete->campioni[(rete->primo_campione + j) % CAMPIONI_MASSIMI];

		somma += c->rtt_us;
		if (c->rtt_us < rete->rtt_base_us)
			rete->rtt_base_us = c->rtt_us;
		contati++;
	}
	if (contati == 0)
	{
		rete->rtt_medio_us = -1;
		rete->rtt_base_us = -1;
		return;
	}
	rete->rtt_medio_us = somma / contati;
}

/*
 * Spedisce una sonda.  Va chiamata SENZA lucchetto: la scrittura sul socket non
 * si tiene sotto un lucchetto che serve anche al thread dei riscontri.
 */
static gboolean manda_sonda(Rete *rete)
{
	uint16_t numero;
	gboolean c_e_posto;
	gint64 adesso = g_get_monotonic_time();

	g_mutex_lock(&rete->lucchetto);
	numero = numero_nuovo(rete);
	c_e_posto = annota_sonda(rete, numero, adesso);
	if (!c_e_posto)
	{
		/* Si riparte da zero: le sonde vecchie non torneranno, e continuare ad
		 * aspettarle terrebbe la tabella piena per sempre. */
		rete->prima_sonda = rete->quante_sonde = 0;
		rete->quanti_campioni = 0;
		rete->rtt_medio_us = rete->rtt_base_us = -1;
	}
	rete->ultima_sonda_us = adesso;
	g_mutex_unlock(&rete->lucchetto);

	if (!c_e_posto)
		avviso("il client non risponde piu' alle sonde di rete: riparto dalla misura vuota");

	return rete->autodetect->RTTMeasureRequest(rete->autodetect, RDP_TRANSPORT_TCP, numero);
}

/* ------------------------------------------------------------------ *
 * I ganci che FreeRDP chiama quando il client risponde
 * ------------------------------------------------------------------ */

static BOOL su_risposta_rtt(rdpAutoDetect *autodetect, RDP_TRANSPORT_TYPE trasporto,
                            UINT16 numero)
{
	Rete *rete = autodetect->custom;
	gint64 adesso = g_get_monotonic_time();
	gint64 partita_us = 0;

	(void) trasporto;
	if (!rete)
		return TRUE;

	g_mutex_lock(&rete->lucchetto);
	if (!ritrova_sonda(rete, numero, &partita_us))
	{
		/* Una risposta senza sonda: o e' un doppione, o la tabella e' stata
		 * svuotata nel frattempo.  Non e' un guasto, e non c'e' niente da
		 * misurare. */
		g_mutex_unlock(&rete->lucchetto);
		return TRUE;
	}
	aggiungi_campione(rete, adesso - partita_us, adesso);
	g_mutex_unlock(&rete->lucchetto);
	return TRUE;
}

static BOOL su_risultati_banda(rdpAutoDetect *autodetect, RDP_TRANSPORT_TYPE trasporto,
                               UINT16 numero, UINT16 tipo_risposta, UINT32 tempo_ms,
                               UINT32 byte_contati)
{
	Rete *rete = autodetect->custom;
	uint64_t bit;

	(void) trasporto;
	(void) numero;
	(void) tipo_risposta;
	if (!rete)
		return TRUE;

	bit = ((uint64_t) byte_contati) * 8u;

	g_mutex_lock(&rete->lucchetto);
	/*
	 * `MAX(tempo, 1)` non e' pigrizia: il client misura a millisecondi interi, e
	 * su un collegamento veloce lo Stop arriva dentro lo stesso millisecondo
	 * dello Start.  Un tempo nullo diventa una divisione per zero; con l'uno al
	 * denominatore diventa invece una banda enormemente sovrastimata, che e' il
	 * limite dichiarato della misura (§16) e non un difetto da nascondere.
	 */
	rete->banda_kbit = (uint32_t) (bit / MAX(tempo_ms, 1u));
	if (rete->stato_banda == BANDA_ATTESA_RISULTATI)
		rete->stato_banda = BANDA_FERMA;
	g_mutex_unlock(&rete->lucchetto);

	/* I due numeri grezzi: la banda stimata da sola non dice se il risultato e'
	 * credibile, lo dice il rapporto fra byte contati e millisecondi. */
	traccia("banda misurata: %u byte in %u ms → %u kbit/s", byte_contati, tempo_ms,
	        (uint32_t) (bit / MAX(tempo_ms, 1u)));
	return TRUE;
}

/*
 * L'autodetect ALLA CONNESSIONE (§16): la macchina a stati di FreeRDP la fa
 * partire da se', prima delle licenze.
 *
 * Il gestore predefinito manderebbe una sonda con un numero suo (0x23) che qui
 * non risulterebbe accoppiata a niente.  Sostituirlo costa tre righe e regala
 * una misura dell'RTT prima ancora che si disegni il primo fotogramma — che e'
 * esattamente il momento in cui il regolatore deve gia' sapere quanto tenere in
 * volo.
 */
static FREERDP_AUTODETECT_STATE su_autodetect_iniziale(rdpAutoDetect *autodetect)
{
	Rete *rete = autodetect->custom;

	if (!rete || !manda_sonda(rete))
		return FREERDP_AUTODETECT_STATE_FAIL;
	return FREERDP_AUTODETECT_STATE_REQUEST;
}

/* ------------------------------------------------------------------ *
 * Costruzione
 * ------------------------------------------------------------------ */

Rete *rete_nuova(rdpContext *contesto, uint32_t fotogrammi_al_secondo,
                 gboolean fingi_sospensione)
{
	Rete *rete;
	rdpAutoDetect *autodetect = autodetect_get(contesto);

	if (!autodetect)
	{
		avviso("nessun autodetect nel contesto: niente misura della rete");
		return NULL;
	}

	rete = g_new0(Rete, 1);
	rete->contesto = contesto;
	rete->autodetect = autodetect;
	rete->fotogrammi_al_secondo = MAX(1u, fotogrammi_al_secondo);
	rete->fingi_sospensione = fingi_sospensione;
	rete->prossimo_numero = 1;
	rete->rtt_medio_us = -1;
	rete->rtt_base_us = -1;
	rete->soglia = SOGLIA_MINIMA;
	g_mutex_init(&rete->lucchetto);

	autodetect->custom = rete;
	autodetect->RTTMeasureResponse = su_risposta_rtt;
	autodetect->BandwidthMeasureResults = su_risultati_banda;
	autodetect->OnConnectTimeAutoDetectBegin = su_autodetect_iniziale;
	return rete;
}

void rete_libera(Rete *rete)
{
	if (!rete)
		return;

	/*
	 * ⛔ I ganci si staccano PRIMA di liberare la struttura.
	 *
	 * `rdpAutoDetect` vive quanto il contesto RDP, non quanto noi: se una
	 * risposta arrivasse dopo, chiamerebbe un gancio che punta a memoria
	 * liberata.  Costa quattro assegnamenti e toglie di mezzo un intero genere di
	 * guasto in chiusura.
	 */
	if (rete->autodetect && rete->autodetect->custom == rete)
	{
		rete->autodetect->RTTMeasureResponse = NULL;
		rete->autodetect->BandwidthMeasureResults = NULL;
		rete->autodetect->OnConnectTimeAutoDetectBegin = NULL;
		rete->autodetect->custom = NULL;
	}
	g_mutex_clear(&rete->lucchetto);
	g_free(rete);
}

/* ------------------------------------------------------------------ *
 * Il passo
 * ------------------------------------------------------------------ */

static gboolean misura_attiva(Rete *rete)
{
	return freerdp_settings_get_bool(rete->contesto->settings, FreeRDP_NetworkAutoDetect);
}

/* Informa il client di quel che si e' misurato.  Senza lucchetto. */
static void manda_netchar(Rete *rete)
{
	rdpNetworkCharacteristicsResult risultato = { 0 };
	uint16_t numero;
	gboolean da_mandare = FALSE;
	gint64 adesso = g_get_monotonic_time();

	g_mutex_lock(&rete->lucchetto);
	if (rete->banda_kbit > 0 && rete->rtt_medio_us >= 0 &&
	    adesso - rete->ultimo_netchar_us >= NETCHAR_OGNI_US)
	{
		risultato.type = RDP_NETCHAR_RESULT_TYPE_BASE_RTT_BW_AVG_RTT;
		risultato.baseRTT = (UINT32) (rete->rtt_base_us / 1000);
		risultato.averageRTT = (UINT32) (rete->rtt_medio_us / 1000);
		risultato.bandwidth = rete->banda_kbit;
		numero = numero_nuovo(rete);
		rete->ultimo_netchar_us = adesso;
		da_mandare = TRUE;
	}
	g_mutex_unlock(&rete->lucchetto);

	if (da_mandare)
		rete->autodetect->NetworkCharacteristicsResult(rete->autodetect, RDP_TRANSPORT_TCP,
		                                               numero, &risultato);
}

void rete_passo(Rete *rete)
{
	gint64 adesso;
	gint64 cadenza_us;
	gboolean alta;
	gboolean da_sondare = FALSE;
	gboolean riassunto = FALSE;
	gboolean sospesi = FALSE;
	gint64 rtt = -1, base = -1;
	uint32_t banda = 0, soglia = 0;
	gint in_volo = 0;
	guint64 spediti = 0;

	if (!rete)
		return;

	if (!rete->detto_se_attiva)
	{
		rete->detto_se_attiva = TRUE;
		if (misura_attiva(rete))
			informazione("misura della rete attiva: il client dichiara di saperla fare");
		else
			informazione("il client non dichiara la misura della rete: "
			             "regolatore alla soglia prudente di %d fotogrammi",
			             SOGLIA_MINIMA);
	}
	if (!misura_attiva(rete))
		return;

	adesso = g_get_monotonic_time();

	g_mutex_lock(&rete->lucchetto);
	alta = (adesso - rete->ultimo_fotogramma_us) < ATTIVITA_US;
	if (alta != rete->cadenza_alta)
	{
		rete->cadenza_alta = alta;
		/* Cambiare cadenza vuol dire sondare subito: se si passa ad alta e si
		 * aspettasse il tempo della bassa, la prima misura precisa arriverebbe
		 * con settecento millisecondi di ritardo, cioe' dopo che il fotogramma
		 * che l'aveva richiesta e' gia' partito. */
		rete->ultima_sonda_us = 0;
	}
	cadenza_us = (alta ? CADENZA_ALTA_MS : CADENZA_BASSA_MS) * G_GINT64_CONSTANT(1000);
	if (adesso - rete->ultima_sonda_us >= cadenza_us)
		da_sondare = TRUE;

	if (adesso - rete->ultimo_riassunto_us >= RIASSUNTO_OGNI_US &&
	    (rete->rtt_medio_us >= 0 || rete->in_volo > 0))
	{
		rete->ultimo_riassunto_us = adesso;
		rtt = rete->rtt_medio_us;
		base = rete->rtt_base_us;
		banda = rete->banda_kbit;
		soglia = rete->soglia;
		in_volo = rete->in_volo;
		spediti = rete->spediti;
		sospesi = rete->riscontri_sospesi;
		riassunto = TRUE;
	}
	g_mutex_unlock(&rete->lucchetto);

	if (da_sondare)
		manda_sonda(rete);

	manda_netchar(rete);

	if (riassunto)
		diagnostica("rete: RTT %.1f ms (minimo %.1f), banda %u kbit/s, "
		            "in volo %d di %u, spediti %" G_GUINT64_FORMAT "%s",
		            rtt >= 0 ? rtt / 1000.0 : -1.0, base >= 0 ? base / 1000.0 : -1.0, banda,
		            in_volo, soglia, spediti, sospesi ? ", senza riscontri" : "");
}

/* ------------------------------------------------------------------ *
 * Il regolatore
 * ------------------------------------------------------------------ */

/*
 * §5 di REFERENCE.md — «non ti mando piu' riscontri».
 *
 * Da qui in poi il regolatore non ha niente da contare, e deve TOGLIERSI DI
 * MEZZO: continuare a strozzare su un conto che non scendera' mai piu' e' un
 * desktop che si ferma per sempre.  Il prezzo e' che con quei client il
 * controllo di flusso non c'e', ed e' il prezzo che il protocollo impone.
 *
 * Col lucchetto.  Restituisce vero se e' la prima volta, cioe' se va detto.
 */
static gboolean applica_sospensione(Rete *rete)
{
	gboolean prima_volta = !rete->sospensione_detta;

	rete->sospensione_detta = TRUE;
	rete->riscontri_sospesi = TRUE;
	rete->strozzato = FALSE;
	rete->in_volo = 0;
	return prima_volta;
}

/*
 * La soglia, dall'RTT (§10.2 di gnome-remote-desktop.md):
 *
 *     quanti fotogrammi stanno «in volo» nel tempo di un round trip, piu' due.
 *
 * Il piu' due e' quel che serve per non fermarsi mai su una rete perfetta: uno
 * appena spedito e uno che sta tornando.  Il tetto ai fotogrammi di un secondo
 * evita che una rete pessima autorizzi una coda lunga un secondo, che sarebbe
 * un desktop che risponde con un secondo di ritardo invece di uno che rallenta.
 *
 * Col lucchetto.
 */
static uint32_t soglia_da_rtt(Rete *rete)
{
	uint32_t fps = rete->fotogrammi_al_secondo;
	uint32_t ritardati;
	uint32_t soglia;

	if (rete->rtt_medio_us <= 0)
		return SOGLIA_MINIMA;

	ritardati = (uint32_t) (rete->rtt_medio_us * fps / G_USEC_PER_SEC);
	soglia = ritardati + 2;
	if (soglia > fps)
		soglia = fps;
	if (soglia < SOGLIA_MINIMA)
		soglia = SOGLIA_MINIMA;
	return soglia;
}

gboolean rete_c_e_posto(Rete *rete)
{
	gboolean posso;
	gboolean strozza_adesso = FALSE, riprende_adesso = FALSE;
	uint32_t soglia;
	gint in_volo;

	if (!rete)
		return TRUE;

	g_mutex_lock(&rete->lucchetto);
	if (rete->riscontri_sospesi)
	{
		g_mutex_unlock(&rete->lucchetto);
		return TRUE;
	}

	soglia = soglia_da_rtt(rete);
	rete->soglia = soglia;
	in_volo = rete->in_volo;

	/*
	 * L'isteresi, e non una soglia sola.
	 *
	 * Con una soglia sola si strozza a N e si riparte a N-1, cioe' si oscilla a
	 * ogni fotogramma attorno al punto di lavoro.  Si riparte invece quando la
	 * coda si e' quasi svuotata: e' il comportamento del riferimento, che
	 * riattiva a «<= 1 non riscontrati», e produce raffiche brevi invece di un
	 * singhiozzo continuo.
	 */
	if (rete->strozzato)
	{
		if (in_volo <= SOGLIA_RIPRESA)
		{
			rete->strozzato = FALSE;
			riprende_adesso = TRUE;
		}
	}
	else if (in_volo >= (gint) soglia)
	{
		rete->strozzato = TRUE;
		strozza_adesso = TRUE;
	}
	posso = !rete->strozzato;
	g_mutex_unlock(&rete->lucchetto);

	if (strozza_adesso)
		diagnostica("strozzo: %d fotogrammi non riscontrati, soglia %u", in_volo, soglia);
	else if (riprende_adesso)
		diagnostica("riprendo: %d fotogrammi non riscontrati, soglia %u", in_volo, soglia);

	return posso;
}

void rete_fotogramma_parte(Rete *rete, uint32_t byte_fotogramma)
{
	if (!rete || !misura_attiva(rete))
		return;

	g_mutex_lock(&rete->lucchetto);
	/*
	 * Qui si SEGNA soltanto: il fotogramma finisce in coda, non sul filo, e la
	 * misura non puo' cominciare prima che la coda si svuoti.  Chi apre e chiude
	 * e' il ciclo, attorno allo svuotamento (vedi rete.h).
	 */
	if (rete->stato_banda == BANDA_FERMA && byte_fotogramma >= BANDA_MINIMA_BYTE)
	{
		rete->stato_banda = BANDA_DA_APRIRE;
		traccia("fotogramma da %u byte: ci si puo' misurare la banda", byte_fotogramma);
	}
	g_mutex_unlock(&rete->lucchetto);
}

void rete_fotogramma_partito(Rete *rete)
{
	gboolean finta = FALSE;

	if (!rete)
		return;

	g_mutex_lock(&rete->lucchetto);
	rete->spediti++;
	rete->in_volo++;
	rete->ultimo_fotogramma_us = g_get_monotonic_time();
	if (rete->fingi_sospensione && !rete->riscontri_sospesi &&
	    rete->spediti >= FOTOGRAMMI_PRIMA_DELLA_FINTA)
	{
		finta = applica_sospensione(rete);
	}
	g_mutex_unlock(&rete->lucchetto);

	if (finta)
		informazione("il client sospende i riscontri: il regolatore si toglie di mezzo"
		             " (FINTA del banco, dopo %d fotogrammi)", FOTOGRAMMI_PRIMA_DELLA_FINTA);
}

void rete_banda_apre(Rete *rete)
{
	gboolean da_avviare = FALSE;

	if (!rete)
		return;

	g_mutex_lock(&rete->lucchetto);
	if (rete->stato_banda == BANDA_DA_APRIRE)
	{
		rete->stato_banda = BANDA_ATTESA_STOP;
		da_avviare = TRUE;
	}
	g_mutex_unlock(&rete->lucchetto);

	if (da_avviare)
		rete->autodetect->BandwidthMeasureStart(rete->autodetect, RDP_TRANSPORT_TCP,
		                                        NUMERO_BANDA);
}

void rete_banda_chiude(Rete *rete)
{
	gboolean da_fermare = FALSE;

	if (!rete)
		return;

	g_mutex_lock(&rete->lucchetto);
	if (rete->stato_banda == BANDA_ATTESA_STOP)
	{
		rete->stato_banda = BANDA_ATTESA_RISULTATI;
		da_fermare = TRUE;
	}
	g_mutex_unlock(&rete->lucchetto);

	if (da_fermare)
		rete->autodetect->BandwidthMeasureStop(rete->autodetect, RDP_TRANSPORT_TCP,
		                                       NUMERO_BANDA, 0);
}

void rete_riscontro(Rete *rete, uint32_t id_fotogramma, uint32_t profondita_coda,
                    uint32_t totale_decodificati)
{
	gboolean da_dire = FALSE;
	gint in_volo;

	if (!rete)
		return;

	g_mutex_lock(&rete->lucchetto);
	if (profondita_coda == SUSPEND_FRAME_ACKNOWLEDGEMENT)
	{
		da_dire = applica_sospensione(rete);
		g_mutex_unlock(&rete->lucchetto);
		if (da_dire)
			informazione("il client sospende i riscontri: il regolatore si toglie di mezzo");
		return;
	}

	if (rete->in_volo > 0)
		rete->in_volo--;

	/*
	 * `totalFramesDecoded` come PAVIMENTO, mai come tetto (§5 di REFERENCE.md).
	 *
	 * Serve a rimettersi in pari quando un riscontro si perde: il conto locale
	 * resterebbe alto per sempre e il regolatore strozzerebbe una rete che
	 * invece e' libera.  Si applica solo quando ABBASSA il conto — un client che
	 * dichiarasse un totale piu' basso del vero (o zero, come fa chi non lo
	 * tiene) non deve poter far credere che ci siano piu' fotogrammi in volo di
	 * quanti ne siano davvero partiti.
	 */
	if (totale_decodificati > 0 && rete->spediti <= G_MAXUINT32 &&
	    (guint64) totale_decodificati <= rete->spediti)
	{
		gint residuo = (gint) (rete->spediti - totale_decodificati);

		if (residuo < rete->in_volo)
			rete->in_volo = residuo;
	}
	in_volo = rete->in_volo;
	g_mutex_unlock(&rete->lucchetto);

	traccia("riscontro fotogramma %u, in volo %d", id_fotogramma, in_volo);
}

gint64 rete_rtt_us(Rete *rete)
{
	gint64 rtt;

	if (!rete)
		return -1;
	g_mutex_lock(&rete->lucchetto);
	rtt = rete->rtt_medio_us;
	g_mutex_unlock(&rete->lucchetto);
	return rtt;
}

uint32_t rete_banda_kbit(Rete *rete)
{
	uint32_t banda;

	if (!rete)
		return 0;
	g_mutex_lock(&rete->lucchetto);
	banda = rete->banda_kbit;
	g_mutex_unlock(&rete->lucchetto);
	return banda;
}

