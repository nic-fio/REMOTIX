#include "server.h"

#include <errno.h>
#include <freerdp/channels/channels.h>
#include <freerdp/channels/cliprdr.h>
#include <freerdp/channels/drdynvc.h>
#include <freerdp/channels/wtsvc.h>
#include <freerdp/codec/color.h>
#include <freerdp/error.h>
#include <freerdp/freerdp.h>
#include <freerdp/pointer.h>
#include <freerdp/peer.h>
#include <freerdp/server/disp.h>
#include <freerdp/server/rdpgfx.h>
#include <gio/gio.h>
#include <glib/gstdio.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <sys/socket.h>
#include <winpr/ssl.h>
#include <winpr/synch.h>

#include "altoparlante.h"
#include "autenticazione.h"
#include "codificatore.h"
#include "immagine.h"
#include "input.h"
#include "misura.h"
#include "palco.h"
#include "registro.h"
#include "rete.h"
#include "scambio.h"
#include "sentinella.h"
#include "sessione.h"

/* R2 — l'elenco DEVE essere completo, dalla piu' alta alla piu' bassa, e la
 * 10.6 ha due valori perche' quello della specifica era sbagliato e l'errata
 * [MS-RDPEGFX]-180912 lo corregge.  Ripiegare su una versione dove l'AVC e'
 * spento significa zero fotogrammi con mstsc. */
static const UINT32 versioni_egfx[] = {
	RDPGFX_CAPVERSION_107, RDPGFX_CAPVERSION_106, RDPGFX_CAPVERSION_106_ERR,
	RDPGFX_CAPVERSION_105, RDPGFX_CAPVERSION_104, RDPGFX_CAPVERSION_103,
	RDPGFX_CAPVERSION_102, RDPGFX_CAPVERSION_101, RDPGFX_CAPVERSION_10,
	RDPGFX_CAPVERSION_81,  RDPGFX_CAPVERSION_8,
};

/* ------------------------------------------------------------------ *
 * La macchina di ridimensionamento (§7.2 di REFERENCE.md)
 *
 *   ATTESA_CONFIG ──(nuova configurazione)──► inibisci il rendering
 *                                               │
 *                                        PREPARA/ATTENDI  (thread a parte)
 *                                               │
 *                                        RIPRENDI ──► disinibisci ──► ATTESA_CONFIG
 *
 * Rispetto al riferimento, che ha uno stato per ciascuna attesa, qui gli stati
 * sono tre e non cinque — e la ragione e' strutturale, non una scorciatoia:
 *
 *   - l'INIBIZIONE del riferimento e' «un conteggio di risorse in uso» perche'
 *     li' i fotogrammi si codificano su un pool di thread.  In REMOTIX codifica
 *     e spedizione avvengono dentro `manda_fotogramma`, sul thread della
 *     connessione, cioe' sullo stesso thread che esegue questa macchina:
 *     quando la macchina gira, per costruzione non c'e' nessun fotogramma a
 *     meta' strada.  Il conteggio sarebbe sempre zero;
 *   - le due attese ATTENDI_STREAM e ATTENDI_MISURE sono distinte perche' il
 *     riferimento ha N stream e N superfici.  Qui il monitor e' uno solo (§3.1
 *     di SPECIFICA.md), quindi le due attese sono la stessa attesa.
 *
 * Quel che NON si semplifica e' il resto: si inibisce prima di toccare
 * qualunque cosa, si aspetta un EVENTO e non un silenzio, l'input col
 * puntatore si scarta finche' la geometria non e' stabile, e una
 * configurazione che arriva mentre se ne applica un'altra SOSTITUISCE quella in
 * coda invece di accodarsi — che e' la risposta alle raffiche di chi trascina
 * il bordo della finestra.
 * ------------------------------------------------------------------ */
typedef enum
{
	MISURA_STABILE,   /* ATTESA_CONFIG: si disegna, e l'input vale        */
	MISURA_INIBITA,   /* il palco sta prendendo la misura nuova           */
	MISURA_DA_RIPRENDERE, /* il palco ha risposto: si ridichiara la tela  */
} StatoMisura;

/*
 * Il ridimensionamento vero e proprio gira su un THREAD SUO, e il perche' e'
 * misurato: `palco_ridimensiona` aspetta la conferma di Mutter e poi il
 * ridisegno del desktop, che sono secondi.  Farlo sul thread della connessione
 * significherebbe non pompare il protocollo per tutto quel tempo — e trascinare
 * il bordo di una finestra produce una RAFFICA di richieste, cioe' una serie di
 * stalli uno dietro l'altro.  E' la regola 7 di §5.8 di SPECIFICA.md: non si
 * aspetta mai dentro il ciclo.
 *
 * La struttura e' contata a riferimenti e NON contiene il contesto della
 * connessione: se il client se ne va mentre il palco si ridimensiona, il thread
 * finisce il suo lavoro — che riguarda la SESSIONE, non la connessione — e
 * lascia cadere il suo riferimento senza toccare memoria di nessuno.  Aspettare
 * qui il thread sarebbe la strada corta, e costerebbe fino a una decina di
 * secondi sul congedo, cioe' il numero che la fase 5 tiene sotto i due secondi.
 */
typedef enum
{
	RIDIM_IN_CORSO,
	RIDIM_FATTO,
	RIDIM_GUASTO,
} EsitoRidim;

typedef struct
{
	gint riferimenti;
	Server *server;
	uint32_t larghezza, altezza, fotogrammi_al_secondo;
	gint esito; /* EsitoRidim, atomico */
} Ridimensionamento;

typedef struct
{
	rdpContext ctx; /* DEVE essere il primo campo */

	Server *server;
	HANDLE vcm;
	HANDLE evento_stop;
	/*
	 * Sveglia il ciclo quando c'e' una misura nuova da applicare.
	 *
	 * ⛔ NON si riusa `evento_stop`: quello significa «chiudi», e il ciclo che lo
	 *    trova segnalato senza un motivo scritto esce dal `while`.  Un evento
	 *    riusato per due significati e' una disconnessione a ogni
	 *    ridimensionamento.
	 */
	HANDLE evento_misura;

	RdpgfxServerContext *gfx;
	gboolean gfx_aperto;
	gboolean gfx_pronto;
	UINT16 id_superficie;

	gboolean superficie_creata;
	UINT32 id_fotogramma;

	/*
	 * Questa connessione ha chiesto al palco i pixel IN CPU, e deve ricordarsene
	 * per rilasciarli.
	 *
	 * Il palco conta le richieste, quindi ogni connessione ne deve fare una sola
	 * e restituirla una sola volta: chi si dimenta il ritorno lascia il palco in
	 * memoria per tutta la vita della sessione, e il sintomo sarebbe una copia
	 * zero che «ogni tanto non si accende».  Il flag e' qui perche' e' l'unico
	 * posto che vive esattamente quanto la connessione.
	 */
	gboolean pixel_in_cpu;

	/*
	 * La misura della rete e il regolatore (fase 7).
	 *
	 * Sta nel contesto e non nel server perche' RTT e banda sono di UNA
	 * connessione: due client sulla stessa macchina possono stare uno in fibra e
	 * uno in tethering, e una misura sola sarebbe la media di due cose che non
	 * si assomigliano.
	 */
	Rete *rete;

	/*
	 * MS-RDPEA — l'audio in uscita della fase 8.
	 *
	 * Il canale e' della CONNESSIONE (il formato lo negozia il client), il sink
	 * da cui si cattura e' della SESSIONE e sta nel palco: e' la stessa
	 * divisione dell'input, per la stessa ragione (§7.5 di REFERENCE.md).
	 */
	Altoparlante *altoparlante;
	gboolean ascolto_acceso;

	/*
	 * MS-RDPECLIP — gli appunti della fase 8.
	 *
	 * Il canale e' STATICO: non aspetta drdynvc, ma aspetta che il client lo
	 * abbia unito, ed e' l'unica cosa da controllare prima di aprirlo.
	 */
	Scambio *scambio;
	gboolean appunti_detti;

	/* MS-RDPEDISP — la risoluzione dinamica della fase 6. */
	DispServerContext *disp;
	gboolean disp_aperto;
	UINT32 disp_canale;
	gboolean disp_pronto; /* il client ha aperto il canale: le capacita' sono partite */

	/* La misura in vigore, e quella che il client ha chiesto e aspetta. */
	Misura misura;
	TipoCodificatore codec; /* scelto UNA volta, al CapsConfirm (R3) */
	GMutex lucchetto_misura;
	Misura misura_in_attesa;
	gboolean c_e_attesa;
	gint64 attesa_da_us;    /* quando e' arrivata la PRIMA della serie  */
	gint64 ultima_da_us;    /* quando e' arrivata l'ULTIMA della serie  */
	gboolean rinvio_detto;

	StatoMisura stato_misura;
	Misura misura_chiesta;
	/*
	 * L'eco: la misura appena lasciata, e fino a quando richiederla vale come
	 * eco invece che come intenzione (vedi ECO_MS).
	 *
	 * ⛔ IL CONFRONTO SI FA ALL'ARRIVO, non quando la richiesta viene raccolta.
	 *    Fra i due momenti passa l'assestamento, e l'eco si riconosce proprio
	 *    dal fatto che arriva SUBITO: rimandare il confronto vorrebbe dire
	 *    misurare un tempo che nel frattempo e' scaduto, e lasciarla passare.
	 *    Stanno quindi sotto `lucchetto_misura`, perche' li scrive il thread
	 *    della connessione e li legge quello del canale DISP.
	 */
	Misura eco_misura;
	gint64 eco_fino_a_us;
	Ridimensionamento *ridim;
	/*
	 * Uno mentre la geometria NON e' stabile.  Lo leggono i gestori del
	 * puntatore, che girano sul thread della connessione come questa macchina,
	 * ma anche — in astratto — su un altro: sta atomico perche' costa nulla.
	 */
	gint geometria_instabile;

	/*
	 * Il client ha chiesto di NON ricevere piu' aggiornamenti dello schermo
	 * (MS-RDPBCGR 2.2.11.3), tipicamente perche' la sua finestra e' minimizzata.
	 *
	 * Lo tocca solo il thread della connessione: la richiesta arriva dentro
	 * `CheckFileDescriptor`, cioe' sullo stesso thread che spedisce.
	 */
	gboolean uscita_soppressa;

	Codificatore *cod;
	Immagine *immagine;
	gint64 avvio_us;

	/*
	 * Quale fotogramma del palco questa connessione ha gia' disegnato.
	 *
	 * Parte da zero, e il palco conta da uno: chi si collega trova quindi
	 * «nuovo» l'ultimo fotogramma conservato e lo disegna subito, anche se e'
	 * di minuti fa e il desktop e' fermo.  E' R9, ottenuta senza un caso
	 * speciale.
	 */
	guint64 visto;

	/* R14 — la guardia parte da NEGATO e solo il validatore la apre. */
	gboolean autenticato;

	/*
	 * Perche' questa connessione deve chiudere, deciso da FUORI.
	 *
	 * Zero significa «nessuno l'ha chiesto».  Ci scrive chi sa qualcosa che il
	 * ciclo non puo' sapere — la sessione sta uscendo, e' comparsa una sessione
	 * locale — e il ciclo lo legge appena si sveglia.  E' un intero atomico e
	 * non un lucchetto perche' il percorso deve essere veloce: chi lo scrive ha
	 * appena saputo che l'utente sta uscendo.
	 */
	gint motivo;
	/* Vero se questa connessione tiene il posto: solo lei lo libera. */
	gboolean tiene_il_posto;

	/*
	 * Da quando si puo' DIRE qualcosa al client, e cosa gli si deve dire.
	 *
	 * `SET_ERROR_INFO` e' un Share Data PDU: esiste solo dopo che la sessione
	 * RDP e' stata attivata, cioe' dopo lo scambio Demand Active / Confirm
	 * Active.  Chi lo spedisce prima — in `Capabilities` o in `PostConnect` —
	 * a volte lo vede partire e a volte no, a seconda di dove il client e'
	 * arrivato: e' esattamente l'intermittenza vista al banco, un giro con
	 * `ERRINFO_SERVER_DENIED_CONNECTION` e il giro dopo con niente.
	 *
	 * Quindi un rifiuto deciso presto non si spedisce: si REGISTRA qui, si
	 * lascia proseguire la connessione fino all'attivazione — senza montare
	 * niente e senza prendere il posto — e la' lo si dice.
	 */
	gboolean attivo;
	UINT32 rifiuto;
	const char *rifiuto_perche;
} ContestoPeer;

typedef enum
{
	INVIO_AVANTI,
	INVIO_SESSIONE_FINITA,
	INVIO_GUASTO,
} EsitoInvio;

struct Server
{
	OpzioniServer opzioni;
	GSocketService *servizio;
	/*
	 * Si conservano i PEM come TESTO, non gli oggetti gia' costruiti.
	 *
	 * `freerdp_settings_set_pointer_len(FreeRDP_RdpServerCertificate, ...)`
	 * non copia: assegna il puntatore, e `freerdp_settings_free` lo libera
	 * insieme al peer.  Condividere un solo certificato fra le connessioni
	 * significa quindi che la PRIMA se lo porta via e la SECONDA usa memoria
	 * liberata — segfault dentro libcrypto, lontanissimo dalla causa.
	 * Costato il 4 agosto: il server moriva alla seconda connessione, e dal
	 * lato del client si vedeva solo «non si collega».
	 */
	char *pem_certificato;
	char *pem_chiave;
	GPtrArray *connessioni;
	GMutex lucchetto;

	/*
	 * Il palco appartiene al SERVER, non alla connessione.
	 *
	 * Smontarlo alla disconnessione lascia Mutter con zero schermi, e le
	 * applicazioni aperte perdono la connessione Wayland: la prova di questa
	 * fase e' «il desktop vero sui tre client», cioe' tre connessioni una dopo
	 * l'altra, ed e' precisamente la sequenza che quel difetto rovina.  Il
	 * perche' per esteso sta in palco.h.
	 */
	Palco *palco;

	/*
	 * Il portiere: uno solo entra.
	 *
	 * E' un `compare_exchange` e non un «leggi, poi scrivi», e non e'
	 * pignoleria: alcuni client aprono DUE connessioni nello stesso istante, e
	 * fra la lettura e la scrittura ci starebbero entrambe.
	 */
	gint occupato;

	/* Le connessioni in corso, per poterle congedare da fuori. */
	GPtrArray *contesti;

	/* Puo' essere NULL: allora la regola della sessione locale non e' in vigore. */
	Sentinella *sentinella;
};

/* ------------------------------------------------------------------ *
 * Chiusura dichiarata (R12)
 *
 * Un client che riceve solo una chiusura di socket mostra «errore di rete» e
 * l'utente non impara niente; il client Android non se ne accorge affatto e
 * resta a fissare l'ultimo fotogramma.
 *
 * ⛔ SERVONO DUE CHIAMATE, e per due mesi ne abbiamo fatta una sola.
 *
 *    `freerdp_set_error_info` **registra** il codice; a spedirlo sul filo e'
 *    `freerdp_send_error_info`, che e' una funzione a parte.  Chiamando solo la
 *    prima e poi chiudendo il trasporto, il client riceve una chiusura di
 *    socket e nient'altro — cioe' esattamente il difetto che R12 esiste per
 *    togliere.  Misurato il 4 agosto guardando il registro del CLIENT, che
 *    diceva «Network disconnect!» mentre il nostro diceva «congedo il client».
 *
 *    E l'ordine conta: prima si spedisce, poi si chiude.  `Disconnect` butta
 *    giu' il trasporto, e cio' che non e' ancora partito non parte piu'.
 * ------------------------------------------------------------------ */
static void congeda(freerdp_peer *peer, UINT32 codice, const char *perche)
{
	ContestoPeer *cp = (ContestoPeer *) peer->context;

	/* Troppo presto per parlare: si segna, e lo dira' `peer_attivato`. */
	if (!cp->attivo)
	{
		cp->rifiuto = codice;
		cp->rifiuto_perche = perche;
		diagnostica("congedo rimandato (%s): la sessione RDP non e' ancora attiva", perche);
		return;
	}

	informazione("congedo il client: %s (0x%04X)", perche, codice);
	freerdp_set_error_info(peer->context->rdp, codice);
	if (!freerdp_send_error_info(peer->context->rdp))
		avviso("l'informazione d'errore non e' partita: il client non sapra' perche'");
	peer->Disconnect(peer);
}

