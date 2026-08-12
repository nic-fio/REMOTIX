/*
 * rcp.h — la stretta di mano di RCP/1, lato server.
 *
 * ---------------------------------------------------------------------------
 * ⛔ CHE COSA SA E CHE COSA NON SA
 *
 * Questo modulo conosce `RCP.md` e **nient'altro**: non sa che sotto c'e' QUIC,
 * non sa che sopra c'e' WebTransport, non apre socket e non guarda l'orologio.
 * Riceve byte, restituisce byte, e chiede a chi lo ospita di mandarli.
 *
 * ⭐ Non e' pulizia estetica: e' la ragione per cui potra' passare dal server
 *    d'esempio di ngtcp2 al server vero senza riscriverlo — e la ragione per
 *    cui `DECISIONI.md` §6.4, se un giorno si riaprisse, non porterebbe via
 *    con se' anche il protocollo.
 *
 * ---------------------------------------------------------------------------
 * ⛔ IL TEMPO ARRIVA DA FUORI
 *
 * `RCP.md` §4.6 impone tre tetti alla stretta di mano, e §4.4-bis impone un
 * **ritardo fisso di un secondo** prima di rispondere a `CREDENZIALI` — anche
 * quando la risposta e' `AMMESSO`.  Un modulo che chiamasse `clock_gettime()`
 * da se' sarebbe impossibile da mettere alla prova: si dovrebbe **aspettare**
 * davvero.  Qui l'ora la passa chi ospita, con `rcp_tempo()`, e un banco puo'
 * farla scorrere come vuole.
 */
#pragma once

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/* La versione maggiore che questo modulo parla — RCP.md §9. */
#define RCP_VERSIONE 1

/* I motivi di §8.2.  Il codice 0 NON DEVE essere usato (§3.1). */
enum {
	RCP_CHIUSO_DALL_UTENTE = 0x01,
	RCP_INATTIVITA = 0x02,
	RCP_SESSIONE_ABBANDONATA = 0x03,
	RCP_SESSIONE_LOCALE_PREVALSA = 0x04,
	RCP_GIA_ATTIVA_LOCALE = 0x05,
	RCP_BUDGET_PIENO = 0x06,
	RCP_CREDENZIALI_ERRATE = 0x07,
	RCP_TROPPI_TENTATIVI = 0x08,
	RCP_NIENTE_IN_COMUNE = 0x09,
	RCP_VERSIONE_INCOMPATIBILE = 0x0A,
	RCP_ERRORE_PROTOCOLLO = 0x0B,
	RCP_SERVER_IN_CHIUSURA = 0x0C,
	RCP_TEMPO_SCADUTO = 0x0D,
	RCP_SESSIONE_NON_SERVIBILE = 0x0E,
	RCP_GIA_ATTIVA_REMOTA = 0x0F,
};

typedef struct rcp_sessione rcp_sessione;

/* I ganci verso chi ospita.  Tre, e nessuno di piu'. */
typedef struct {
	void *ctx;
	/* Manda byte sul canale di controllo (lo stream bidirezionale che il
	 * client ha aperto per primo — §4.2). */
	void (*manda)(void *ctx, const uint8_t *dati, size_t len);
	/* ⛔ §3.1 punto 3: chiude la SESSIONE WebTransport con il codice
	 * d'errore applicativo pari al codice del motivo.  Non la connessione
	 * QUIC: quella puo' reggere altro, e una pagina non la puo' chiudere. */
	void (*chiudi)(void *ctx, uint8_t motivo);
	/* Una riga nel registro del server.  ⛔ §3.1 punto 1: si scrive CHE COSA
	 * non si e' capito, non «errore di protocollo». */
	void (*registra)(void *ctx, const char *riga);
	/* Verifica le credenziali.  Separato perche' PAM non c'entra col
	 * protocollo, e perche' un banco lo possa sostituire dichiarandolo.
	 *
	 * ⛔⭐ QUESTO GANCIO BLOCCA CHI LO CHIAMA, e dal 12 agosto 2026 e' il
	 *     RIPIEGO, non la strada buona: si usa solo quando `chiedi_verifica`
	 *     e' NULL.  ⚠ Non e' stato tolto, e non per pigrizia — l'innesto di
	 *     `banchi/01-b3-rcp-innesta.py` monta questo stesso modulo su un
	 *     ospite che non ha un ciclo suo da liberare, e romperlo in silenzio
	 *     sarebbe peggio del difetto (`CODER.md` §4.2: il ripiego si
	 *     DICHIARA). */
	bool (*verifica)(void *ctx, const char *utente, const char *parola);
	/* ⭐ LA VERIFICA ASINCRONA — `DECISIONI.md` §1.10, 12 agosto 2026.
	 *
	 * ⛔ `verifica` blocca chi la chiama, e nel prodotto chi la chiama e'
	 *    l'unico ciclo `poll` del server: `[M]` B8, 11 agosto 2026, **da 1,0 a
	 *    2,2 secondi** in cui nessun altro riceve un pacchetto.  Questo gancio
	 *    invece **torna subito**: chiede la verifica a un processo aiutante e
	 *    lascia un numero di pratica, e l'esito rientra da `rcp_verdetto()`.
	 *
	 * Restituisce `false` se la domanda **non e' partita**.  ⛔ E allora
	 * l'esito e' NO, subito e senza appello — invariante I3: il fallimento e'
	 * un no, non un forse.
	 *
	 * ⚠ Se e' NULL si usa `verifica`, e il modulo si comporta esattamente
	 *   come prima del 12 agosto 2026: e' quel che fanno i banchi in-processo,
	 *   ed e' anche il GUASTO che `banchi/02-pam-*` innesta per certificarsi. */
	bool (*chiedi_verifica)(void *ctx, const char *utente, const char *parola,
	                        uint64_t *pratica);
} rcp_ganci;

