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
	 * protocollo, e perche' un banco lo possa sostituire dichiarandolo. */
	bool (*verifica)(void *ctx, const char *utente, const char *parola);
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

/* Per il banco e per il registro. */
const char *rcp_stato_nome(const rcp_sessione *s);
const char *rcp_utente(const rcp_sessione *s);

/* ⛔ Azzera il registro delle sessioni attive.  Serve SOLO al banco, fra una
 * prova e l'altra: in un server vero non lo chiama nessuno. */
void rcp_azzera_registro_sessioni(void);

#ifdef __cplusplus
}
#endif