/* ------------------------------------------------------------------ *
 * Contesto del peer
 * ------------------------------------------------------------------ */
static BOOL contesto_nuovo(freerdp_peer *peer, rdpContext *contesto)
{
	ContestoPeer *cp = (ContestoPeer *) contesto;

	cp->vcm = WTSOpenServerA((LPSTR) contesto);
	if (!cp->vcm || cp->vcm == INVALID_HANDLE_VALUE)
	{
		errore("WTSOpenServerA fallita");
		return FALSE;
	}
	cp->evento_stop = CreateEvent(NULL, TRUE, FALSE, NULL);
	cp->evento_misura = CreateEvent(NULL, TRUE, FALSE, NULL);
	cp->id_superficie = 1;
	cp->stato_misura = MISURA_STABILE;
	g_mutex_init(&cp->lucchetto_misura);
	cp->avvio_us = g_get_monotonic_time();
	return TRUE;
}

static void ridimensionamento_lascia(Ridimensionamento *ridim);
static void spegni_ascolto(ContestoPeer *cp);

static void contesto_libera(freerdp_peer *peer, rdpContext *contesto)
{
	ContestoPeer *cp = (ContestoPeer *) contesto;

	if (!cp)
		return;

	/*
	 * ⛔ PRIMA LA CATTURA AUDIO, POI IL CANALE, e l'ordine e' obbligato: finche'
	 *    la cattura e' accesa, il thread di PipeWire accoda campioni dentro
	 *    l'altoparlante.  Liberarlo prima significherebbe consegnargli memoria
	 *    gia' liberata — lo stesso difetto dei due canali dinamici qui sotto,
	 *    solo con un thread che non e' nemmeno di FreeRDP.
	 */
	spegni_ascolto(cp);
	g_clear_pointer(&cp->altoparlante, altoparlante_chiudi);
	/* Gli appunti hanno il loro thread e parlano con la sessione: si chiudono
	 * qui, dove nessuno sta piu' usando questo contesto. */
	g_clear_pointer(&cp->scambio, scambio_chiudi);
	/*
	 * ⛔ I DUE CANALI DINAMICI SI CHIUDONO PER PRIMI, e non e' ordine estetico:
	 *    ciascuno ha un THREAD SUO dentro FreeRDP che richiama i nostri gestori
	 *    passandogli questo contesto.  `Close` aspetta quel thread; liberare
	 *    prima significherebbe consegnargli memoria gia' liberata, con il
	 *    segfault che compare in un thread che non ha il nostro nome.
	 */
	if (cp->disp)
	{
		if (cp->disp_aperto)
			cp->disp->Close(cp->disp);
		disp_server_context_free(cp->disp);
		cp->disp = NULL;
	}
	if (cp->gfx)
	{
		if (cp->gfx_aperto)
			cp->gfx->Close(cp->gfx);
		rdpgfx_server_context_free(cp->gfx);
		cp->gfx = NULL;
	}
	/* Il thread del ridimensionamento, se c'e' ancora, tiene il proprio
	 * riferimento: qui si lascia il nostro e chi arriva ultimo libera. */
	if (cp->ridim)
	{
		ridimensionamento_lascia(cp->ridim);
		cp->ridim = NULL;
	}
	/* Dopo i due canali dinamici: `rete_riscontro` arriva dal thread di EGFX, e
	 * finche' quel thread e' vivo la misura dev'essere ancora la'. */
	g_clear_pointer(&cp->rete, rete_libera);
	g_clear_pointer(&cp->cod, codificatore_libera);
	g_clear_pointer(&cp->immagine, immagine_libera);

	/*
	 * I pixel in CPU si restituiscono DOPO il codificatore, e non e' ordine
	 * estetico: rilasciarli riporta la cattura sulla scheda, e un codificatore
	 * ancora vivo su quella strada si troverebbe a chiedere fotogrammi in memoria
	 * che non arrivano piu'.  Prima si smette di codificare, poi si rende la
	 * strada a chi viene dopo.
	 */
	if (cp->pixel_in_cpu)
	{
		cp->pixel_in_cpu = FALSE;
		if (cp->server)
			palco_pixel_in_cpu(cp->server->palco, FALSE);
	}
	g_mutex_clear(&cp->lucchetto_misura);
	if (cp->evento_misura)
		CloseHandle(cp->evento_misura);
	if (cp->evento_stop)
		CloseHandle(cp->evento_stop);
	if (cp->vcm && cp->vcm != INVALID_HANDLE_VALUE)
		WTSCloseServer(cp->vcm);
}

/* ------------------------------------------------------------------ *
 * §3.3 — cosa pretendere dal client, e dirlo quando manca
 * ------------------------------------------------------------------ */
static BOOL peer_capabilities(freerdp_peer *peer)
{
	rdpSettings *imp = peer->context->settings;

	if (!freerdp_settings_get_bool(imp, FreeRDP_SupportGraphicsPipeline))
	{
		avviso("il client non dichiara la pipeline grafica: chiudo");
		congeda(peer, ERRINFO_BAD_CAPABILITIES, "niente EGFX");
		return TRUE; /* si prosegue solo per poter dire di no */
	}
	if (freerdp_settings_get_uint32(imp, FreeRDP_ColorDepth) != 32)
	{
		avviso("il client non dichiara 32 bpp: chiudo");
		congeda(peer, ERRINFO_BAD_CAPABILITIES, "niente 32 bpp");
		return TRUE; /* si prosegue solo per poter dire di no */
	}
	if (!freerdp_settings_get_bool(imp, FreeRDP_DesktopResize))
	{
		avviso("il client non sa ridimensionare il desktop: chiudo");
		congeda(peer, ERRINFO_BAD_CAPABILITIES, "niente DesktopResize");
		return TRUE; /* si prosegue solo per poter dire di no */
	}
	if (freerdp_settings_get_uint32(imp, FreeRDP_PointerCacheSize) == 0)
	{
		avviso("il client non ha cache dei puntatori: chiudo");
		congeda(peer, ERRINFO_BAD_CAPABILITIES, "cache puntatori a zero");
		return TRUE; /* si prosegue solo per poter dire di no */
	}
	if (!freerdp_settings_get_bool(imp, FreeRDP_FastPathOutput))
	{
		avviso("il client non fa fastpath in uscita: chiudo");
		congeda(peer, ERRINFO_BAD_CAPABILITIES, "niente fastpath");
		return TRUE; /* si prosegue solo per poter dire di no */
	}
	return TRUE;
}

/* ------------------------------------------------------------------ *
 * Il portiere, il registro delle connessioni e il congedo pilotato
 * ------------------------------------------------------------------ */
static void registra_connessione(Server *server, ContestoPeer *cp)
{
	g_mutex_lock(&server->lucchetto);
	g_ptr_array_add(server->contesti, cp);
	g_mutex_unlock(&server->lucchetto);
}

static void dimentica_connessione(Server *server, ContestoPeer *cp)
{
	g_mutex_lock(&server->lucchetto);
	g_ptr_array_remove_fast(server->contesti, cp);
	g_mutex_unlock(&server->lucchetto);
}

void server_congeda_tutti(Server *server, uint32_t codice, const char *perche)
{
	guint quante = 0;

	if (!server)
		return;

	g_mutex_lock(&server->lucchetto);
	for (guint i = 0; i < server->contesti->len; i++)
	{
		ContestoPeer *cp = g_ptr_array_index(server->contesti, i);

		/* Si segna il motivo e si sveglia il thread.  Niente di piu': qui non
		 * si tocca il peer, che appartiene al SUO thread — toccarlo da fuori
		 * sarebbe una corsa fra chi congeda e chi sta spedendo un fotogramma. */
		g_atomic_int_set(&cp->motivo, (gint) codice);
		SetEvent(cp->evento_stop);
		quante++;
	}
	g_mutex_unlock(&server->lucchetto);

	if (quante)
		informazione("congedo %u connessioni: %s", quante, perche);
}

void server_smonta_palco(Server *server)
{
	if (server)
		palco_smonta(server->palco);
}

guint server_connessioni_attive(Server *server)
{
	guint quante;

	if (!server)
		return 0;
	g_mutex_lock(&server->lucchetto);
	quante = server->contesti->len;
	g_mutex_unlock(&server->lucchetto);
	return quante;
}

TipoCompositore server_compositore(Server *server)
{
	return server ? palco_compositore(server->palco) : COMPOSITORE_AUTO;
}

void server_sentinella(Server *server, Sentinella *sentinella)
{
	server->sentinella = sentinella;
}

/*
 * Le regole d'accesso di §3.4, applicate nell'ordine in cui contano.
 *
 * Stanno QUI, in `PostConnect`, e non all'accettazione del socket, perche' un
 * rifiuto va DETTO: `ERRINFO_SERVER_DENIED_CONNECTION` esiste apposta, e ogni
 * client moderno lo legge.  Chi riceve solo una chiusura di socket mostra
 * «errore di rete» e l'utente non impara niente (R12).
 */
static BOOL regole_di_accesso(freerdp_peer *peer)
{
	ContestoPeer *cp = (ContestoPeer *) peer->context;
	Server *server = cp->server;
	char descrizione[128] = "";

	/* 1. La sessione LOCALE vince, sempre.  Caso 6 della tabella delle nove
	 *    combinazioni. */
	if (sentinella_locale_presente(server->sentinella, descrizione, sizeof descrizione))
	{
		avviso("rifiuto: l'utente ha gia' una sessione grafica locale (%s)", descrizione);
		congeda(peer, ERRINFO_SERVER_DENIED_CONNECTION, "c'e' gia' una sessione locale");
		return FALSE;
	}

	/* 2. Una connessione per volta.  Caso 9: si legge «seconda connessione
	 *    SIMULTANEA» — se il client precedente se n'e' andato, il posto e' gia'
	 *    libero e chi torna si riaggancia. */
	if (!g_atomic_int_compare_and_exchange(&server->occupato, 0, 1))
	{
		avviso("rifiuto: c'e' gia' un client collegato");
		congeda(peer, ERRINFO_SERVER_DENIED_CONNECTION, "c'e' gia' qualcuno");
		return FALSE;
	}
	cp->tiene_il_posto = TRUE;
	registra_connessione(server, cp);
	return TRUE;
}

/* ------------------------------------------------------------------ *
 * Input (fase 4)
 *
 * I gestori si installano SOLO dopo che la guardia si e' aperta, e in piu'
 * verificano `autenticato` a ogni evento.  E' difesa in profondita' voluta
 * (§3.4 di SPECIFICA.md): fra l'arrivo di un evento e la chiusura di una
 * connessione rifiutata passa un istante, e in quell'istante nessuno deve
 * poter comandare nulla.
 *
 * Qui dentro non si aspetta niente: si accoda e si torna. Una chiamata che
 * attende dentro il ciclo del protocollo ferma la connessione intera.
 * ------------------------------------------------------------------ */
static Palco *palco_della_connessione(rdpInput *rdp_input)
{
	ContestoPeer *cp = (ContestoPeer *) rdp_input->context;

	if (!cp || !cp->autenticato)
		return NULL;
	return cp->server->palco;
}

static BOOL su_tastiera(rdpInput *rdp_input, UINT16 flags, UINT8 codice)
{
	Palco *palco = palco_della_connessione(rdp_input);
	Input *input = palco_input_prendi(palco);

	if (input)
		input_tasto(input, flags, codice);
	palco_input_lascia(palco);
	return TRUE;
}

static BOOL su_tastiera_unicode(rdpInput *rdp_input, UINT16 flags, UINT16 carattere)
{
	Palco *palco = palco_della_connessione(rdp_input);
	Input *input = palco_input_prendi(palco);

	if (input)
		input_tasto_unicode(input, flags, carattere);
	palco_input_lascia(palco);
	return TRUE;
}

/*
 * Il puntatore si scarta mentre la geometria non e' stabile — e SOLO il
 * puntatore.
 *
 * E' quel che fa il riferimento, dove la guardia sta dentro
 * `grd_rdp_layout_manager_transform_position`: fuori dallo stato ATTESA_CONFIG
 * la trasformazione rifiuta le coordinate, perche' una coordinata assoluta si
 * riscala su una regione che in quel momento sta cambiando misura, e il
 * risultato sarebbe un puntatore che salta.
 *
 * La tastiera invece passa: non ha geometria da riscalare, e scartare un tasto
 * significa perdere una lettera — il genere di difetto che §5.8 di
 * SPECIFICA.md ha gia' pagato una volta.
 */
static gboolean geometria_ferma(rdpInput *rdp_input)
{
	ContestoPeer *cp = (ContestoPeer *) rdp_input->context;

	if (cp && g_atomic_int_get(&cp->geometria_instabile))
	{
		traccia("evento del puntatore scartato: la geometria sta cambiando");
		return FALSE;
	}
	return TRUE;
}

static BOOL su_mouse(rdpInput *rdp_input, UINT16 flags, UINT16 x, UINT16 y)
{
	Palco *palco;
	Input *input;

	/* Si esce PRIMA di prendere il lucchetto: `palco_input_prendi` e
	 * `palco_input_lascia` sono una coppia, e un ramo che prende senza
	 * lasciare blocca lo smontaggio del palco per sempre. */
	if (!geometria_ferma(rdp_input))
		return TRUE;

	palco = palco_della_connessione(rdp_input);
	input = palco_input_prendi(palco);
	if (input)
		input_mouse(input, flags, x, y);
	palco_input_lascia(palco);
	return TRUE;
}

static BOOL su_mouse_esteso(rdpInput *rdp_input, UINT16 flags, UINT16 x, UINT16 y)
{
	Palco *palco;
	Input *input;

	if (!geometria_ferma(rdp_input))
		return TRUE;

	palco = palco_della_connessione(rdp_input);
	input = palco_input_prendi(palco);
	if (input)
		input_mouse_esteso(input, flags, x, y);
	palco_input_lascia(palco);
	return TRUE;
}

static BOOL su_sincronizza(rdpInput *rdp_input, UINT32 flags)
{
	Palco *palco = palco_della_connessione(rdp_input);
	Input *input = palco_input_prendi(palco);

	if (input)
		input_sincronizza(input, flags);
	palco_input_lascia(palco);
	return TRUE;
}

/*
 * La guardia (R14), e perche' sta QUI e non in peer->Logon.
 *
 * `peer->Logon` sembra il posto giusto e non lo e': FreeRDP lo chiama alla
 * NEGOZIAZIONE, e nel ramo senza NLA gli passa un'identita' VUOTA
 * (`libfreerdp/core/peer.c`, «IFCALLRESULT(TRUE, client->Logon, client,
 * &client->identity, FALSE)»).  Un server che autentica li' non autentica
 * niente — che e' esattamente il difetto da cui R14 nasce, in una forma nuova.
 *
 * Le credenziali del Client Info PDU arrivano allo stato
 * SECURE_SETTINGS_EXCHANGE e finiscono nelle impostazioni; `PostConnect` viene
 * dopo, quindi qui ci sono davvero.  E siccome tornare FALSE da qui chiude la
 * connessione prima dell'attivazione, chi non passa non vede un pixel.
 */