/* Apre una sessione RCP su un canale di controllo appena nato.
 * `provenienza` e' l'indirizzo di chi si collega: serve al contatore per
 * indirizzo di §4.4-bis e al registro.  `ora_ms` e' un orologio monotono. */
rcp_sessione *rcp_apri(const rcp_ganci *g, const char *provenienza,
                       uint64_t ora_ms);

/* Chiude e libera.  Se la sessione era attaccata, libera il posto. */
void rcp_libera(rcp_sessione *s);

/* Byte arrivati sul canale di controllo.
 * Restituisce false se la sessione e' finita (per congedo o per violazione). */
bool rcp_ricevi(rcp_sessione *s, const uint8_t *dati, size_t len,
                uint64_t ora_ms);

/* Fa scorrere il tempo: i tetti di §4.6 e il ritardo fisso di §4.4-bis.
 * Restituisce false se la sessione e' finita. */
bool rcp_tempo(rcp_sessione *s, uint64_t ora_ms);

/* ⭐ L'esito della verifica asincrona rientra da qui — `DECISIONI.md` §1.10.
 *
 * ⛔ Restituisce `true` solo se la pratica era DI QUESTA sessione e la sessione
 *    la stava davvero aspettando.  L'ospite lo usa per riconoscere a chi
 *    consegnare: passa la pratica a tutte le sessioni vive, e una sola la
 *    prende.  ⚠ Una pratica che non trova nessuno **si perde, ed e' giusto**:
 *    vuol dire che la connessione e' morta mentre PAM rispondeva.
 *
 * ⛔ E il conto di §4.4-bis si muove QUI, non piu' quando arriva `CREDENZIALI`:
 *    e' qui che si sa se il tentativo e' fallito.
 *
 * ⚠ NON manda niente sul filo: `AMMESSO`/`RESPINTO` escono da `rcp_tempo()`,
 *   perche' il ritardo fisso di §4.4-bis deve essere scaduto — e il verdetto,
 *   adesso, puo' arrivare prima o dopo di lui. */
bool rcp_verdetto(rcp_sessione *s, uint64_t pratica, bool ammesso,
                  uint64_t ora_ms);

/* ⛔ §8.1: chi chiude DEVE mandare `CONGEDO` con un motivo PRIMA di chiudere la
 * sessione WebTransport, e DEVE ripetere il motivo nel codice d'errore
 * applicativo della chiusura (§3.1).  Questa funzione percorre tutt'e due le
 * strade; il motivo di §8.2 lo sceglie chi ospita, perche' solo lui sa perche'
 * sta chiudendo.
 *
 * ⭐ Il caso per cui e' nata (rilievo B-7, 10 agosto 2026 notte): il server che
 *    si spegne, cioe' `RCP_SERVER_IN_CHIUSURA`.  Quel motivo era definito qui
 *    sopra e non lo emetteva nessuna riga del prodotto: chi era collegato
 *    aspettava i 30 s dell'inattivita' e leggeva «errore di rete».
 *
 * ⚠ Su una sessione gia' finita non fa niente e non e' un errore: mandare un
 *   secondo motivo per lo stesso fatto direbbe due verita' sulla stessa cosa. */
void rcp_congeda(rcp_sessione *s, uint8_t motivo, const char *dettaglio);

/* ⛔ §2.5: una violazione rilevata da chi ospita — uno stream di troppo, un
 * canale nel verso sbagliato — chiusa come dice §3.1.  L'ospite vede gli
 * stream; il modo di chiudere lo sa solo questo modulo. */
void rcp_violazione(rcp_sessione *s, const char *dettaglio);

/* ⛔ §4.2: il canale di controllo si e' chiuso, e il suo chiudersi E' la fine
 * della sessione — ANCHE quando a chiuderlo e' stato il server.  L'ospite e'
 * l'unico che vede il FIN; che cosa comporti lo sa solo questo modulo.
 *
 * ⚠ La sessione NON si libera: resta viva per osservare i byte che §4.2 vieta
 *   al client di spedire dopo la fine.  Quel che si lascia e' il POSTO. */
void rcp_canale_chiuso(rcp_sessione *s);

