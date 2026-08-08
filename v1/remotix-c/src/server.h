/*
 * server — accettazione delle connessioni e ciclo di una sessione RDP.
 *
 * Le connessioni si accettano con un GSocketService, cioe' in parallelo per
 * costruzione, e ciascuna viene servita da un thread suo (e' la struttura del
 * riferimento, §3 di gnome-remote-desktop.md).
 */
#pragma once

#include <glib.h>
#include <stdint.h>

#include "compositore.h"

typedef struct Server Server;
typedef struct Sentinella Sentinella;

typedef struct
{
	uint16_t porta;
	char *indirizzo;   /* NULL = tutti */
	char *certificato; /* percorso PEM; se manca, se ne genera uno */
	char *chiave;
	uint32_t bitrate_kbit;
	uint32_t fotogrammi_al_secondo;
	gboolean senza_autenticazione; /* solo per il banco: salta PAM */
	/*
	 * Manda la scena sintetica invece del desktop vero.
	 *
	 * Non e' un residuo della fase 2: e' lo strumento che isola il protocollo
	 * dalla cattura.  Se qualcosa non si vede, con questa accesa il sospetto
	 * cade su una cosa sola — ed e' la lezione di §5.4 di SPECIFICA.md.  Serve
	 * anche a provare la pipeline dove una sessione grafica non c'e' affatto,
	 * per esempio nel contenitore di sviluppo.
	 */
	gboolean immagine_di_prova;
	/*
	 * Fa come se il client avesse chiesto di non ricevere piu' riscontri
	 * (`queueDepth == 0xFFFFFFFF`), dopo un centinaio di fotogrammi.
	 *
	 * Solo per il banco, e per una ragione precisa: quel caso e' l'unico in cui
	 * un regolatore scritto male si ferma PER SEMPRE invece di rallentare, e
	 * nessuno dei tre client di riferimento lo produce a comando.  Senza questa,
	 * la riga di codice che lo gestisce resterebbe non provata.
	 */
	gboolean fingi_riscontri_sospesi;
	/* Come si avvia la sessione grafica, se manca.  NULL = il predefinito. */
	char *comando_sessione;
	/*
	 * Chi codifica l'AVC420: NULL o "auto" per la scelta automatica, oppure il
	 * nome di un codificatore di libavcodec (`h264_vaapi`, `libx264`, …), o
	 * "freerdp" per il vecchio percorso.
	 *
	 * Chiedendolo per nome NON si ripiega: chi lo indica sta misurando, e un
	 * ripiego silenzioso darebbe due misure diverse sotto la stessa etichetta.
	 */
	char *codificatore;
	/*
	 * Chi possiede schermo e input: si RICONOSCE all'avvio (§2 di SPECIFICA.md),
	 * e questo lo forza.  Serve al banco — dove i due compositori possono
	 * convivere sulla stessa macchina — e serve a chi misura, per la stessa
	 * ragione per cui il codificatore si sceglie per nome: un riconoscimento
	 * automatico che sbaglia da' due misure sotto la stessa etichetta.
	 */
	TipoCompositore compositore;
} OpzioniServer;

Server *server_nuovo(const OpzioniServer *opzioni, GError **sbaglio);

/*
 * La sentinella della sessione locale.  Si consegna dopo la costruzione perche'
 * il server non la possiede: e' di `main`, che la spegne per ultima.
 * Con NULL la regola non e' in vigore, e va bene: §2 di SPECIFICA.md dice
 * degradare, non fallire.
 */
void server_sentinella(Server *server, Sentinella *sentinella);

/* Chi possiede schermo e input: lo sa il palco, e serve a `main` per avviare e
 * chiudere la sessione nel modo giusto. */
TipoCompositore server_compositore(Server *server);

/*
 * Congeda tutte le connessioni in corso, dichiarando PERCHE' (R12).
 *
 * Non aspetta e non fa I/O: segna il motivo e sveglia i thread, che chiudono
 * ciascuno la propria.  Deve essere veloce, perche' la chiama chi ha appena
 * saputo che la sessione sta uscendo — ed e' tutto il punto di saperlo presto.
 */
void server_congeda_tutti(Server *server, uint32_t codice, const char *perche);

/*
 * Smonta il palco.
 *
 * Va fatto quando la sessione grafica se n'e' andata: cattura e monitor
 * virtuale sono oggetti di un compositore che non esiste piu', e chi si
 * ricollegasse alla stessa misura li troverebbe «gia' montati» — cioe' schermo
 * nero.  Non e' un dettaglio, ed e' il punto 3 di §5.10 di SPECIFICA.md.
 */
void server_smonta_palco(Server *server);

/* Quante connessioni si stanno servendo adesso. */
guint server_connessioni_attive(Server *server);
gboolean server_avvia(Server *server, GError **sbaglio);
void server_ferma(Server *server);
void server_libera(Server *server);