static BOOL peer_post_connect(freerdp_peer *peer)
{
	ContestoPeer *cp = (ContestoPeer *) peer->context;
	rdpSettings *imp = peer->context->settings;
	const char *utente;
	const char *dominio;
	const char *parola;

	/* Gia' respinto in `Capabilities`: si sta arrivando all'attivazione solo per
	 * poterglielo dire, e nel frattempo non gli si allestisce niente. */
	if (cp->rifiuto)
		return TRUE;

	/* §3.3 — senza canali dinamici non c'e' EGFX, e senza EGFX non c'e' nulla. */
	if (!WTSVirtualChannelManagerIsChannelJoined(cp->vcm, DRDYNVC_SVC_CHANNEL_NAME))
	{
		avviso("il client non ha aperto il canale DRDYNVC: chiudo");
		congeda(peer, ERRINFO_BAD_CAPABILITIES, "niente DRDYNVC");
		return TRUE; /* si prosegue solo per poter dire di no */
	}

	if (cp->server->opzioni.senza_autenticazione)
	{
		avviso("autenticazione DISATTIVATA da riga di comando: e' un banco, non un server");
		cp->autenticato = TRUE;
	}
	else
	{
		utente = freerdp_settings_get_string(imp, FreeRDP_Username);
		dominio = freerdp_settings_get_string(imp, FreeRDP_Domain);
		parola = freerdp_settings_get_string(imp, FreeRDP_Password);

		if (!autenticazione_verifica(utente, dominio, parola))
		{
			cp->autenticato = FALSE;
			congeda(peer, ERRINFO_SERVER_DENIED_CONNECTION, "credenziali rifiutate");
			return TRUE; /* si prosegue solo per poter dire di no */
		}
		cp->autenticato = TRUE;
		informazione("autenticato: %s", utente);
	}

	if (!regole_di_accesso(peer))
		return TRUE; /* si prosegue solo per poter dire di no */

	/*
	 * La misura della connessione passa dallo STESSO filtro del MONITOR_LAYOUT
	 * (§12.1 di gnome-remote-desktop.md: le regole sono identiche per tutte le
	 * sorgenti).  Se il Client Core Data porta una misura inaccettabile non c'e'
	 * niente da montare, e lo si dice con il codice che esiste apposta.
	 */
	{
		g_autoptr(GError) sbaglio_misura = NULL;
		g_autofree char *descrizione = NULL;

		if (!misura_da_client(imp, &cp->misura, &sbaglio_misura))
		{
			errore("misura del client rifiutata: %s", sbaglio_misura->message);
			congeda(peer, ERRINFO_BAD_MONITOR_DATA, "misura del client non valida");
			return TRUE; /* si prosegue solo per poter dire di no */
		}
		descrizione = misura_descrivi(&cp->misura);
		informazione("client «%s», desktop %s",
		             freerdp_settings_get_string(imp, FreeRDP_ClientHostname) ?: "?", descrizione);
	}

	/*
	 * Il desktop si allestisce QUI, prima della negoziazione EGFX, per due
	 * motivi.
	 *
	 * Il primo: la misura del client si legge dal Client Core Data, che a
	 * questo punto c'e' gia'.  Il secondo, che conta di piu': quando la
	 * pipeline grafica sara' pronta, il primo fotogramma dovra' essere gia'
	 * disponibile — «il desktop compare ALL'ISTANTE, non si forma
	 * progressivamente» e' un controllo di §9 di REFERENCE.md, non un
	 * dettaglio estetico.
	 *
	 * Puo' volerci parecchio, se la sessione grafica va avviata da zero: si sta
	 * sul thread di QUESTA connessione, quindi non si ferma nessun altro.
	 */
	if (!cp->server->opzioni.immagine_di_prova)
	{
		g_autoptr(GError) sbaglio = NULL;

		/*
		 * ⛔ LA MISURA DEL CLIENT ARRIVA FIN QUI, e su KDE decide il desktop.
		 *    `--virtual` vuole `--width/--height` all'AVVIO: la misura del primo
		 *    client che si collega diventa quella della sessione, ed e' la
		 *    decisione dell'utente dell'8 agosto — misura fissa alla connessione —
		 *    presa alla lettera invece che subita.
		 */
		if (!sessione_assicura(cp->server->opzioni.comando_sessione,
		                       palco_compositore(cp->server->palco), cp->misura.larghezza,
		                       cp->misura.altezza, NULL, &sbaglio))
		{
			errore("sessione grafica non disponibile: %s", sbaglio->message);
			congeda(peer, ERRINFO_GRAPHICS_SUBSYSTEM_FAILED, "nessuna sessione grafica");
			return TRUE; /* si prosegue solo per poter dire di no */
		}
		if (!palco_assicura(cp->server->palco, cp->misura.larghezza, cp->misura.altezza,
		                    cp->server->opzioni.fotogrammi_al_secondo, &sbaglio))
		{
			errore("cattura del desktop non avviata: %s", sbaglio->message);
			congeda(peer, ERRINFO_GRAPHICS_SUBSYSTEM_FAILED, "cattura non avviata");
			return TRUE; /* si prosegue solo per poter dire di no */
		}

		/*
		 * ⛔ LA MISURA DELLA TELA E' QUELLA DEL PALCO, NON QUELLA CHIESTA.
		 *
		 *    Su Mutter coincidono — il monitor virtuale si fa della misura chiesta
		 *    — e questa riga non fa niente.  Su KWin no: la misura la decide il
		 *    compositore (`palco.h`), e dichiarare al client una tela piu' grande
		 *    di quel che si cattura significa un desktop che ne copre una parte,
		 *    col resto grigio, senza alcun errore.
		 *
		 * ⛔ E IL CLIENT NON SCALA NIENTE — questa riga lo diceva, ed era FALSO.
		 *    [M, 8 agosto 2026, e l'ha trovato l'utente: «non riesco a vedere
		 *    tutto lo schermo, la risoluzione sembra ignorata»]
		 *
		 *    `xfreerdp3` apre una finestra grande quanto la tela dichiarata: se il
		 *    desktop e' 1920x1080 e lo schermo di chi guarda e' piu' piccolo, la
		 *    finestra non ci sta e basta.  La scalatura lato client esiste, ma
		 *    passa da `MAPSURFACETOSCALEDOUTPUT` — che il 7 agosto abbiamo
		 *    misurato essere resa da UN CLIENT SU TRE (§10.2 di REFERENCE.md).
		 *
		 *    Quindi su KWin 6.3.6 la misura del desktop la decide **la prima
		 *    connessione**, e per cambiarla bisogna far finire la sessione.  Lo si
		 *    dice, invece di lasciare credere a una scalatura che non avviene.
		 */
		{
			uint32_t vera_l = 0, vera_a = 0;

			palco_misura(cp->server->palco, &vera_l, &vera_a);
			if (vera_l && (vera_l != cp->misura.larghezza || vera_a != cp->misura.altezza))
			{
				avviso("il desktop e' %ux%u, non i %ux%u che hai chiesto: su questo "
				       "compositore la misura la fissa la PRIMA connessione, e per cambiarla "
				       "bisogna uscire dalla sessione. La finestra del client sara' grande "
				       "%ux%u",
				       vera_l, vera_a, cp->misura.larghezza, cp->misura.altezza, vera_l,
				       vera_a);
				cp->misura.larghezza = vera_l;
				cp->misura.altezza = vera_a;
			}
		}
	}

	/*
	 * I gestori d'input si installano QUI, cioe' dopo che la guardia si e'
	 * aperta: chi non e' passato di qui non ne ha nemmeno uno, e non comanda
	 * nulla per costruzione invece che per controllo.
	 */
	if (cp->server->palco && palco_input_prendi(cp->server->palco))
	{
		rdpInput *ingresso = peer->context->input;

		palco_input_lascia(cp->server->palco);

		ingresso->KeyboardEvent = su_tastiera;
		ingresso->UnicodeKeyboardEvent = su_tastiera_unicode;
		ingresso->MouseEvent = su_mouse;
		ingresso->ExtendedMouseEvent = su_mouse_esteso;
		ingresso->SynchronizeEvent = su_sincronizza;
		informazione("tastiera e mouse collegati alla sessione");
	}
	else if (cp->server->palco)
	{
		palco_input_lascia(cp->server->palco);
	}

	return TRUE;
}

/*
 * La sessione RDP e' attiva: da adesso un PDU di dati arriva davvero.
 *
 * E' il primo istante in cui `SET_ERROR_INFO` ha senso, quindi e' qui che si
 * spediscono i rifiuti decisi prima.  Chi e' stato respinto non ha montato
 * nulla e non tiene il posto: gli si deve solo il motivo.
 */
/*
 * Nasconde il puntatore che il CLIENT disegna da se'.
 *
 * ⛔ SERVE DOVE IL COMPOSITORE DISEGNA IL CURSORE DENTRO L'IMMAGINE, e su KWin
 *    con `--virtual` lo fa sempre: il backend virtuale non ha un piano cursore
 *    hardware, quindi KWin ripiega sul cursore software, che finisce nel
 *    framebuffer che catturiamo (`compositore.h`).  Senza questa riga se ne
 *    vedono DUE — quello del client, che segue il mouse all'istante, e quello di
 *    KDE, che lo insegue dentro il video.
 *
 *    [M, 8 agosto 2026, e l'ha visto l'utente: «e' quello di KDE che segue
 *    quello vero».  E' anche l'unica cura possibile: quello di KDE non si puo'
 *    togliere.]
 *
 * ⚠ IL PREZZO, e va detto: il puntatore si muove alla latenza del VIDEO invece
 *   che a quella della rete.  Su una rete di casa e' un fotogramma — a 60 al
 *   secondo, diciassette millesimi — e si vede solo muovendo il mouse in fretta.
 *   Su un collegamento povero si sentira'.
 *
 * ⚠ E NON si fa su Mutter: la' il cursore resta fuori dall'immagine, e
 *   nascondere quello del client lascerebbe l'utente senza alcun puntatore —
 *   cioe' un difetto molto peggiore di quello che si sta curando.
 *
 * `SYSPTR_NULL` e' RDP di base (MS-RDPBCGR 2.2.9.1.1.4.3): lo capiscono tutti e
 * tre i client di riferimento, e non richiede la cache dei cursori.
 */
static void nascondi_puntatore_del_client(freerdp_peer *peer)
{
	ContestoPeer *cp = (ContestoPeer *) peer->context;
	POINTER_SYSTEM_UPDATE sistema = { 0 };
	rdpPointerUpdate *puntatore = peer->context->update->pointer;

	if (!compositore_cursore_nell_immagine(server_compositore(cp->server)))
		return;
	if (!puntatore || !puntatore->PointerSystem)
		return;

	sistema.type = SYSPTR_NULL;
	if (puntatore->PointerSystem(peer->context, &sistema))
		informazione("puntatore del client nascosto: su questo compositore il cursore e' gia' "
		             "dentro l'immagine, e mostrarli tutti e due sarebbe peggio");
	else
		avviso("il client non ha accettato di nascondere il proprio puntatore: se ne vedranno "
		       "due");
}

static BOOL peer_attivato(freerdp_peer *peer)
{
	ContestoPeer *cp = (ContestoPeer *) peer->context;

	cp->attivo = TRUE;

	if (cp->rifiuto)
	{
		congeda(peer, cp->rifiuto, cp->rifiuto_perche);
		return FALSE;
	}

	/*
	 * Qui e non prima: un aggiornamento del puntatore e' un PDU di dati, e prima
	 * dell'attivazione non ha dove andare — la stessa ragione per cui il congedo
	 * di R12 si dice proprio in questa funzione.
	 */
	nascondi_puntatore_del_client(peer);
	return TRUE;
}

/* ------------------------------------------------------------------ *
 * EGFX
 * ------------------------------------------------------------------ */
static UINT32 orario_impacchettato(void)
{
	/* [MS-RDPEGFX] 2.2.2.14: ora<<22 | minuti<<16 | secondi<<10 | millesimi */
	g_autoptr(GDateTime) adesso = g_date_time_new_now_local();
	return ((UINT32) g_date_time_get_hour(adesso) << 22) |
	       ((UINT32) g_date_time_get_minute(adesso) << 16) |
	       ((UINT32) g_date_time_get_second(adesso) << 10) |
	       ((UINT32) (g_date_time_get_microsecond(adesso) / 1000) & 0x3FF);
}

/*
 * Dichiara la tela grafica della misura indicata.
 *
 * ⛔ R7 — CON EGFX ATTIVO, IL RIDIMENSIONAMENTO NON PASSA DALLA RIATTIVAZIONE.
 *    La misura nuova si comunica RIDICHIARANDO QUESTA TELA: superficie nuova
 *    piu' `ResetGraphics`.  Un `Deactivate All` costringerebbe il client a
 *    rifare lo scambio di capacita', e il client Android dopo una riattivazione
 *    NON RINEGOZIA PIU' EGFX per il resto della sessione — da li' in poi resta
 *    il ripiego a pixel non compressi, dieci megabyte a fotogramma.  Misurato
 *    il 2 agosto.
 *
 * Serve sia la prima volta, dopo il `CapsConfirm`, sia a ogni cambio di misura:
 * e' esattamente lo stesso lavoro, e tenerlo in un posto solo e' cio' che
 * impedisce che i due percorsi divergano.
 */
static gboolean allestisci_tela(ContestoPeer *cp, const Misura *misura)
{
	rdpSettings *imp = cp->ctx.settings;
	UINT32 larghezza = misura->larghezza;
	UINT32 altezza = misura->altezza;
	RDPGFX_RESET_GRAPHICS_PDU reset = { 0 };
	MONITOR_DEF monitor = { 0 };
	RDPGFX_CREATE_SURFACE_PDU crea = { 0 };
	RDPGFX_MAP_SURFACE_TO_OUTPUT_PDU mappa = { 0 };
	RDPGFX_DELETE_SURFACE_PDU cancella = { 0 };

	/*
	 * R6 — «tutte le superfici vanno cancellate prima» di un `ResetGraphics`.
	 * Alla prima volta non ce n'e' nessuna; a ogni ridimensionamento c'e'
	 * quella di prima, e lasciarla in vita significa due superfici che si
	 * contendono la stessa uscita.
	 *
	 * L'identificativo si CAMBIA invece di riusarlo: quello vecchio il client
	 * lo ha appena visto morire, e riproporglielo con una misura diversa e' il
	 * genere di ambiguita' che un client severo risolve non disegnando.
	 */
	if (cp->superficie_creata)
	{
		cancella.surfaceId = cp->id_superficie;
		if (cp->gfx->DeleteSurface(cp->gfx, &cancella) != CHANNEL_RC_OK)
		{
			errore("DeleteSurface fallita");
			return FALSE;
		}
		cp->superficie_creata = FALSE;
		if (++cp->id_superficie == 0)
			cp->id_superficie = 1;
	}

	/*
	 * Codificatore e tela si rifanno: entrambi nascono con la misura ALLINEATA
	 * dentro (R4), e un codificatore H.264 riconfigurato a caldo su misure
	 * diverse non e' una cosa che si chieda a `h264_context_reset` a meta'
	 * flusso.  Un contesto nuovo produce anche il fotogramma chiave che il
	 * decodificatore del client, ripartito da zero, sta aspettando.
	 */
	g_clear_pointer(&cp->cod, codificatore_libera);
	g_clear_pointer(&cp->immagine, immagine_libera);

	cp->immagine = immagine_nuova(larghezza, altezza);
	/*
	 * Le superfici del palco, se sta lavorando a copia zero.  Il codificatore ci
	 * si apre sopra e da li' in poi il fotogramma non viene piu' copiato: dalla
	 * cattura alla codifica resta sulla scheda.  Con NULL — o con un codec che i
	 * pixel li vuole in CPU, come RemoteFX Progressive — vale il percorso di
	 * sempre.
	 */
	cp->cod = codificatore_nuovo(cp->codec, cp->server->opzioni.codificatore,
	                             cp->codec == CODIFICATORE_AVC420 ? palco_superfici(cp->server->palco)
	                                                              : NULL,
	                             immagine_larghezza_allineata(cp->immagine),
	                             immagine_altezza_allineata(cp->immagine),
	                             cp->server->opzioni.bitrate_kbit,
	                             cp->server->opzioni.fotogrammi_al_secondo);
	if (!cp->cod)
		return FALSE;

	/*
	 * ⛔ E ADESSO SI DICE AL PALCO DA CHE PARTE CI SERVONO I PIXEL.
	 *
	 *    Non lo decide il codec, lo decide IL CODIFICATORE CHE SI E' APERTO
	 *    DAVVERO — ed e' la stessa lezione di R27, applicata a un'altra
	 *    domanda: fra il chiedere e l'ottenere c'e' di mezzo cosa la macchina sa
	 *    fare, e dedurlo invece di leggerlo produce due strade sotto la stessa
	 *    etichetta.  Tre casi diversi finiscono tutti qui:
	 *
	 *      - RemoteFX Progressive, cioe' ogni client Android (§1.4 di
	 *        REFERENCE.md): e' un codec a wavelet e gira in CPU;
	 *      - `--codificatore libx264`, che e' AVC420 ma in CPU, ed e' il termine
	 *        di paragone con cui si misura la fase 9;
	 *      - un `h264_vaapi` che non si e' aperto sulle superfici del palco e ha
	 *        ripiegato sul proprio nodo.
	 *
	 *    In tutti e tre il codificatore vuole i pixel in memoria, e il palco puo'
	 *    starli consegnando alla scheda — dove pixel in memoria non ce ne sono
	 *    affatto.  Chi ne cercasse non troverebbe un errore: troverebbe il nulla,
	 *    cioe' uno schermo fermo.
	 *
	 *    Il codificatore NON va riaperto dopo: quando non sa lavorare sulle
	 *    superfici le ignora gia' adesso, quindi quello aperto qui sopra e' gia'
	 *    quello giusto.  Cambia solo da dove arrivano i fotogrammi.
	 */
	if (!cp->server->opzioni.immagine_di_prova && cp->server->palco && !cp->pixel_in_cpu &&
	    !codificatore_su_superfici(cp->cod))
	{
		cp->pixel_in_cpu = TRUE;
		palco_pixel_in_cpu(cp->server->palco, TRUE);
	}

	/* R6 — mai con l'elenco monitor vuoto: mstsc disegna fuori posto.
	 * R5 — il MONITOR_DEF usa bordi INCLUSIVI, al contrario di tutto il resto. */
	monitor.left = 0;
	monitor.top = 0;
	monitor.right = (INT32) larghezza - 1;
	monitor.bottom = (INT32) altezza - 1;
	monitor.flags = MONITOR_PRIMARY;

	reset.width = larghezza;
	reset.height = altezza;
	reset.monitorCount = 1;
	reset.monitorDefArray = &monitor;
	if (cp->gfx->ResetGraphics(cp->gfx, &reset) != CHANNEL_RC_OK)
	{
		errore("ResetGraphics fallita");
		return FALSE;
	}

	/* R1 — creare la superficie e agganciarla all'uscita sono DUE comandi, e
	 * servono entrambi.  FreeRDP e Android disegnano lo stesso anche senza il
	 * secondo; mstsc e RDM no, ed e' costato due giorni il 2 agosto. */
	crea.surfaceId = cp->id_superficie;
	crea.width = (UINT16) immagine_larghezza_allineata(cp->immagine);
	crea.height = (UINT16) immagine_altezza_allineata(cp->immagine);
	crea.pixelFormat = GFX_PIXEL_FORMAT_XRGB_8888;
	if (cp->gfx->CreateSurface(cp->gfx, &crea) != CHANNEL_RC_OK)
	{
		errore("CreateSurface fallita");
		return FALSE;
	}

	mappa.surfaceId = cp->id_superficie;
	mappa.outputOriginX = 0;
	mappa.outputOriginY = 0;
	if (cp->gfx->MapSurfaceToOutput(cp->gfx, &mappa) != CHANNEL_RC_OK)
	{
		errore("MapSurfaceToOutput fallita");
		return FALSE;
	}
	cp->superficie_creata = TRUE;

	/*
	 * R9 — l'ultimo fotogramma conservato si RISPEDISCE sulla tela nuova.
	 *
	 * Azzerare `visto` fa risultare «nuovo» il fotogramma che il palco tiene da
	 * parte.  Senza, su un desktop fermo non arriverebbe piu' niente e la tela
	 * appena creata resterebbe vuota a tempo indeterminato — che e' proprio il
	 * nero che R9 esiste per togliere, solo spostato dopo un ridimensionamento
	 * invece che dopo una connessione.
	 */
	cp->visto = 0;

	/*
	 * Le impostazioni di FreeRDP si allineano alla misura nuova.
	 *
	 * Non fa partire nessun PDU — la riattivazione la innesca `DesktopResize`,
	 * che non si chiama — ma tiene coerente cio' che chiunque altro legga da
	 * qui, a cominciare dal registro.  Due verita' sulla misura del desktop
	 * dentro lo stesso processo sono una diagnosi sbagliata che aspetta.
	 */
	freerdp_settings_set_uint32(imp, FreeRDP_DesktopWidth, larghezza);
	freerdp_settings_set_uint32(imp, FreeRDP_DesktopHeight, altezza);

	cp->misura = *misura;
	cp->gfx_pronto = TRUE;
	return TRUE;
}