/* ⭐ §3.1 punto 3: il motivo viaggia anche nel codice di chiusura, e quella
 * strada la vede solo l'ospite.  Per giudicarla serve sapere se la sessione
 * era gia' finita quando il codice e' arrivato — perche' e' esattamente li'
 * che il `CONGEDO` del client non poteva piu' passare dal canale. */
bool rcp_e_finita(const rcp_sessione *s);

/* ⛔ §4.2: la pagina ha chiuso la sessione WebTransport, e lo ha detto col
 * motivo dentro la chiusura.  Il posto (§8.2 motivo 0x0F) si lascia QUI:
 * aspettare che il trasporto finisca di smontarsi lo tiene occupato addosso a
 * chi si ricollega subito. */
void rcp_chiusa_dal_client(rcp_sessione *s, uint8_t codice);

/* Per il banco e per il registro.
 *
 * ⚠ I nomi sono: `attesa-ciao` · `attesa-credenziali` · `attesa-verdetto` ·
 *   `attesa-attacca` · `attiva` · `staccata-per-silenzio` · `finita`.
 *
 * ⛔ `staccata-per-silenzio` e' del 10 agosto 2026, rilievo R9.2: una sessione
 *    che ha taciuto trenta secondi ha lasciato il posto (§8.2 motivo 0x0F) e
 *    **non e' piu' attiva**.  Prima restava `attiva`, e il server finiva con due
 *    sessioni «attiva» per lo stesso utente — quel che l'invariante I2 vieta.
 *    Chi confronta questa stringa deve sapere che il caso esiste; se torna a
 *    parlare e il posto e' libero, la sessione torna `attiva` da sola. */
const char *rcp_stato_nome(const rcp_sessione *s);
const char *rcp_utente(const rcp_sessione *s);

/* ⛔ Azzera il registro delle sessioni attive.  Serve SOLO al banco, fra una
 * prova e l'altra: in un server vero non lo chiama nessuno. */
void rcp_azzera_registro_sessioni(void);

/* ------------------------------------------------------------------------ */
/* §4.4-bis — IL BAN DELL'INDIRIZZO, e le tre cose che il padrone di casa deve
 * poter fare.  La regola sta in `DECISIONI.md` §1.9, decisa dall'utente il 10
 * agosto 2026: tre autenticazioni fallite consecutive dallo stesso indirizzo, e
 * quell'indirizzo e' fuori per dodici ore.                                    */

/* ⛔ «Questo indirizzo e' bannato?», e quanto gli resta.  La chiama **chi serve
 * la pagina in TCP**: §4.4-bis vuole che la pagina si carichi lo stesso e dica
 * che i tentativi sono esauriti — mai un errore di rete, mai un silenzio, perche'
 * chi e' bannato per errore e' quasi sempre il proprietario.
 * `provenienza` puo' portare la porta: viene tagliata qui dentro. */
bool rcp_bannato(const char *provenienza, uint64_t ora_ms, uint64_t *restano_ms);

/* ⛔ Il comando di sblocco — l'altra via d'uscita oltre alle dodici ore.
 * Restituisce `true` se l'indirizzo era davvero bannato: «non era bannato» e
 * «l'ho sbloccato» sono due fatti diversi, e chi comanda deve poterli
 * distinguere.  ⭐ E' anche quel che rende possibile il banco B8, che di
 * campioni ne vuole molti piu' di tre. */
bool rcp_sblocca(const char *indirizzo, uint64_t ora_ms);

/* ⛔ Dichiara il file dei ban e lo rilegge: senza, il ban vive in memoria e un
 * riavvio lo porta via — invariante I7.  Restituisce quanti ne ha caricati,
 * ⛔ e **-1 se il file c'era e non si e' potuto leggere**: «zero ban» e «non ho
 * potuto guardare» sono due fatti diversi (`LEZIONI.md` §1.9 regola 1), e chi
 * chiama DEVE stamparli diversi — un -1 letto come zero e' la protezione spenta
 * con l'aria di non avere niente da proteggere.
 * ⚠ Un percorso vuoto o NULL spegne la persistenza (e' il caso del banco). */
int rcp_ban_carica(const char *percorso, uint64_t ora_ms);

/* ⛔ La chiave del ban nella forma in cui §4.4-bis la conta, da qualunque forma
 * di indirizzo: `127.0.0.1` · `127.0.0.1:53` · `[127.0.0.1]:53` · `fe80::1`
 * diventano tutti `[127.0.0.1]` / `[fe80::1]`.
 *
 * ⭐ Serve al COMANDO DI SBLOCCO, che riceve un indirizzo digitato da una
 *    persona mentre la chiave l'ha fatta `util::straddr()` dell'ospite, che
 *    mette le quadre anche a IPv4.  Senza questa funzione l'ospite se la
 *    costruirebbe da se', e il giorno in cui le due forme divergessero lo
 *    sblocco risponderebbe «non era bannato» a ogni indirizzo — in silenzio, e
 *    per sempre. */
void rcp_chiave_indirizzo(const char *testo, char *fuori, size_t cap);

#ifdef __cplusplus
}
#endif
