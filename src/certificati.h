/*
 * certificati.h — ⛔ I DUE CERTIFICATI, E SONO DUE (`RCP.md` §4.1-bis).
 *
 * ---------------------------------------------------------------------------
 * ⛔ PERCHE' DUE, E CHE COSA COSTA CONFONDERLI
 *
 *   il LONGEVO   serve la PAGINA, in TCP.  E' quello su cui l'utente concede
 *                l'eccezione la prima volta su ogni dispositivo, quindi ⛔ NON
 *                deve cambiare piu' spesso del necessario.
 *
 *   il BREVE     serve la SESSIONE WebTransport.  Il browser non guarda
 *                l'eccezione su quella connessione — guarda l'impronta che la
 *                pagina gli passa (`serverCertificateHashes`) — e per quella
 *                strada pretende un certificato valido MENO DI 14 GIORNI [S].
 *                Quindi ruota, e ruota da se'.
 *
 * ⚠ Chi ne fa uno solo passa tutti i banchi e fa ricomparire l'avviso ogni due
 *   settimane, «e nessuno collegherebbe le due cose» (§4.1-bis).  E' il difetto
 *   che B13.1 esiste per vedere, e il modo di non commetterlo e' che i due
 *   abbiano due nomi diversi fin qui dentro.
 *
 * ---------------------------------------------------------------------------
 * ⛔ IL CERTIFICATO DELL'AMMINISTRATORE NON SI TOCCA
 *
 * `RCP.md` §4.1: «se l'amministratore ne installa uno emesso da un'autorita', il
 * server DEVE usarlo e NON DEVE rigenerare il proprio».  Il modo di saperlo
 * senza indovinare: ogni certificato generato DA NOI si porta accanto un file
 * di marca (`.nostro`).  ⛔ Un `pagina.pem` senza marca e' di qualcun altro, e
 * non si rigenera mai — nemmeno quando scade.
 *
 * ⚠ Il criterio e' «l'abbiamo scritto noi?», non «e' autofirmato?»: il secondo
 *   e' una deduzione (forma E1), e sbaglierebbe su una CA privata autofirmata.
 */
#ifndef REMOTIX_CERTIFICATI_H
#define REMOTIX_CERTIFICATI_H

#include <stdbool.h>
#include <time.h>

/* I giorni, e da dove vengono. */
#define CERT_GIORNI_PAGINA 365 /* longevo: l'eccezione dell'utente dura */
#define CERT_GIORNI_SESSIONE 13 /* ⛔ sotto il tetto di 14 di §4.1-bis */
#define CERT_MARGINE_GIORNI 2 /* si ruota QUANDO NE RESTANO tanti, non a scadenza */

typedef struct {
	char dir[256];
	char indirizzo[128];

	char pagina_pem[320], pagina_key[320], pagina_marca[320];
	char sessione_pem[320], sessione_key[320], sessione_marca[320];

	/* L'impronta SHA-256 del DER del certificato di SESSIONE, in base64:
	 * ⛔ del certificato, non della chiave pubblica (rilievo R1.14 di
	 * `RCP.md`) — chi pubblicava quella della chiave otteneva un confronto
	 * che non combacia mai, e il sintomo era «WebTransport non si connette»
	 * senza che nessun errore nominasse l'impronta. */
	char impronta[64];
	/* La stessa in esadecimale, che e' la forma dei registri e dei messaggi
	 * d'errore dei browser. */
	char impronta_esa[80];
	time_t sessione_scade;
	/* ⛔ Quante volte il certificato di sessione e' stato ruotato da quando
	 *    il server e' acceso.  E' il denominatore di B13.1: «e' ruotato» e
	 *    «non e' mai stato provato» hanno lo stesso aspetto senza. */
	unsigned rotazioni;
	bool pagina_e_nostro;
} certificati;

/* Prepara i due certificati: li legge se ci sono e valgono, li genera se no.
 * Restituisce false solo se non se ne puo' avere uno utilizzabile. */
bool certificati_prepara(certificati *c, const char *dir, const char *indirizzo);

/* ⛔ Ruota il certificato di SESSIONE prima che scada, non dopo: se ne restano
 * meno di `CERT_MARGINE_GIORNI` se ne fa uno nuovo e si ricalcola l'impronta.
 * Restituisce true se ha ruotato — chi ospita deve rifare il contesto TLS.
 *
 * ⚠ Il certificato della pagina NON ruota qui: e' longevo apposta. */
bool certificati_ruota_se_serve(certificati *c);

#endif