static UINT su_caps_advertise(RdpgfxServerContext *gfx, const RDPGFX_CAPS_ADVERTISE_PDU *avviso_pdu)
{
	ContestoPeer *cp = gfx->custom;
	RDPGFX_CAPSET *scelta = NULL;
	UINT32 versione_scelta = 0;
	gboolean avc = FALSE;
	RDPGFX_CAPS_CONFIRM_PDU conferma = { 0 };

	/* R2 — si sceglie la piu' alta che il client dichiara, e si conferma
	 * QUELLA SOLA.  L'elenco e' percorso dall'alto: la prima corrispondenza e'
	 * la migliore. */
	for (gsize v = 0; v < G_N_ELEMENTS(versioni_egfx) && !scelta; v++)
	{
		for (UINT16 i = 0; i < avviso_pdu->capsSetCount; i++)
		{
			if (avviso_pdu->capsSets[i].version == versioni_egfx[v])
			{
				scelta = &avviso_pdu->capsSets[i];
				versione_scelta = versioni_egfx[v];
				break;
			}
		}
	}

	if (!scelta)
	{
		errore("nessuna versione EGFX in comune con il client");
		congeda(cp->ctx.peer, ERRINFO_BAD_CAPABILITIES, "nessuna versione EGFX comune");
		return ERROR_INTERNAL_ERROR;
	}

	/* R3 — la logica dei flag AVC, che decide il codec per tutta la
	 * connessione.  La 10.1 non ha un campo flags valido: li' `flags` vale 0 e
	 * la formula da comunque AVC disponibile, che e' l'esito giusto. */
	if (versione_scelta >= RDPGFX_CAPVERSION_10)
		avc = !(scelta->flags & RDPGFX_CAPS_FLAG_AVC_DISABLED);
	else if (versione_scelta == RDPGFX_CAPVERSION_81)
		avc = !!(scelta->flags & RDPGFX_CAPS_FLAG_AVC420_ENABLED);
	else
		avc = FALSE;

	informazione("EGFX negoziato: versione 0x%08X, flag 0x%02X → AVC %s", versione_scelta,
	             scelta->flags, avc ? "disponibile" : "NON disponibile");

	conferma.capsSet = scelta;
	if (gfx->CapsConfirm(gfx, &conferma) != CHANNEL_RC_OK)
	{
		errore("CapsConfirm fallita");
		return ERROR_INTERNAL_ERROR;
	}

	/* Il codec si sceglie QUI e non si cambia piu' (R3): vale per tutta la
	 * connessione, ridimensionamenti compresi. */
	cp->codec = avc ? CODIFICATORE_AVC420 : CODIFICATORE_PROGRESSIVE;

	if (!allestisci_tela(cp, &cp->misura))
	{
		congeda(cp->ctx.peer, ERRINFO_GRAPHICS_SUBSYSTEM_FAILED, "tela grafica non allestita");
		return ERROR_INTERNAL_ERROR;
	}
	informazione("tela pronta: desktop %ux%u, superficie %ux%u, codec %s", cp->misura.larghezza,
	             cp->misura.altezza, immagine_larghezza_allineata(cp->immagine),
	             immagine_altezza_allineata(cp->immagine), codificatore_nome(cp->cod));

	/*
	 * ⛔ E QUI, non prima, si guarda se c'era una misura in attesa (R8).
	 *
	 *    I client Android chiedono la propria misura ENTRO UN DECIMO DI SECONDO
	 *    dalla connessione, cioe' prima di aver negoziato EGFX.  Applicarla
	 *    subito vorrebbe dire non avere una tela da ridichiarare, quindi
	 *    ricadere nella riattivazione — R7.  Si rinvia, e questo e' il momento
	 *    in cui il rinvio scade bene: la sveglia fa raccogliere l'attesa al
	 *    ciclo della connessione, che e' il solo che puo' toccare la tela.
	 */
	SetEvent(cp->evento_misura);
	return CHANNEL_RC_OK;
}

static UINT su_frame_acknowledge(RdpgfxServerContext *gfx,
                                 const RDPGFX_FRAME_ACKNOWLEDGE_PDU *riscontro)
{
	ContestoPeer *cp = gfx->custom;

	/*
	 * ⛔ QUESTO GIRA SUL THREAD DI EGFX, non su quello della connessione:
	 *    `rdpgfx_server_context_new` mette `ownThread = TRUE` e il canale si
	 *    legge da la'.  Tutto quel che si tocca qui dev'essere protetto — ed e'
	 *    il motivo per cui il conto dei fotogrammi in volo vive dentro `Rete`,
	 *    sotto il suo lucchetto, invece di stare qui come intero.
	 *
	 * Il caso `queueDepth == 0xFFFFFFFF` (§5 di REFERENCE.md) lo gestisce
	 * `rete_riscontro`: e' il regolatore che deve sapere di non avere piu'
	 * niente da contare.
	 */
	rete_riscontro(cp->rete, riscontro->frameId, riscontro->queueDepth,
	               riscontro->totalFramesDecoded);
	return CHANNEL_RC_OK;
}

static UINT su_cache_import_offer(RdpgfxServerContext *gfx,
                                  const RDPGFX_CACHE_IMPORT_OFFER_PDU *offerta)
{
	/* §5 — va RISPOSTO, anche a vuoto: ignorarlo lascia il client in attesa.
	 * La cache non la usiamo, come nel riferimento. */
	RDPGFX_CACHE_IMPORT_REPLY_PDU risposta = { 0 };
	return gfx->CacheImportReply(gfx, &risposta);
}

static UINT su_qoe_frame_acknowledge(RdpgfxServerContext *gfx,
                                     const RDPGFX_QOE_FRAME_ACKNOWLEDGE_PDU *qoe)
{
	return CHANNEL_RC_OK; /* accettare e ignorare */
}

static gboolean apri_egfx(ContestoPeer *cp)
{
	cp->gfx = rdpgfx_server_context_new(cp->vcm);
	if (!cp->gfx)
	{
		errore("rdpgfx_server_context_new fallita");
		return FALSE;
	}
	cp->gfx->custom = cp;
	cp->gfx->rdpcontext = &cp->ctx;
	cp->gfx->CapsAdvertise = su_caps_advertise;
	cp->gfx->FrameAcknowledge = su_frame_acknowledge;
	cp->gfx->CacheImportOffer = su_cache_import_offer;
	cp->gfx->QoeFrameAcknowledge = su_qoe_frame_acknowledge;

	if (!cp->gfx->Open(cp->gfx))
	{
		errore("apertura del canale EGFX fallita");
		return FALSE;
	}
	cp->gfx_aperto = TRUE;
	diagnostica("canale EGFX aperto, aspetto CapsAdvertise");
	return TRUE;
}

/* ------------------------------------------------------------------ *
 * MS-RDPEDISP — la risoluzione dinamica (fase 6)
 *
 * Il piu' semplice dei canali e il piu' utile: il server apre
 * `Microsoft::Windows::RDS::DisplayControl`, manda le proprie capacita', e il
 * client risponde quando vuole con un `MONITOR_LAYOUT` — tipicamente quando
 * l'utente ridimensiona la finestra o gira il telefono.
 *
 * ⚠ MSTSC NON RIDIMENSIONA DA SE'.  Apre il canale (§1.2 di REFERENCE.md lo ha
 *   misurato fra i suoi canali dinamici) ma non manda un `MONITOR_LAYOUT`
 *   trascinando il bordo: e' scritto in §5.7 di SPECIFICA.md — «mstsc: negozia
 *   EGFX subito, NON ridimensiona da se'» — ed e' il motivo per cui le regole
 *   1 e 2 di quel paragrafo sono state trovate dal client Android e non da lui.
 *
 *   Ne discendono due cose pratiche, e vanno tenute insieme:
 *
 *     1. la prova della fase 6 NON si puo' fare su mstsc.  Trascinare il bordo
 *        li' non prova niente: se l'immagine segue e' perche' il client scala,
 *        se non segue non e' un difetto nostro.  Il ridimensionamento si prova
 *        su `xfreerdp3 /dynamic-resolution` e su RDM, che lo fanno davvero;
 *     2. su mstsc la fase 6 e' una prova di NON REGRESSIONE, e va fatta lo
 *        stesso: il canale si apre anche per lui, le capacita' partono anche
 *        per lui, e un PDU malformato o una superficie cancellata a sproposito
 *        si vedrebbero proprio la' — su mstsc, che e' il client severo.
 *
 *   Il codice qui sotto non guarda CHI e' il client: se un giorno mstsc
 *   comincera' a mandare `MONITOR_LAYOUT` — l'opzione «aggiorna la risoluzione
 *   al ridimensionamento» esiste — funzionera' senza toccare una riga.  Quel
 *   che non si fa e' fondare una prova su un comportamento che non c'e'.
 * ------------------------------------------------------------------ */

/* Quanto si e' disposti a rinviare un layout arrivato prima di EGFX (R8). */
#define RINVIO_MASSIMO_MS 1500

/*
 * ⛔ L'ASSESTAMENTO, e non e' un ritardo di comodo: e' la misura che tiene
 *    insieme una raffica.  Misurato il 5 agosto 2026, sul banco della fase 6.
 *
 * Applicare ogni `MONITOR_LAYOUT` appena arriva sembra la cosa giusta e non lo
 * e'.  Un ridimensionamento del palco costa circa mezzo secondo — aggiornamento
 * dei parametri PipeWire piu' attesa del ridisegno (R10) — e in quel mezzo
 * secondo il client continua a mandarne.  Quando finalmente si ridichiara la
 * tela, al client si comunica una misura che nel frattempo e' gia' vecchia: lui
 * si adegua, se ne accorge, e la richiede indietro.  Sul banco questo produce
 * un ping-pong che va avanti da solo per decine di secondi DOPO che l'utente ha
 * smesso di trascinare: 8 trascinamenti, 38 richieste, 37 ridimensionamenti.
 *
 * Che la causa sia la nostra latenza e non il protocollo lo dice la misura di
 * controllo, fatta con la scena sintetica — stesso client, stesso banco, stesso
 * codice del protocollo, ma ridimensionamento istantaneo perche' non c'e' un
 * palco: 8 trascinamenti, 8 richieste, 8 ridimensionamenti, nessun ping-pong.
 * E' la lezione di §5.4 di SPECIFICA.md applicata a una latenza invece che a un
 * codec.
 *
 * Da cui: si aspetta che le richieste SMETTANO di arrivare, e si applica solo
 * l'ultima.  Su Android questo vale doppio, perche' li' ogni cambio e' anche un
 * riavvio del decodificatore (§4.3 di client-android.md).
 *
 * La quiete e' un po' piu' larga dei 200 ms con cui il client di FreeRDP
 * accorpa per conto suo (`RESIZE_MIN_DELAY`): piu' stretta e si accorperebbe
 * quel che il client ha gia' accorpato, cioe' niente.
 */
#define ASSESTAMENTO_MS 300

/*
 * Il tetto: oltre questo si applica comunque, anche se le richieste continuano
 * ad arrivare.  Senza, un client che ne manda una ogni 250 ms — o un ping-pong
 * gia' avviato — terrebbe il desktop fermo alla misura di partenza per sempre,
 * e l'utente vedrebbe un ridimensionamento che «non funziona» invece di uno
 * lento.
 */
#define ATTESA_MASSIMA_MS 1200

/*
 * ⛔ L'ECO, ed e' la scoperta che e' costata piu' tempo di tutta la fase.
 *   Misurata il 5 agosto 2026.
 *
 * L'assestamento accorpa le raffiche e non basta, perche' non tocca il caso
 * peggiore: una richiesta che arriva MENTRE un ridimensionamento e' in volo.
 * Quella richiesta descrive la finestra com'era PRIMA che il client sapesse la
 * nostra risposta; noi la applichiamo, il client si adegua e ci rimanda quella
 * di prima — e da li' i due lati si rincorrono all'infinito.
 *
 * Sul banco: 8 trascinamenti in 2,4 s producevano 38 richieste e 37
 * ridimensionamenti, che continuavano DA SOLI per oltre quaranta secondi dopo
 * che nessuno toccava piu' niente.  Su Android sarebbero stati altrettanti
 * riavvii del decodificatore (§4.3 di client-android.md).
 *
 * ⛔ CHE FOSSE LA NOSTRA LATENZA E NON IL PROTOCOLLO lo dicono due misure di
 *    controllo, e nessuna delle due e' stata dedotta:
 *
 *      scena sintetica, stessa raffica     8 richieste, 8 applicazioni, ferma
 *        (ridimensionamento istantaneo:     — il protocollo, da solo, converge
 *         non c'e' palco da riconfigurare)
 *
 *      desktop vero, 3 trascinamenti       3 richieste, 3 applicazioni, ferma
 *        distanziati di 3 s                 — nessuna richiesta arriva in volo
 *
 *    Cioe': l'eco compare quando, e solo quando, una richiesta arriva mentre il
 *    palco sta cambiando misura.  E' la stessa forma della regola di §7.2 sul
 *    puntatore — l'input che descrive una geometria instabile non vale — solo
 *    applicata al `MONITOR_LAYOUT` invece che alle coordinate.
 *
 * La firma dell'eco e' precisa e non si confonde con niente: chiede ESATTAMENTE
 * la misura che si e' appena lasciata, e arriva entro poche decine di
 * millisecondi dalla ridichiarazione della tela (25–100 ms, misurati).  La
 * finestra e' tenuta stretta apposta: fuori di li' un ritorno alla misura di
 * prima e' un utente che ha trascinato avanti e indietro, e va onorato.
 *
 * ⛔ IL CONFRONTO SI FA ALL'ARRIVO, in `su_layout_monitor`, e non quando la
 *    richiesta viene raccolta: fra i due momenti c'e' l'assestamento, e l'eco
 *    si riconosce proprio dall'arrivare SUBITO.  Rimandare il confronto
 *    significa misurare un tempo gia' scaduto, cioe' non riconoscerla piu'.
 */
#define ECO_MS 250

static void ridimensionamento_lascia(Ridimensionamento *ridim)
{
	if (ridim && g_atomic_int_dec_and_test(&ridim->riferimenti))
		g_free(ridim);
}

static gpointer thread_ridimensiona(gpointer dati)
{
	Ridimensionamento *ridim = dati;
	g_autoptr(GError) sbaglio = NULL;

	if (palco_ridimensiona(ridim->server->palco, ridim->larghezza, ridim->altezza,
	                       ridim->fotogrammi_al_secondo, &sbaglio))
	{
		g_atomic_int_set(&ridim->esito, RIDIM_FATTO);
	}
	else
	{
		errore("il palco non ha preso la misura %ux%u: %s", ridim->larghezza, ridim->altezza,
		       sbaglio->message);
		g_atomic_int_set(&ridim->esito, RIDIM_GUASTO);
	}

	ridimensionamento_lascia(ridim);
	return NULL;
}

static void avvia_ridimensionamento(ContestoPeer *cp, const Misura *chiesta)
{
	g_autofree char *descrizione = misura_descrivi(chiesta);
	Ridimensionamento *ridim;
	GThread *thread;

	informazione("il client chiede una misura nuova: %s", descrizione);

	/*
	 * PRIMO PASSO, e viene prima di toccare qualunque cosa: si inibisce il
	 * rendering.  Da qui in poi `manda_fotogramma` non spedisce e il puntatore
	 * si scarta, perche' fra la vecchia misura e la nuova non deve partire
	 * niente — un fotogramma a meta' strada arriverebbe su una superficie che
	 * sta per non esistere piu'.
	 */
	g_atomic_int_set(&cp->geometria_instabile, 1);
	cp->misura_chiesta = *chiesta;

	if (cp->server->opzioni.immagine_di_prova)
	{
		/* La scena sintetica non ha un palco da ridimensionare.  Serve, e non
		 * e' un caso di comodo: e' cio' che rende provabile il protocollo del
		 * ridimensionamento dove una sessione grafica non c'e' affatto — la
		 * stessa ragione per cui la scena esiste (§5.4 di SPECIFICA.md). */
		cp->stato_misura = MISURA_DA_RIPRENDERE;
		return;
	}

	ridim = g_new0(Ridimensionamento, 1);
	ridim->riferimenti = 2; /* uno del ciclo, uno del thread */
	ridim->server = cp->server;
	ridim->larghezza = chiesta->larghezza;
	ridim->altezza = chiesta->altezza;
	ridim->fotogrammi_al_secondo = cp->server->opzioni.fotogrammi_al_secondo;
	ridim->esito = RIDIM_IN_CORSO;

	cp->ridim = ridim;
	cp->stato_misura = MISURA_INIBITA;

	thread = g_thread_new("remotix-misura", thread_ridimensiona, ridim);
	g_thread_unref(thread);
}

/*
 * Un passo della macchina di §7.2, eseguito dal ciclo della connessione.
 *
 * Restituisce FALSE quando la connessione deve chiudere: in quel caso il
 * congedo e' gia' stato dichiarato (R12).
 */
static gboolean passo_misura(ContestoPeer *cp)
{
	switch (cp->stato_misura)
	{
		case MISURA_STABILE:
		{
			Misura chiesta;
			gboolean c_e;
			gint64 adesso = g_get_monotonic_time();
			gint64 da_us, ultima_us;
			gboolean assestata;

			g_mutex_lock(&cp->lucchetto_misura);
			c_e = cp->c_e_attesa;
			chiesta = cp->misura_in_attesa;
			da_us = cp->attesa_da_us;
			ultima_us = cp->ultima_da_us;
			/*
			 * Si raccoglie solo quando la serie si e' ASSESTATA: nessuna
			 * richiesta nuova da `ASSESTAMENTO_MS`, oppure il tetto raggiunto.
			 * Finche' arrivano, la coda continua a sostituire — che e' la
			 * regola di §7.2, qui con un tempo attaccato.
			 */
			assestata = (adesso - ultima_us >= (gint64) ASSESTAMENTO_MS * 1000) ||
			            (adesso - da_us >= (gint64) ATTESA_MASSIMA_MS * 1000);
			if (c_e && cp->gfx_pronto && assestata)
			{
				cp->c_e_attesa = FALSE;
				cp->rinvio_detto = FALSE;
			}
			g_mutex_unlock(&cp->lucchetto_misura);

			if (!c_e)
				return TRUE;
			if (cp->gfx_pronto && !assestata)
				return TRUE; /* stanno ancora arrivando: si aspetta */

			if (!cp->gfx_pronto)
			{
				/*
				 * R8 — un `MONITOR_LAYOUT` arrivato prima della negoziazione
				 * EGFX SI RINVIA.  Resta dov'e', in coda, e verra' raccolto dal
				 * `SetEvent` che parte alla fine del `CapsAdvertise`.
				 *
				 * Il riferimento, se la pipeline non arrivasse affatto,
				 * ripiegherebbe sulla riattivazione della sessione.  Qui quel
				 * ramo non esiste, ed e' una scelta e non una dimenticanza:
				 * §3.3 di REFERENCE.md impone di CHIUDERE il client che non
				 * dichiara la pipeline grafica, quindi una connessione senza
				 * EGFX non arriva mai fin qui.  Se l'attesa si allunga, lo si
				 * dice una volta e si continua ad aspettare — che e' meglio di
				 * una riattivazione, la quale su Android spegne EGFX per il
				 * resto della sessione (R7).
				 */
				if (!cp->rinvio_detto && g_get_monotonic_time() - da_us > RINVIO_MASSIMO_MS * 1000)
				{
					cp->rinvio_detto = TRUE;
					avviso("layout monitor rinviato da piu' di %d ms: la pipeline grafica non e' "
					       "ancora pronta e senza tela non c'e' niente da ridichiarare",
					       RINVIO_MASSIMO_MS);
				}
				return TRUE;
			}

			if (misura_uguale(&chiesta, &cp->misura))
			{
				/* E' il caso normale del client Android, che ripete sul canale
				 * DISP la misura che aveva gia' dichiarato alla connessione. */
				diagnostica("la misura chiesta (%ux%u) e' gia' quella in uso: niente da fare",
				            chiesta.larghezza, chiesta.altezza);
				return TRUE;
			}

			avvia_ridimensionamento(cp, &chiesta);
			return TRUE;
		}

		case MISURA_INIBITA:
			switch (g_atomic_int_get(&cp->ridim->esito))
			{
				case RIDIM_IN_CORSO:
					return TRUE;
				case RIDIM_FATTO:
					cp->stato_misura = MISURA_DA_RIPRENDERE;
					break;
				default:
					/* Il palco non ha preso la misura nuova nemmeno col
					 * ripiego: la sessione grafica non e' piu' servibile, e lo
					 * si dice invece di continuare a spedire su una superficie
					 * che non corrisponde piu' a niente. */
					ridimensionamento_lascia(cp->ridim);
					cp->ridim = NULL;
					g_atomic_int_set(&cp->geometria_instabile, 0);
					cp->stato_misura = MISURA_STABILE;
					congeda(cp->ctx.peer, ERRINFO_GRAPHICS_SUBSYSTEM_FAILED,
					        "il desktop non ha preso la misura nuova");
					return FALSE;
			}
			ridimensionamento_lascia(cp->ridim);
			cp->ridim = NULL;
			/* Si prosegue col passo dopo al giro seguente. */
			return TRUE;

		case MISURA_DA_RIPRENDERE:
		{
			uint32_t prima_l = cp->misura.larghezza;
			uint32_t prima_a = cp->misura.altezza;
			g_autofree char *descrizione = NULL;
			Misura lasciata = cp->misura;

			/*
			 * ⛔ ANCHE QUI LA MISURA E' QUELLA DEL PALCO.  Il client ha chiesto
			 *    la sua; il palco puo' aver servito un'altra, perche' su KWin il
			 *    ridimensionamento non c'e' fino alla 6.8.  Ridichiarare la tela
			 *    con quella chiesta lascerebbe il client a disegnare su una
			 *    superficie che i fotogrammi non riempiono.
			 */
			if (!cp->server->opzioni.immagine_di_prova)
			{
				uint32_t vera_l = 0, vera_a = 0;

				palco_misura(cp->server->palco, &vera_l, &vera_a);
				if (vera_l)
				{
					cp->misura_chiesta.larghezza = vera_l;
					cp->misura_chiesta.altezza = vera_a;
				}
			}

			/*
			 * E se la misura non e' cambiata, non si ridichiara niente.
			 *
			 * Non e' un'ottimizzazione: ridichiarare la tela costa al client la
			 * distruzione e la ricreazione della superficie, e su Android anche un
			 * riavvio del decodificatore (§4.3 di client-android.md).  Farlo per
			 * tornare esattamente dov'eravamo sarebbe pagare quel prezzo per
			 * niente — e su un compositore che non ridimensiona succederebbe a ogni
			 * trascinamento del bordo.
			 */
			if (misura_uguale(&cp->misura_chiesta, &cp->misura))
			{
				diagnostica("la misura servita non e' cambiata (%ux%u): la tela resta com'e'",
				            prima_l, prima_a);
				g_atomic_int_set(&cp->geometria_instabile, 0);
				cp->stato_misura = MISURA_STABILE;
				return TRUE;
			}

			/*
			 * R7 — si ridichiara la tela, NON si riattiva la sessione.  E'
			 * questa riga che il registro deve mostrare a ogni
			 * ridimensionamento; una seconda «nuova sorgente» al suo posto
			 * significa che e' avvenuta una riattivazione (§9 di REFERENCE.md).
			 */
			if (!allestisci_tela(cp, &cp->misura_chiesta))
			{
				congeda(cp->ctx.peer, ERRINFO_GRAPHICS_SUBSYSTEM_FAILED,
				        "tela grafica non ridichiarata");
				return FALSE;
			}

			descrizione = misura_descrivi(&cp->misura);
			informazione("ridimensiono la tela grafica: %ux%u → %s, superficie %ux%u", prima_l,
			             prima_a, descrizione, immagine_larghezza_allineata(cp->immagine),
			             immagine_altezza_allineata(cp->immagine));

			/* ULTIMO PASSO: si disinibisce.  Da adesso i fotogrammi ripartono —
			 * a cominciare da quello conservato, che `allestisci_tela` ha fatto
			 * tornare «nuovo» (R9) — e il puntatore torna a valere. */
			g_atomic_int_set(&cp->geometria_instabile, 0);
			cp->stato_misura = MISURA_STABILE;

			g_mutex_lock(&cp->lucchetto_misura);
			/* Da adesso, e per ECO_MS, chiedere indietro la misura appena
			 * lasciata e' un'eco e non un'intenzione. */
			cp->eco_misura = lasciata;
			cp->eco_fino_a_us = g_get_monotonic_time() + (gint64) ECO_MS * 1000;
			/*
			 * ⛔ E SE E' RIMASTA UNA RICHIESTA IN CODA, L'ASSESTAMENTO RIPARTE.
			 *
			 *    Quella richiesta e' arrivata MENTRE la geometria cambiava:
			 *    descrive una finestra che non aveva ancora visto la misura
			 *    nuova, quindi non e' un'intenzione fresca.  Applicarla subito
			 *    e' cio' che faceva perdere l'ULTIMO trascinamento della
			 *    raffica — ridimensionando, si sovrascriveva la finestra del
			 *    client prima che facesse in tempo a mandare la misura vera, e
			 *    il desktop restava indietro di un passo.  Misurato il 5 agosto.
			 */
			if (cp->c_e_attesa)
			{
				cp->attesa_da_us = g_get_monotonic_time();
				cp->ultima_da_us = cp->attesa_da_us;
			}
			g_mutex_unlock(&cp->lucchetto_misura);

			/* Se nel frattempo ne e' arrivata un'altra — ed e' quel che succede
			 * trascinando il bordo — sta gia' in coda: si sveglia il ciclo
			 * perche' la raccolga senza aspettare il prossimo fotogramma. */
			SetEvent(cp->evento_misura);
			return TRUE;
		}
	}

	return TRUE;
}

/*
 * Un `MONITOR_LAYOUT` dal client.
 *
 * ⛔ GIRA SUL THREAD INTERNO DEL CANALE DISP, non su quello della connessione:
 *    `disp_server_open` ne crea uno suo che legge il canale e richiama questo
 *    gestore.  Qui quindi si VALIDA e si ACCODA, e nient'altro — toccare la
 *    tela da qui sarebbe scrivere sul canale EGFX da due thread insieme.
 *
 * La coda ha un posto solo, e chi arriva SOSTITUISCE chi c'era: trascinando il
 * bordo di una finestra i client mandano raffiche, e applicarle una per una
 * significherebbe una sequenza di rimontaggi di cui conta solo l'ultimo — che
 * su Android sono anche altrettanti riavvii del decodificatore.
 */
static UINT su_layout_monitor(DispServerContext *disp,
                              const DISPLAY_CONTROL_MONITOR_LAYOUT_PDU *pdu)
{
	ContestoPeer *cp = disp->custom;
	g_autoptr(GError) sbaglio = NULL;
	Misura nuova;

	if (!cp->disp_pronto)
	{
		/*
		 * Il client ha parlato prima che le capacita' fossero partite.  Il
		 * riferimento chiude la sessione con `ERRINFO_BAD_MONITOR_DATA`; qui si
		 * IGNORA e si continua, per la stessa ragione per cui si ignora una
		 * misura fuori limite (vedi sotto): buttare giu' una sessione viva per
		 * una scortesia del client e' una cura peggiore del male.
		 */
		avviso("layout monitor arrivato prima delle capacita' DISP: lo ignoro");
		return CHANNEL_RC_OK;
	}

	if (!misura_da_layout(pdu, &nuova, &sbaglio))
	{
		/*
		 * ⛔ SI RIFIUTA LA RICHIESTA, NON LA SESSIONE.
		 *
		 *    E' §4.1 di client-android.md, che sul caso concreto e' esplicito:
		 *    una finestra ridotta a striscia in multi-finestra Android sta
		 *    sotto i 200 px di lato, «e la richiesta va rifiutata invece che
		 *    applicata».  Il client resta collegato alla misura di prima, che
		 *    e' esattamente cio' che l'utente si aspetta quando rimpicciolisce
		 *    troppo una finestra.
		 */
		avviso("layout monitor rifiutato, la sessione continua com'e': %s", sbaglio->message);
		return CHANNEL_RC_OK;
	}

	g_mutex_lock(&cp->lucchetto_misura);

	/*
	 * L'eco si riconosce QUI, all'arrivo, ed e' l'unico posto in cui si puo':
	 * la sua firma e' «la misura appena lasciata, richiesta subito».  Vedi
	 * ECO_MS — applicarla avvia una rincorsa fra i due lati che non finisce.
	 */
	if (g_get_monotonic_time() < cp->eco_fino_a_us && misura_uguale(&nuova, &cp->eco_misura))
	{
		g_mutex_unlock(&cp->lucchetto_misura);
		informazione("scarto l'eco del ridimensionamento: il client richiede %ux%u, cioe' la "
		             "misura che ha appena lasciato",
		             nuova.larghezza, nuova.altezza);
		return CHANNEL_RC_OK;
	}

	if (cp->c_e_attesa)
		diagnostica("raffica di ridimensionamenti: la misura in coda viene sostituita");
	else
		cp->attesa_da_us = g_get_monotonic_time();
	cp->ultima_da_us = g_get_monotonic_time();
	cp->misura_in_attesa = nuova;
	cp->c_e_attesa = TRUE;
	g_mutex_unlock(&cp->lucchetto_misura);

	SetEvent(cp->evento_misura);
	return CHANNEL_RC_OK;
}

static BOOL su_disp_canale_assegnato(DispServerContext *disp, UINT32 id_canale)
{
	ContestoPeer *cp = disp->custom;

	cp->disp_canale = id_canale;
	diagnostica("canale DISP: identificativo %u", id_canale);
	return TRUE;
}

/*
 * Il client ha risposto alla creazione di un canale dinamico.
 *
 * ⛔ LE CAPACITA' DISP SI MANDANO QUI, non subito dopo `Open`.  `Open` apre il
 *    canale dal nostro lato e chiede al client di crearlo; finche' il client
 *    non ha risposto, quel canale non ha un altro capo.  E' il punto in cui il
 *    riferimento manda `DisplayControlCaps` (`dvc_creation_status`), e sta li'
 *    per questo.
 *
 * Gira sul thread della connessione, dentro
 * `WTSVirtualChannelManagerCheckFileDescriptor`.  La richiamata e' una sola per
 * gestore dei canali, quindi arriva anche per EGFX: si guarda l'identificativo.
 */
static BOOL su_creazione_canale(void *dati, UINT32 id_canale, INT32 esito)
{
	ContestoPeer *cp = dati;

	/* La richiamata e' UNA per tutti i canali dinamici: si guarda di chi e'.
	 * L'audio ha il proprio identificativo, e un rifiuto li' significa sessione
	 * muta, non sessione rotta. */
	if (cp->altoparlante && id_canale == altoparlante_canale(cp->altoparlante))
	{
		altoparlante_esito_canale(cp->altoparlante, esito);
		return TRUE;
	}

	if (!cp->disp_aperto || id_canale != cp->disp_canale)
		return TRUE;

	if (esito < 0)
	{
		/*
		 * Il client non ha voluto il canale.  Non e' un guasto: e' una sessione
		 * senza risoluzione dinamica, cioe' quel che REMOTIX faceva fino alla
		 * fase 5.  Si degrada e si dichiara (§2 di SPECIFICA.md).
		 */
		avviso("il client non ha aperto il canale DISP (esito %d): niente risoluzione dinamica "
		       "per questa sessione",
		       esito);
		return TRUE;
	}

	cp->disp_pronto = TRUE;
	if (cp->disp->DisplayControlCaps(cp->disp) != CHANNEL_RC_OK)
	{
		avviso("capacita' DISP non spedite: il client non chiedera' ridimensionamenti");
		cp->disp_pronto = FALSE;
		return TRUE;
	}
	informazione("canale DISP aperto: al massimo %u monitor, %ux%u per lato",
	             cp->disp->MaxNumMonitors, cp->disp->MaxMonitorAreaFactorA,
	             cp->disp->MaxMonitorAreaFactorB);
	return TRUE;
}

static gboolean apri_disp(ContestoPeer *cp)
{
	cp->disp = disp_server_context_new(cp->vcm);
	if (!cp->disp)
	{
		avviso("disp_server_context_new fallita: niente risoluzione dinamica");
		return FALSE;
	}
	cp->disp->custom = cp;
	cp->disp->rdpcontext = &cp->ctx;

	/*
	 * UN monitor, e lo si DICHIARA.
	 *
	 * Il multi-monitor e' fuori scope (§3.1 di SPECIFICA.md).  Dichiarare 1
	 * invece di 16 non e' una rinuncia nascosta: e' il modo in cui il protocollo
	 * permette di dirlo, e un client corretto non chiedera' mai il secondo.  Se
	 * lo chiedesse comunque, FreeRDP scarta il PDU prima di consegnarcelo — e
	 * con lui, purtroppo, chiude il proprio thread di lettura: da quel momento
	 * la sessione resterebbe senza ridimensionamenti.  Motivo in piu' per
	 * dichiarare il vero.
	 *
	 * I due fattori d'area sono quelli del riferimento, e sono il limite per
	 * lato di MS-RDPEDISP.
	 */
	cp->disp->MaxNumMonitors = 1;
	cp->disp->MaxMonitorAreaFactorA = 8192;
	cp->disp->MaxMonitorAreaFactorB = 8192;

	cp->disp->ChannelIdAssigned = su_disp_canale_assegnato;
	cp->disp->DispMonitorLayout = su_layout_monitor;

	WTSVirtualChannelManagerSetDVCCreationCallback(cp->vcm, su_creazione_canale, cp);

	if (cp->disp->Open(cp->disp) != CHANNEL_RC_OK)
	{
		avviso("apertura del canale DISP fallita: niente risoluzione dinamica");
		disp_server_context_free(cp->disp);
		cp->disp = NULL;
		return FALSE;
	}
	cp->disp_aperto = TRUE;
	diagnostica("canale DISP aperto, aspetto che il client lo confermi");
	return TRUE;
}

/* ------------------------------------------------------------------ *
 * MS-RDPEA — l'audio in uscita (fase 8)
 *
 * Tre pezzi, e ciascuno sta dove sta per un motivo:
 *
 *   - il CANALE lo apre il ciclo, quando drdynvc e' pronto, come EGFX e DISP;
 *   - il FORMATO lo sceglie il client, e lo si scopre sul thread del canale;
 *   - la CATTURA la accende il ciclo, appena il formato si sa: aprire un flusso
 *     PipeWire da dentro una richiamata di FreeRDP significherebbe far
 *     aspettare il canale mentre PipeWire negozia.
 * ------------------------------------------------------------------ */
static void accendi_ascolto(ContestoPeer *cp)
{
	uint32_t frequenza = 0;
	uint32_t canali = 0;
	Suono *suono;
	g_autoptr(GError) sbaglio = NULL;

	if (cp->ascolto_acceso || !cp->altoparlante)
		return;
	if (!altoparlante_formato(cp->altoparlante, &frequenza, &canali))
		return; /* il client non ha ancora scelto: si riprovera' al giro dopo */

	suono = palco_suono_prendi(cp->server->palco);
	if (!suono)
	{
		/* Nessun sink nella sessione: lo ha gia' detto il palco, e riprovarci a
		 * ogni giro riempirebbe il registro di una notizia sola. */
		palco_suono_lascia(cp->server->palco);
		cp->ascolto_acceso = TRUE;
		return;
	}

	if (suono_ascolto_avvia(suono, frequenza, canali, altoparlante_campioni, cp->altoparlante,
	                        &sbaglio))
		informazione("suono collegato alla sessione: %u Hz, %u canali", frequenza, canali);
	else
		avviso("cattura audio non avviata (%s): la sessione resta muta", sbaglio->message);

	/* Acceso o no, non ci si riprova: un guasto qui non si cura ripetendolo. */
	cp->ascolto_acceso = TRUE;
	palco_suono_lascia(cp->server->palco);
}

static void spegni_ascolto(ContestoPeer *cp)
{
	Suono *suono;

	if (!cp->ascolto_acceso)
		return;

	suono = palco_suono_prendi(cp->server->palco);
	if (suono)
		suono_ascolto_ferma(suono);
	palco_suono_lascia(cp->server->palco);
	cp->ascolto_acceso = FALSE;
}

static gboolean apri_audio(ContestoPeer *cp)
{
	cp->altoparlante = altoparlante_apri(cp->vcm, &cp->ctx);
	if (!cp->altoparlante)
	{
		/* Come per DISP: non e' obbligatorio, e una sessione muta e' meglio di
		 * nessuna sessione (§2 di SPECIFICA.md). */
		avviso("canale audio non aperto: la sessione sara' muta");
		return FALSE;
	}
	return TRUE;
}

/* ------------------------------------------------------------------ *
 * MS-RDPECLIP — gli appunti (fase 8)
 *
 * Il canale e' statico, quindi non passa da drdynvc: si apre appena la sessione
 * RDP e' attiva e la guardia si e' aperta.  Come DISP e come l'audio, non e'
 * obbligatorio — una sessione senza copia-incolla e' meno di quel che si
 * voleva, ma e' molto piu' di niente (§2 di SPECIFICA.md).
 * ------------------------------------------------------------------ */
static void apri_appunti(ContestoPeer *cp)
{
	if (cp->scambio || !cp->server->palco)
		return;

	/* Il client deve avere unito il canale: senza, `WTSVirtualChannelOpen`
	 * fallisce e basta, e il registro direbbe solo «non aperto». */
	if (!WTSVirtualChannelManagerIsChannelJoined(cp->vcm, CLIPRDR_SVC_CHANNEL_NAME))
	{
		if (!cp->appunti_detti)
		{
			cp->appunti_detti = TRUE;
			informazione("il client non ha aperto il canale degli appunti: niente copia-incolla");
		}
		return;
	}

	cp->scambio = scambio_apri(cp->vcm, &cp->ctx, cp->server->palco);
	if (cp->scambio)
	{
		cp->appunti_detti = TRUE;
		informazione("appunti collegati alla sessione");
		return;
	}

	/*
	 * ⛔ IL GUASTO SI DICE UNA VOLTA, e il tentativo si ripete in silenzio.
	 *
	 *    Questa funzione la chiama il ciclo della connessione a ogni giro, perche'
	 *    il canale puo' aprirsi tardi.  Finche' non riesce, `cp->scambio` resta
	 *    NULL e si ritenta — che e' giusto — ma dirlo ogni volta significa una
	 *    riga di registro per ogni giro del ciclo.  Su KDE, dove gli appunti
	 *    passano da un'altra strada e questa non riuscira' mai (voce 4 del piano
	 *    di fase 11), erano centinaia di righe che seppellivano tutto il resto.
	 */
	if (!cp->appunti_detti)
	{
		cp->appunti_detti = TRUE;
		avviso("appunti non collegati: la sessione resta senza copia-incolla");
	}
}

/* ------------------------------------------------------------------ *
 * Soppressione dell'uscita e richiesta di ridisegno (MS-RDPBCGR 2.2.11.2-3)
 *
 * ⛔ IL CLIENT NON PUO' CHIEDERLO SE IL SERVER NON LO DICHIARA.  Le due
 *    capacita' stanno nel General Capability Set, e un client corretto tace se
 *    il server ha scritto zero.  REMOTIX scriveva zero: minimizzando la
 *    finestra di mstsc, il client non aveva modo di dire «fermati» e il server
 *    continuava a codificare e spedire dieci megabit al secondo verso una
 *    finestra che nessuno guardava.  §10.3 di gnome-remote-desktop.md e §7 di
 *    client-android.md lo chiedevano fin dallo studio: «spreco puro, su
 *    entrambe le batterie».
 *
 * ⚠ NON C'ENTRA CON LA PERSISTENZA DELLA SESSIONE.  Qui si ferma la sola
 *   SPEDIZIONE dei fotogrammi: la sessione grafica, il palco, le applicazioni,
 *   la cattura, l'audio e gli appunti continuano esattamente come prima.  E'
 *   una cosa diversa dalla disconnessione, che la fase 5 tratta altrove.
 *
 * Entrambe le richiamate girano sul thread della connessione, dentro
 * `CheckFileDescriptor`: possono toccare `visto` senza cerimonie.
 * ------------------------------------------------------------------ */
static BOOL su_soppressione(rdpContext *contesto, BYTE permetti, const RECTANGLE_16 *area)
{
	ContestoPeer *cp = (ContestoPeer *) contesto;

	if (!permetti)
	{
		informazione("il client non vuole piu' aggiornamenti dello schermo (finestra minimizzata?): "
		             "smetto di codificare");
		cp->uscita_soppressa = TRUE;
		return TRUE;
	}

	informazione("il client rivuole gli aggiornamenti%s: riprendo", area ? " (con area)" : "");
	cp->uscita_soppressa = FALSE;
	/* R9 applicata al ritorno: si rimanda subito l'ultimo fotogramma, o la
	 * finestra appena riaperta resterebbe su quel che c'era prima. */
	cp->visto = 0;
	SetEvent(cp->evento_misura);
	return TRUE;
}

static BOOL su_ridisegno(rdpContext *contesto, BYTE quante, const RECTANGLE_16 *aree)
{
	ContestoPeer *cp = (ContestoPeer *) contesto;

	/*
	 * Il client chiede di ridisegnare una parte dello schermo.  Noi mandiamo
	 * sempre il fotogramma intero, quindi le aree non servono: basta far
	 * risultare «nuovo» l'ultimo fotogramma.
	 */
	diagnostica("il client chiede un ridisegno di %u aree: rispedisco il fotogramma", quante);
	cp->visto = 0;
	SetEvent(cp->evento_misura);
	return TRUE;
}

static EsitoInvio manda_fotogramma(ContestoPeer *cp)
{
	RDPGFX_SURFACE_COMMAND cmd = { 0 };
	RDPGFX_START_FRAME_PDU inizio = { 0 };
	RDPGFX_END_FRAME_PDU fine = { 0 };

	if (!cp->gfx_pronto || !cp->autenticato)
		return INVIO_AVANTI;

	/*
	 * Il client ha detto che non guarda: non si codifica e non si spedisce.
	 * Sta PRIMA del regolatore e prima del prelievo dal palco, perche' il
	 * risparmio vero e' la codifica, non la scrittura.
	 */
	if (cp->uscita_soppressa)
		return INVIO_AVANTI;

	/*
	 * L'inibizione del rendering, e sta QUI perche' qui c'e' l'unico punto in
	 * cui un fotogramma parte.  Fra la misura vecchia e quella nuova non deve
	 * uscire niente: la superficie a cui il fotogramma si riferisce sta per
	 * essere cancellata, e un fotogramma che la insegue arriverebbe al client
	 * dopo la sua morte.
	 */
	if (g_atomic_int_get(&cp->geometria_instabile))
		return INVIO_AVANTI;

	/*
	 * Il regolatore (fase 7): non si spedisce piu' di quanto il client digerisca.
	 *
	 * Va PRIMA di prelevare dal palco: prelevare e poi rinunciare consumerebbe
	 * il fotogramma senza spedirlo, e su un desktop fermo non ne arriverebbe un
	 * altro (R9).
	 */
	if (!rete_c_e_posto(cp->rete))
		return INVIO_AVANTI;

	cmd.surfaceId = cp->id_superficie;
	cmd.contextId = 0;

	/*
	 * Due strade, e la differenza e' tutta in quanto lavoro si fa PRIMA di
	 * codificare.
	 *
	 *   a copia zero  il fotogramma e' gia' sulla scheda, gia' convertito e gia'
	 *                 allineato: si codifica e basta;
	 *   in memoria    il fotogramma si copia nella tela, si converte e si
	 *                 carica — ed e' la strada di sempre, obbligatoria per
	 *                 RemoteFX Progressive e per la scena sintetica.
	 */
	if (codificatore_su_superfici(cp->cod) && !cp->server->opzioni.immagine_di_prova)
	{
		AVFrame *superficie = NULL;
		gboolean compresso;

		switch (palco_preleva_superficie(cp->server->palco, &superficie, &cp->visto))
		{
			case PALCO_NUOVO:
				break;
			case PALCO_NIENTE:
				return INVIO_AVANTI;
			case PALCO_FINITA:
				return INVIO_SESSIONE_FINITA;
		}

		/* La spia all'altro capo: quel che il codificatore riceve davvero. */
		palco_spia_superficie(cp->server->palco, superficie);
		compresso = codificatore_comprimi_superficie(cp->cod, superficie, cp->misura.larghezza,
		                                             cp->misura.altezza, &cmd);
		/*
		 * Il riferimento si lascia SUBITO, anche quando la compressione e'
		 * riuscita: il pacchetto compresso non lo tiene, e trattenerlo un giro
		 * in piu' toglierebbe una superficie al palco proprio mentre ne sta
		 * cercando una libera.
		 */
		av_frame_free(&superficie);
		if (!compresso)
		{
			codificatore_rilascia(cp->cod);
			return INVIO_AVANTI;
		}
	}
	else
	{
		if (cp->server->opzioni.immagine_di_prova)
		{
			immagine_disegna(cp->immagine, (g_get_monotonic_time() - cp->avvio_us) / 1000);
		}
		else
		{
			switch (palco_preleva(cp->server->palco, cp->immagine, &cp->visto))
			{
				case PALCO_NUOVO:
					break;
				case PALCO_NIENTE:
					/* Il desktop e' fermo.  E' la condizione normale, non un
					 * guasto: Mutter manda un fotogramma solo quando qualcosa
					 * cambia, e chi consuma non deve interpretare il silenzio
					 * come un errore. */
					return INVIO_AVANTI;
				case PALCO_FINITA:
					return INVIO_SESSIONE_FINITA;
			}
		}

		if (!codificatore_comprimi(cp->cod, immagine_pixel(cp->immagine),
		                           immagine_passo(cp->immagine),
		                           immagine_larghezza_allineata(cp->immagine),
		                           immagine_altezza_allineata(cp->immagine),
		                           immagine_larghezza(cp->immagine),
		                           immagine_altezza(cp->immagine), &cmd))
		{
			codificatore_rilascia(cp->cod);
			return INVIO_AVANTI; /* niente di nuovo: non e' un errore */
		}
	}

	inizio.frameId = ++cp->id_fotogramma;
	inizio.timestamp = orario_impacchettato();
	fine.frameId = inizio.frameId;

	/*
	 * La misura di banda si stringe attorno al fotogramma, e attorno a QUESTO
	 * fotogramma soltanto.
	 *
	 * Il client conta i byte di ogni PDU che riceve fra lo Start e lo Stop —
	 * `rdp.c:1678` di FreeRDP li somma nel percorso di ricezione, canale
	 * dinamico compreso — quindi il carico della misura e' il fotogramma vero, e
	 * non serve spedire i dati di riempimento che il protocollo prevede per la
	 * misura alla connessione.
	 */
	rete_fotogramma_parte(cp->rete, codificatore_byte(cp->cod, &cmd));

	if (cp->gfx->SurfaceFrameCommand(cp->gfx, &cmd, &inizio, &fine) != CHANNEL_RC_OK)
	{
		errore("invio del fotogramma fallito");
		codificatore_rilascia(cp->cod);
		return INVIO_GUASTO;
	}
	rete_fotogramma_partito(cp->rete);
	codificatore_rilascia(cp->cod);
	traccia("fotogramma %u spedito", inizio.frameId);
	return INVIO_AVANTI;
}

/*
 * Opzioni TCP: accorgersi in fretta di chi se n'e' andato.
 *
 * ⛔ E' la conseguenza diretta della sessione unica: se si rifiuta la seconda
 *    connessione, un client sparito senza salutare — caduta di rete, portatile
 *    chiuso — terrebbe la porta sbarrata all'utente legittimo.
 *
 * ⛔ E IL KEEPALIVE DA SOLO NON BASTA, misurato il 3 agosto.  Il keepalive si
 *    applica solo a un socket INATTIVO, ed e' fatto per scoprire chi se n'e'
 *    andato mentre non si aveva niente da dirgli.  Se invece ci sono dati non
 *    riscontrati — e un server RDP ne ha quasi sempre — comanda l'RTO, che con
 *    i valori predefiniti insiste per **un quarto d'ora**.  Fingendo una rete
 *    che sparisce, dopo un minuto il server non se n'era ancora accorto e il
 *    socket era all'ottavo raddoppio del timer di ritrasmissione.
 *
 *    Il rimedio e' `TCP_USER_TIMEOUT`, che pone un tetto ASSOLUTO al tempo in
 *    cui i dati possono restare non riscontrati.  Trenta secondi, un po' piu'
 *    larghi dei venticinque del keepalive perche' qui si conta anche il tempo
 *    che serve ad accorgersi di dover cominciare a preoccuparsi.
 */
static void opzioni_tcp(int fd)
{
	int acceso = 1;
	int attesa = 10; /* prima sonda dopo 10 s di silenzio */
	int passo = 5;   /* poi una ogni 5 s                  */
	int tentativi = 3;
	int tetto_ms = 30000;

	/* TCP_NODELAY toglie i quaranta millesimi che Nagle metterebbe fra un tasto
	 * e la sua eco. */
	if (setsockopt(fd, IPPROTO_TCP, TCP_NODELAY, &acceso, sizeof acceso) < 0)
		diagnostica("TCP_NODELAY non impostato: %s", g_strerror(errno));
	setsockopt(fd, SOL_SOCKET, SO_KEEPALIVE, &acceso, sizeof acceso);
	setsockopt(fd, IPPROTO_TCP, TCP_KEEPIDLE, &attesa, sizeof attesa);
	setsockopt(fd, IPPROTO_TCP, TCP_KEEPINTVL, &passo, sizeof passo);
	setsockopt(fd, IPPROTO_TCP, TCP_KEEPCNT, &tentativi, sizeof tentativi);
	if (setsockopt(fd, IPPROTO_TCP, TCP_USER_TIMEOUT, &tetto_ms, sizeof tetto_ms) < 0)
		avviso("TCP_USER_TIMEOUT non impostato (%s): una caduta di rete potrebbe tenere la "
		       "porta occupata per un quarto d'ora",
		       g_strerror(errno));
}

/* ------------------------------------------------------------------ *
 * Il ciclo di una connessione, su un thread suo
 * ------------------------------------------------------------------ */
static gpointer thread_connessione(gpointer dati)
{
	GSocketConnection *connessione = dati;
	GSocket *socket = g_socket_connection_get_socket(connessione);
	Server *server = g_object_get_data(G_OBJECT(connessione), "server");
	freerdp_peer *peer = NULL;
	ContestoPeer *cp = NULL;
	rdpSettings *imp = NULL;
	HANDLE eventi[32] = { 0 };
	HANDLE evento_canale = NULL;
	gint64 prossimo_fotogramma;
	guint32 periodo_ms;
	UINT16 stato_dvc_visto = 0xFFFF;
	gboolean se_ne_va_lui = FALSE;

	opzioni_tcp(g_socket_get_fd(socket));
	peer = freerdp_peer_new(g_socket_get_fd(socket));
	if (!peer)
	{
		errore("freerdp_peer_new fallita");
		goto fine;
	}

	peer->ContextSize = sizeof(ContestoPeer);
	peer->ContextNew = contesto_nuovo;
	peer->ContextFree = contesto_libera;
	if (!freerdp_peer_context_new(peer))
	{
		errore("freerdp_peer_context_new fallita");
		goto fine;
	}

	cp = (ContestoPeer *) peer->context;
	cp->server = server;
	imp = peer->context->settings;

	/* §3.2 — sicurezza: TLS puro, niente NLA.  R13: regge su tutti e tre i
	 * client, e nessuno pretende NLA.  TLS 1.2 va lasciato acceso, perche' RDM
	 * non fa TLS 1.3 e un server solo-1.3 lo escluderebbe. */
	freerdp_settings_set_bool(imp, FreeRDP_RdpSecurity, FALSE);
	freerdp_settings_set_bool(imp, FreeRDP_TlsSecurity, TRUE);
	freerdp_settings_set_bool(imp, FreeRDP_NlaSecurity, FALSE);
	/* 0x0303 e' TLS 1.2 nella numerazione di OpenSSL, che e' quella che
	 * FreeRDP si aspetta qui.  Va lasciato acceso e non alzato a 1.3: RDM non
	 * fa TLS 1.3, e un server solo-1.3 escluderebbe il client Android di
	 * riferimento (R13).  Si scrive il numero invece di tirarsi dentro gli
	 * header di OpenSSL per una costante sola. */
	freerdp_settings_set_uint16(imp, FreeRDP_TLSMinVersion, 0x0303);

	/* Un esemplare NUOVO per ogni connessione: vedi il commento su Server. */
	{
		rdpCertificate *certificato = freerdp_certificate_new_from_pem(server->pem_certificato);
		rdpPrivateKey *chiave = freerdp_key_new_from_pem(server->pem_chiave);

		if (!certificato || !chiave)
		{
			errore("certificato o chiave non ricostruibili per questa connessione");
			freerdp_certificate_free(certificato);
			freerdp_key_free(chiave);
			goto fine;
		}
		freerdp_settings_set_pointer_len(imp, FreeRDP_RdpServerCertificate, certificato, 1);
		freerdp_settings_set_pointer_len(imp, FreeRDP_RdpServerRsaKey, chiave, 1);
	}

	freerdp_settings_set_uint32(imp, FreeRDP_OsMajorType, OSMAJORTYPE_UNIX);
	freerdp_settings_set_uint32(imp, FreeRDP_OsMinorType, OSMINORTYPE_PSEUDO_XSERVER);
	freerdp_settings_set_uint32(imp, FreeRDP_ColorDepth, 32);

	/* Accendere SupportGraphicsPipeline fa due cose: dichiara EGFX nelle
	 * capacita' E accende DYNVC_GFX_PROTOCOL_SUPPORTED nella risposta di
	 * negoziazione X.224 (§3.1).  L'altra bandiera richiesta,
	 * EXTENDED_CLIENT_DATA_SUPPORTED, FreeRDP la mette sempre. */
	freerdp_settings_set_bool(imp, FreeRDP_SupportGraphicsPipeline, TRUE);
	freerdp_settings_set_bool(imp, FreeRDP_GfxAVC444v2, FALSE);
	freerdp_settings_set_bool(imp, FreeRDP_GfxAVC444, FALSE);
	freerdp_settings_set_bool(imp, FreeRDP_GfxH264, FALSE); /* si accende al CapsAdvertise */
	freerdp_settings_set_bool(imp, FreeRDP_GfxSmallCache, FALSE);
	freerdp_settings_set_bool(imp, FreeRDP_GfxThinClient, FALSE);

	freerdp_settings_set_bool(imp, FreeRDP_SurfaceFrameMarkerEnabled, TRUE);
	freerdp_settings_set_bool(imp, FreeRDP_FrameMarkerCommandEnabled, TRUE);
	freerdp_settings_set_uint32(imp, FreeRDP_PointerCacheSize, 100);
	freerdp_settings_set_bool(imp, FreeRDP_FastPathOutput, TRUE);
	freerdp_settings_set_bool(imp, FreeRDP_NetworkAutoDetect, TRUE);
	/*
	 * Le due capacita' che permettono al client di dire «non guardo» e
	 * «ridisegnami»: senza dichiararle, un client corretto non le manda mai —
	 * e infatti mstsc, minimizzato, non mandava niente.
	 */
	freerdp_settings_set_bool(imp, FreeRDP_RefreshRect, TRUE);
	freerdp_settings_set_bool(imp, FreeRDP_SuppressOutput, TRUE);
	freerdp_settings_set_bool(imp, FreeRDP_SupportMultitransport, FALSE); /* niente UDP */
	freerdp_settings_set_uint32(imp, FreeRDP_VCFlags, VCCAPS_COMPR_SC);
	freerdp_settings_set_uint32(imp, FreeRDP_VCChunkSize, 16256);
	freerdp_settings_set_bool(imp, FreeRDP_HasExtendedMouseEvent, TRUE);
	freerdp_settings_set_bool(imp, FreeRDP_HasHorizontalWheel, TRUE);
	freerdp_settings_set_bool(imp, FreeRDP_HasRelativeMouseEvent, TRUE);
	freerdp_settings_set_bool(imp, FreeRDP_UnicodeInput, TRUE);

	peer->Capabilities = peer_capabilities;
	peer->PostConnect = peer_post_connect;
	peer->Activate = peer_attivato;

	/* Si installano subito: arrivano sul thread di questo ciclo, e non
	 * dipendono dall'autenticazione — un client che chiede di non ricevere
	 * niente va accontentato in ogni caso. */
	peer->context->update->SuppressOutput = su_soppressione;
	peer->context->update->RefreshRect = su_ridisegno;

	/*
	 * La misura della rete si allestisce QUI, prima di `Initialize`.
	 *
	 * ⛔ Non in `PostConnect`, che sarebbe il posto naturale: l'autodetect alla
	 *    connessione sta nella macchina a stati fra le impostazioni riservate e
	 *    le licenze, cioe' PRIMA che `PostConnect` venga chiamata.  Ganci messi
	 *    dopo perderebbero la prima misura dell'RTT — l'unica disponibile quando
	 *    si spedisce il primo fotogramma, che e' anche il momento in cui il
	 *    regolatore deve gia' sapere quanti tenerne in volo.
	 */
	cp->rete = rete_nuova(peer->context, server->opzioni.fotogrammi_al_secondo,
	                      server->opzioni.fingi_riscontri_sospesi);

	if (!peer->Initialize(peer))
	{
		errore("inizializzazione del peer fallita");
		goto fine;
	}

	informazione("connessione da %s", peer->hostname ? peer->hostname : "?");

	evento_canale = WTSVirtualChannelManagerGetEventHandle(cp->vcm);
	periodo_ms = 1000 / MAX(1u, server->opzioni.fotogrammi_al_secondo);
	prossimo_fotogramma = g_get_monotonic_time() + periodo_ms * 1000;

	while (TRUE)
	{
		guint32 n = 0;
		guint32 n_freerdp;
		gint64 adesso;
		DWORD attesa;

		eventi[n++] = cp->evento_stop;
		eventi[n++] = cp->evento_misura;
		eventi[n++] = evento_canale;
		n_freerdp = peer->GetEventHandles(peer, &eventi[n], 32 - n);
		if (!n_freerdp)
		{
			avviso("nessun descrittore dal peer: chiudo");
			break;
		}
		n += n_freerdp;

		adesso = g_get_monotonic_time();
		attesa = prossimo_fotogramma > adesso ? (DWORD) ((prossimo_fotogramma - adesso) / 1000) : 0;
		WaitForMultipleObjects(n, eventi, FALSE, attesa);

		if (WaitForSingleObject(cp->evento_stop, 0) == WAIT_OBJECT_0)
		{
			UINT32 motivo = (UINT32) g_atomic_int_get(&cp->motivo);

			if (motivo)
			{
				congeda(peer, motivo, "chiesto da fuori");
				goto chiudi;
			}
			break;
		}

		if (!peer->CheckFileDescriptor(peer))
		{
			/* Se ne va lui: il codice d'errore lo ha gia' messo FreeRDP, e
			 * sovrascriverlo sarebbe una bugia oltre che inutile. */
			informazione("il client se n'e' andato");
			se_ne_va_lui = TRUE;
			break;
		}

		if (peer->connected && WTSVirtualChannelManagerIsChannelJoined(cp->vcm, DRDYNVC_SVC_CHANNEL_NAME))
		{
			UINT16 stato = WTSVirtualChannelManagerGetDrdynvcState(cp->vcm);

			if (stato != stato_dvc_visto)
			{
				diagnostica("stato di drdynvc: %u", stato);
				stato_dvc_visto = stato;
			}
			switch (stato)
			{
				case DRDYNVC_STATE_NONE:
					/* Serve a far chiamare WTSVirtualChannelManagerCheckFileDescriptor,
					 * che e' cio' che inizializza drdynvc. */
					SetEvent(evento_canale);
					break;
				case DRDYNVC_STATE_READY:
					/*
					 * Solo per chi e' passato dalla guardia.  A chi e' stato
					 * respinto non si allestisce NIENTE: prosegue fino
					 * all'attivazione solo per potergli dire di no (R12), e un
					 * canale grafico aperto per lui sarebbe lavoro fatto per
					 * qualcuno che non vedra' un pixel.
					 */
					if (cp->rifiuto || !cp->autenticato)
						break;
					if (!cp->gfx_aperto && !apri_egfx(cp))
					{
						congeda(peer, ERRINFO_GRAPHICS_SUBSYSTEM_FAILED, "EGFX non apribile");
						goto chiudi;
					}
					/* DISP invece non e' obbligatorio: se non si apre, la
					 * sessione vive senza risoluzione dinamica. */
					if (!cp->disp_aperto && !cp->disp)
						apri_disp(cp);
					/*
					 * E nemmeno l'audio lo e'.  Non si apre con la scena
					 * sintetica: li' non c'e' una sessione grafica, quindi non
					 * c'e' il sink da cui catturare — aprire il canale
					 * significherebbe promettere al client un suono che nessuno
					 * puo' produrre.
					 */
					if (!cp->altoparlante && cp->server->palco)
						apri_audio(cp);
					break;
				default:
					break;
			}
		}

		/*
		 * ⛔ L'AUDIO SI COMPONE PRIMA DELLO SVUOTAMENTO, NON DOPO.
		 *
		 * L'ordine di queste due cose e' una misura, non un gusto.  I byte
		 * partono quando il ciclo svuota la coda dei canali, poche righe piu' in
		 * basso; comporre il blocco DOPO significa farlo partire al giro
		 * SEGUENTE, cioe' dopo una codifica di fotogramma intera — decine di
		 * millisecondi, e ogni volta diverse, perche' senza accelerazione il
		 * codificatore sta in questo stesso ciclo.  E' il ritardo variabile che
		 * si sente come micro-stutter (§10 n.13 di REFERENCE.md).
		 *
		 * Messo qui, il blocco parte nello stesso giro in cui e' stato composto,
		 * PRIMA del fotogramma.  L'accodamento sveglia da solo l'evento del
		 * gestore dei canali, quindi lo svuotamento qui sotto lo vede.
		 *
		 * E i byte dell'audio restano dentro la finestra della misura di banda,
		 * che e' dove devono stare (R19): sul filo ci passano davvero.
		 */
		if (cp->altoparlante && cp->autenticato)
		{
			accendi_ascolto(cp);
			altoparlante_passo(cp->altoparlante);
		}

		/* Solo quando l'evento e' segnalato, come nel riferimento: chiamarla a
		 * ogni giro non fa avanzare la macchina a stati di drdynvc. */
		if (WaitForSingleObject(evento_canale, 0) == WAIT_OBJECT_0)
		{
			gboolean vivo;

			/*
			 * ⛔ QUI, E NON ATTORNO A `manda_fotogramma`, STA LA MISURA DI BANDA.
			 *
			 *    Questa chiamata e' il momento in cui i byte del fotogramma
			 *    passano davvero sul filo: `WTSVirtualChannelWrite` li aveva solo
			 *    accodati.  I PDU di autodetect invece si scrivono dritti sul
			 *    socket, quindi uno «Stop» mandato subito dopo `SurfaceFrameCommand`
			 *    scavalcherebbe il fotogramma che deve pesare — e il client
			 *    risponderebbe di aver contato dieci byte, come e' successo al
			 *    banco il 5 agosto.
			 */
			rete_banda_apre(cp->rete);
			vivo = WTSVirtualChannelManagerCheckFileDescriptor(cp->vcm);
			rete_banda_chiude(cp->rete);
			if (!vivo)
			{
				avviso("il gestore dei canali virtuali si e' chiuso");
				break;
			}
		}

		/*
		 * Un passo della macchina di ridimensionamento, a ogni giro.
		 *
		 * L'evento si azzera PRIMA di eseguire il passo, non dopo: se una
		 * misura nuova arrivasse mentre il passo e' in corso, azzerando dopo se
		 * ne perderebbe la sveglia e resterebbe in coda fino al prossimo
		 * fotogramma.  Il passo si chiama comunque a ogni giro — costa un
		 * lucchetto e un `switch` — cosi' l'attesa del thread che ridimensiona
		 * non ha bisogno di un evento suo.
		 */
		if (WaitForSingleObject(cp->evento_misura, 0) == WAIT_OBJECT_0)
			ResetEvent(cp->evento_misura);
		if (!passo_misura(cp))
			goto chiudi;

		/*
		 * Un passo della misura della rete, a ogni giro.
		 *
		 * Non serve un timer suo: il ciclo si sveglia gia' a ogni periodo di
		 * fotogramma — 33 ms a 30 al secondo — che e' piu' fitto della cadenza
		 * alta delle sonde (70 ms).  Solo da attivati: prima non c'e' ancora il
		 * canale su cui spedirle.
		 */
		if (cp->attivo)
			rete_passo(cp->rete);

		/*
		 * Gli appunti si aprono appena la sessione RDP e' attiva: il canale e'
		 * statico e il `MONITOR_READY` che il suo thread manda e' un PDU come un
		 * altro — spedirlo prima dell'attivazione e' la stessa scommessa persa
		 * dei rifiuti anticipati (vedi `congeda`).
		 */
		if (cp->attivo && cp->autenticato && !cp->rifiuto && !cp->scambio)
			apri_appunti(cp);

		adesso = g_get_monotonic_time();
		if (adesso >= prossimo_fotogramma)
		{
			prossimo_fotogramma = adesso + periodo_ms * 1000;
			switch (manda_fotogramma(cp))
			{
				case INVIO_AVANTI:
					break;
				case INVIO_SESSIONE_FINITA:
					/*
					 * R12 — non basta chiudere: bisogna dire perche'.  Il
					 * client Android, alla sola chiusura del socket, resta a
					 * fissare l'ultimo fotogramma, e uno sfondo pulito senza
					 * finestre e' visivamente identico a un desktop vivo.
					 *
					 * La causa quasi sempre e' un «Esci» dal menu di sistema,
					 * ed e' quella che il codice dichiara.  Accorgersene
					 * PRIMA — registrandosi con `gnome-session` invece di
					 * aspettare che muoia la cattura — e' materia della fase 5.
					 */
					congeda(peer, ERRINFO_LOGOFF_BY_USER, "la sessione grafica e' finita");
					goto chiudi;
				case INVIO_GUASTO:
					congeda(peer, ERRINFO_GRAPHICS_SUBSYSTEM_FAILED,
					        "invio del fotogramma fallito");
					goto chiudi;
			}
		}
	}

chiudi:
	/*
	 * Si rilascia tutto quel che era rimasto premuto, PRIMA di chiudere.
	 *
	 * Va fatto anche — soprattutto — quando la connessione muore male: il conto
	 * dei tasti premuti vive nel palco, che sopravvive alla connessione, e
	 * lasciarlo sporco si paga alla connessione SUCCESSIVA, dove il primo colpo
	 * su un tasto che risulta ancora premuto viene ingoiato e la lettera non
	 * compare.  E' il difetto trovato in prova il 2 agosto (§5.8 regola 4).
	 */
	if (cp && cp->autenticato && cp->server->palco)
	{
		Input *ingresso = palco_input_prendi(cp->server->palco);

		if (ingresso)
			input_rilascia_tutto(ingresso);
		palco_input_lascia(cp->server->palco);
	}

	/*
	 * E si spegne la cattura audio, qui e non solo alla distruzione del
	 * contesto: fra le due cose c'e' la chiusura del peer, e catturare per un
	 * client che se n'e' andato e' lavoro fatto per nessuno.  Chiamarla due
	 * volte non fa danno, ed e' voluto — l'altra sta sul percorso dei guasti.
	 */
	if (cp)
	{
		guint64 spediti = 0, scartati = 0, riscontrati = 0, taciuti = 0;

		guint verso_client = 0, verso_sessione = 0;

		spegni_ascolto(cp);
		scambio_conti(cp->scambio, &verso_client, &verso_sessione);
		if (verso_client || verso_sessione)
			informazione("appunti: %u trasferimenti verso il client, %u verso la sessione",
			             verso_client, verso_sessione);
		altoparlante_conti(cp->altoparlante, &spediti, &scartati, &riscontrati, &taciuti);
		if (spediti || scartati || taciuti)
			informazione("audio: %" G_GUINT64_FORMAT " fotogrammi spediti, %" G_GUINT64_FORMAT
			             " di silenzio taciuto, %" G_GUINT64_FORMAT " buttati, %" G_GUINT64_FORMAT
			             " blocchi riscontrati dal client",
			             spediti, taciuti, scartati, riscontrati);
	}

	/* R12 — il congedo si dichiara solo quando a chiudere siamo noi. */
	if (peer->connected && !se_ne_va_lui)
		congeda(peer, ERRINFO_RPC_INITIATED_DISCONNECT, "chiusura del server");
	peer->Close(peer);

fine:
	/*
	 * Il posto si libera PRIMA di distruggere il contesto, e solo se lo si
	 * teneva davvero: liberarlo da chi era stato rifiutato lo toglierebbe a chi
	 * e' dentro e sta lavorando.
	 */
	if (cp)
	{
		dimentica_connessione(server, cp);
		if (cp->tiene_il_posto)
			g_atomic_int_set(&server->occupato, 0);
	}
	if (peer)
	{
		freerdp_peer_context_free(peer);
		freerdp_peer_free(peer);
	}
	if (server)
	{
		g_mutex_lock(&server->lucchetto);
		g_ptr_array_remove_fast(server->connessioni, connessione);
		g_mutex_unlock(&server->lucchetto);
	}
	informazione("connessione conclusa");
	g_object_unref(connessione);
	return NULL;
}

static gboolean su_connessione(GSocketService *servizio, GSocketConnection *connessione,
                               GObject *sorgente, gpointer dati)
{
	Server *server = dati;
	GThread *thread;

	g_object_ref(connessione);
	g_object_set_data(G_OBJECT(connessione), "server", server);

	g_mutex_lock(&server->lucchetto);
	g_ptr_array_add(server->connessioni, connessione);
	g_mutex_unlock(&server->lucchetto);

	thread = g_thread_new("remotix-peer", thread_connessione, connessione);
	g_thread_unref(thread);
	return TRUE;
}

/* ------------------------------------------------------------------ *
 * Certificato
 * ------------------------------------------------------------------ */
static gboolean genera_certificato(const char *cert, const char *chiave, GError **sbaglio)
{
	g_autofree char *comando = NULL;
	int stato = 0;

	informazione("genero un certificato autofirmato in %s", cert);
	comando = g_strdup_printf(
	    "openssl req -x509 -newkey rsa:2048 -nodes -keyout '%s' -out '%s' -days 3650 -subj '/CN=remotix'",
	    chiave, cert);
	if (!g_spawn_command_line_sync(comando, NULL, NULL, &stato, sbaglio))
		return FALSE;
	if (stato != 0)
	{
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_FAILED, "openssl e' uscito con stato %d", stato);
		return FALSE;
	}
	g_chmod(chiave, 0600);
	return TRUE;
}

static gboolean carica_certificato(Server *server, GError **sbaglio)
{
	g_autofree char *pem_cert = NULL;
	g_autofree char *pem_chiave = NULL;

	if (!g_file_test(server->opzioni.certificato, G_FILE_TEST_EXISTS) ||
	    !g_file_test(server->opzioni.chiave, G_FILE_TEST_EXISTS))
	{
		if (!genera_certificato(server->opzioni.certificato, server->opzioni.chiave, sbaglio))
			return FALSE;
	}

	if (!g_file_get_contents(server->opzioni.certificato, &pem_cert, NULL, sbaglio))
		return FALSE;
	if (!g_file_get_contents(server->opzioni.chiave, &pem_chiave, NULL, sbaglio))
		return FALSE;

	/* Si verifica SUBITO che siano leggibili, cosi' un certificato guasto si
	 * manifesta all'avvio e non alla prima connessione. */
	{
		rdpCertificate *prova_cert = freerdp_certificate_new_from_pem(pem_cert);
		rdpPrivateKey *prova_chiave = freerdp_key_new_from_pem(pem_chiave);
		gboolean buoni = prova_cert && prova_chiave;

		freerdp_certificate_free(prova_cert);
		freerdp_key_free(prova_chiave);
		if (!buoni)
		{
			g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_FAILED,
			            "certificato o chiave non leggibili (%s, %s)",
			            server->opzioni.certificato, server->opzioni.chiave);
			return FALSE;
		}
	}

	server->pem_certificato = g_steal_pointer(&pem_cert);
	server->pem_chiave = g_steal_pointer(&pem_chiave);
	return TRUE;
}

/* ------------------------------------------------------------------ *
 * Ciclo di vita
 * ------------------------------------------------------------------ */
Server *server_nuovo(const OpzioniServer *opzioni, GError **sbaglio)
{
	Server *server = g_new0(Server, 1);

	server->opzioni = *opzioni;
	server->opzioni.indirizzo = g_strdup(opzioni->indirizzo);
	server->opzioni.certificato = g_strdup(opzioni->certificato);
	server->opzioni.chiave = g_strdup(opzioni->chiave);
	server->opzioni.comando_sessione = g_strdup(opzioni->comando_sessione);
	server->opzioni.codificatore = g_strdup(opzioni->codificatore);
	server->connessioni = g_ptr_array_new();
	server->contesti = g_ptr_array_new();
	g_mutex_init(&server->lucchetto);

	if (!server->opzioni.immagine_di_prova)
		server->palco = palco_nuovo(opzioni->compositore);
	else
		avviso("mando la SCENA SINTETICA, non il desktop: e' il banco di prova del protocollo");

	winpr_InitializeSSL(WINPR_SSL_INIT_DEFAULT);

	/*
	 * Va fatto UNA VOLTA, prima di qualunque WTSOpenServerA.
	 *
	 * Senza, WinPR non sa che la sua API WTS la implementa FreeRDP e ripiega
	 * sugli stub di FreeRDS: prova a caricare `libfreerds-fdsapi.so`, non la
	 * trova, e `WTSOpenServerA` restituisce NULL.  Il sintomo non nomina la
	 * causa — «failed to parse freerds.instance» — e la connessione muore
	 * prima di esistere.  Lo chiamano tutti i server di FreeRDP (shadow, proxy,
	 * sample) e anche gnome-remote-desktop.
	 */
	WTSRegisterWtsApiFunctionTable(FreeRDP_InitWtsApi());

	if (!carica_certificato(server, sbaglio))
	{
		server_libera(server);
		return NULL;
	}
	return server;
}

gboolean server_avvia(Server *server, GError **sbaglio)
{
	server->servizio = g_socket_service_new();

	if (server->opzioni.indirizzo)
	{
		g_autoptr(GInetAddress) indirizzo =
		    g_inet_address_new_from_string(server->opzioni.indirizzo);
		g_autoptr(GSocketAddress) sa = NULL;

		if (!indirizzo)
		{
			g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_INVALID_ARGUMENT,
			            "indirizzo non valido: %s", server->opzioni.indirizzo);
			return FALSE;
		}
		sa = g_inet_socket_address_new(indirizzo, server->opzioni.porta);
		if (!g_socket_listener_add_address(G_SOCKET_LISTENER(server->servizio), sa,
		                                   G_SOCKET_TYPE_STREAM, G_SOCKET_PROTOCOL_TCP, NULL, NULL,
		                                   sbaglio))
			return FALSE;
	}
	else if (!g_socket_listener_add_inet_port(G_SOCKET_LISTENER(server->servizio),
	                                          server->opzioni.porta, NULL, sbaglio))
	{
		return FALSE;
	}

	g_signal_connect(server->servizio, "incoming", G_CALLBACK(su_connessione), server);
	g_socket_service_start(server->servizio);

	informazione("in ascolto su %s:%u", server->opzioni.indirizzo ?: "*", server->opzioni.porta);
	return TRUE;
}

void server_ferma(Server *server)
{
	if (!server)
		return;
	if (server->servizio)
	{
		g_socket_service_stop(server->servizio);
		g_socket_listener_close(G_SOCKET_LISTENER(server->servizio));
	}
}

void server_libera(Server *server)
{
	if (!server)
		return;
	server_ferma(server);
	g_clear_object(&server->servizio);
	/* Il palco si smonta QUI e non alla disconnessione: e' l'unico momento in
	 * cui togliere a Mutter il suo unico schermo non fa danno, perche' non c'e'
	 * piu' nessuno che debba ritrovarcelo. */
	g_clear_pointer(&server->palco, palco_libera);
	g_clear_pointer(&server->pem_certificato, g_free);
	g_clear_pointer(&server->pem_chiave, g_free);
	if (server->connessioni)
		g_ptr_array_free(server->connessioni, TRUE);
	if (server->contesti)
		g_ptr_array_free(server->contesti, TRUE);
	g_mutex_clear(&server->lucchetto);
	g_free(server->opzioni.indirizzo);
	g_free(server->opzioni.certificato);
	g_free(server->opzioni.chiave);
	g_free(server->opzioni.comando_sessione);
	g_free(server->opzioni.codificatore);
	g_free(server);
}
