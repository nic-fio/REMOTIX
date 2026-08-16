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
	/* ⭐ 15 agosto 2026, `DECISIONI.md` §4.1-quater: l'utente e' USCITO dal
	 * desktop («Esci/logout»).  ⛔ NON e' `0x01`: quello e' il filo che cade e
	 * porta la promessa «riattacca e ritrovi tutto», che dopo un logout e'
	 * falsa — la sessione grafica e' finita e i programmi sono chiusi. */
	RCP_SESSIONE_TERMINATA = 0x10,
};

typedef struct rcp_sessione rcp_sessione;

/* ⛔⭐ Le due risposte NON-CONTO del gancio `input_rilascia_tutto` (§7.3): la
 *     ragione per cui esistono e' scritta sul gancio, piu' sotto.  ⚠ Sono
 *     negative apposta, cosi' un conto vero non puo' mai somigliarci. */
#define RCP_RILASCIO_SENZA_CONTO (-1)
#define RCP_RILASCIO_IMPOSSIBILE (-2)

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

	/* ------------------------------------------------------------------ */
	/* ⭐ I QUATTRO GANCI DEL CANALE VIDEO — §2.5, §5.1, §6.2.
	 *
	 * ⛔ SONO QUATTRO E NON UNO, e la ragione e' normativa: §6.2 dice che
	 *    **come lo stream finisce e' parte del messaggio** — FIN vuol dire
	 *    «fotogramma completo», `RESET_STREAM` vuol dire «incompleto, si
	 *    butta».  Un gancio solo che «manda un fotogramma» non saprebbe dire
	 *    la differenza, e un fotogramma abbandonato e uno completo tornerebbero
	 *    ad avere lo stesso aspetto: e' la forma d'errore **E8**, e su questo
	 *    esatto campo e' gia' stata pagata (rilievo R1.7, 9 agosto 2026).
	 *
	 * ⛔ E SONO **OPZIONALI**: se `video_apri` e' NULL questo server non ha un
	 *    canale video, e `rcp_video_apri()` restituisce
	 *    `RCP_VIDEO_NIENTE_CANALE` invece di tacere.  ⚠ «Non ho un canale
	 *    video» e «il fotogramma non e' partito» sono due fatti diversi
	 *    (`LEZIONI.md` §1.9 regola 1), e i banchi in-processo della fase 1 non
	 *    hanno stream unidirezionali da offrire.
	 *
	 * ⚠ Chi li collega li collega TUTTI E QUATTRO: un ospite che sapesse
	 *   aprire e non sapesse azzerare non potrebbe onorare §5.1, e il modulo
	 *   se ne accorge e rifiuta di aprire. */

	/* ⛔ §2.5: apre uno stream **unidirezionale nuovo**, uno **per
	 * fotogramma**, dal server verso il client.  ⛔ NON e' il canale di
	 * controllo: un `0x03` sul canale di controllo e' `ERRORE_PROTOCOLLO`
	 * (§2.5, riga `0x03`).  Restituisce `true` e riempie `stream` con
	 * l'identificatore, oppure `false` se non se ne puo' aprire uno adesso —
	 * ⚠ e allora NON si e' spedito niente, che e' meglio di mezzo fotogramma.
	 *
	 * ⛔⭐ E `restano` E' UN PARAMETRO D'USCITA, NON UN LUSSO — §2.3, fase 3.
	 *
	 *     §2.3 impone due comportamenti DIVERSI quando lo stream non si apre:
	 *     un **delta** si butta, una **chiave** si aspetta.  Chi deve
	 *     scegliere e' questo modulo, che sa se il fotogramma e' una chiave;
	 *     ⛔ ma il numero che spiega il perche' — quanti stream il client
	 *     concede ancora — lo sa soltanto chi tiene il trasporto.  Senza
	 *     riportarlo qui, la riga di registro che §2.3 pretende («e in
	 *     tutt'e due i casi si scrive nel registro») direbbe «non si e'
	 *     potuto» senza dire quanto manca, cioe' il sintomo *«schermo fermo,
	 *     e nessuna riga che dica perche'»* del rilievo R1.9.
	 *
	 *     ⚠ Chi non lo sa scrive `0` e la riga lo dira'. */
	bool (*video_apri)(void *ctx, int64_t *stream, uint64_t *restano);
	/* Scrive byte su quello stream.  ⛔ `false` vuol dire «non sono entrati»,
	 * e chi chiama AZZERA: non si chiude con FIN uno stream a cui manca un
	 * pezzo, perche' FIN vuol dire «completo» (§6.2). */
	bool (*video_scrivi)(void *ctx, int64_t stream, const uint8_t *dati,
	                     size_t len);
	/* ⛔ §6.2: FIN ⇒ il fotogramma e' **completo** e si consegna al
	 * decodificatore. */
	void (*video_fin)(void *ctx, int64_t stream);
	/* ⛔ §5.1, §6.2: `RESET_STREAM` ⇒ il fotogramma e' **incompleto**, il
	 * client lo butta, NON lo consegna, e lo tratta come un buco. */
	void (*video_azzera)(void *ctx, int64_t stream);

	/* ------------------------------------------------------------------ */
	/* ⭐ I SEI GANCI DEL CANALE DI INPUT — `RCP.md` §7.3, e le firme sono
	 *    quelle di `src/input.h` campo per campo.
	 *
	 * ⛔⭐ PERCHE' SONO GANCI E NON UN `#include "input.h"` — e non e' una
	 *     preferenza di stile, e' il `Makefile`.
	 *
	 *     `src/input.h` dice, nella sua intestazione, che a chiamare quelle
	 *     funzioni e' `rcp.c`.  ⛔ Ma `rcp.c` esiste in DUE cartelle —
	 *     `src/` e `banchi/rcp/` — e il `Makefile` (variabile `GEMELLATI`)
	 *     pretende che le due copie combacino byte per byte.  La seconda
	 *     viene copiata da `banchi/01-b3-rcp-innesta.py` dentro
	 *     `examples/` di ngtcp2, dove `input.h` **non c'e' e non ci puo'
	 *     andare**: quel file elenca esattamente tre nomi
	 *     (`rcp.c`, `rcp.h`, `autenticazione.c`).
	 *     ⇒ Un `#include "input.h"` qui NON compila l'innesto, cioe' spegne
	 *       B3, B5, B6, B8 e B11 in un colpo solo.
	 *
	 * ⭐ E la forma dei ganci e' quella che questo file gia' usa per le altre
	 *    due cose che `rcp.c` non puo' conoscere: PAM (`verifica`) e gli
	 *    stream (`video_*`).  «Riceve byte, restituisce byte, e chiede a chi
	 *    lo ospita di fare» — l'intestazione di questo file, applicata.
	 *
	 * ⛔ SONO **OPZIONALI**, e la loro assenza NON e' una violazione del
	 *    client: un server senza canale di input **convalida lo stesso** il
	 *    messaggio (quello e' protocollo, e §3 non fa sconti) e poi scrive
	 *    nel registro che non l'ha iniettato.  ⚠ «Non ho un canale di input»
	 *    e «il client ha sbagliato» sono due fatti diversi, e chiudere la
	 *    sessione per il primo punirebbe chi non ha sbagliato niente.
	 *
	 * ⚠ Chi li collega li collega TUTTI E CINQUE: `rcp.c` guarda il primo e
	 *   se c'e' pretende gli altri, perche' un canale che sa muovere il
	 *   puntatore e non sa rilasciare un pulsante lascia il desktop peggio di
	 *   come l'ha trovato.
	 *
	 * ⛔ IL VALORE DI RITORNO E' QUELLO DI `input.h`, e sono TRE stati, non
	 *    due: `0` consegnato al compositore · `-1` no · `1` — solo per
	 *    `input_lettera` — «quel carattere NON e' producibile con la
	 *    disposizione della sessione», che §7.3 obbliga a scrivere nel
	 *    registro e vieta di sostituire con un'altra lettera o col silenzio. */
	int (*input_puntatore)(void *ctx, uint32_t x, uint32_t y);
	int (*input_pulsante)(void *ctx, uint16_t codice, int premuto);
	/* ⛔⛔ IL SEGNO NON SI INVERTE QUI, E NON SI INVERTE IN `rcp.c`.
	 *
	 *     `RCP.md` §7.3 (riquadro «Il segno della rotella», `[M]` 10 agosto
	 *     2026) impone al server di invertire l'asse verticale, e
	 *     `src/input.h` dichiara che l'inversione avviene **dentro
	 *     `input_rotella()`, una volta sola, in un posto solo**.  Invertirlo
	 *     anche qui lo annullerebbe, e il sintomo — «la rotella va al
	 *     contrario» — e' la forma d'errore E11 che quel riquadro esiste per
	 *     evitare.
	 * ⚠ E i mezzi scatti passano interi: 120 = uno scatto, 60 = mezzo, e
	 *   `rcp.c` NON arrotonda. */
	int (*input_rotella)(void *ctx, int32_t asse_x, int32_t asse_y);
	int (*input_lettera)(void *ctx, uint32_t carattere);
	int (*input_posizione)(void *ctx, uint16_t codice, int premuto);
	/* ⛔⭐ §7.3, ultimo capoverso: «Al distacco si rilascia tutto.  Quando una
	 *     connessione finisce — per congedo, per silenzio, per errore — il
	 *     server DEVE rilasciare ogni tasto e ogni pulsante che risultano
	 *     premuti».  ⭐ `RCP.md` §11 la chiama «la regola col rapporto
	 *     danno/costo piu' alto del documento».
	 *
	 * ⛔ E il gancio sta QUI perche' i tre modi in cui «una connessione
	 *    finisce» si osservano tutti e tre da dentro questo modulo, e da
	 *    nessun'altra parte insieme: il congedo (`congeda()`), il silenzio di
	 *    trenta secondi (`rcp_tempo()`), l'errore (`rcp_violazione()`).
	 *
	 * ⚠ `input.h` lo assegna anche a `figlio.c` («chiama
	 *   `input_rilascia_tutto()` al distacco»), e le due chiamate non
	 *   litigano: la funzione rilascia quel che RISULTA premuto e la seconda
	 *   volta non trova niente da rilasciare — restituisce 0.  ⛔ Ma il
	 *   doppione va coordinato, non subito: vedi il rapporto
	 *   `fasi/rapporti/F4-A3-filo-input.md`.
	 *
	 * ⛔⛔⭐ E LA RISPOSTA HA TRE VALORI, NON UNO — 16 agosto 2026, e l'ha
	 *      trovata la prima prova col browser di questa regola.
	 *
	 *      Diceva «restituisce quanti ne ha rilasciati, perche' il banco possa
	 *      contarli», e nel prodotto vero quel conto **non puo' esistere qui**:
	 *      chi preme e chi rilascia e' il FIGLIO, un altro processo, e la
	 *      risposta non torna indietro.  ⇒ `webtransport.c` rispondeva `0`
	 *      intendendo «la richiesta e' partita», e `rcp.c` lo scriveva nel
	 *      registro come «0 erano premuti».
	 *
	 *      `[M]` Misurato: quattro distacchi col tasto e il pulsante DAVVERO
	 *      giu' — la riga diceva `0` e il figlio, due righe sotto, `2`.
	 *      ⛔ E' `LEZIONI.md` §1.9 nel posto peggiore: la regola col rapporto
	 *      danno/costo piu' alto del documento aveva l'unico testimone che
	 *      diceva sempre «non c'era niente giu'», cioe' **la faccia del verde
	 *      su un rilascio che non fosse avvenuto affatto**.
	 *
	 *   `>= 0`                     → il conto VERO (lo sa chi cuce: banchi in
	 *                                processo, `04-b23`, `04-b24`);
	 *   `RCP_RILASCIO_SENZA_CONTO` → chiesto, e il conto lo sa UN ALTRO — si
	 *                                scrive dove cercarlo, non un numero;
	 *   `RCP_RILASCIO_IMPOSSIBILE` → ⛔ NON si e' potuto chiedere: se qualcosa
	 *                                era premuto, **resta premuto**. */
	int (*input_rilascia_tutto)(void *ctx);

	/* ⭐⭐ IL GANCIO DELLA TELA — §7.1 `ADATTA_TELA`, e `DECISIONI.md`
	 *     §5.0-sexies: *«la tela del server si chiede della misura della tela
	 *     del client»*.
	 *
	 * ⛔ E' OPZIONALE, e la sua assenza NON e' un difetto del client: un ospite
	 *    che non lo collega non sa ridimensionare, e §7.1 dice che cosa
	 *    rispondere — `TELA(RIFIUTATA, COMPOSITORE_INCAPACE)`, che e' vero e
	 *    non chiude la sessione.  ⚠ E' quel che facevano i banchi della fase 1,
	 *    ed e' quel che ha fatto il prodotto fino al 15 agosto 2026.
	 *
	 * ⛔⭐ IL VALORE DI RITORNO E' «LA DOMANDA E' PARTITA», NON «LA TELA E'
	 *     CAMBIATA», e confondere le due cose e' il difetto che questo riquadro
	 *     esiste per evitare.  `[M]` 14 agosto 2026: chiedere a labwc la misura
	 *     che l'output HA GIA' risponde «riuscito» **senza mandare nessun
	 *     evento**; e §4.5 permette al compositore di concedere una misura
	 *     diversa da quella chiesta.  ⇒ Chi risponde `true` sta dicendo soltanto
	 *     «l'ho chiesto a chi di dovere».
	 *
	 * ⇒ La tela in vigore cambia — e `TELA` parte — soltanto quando arriva la
	 *   prova: un fotogramma alla misura nuova, che l'ospite riporta qui dentro
	 *   con `rcp_tela_concessa()`.  ⛔ E se non arriva, ci pensa il fondo di
	 *   `RCP_TELA_ATTESA_MS`: §7.1 vuole una risposta comunque.
	 *
	 * ⚠ La misura che arriva qui e' gia' passata da `rcp_misura_ammessa()`:
	 *   intervallo e parita' sono garantiti, e chi ospita non li ricontrolla —
	 *   due regole sullo stesso valore in due posti diventano due regole diverse
	 *   il giorno in cui una cambia. */
	bool (*ritela)(void *ctx, uint32_t larghezza, uint32_t altezza);

	/* ⛔⭐⭐ «CHE MISURA HA IL PALCO ADESSO?» — e senza questa domanda il
	 *     RI-ATTACCO nasce con due verita'.
	 *
	 * ⛔ IL CASO, ed e' quello che `DECISIONI.md` §5.0-sexies annota come
	 *    inevitabile: il palco sopravvive al client (invariante I4) e la tela
	 *    nasce a ogni attacco (§5.0).  ⇒ L'utente si stacca dal DeX con la tela
	 *    a 1912×1044 e si riattacca dal portatile, dove la pagina chiede
	 *    1920×1080.  §4.5 direbbe di concedere quel che si chiede — ⛔ ma il
	 *    palco continua a consegnare 1912×1044, e §6.2 impone di NON spedire un
	 *    fotogramma la cui misura non e' la tela in vigore.  ⇒ **Zero pixel, e
	 *    nessuna riga che dica perche'**, finche' qualcuno non muove la tela.
	 *
	 * ⇒ Si CHIEDE, invece di concedere alla cieca: se il palco ha gia' una
	 *   misura, `SESSIONE` concede QUELLA (§4.5 lo permette esplicitamente, e la
	 *   pagina la dichiara nel registro), e la sessione parte in accordo col
	 *   mondo.  ⭐ Poi la pagina manda il suo `ADATTA_TELA` e si arriva dove si
	 *   voleva — ma passando per uno stato in cui i pixel arrivano.
	 *
	 * ⛔ E' OPZIONALE: chi non lo collega concede quel che il client chiede, che
	 *    e' esattamente il comportamento di prima del 15 agosto 2026.
	 *
	 * `false` = «non lo so» — nessun palco, o nessun fotogramma ancora.  ⚠ Non
	 * e' «0x0»: la differenza e' la stessa di `rcp_tela_in_vigore()`. */
	bool (*tela_del_palco)(void *ctx, uint32_t *larghezza, uint32_t *altezza);

	/* ⛔⭐ «QUEST'UTENTE HA GIA' UNA SESSIONE GRAFICA LOCALE?» — §5.1 di
	 *     `SPECIFICHE.md`, motivo `0x05 GIA_ATTIVA_LOCALE`.
	 *
	 * ⛔ E' UN GANCIO E NON UNA CHIAMATA A logind, per la stessa ragione dei
	 *    sei dell'input: `rcp.c` esiste in DUE cartelle e la copia di
	 *    `banchi/rcp/` viene innestata dentro `examples/` di ngtcp2, dove non
	 *    c'e' ne' `gio-2.0` ne' un bus di sistema.  Un `#include <gio/gio.h>`
	 *    qui spegnerebbe B3, B5, B6, B8 e B11 in un colpo solo.
	 *
	 * ⛔ E' OPZIONALE, e la sua assenza NON e' una violazione del client: chi
	 *    non lo collega non applica la regola di §5.1, e ⛔ `rcp.c` lo SCRIVE
	 *    NEL REGISTRO invece di tacere (`CODER.md` §4.2: il ripiego si
	 *    dichiara).  ⚠ Una regola che non c'e' e una regola che dice «no» sono
	 *    due fatti diversi, e nel registro devono restare tali.
	 *
	 * `descrizione` — se non NULL — riceve di che sessione si tratta, per il
	 * registro del server.  ⛔ NON finisce nel corpo del congedo: §8.2 vieta di
	 * dire al client i fatti delle sessioni altrui.
	 *
	 * Restituisce `true` se una sessione grafica **locale** di quell'utente
	 * esiste adesso. */
	bool (*sessione_locale)(void *ctx, const char *utente, char *descrizione,
	                        size_t quanto);

	/* ⛔⭐ «L'UTENTE HA CHIESTO DI USCIRE» — `RCP.md` §7.6, `TERMINA_SESSIONE`.
	 *
	 * ⛔ E' l'altra meta' di `DECISIONI.md` §4.1-ter: il filo che cade lascia
	 *    la sessione viva (I4), questo la FINISCE — e con lei si chiudono i
	 *    programmi dell'utente.
	 *
	 * ⚠ Chiamato DOPO che il congedo `0x10` e' partito, e l'ordine e'
	 *   normativo: quando il compositore cade, il palco cade con lui e il
	 *   canale non serve piu'.  Un `0x10` spedito dopo e' il rilievo B-7 con un
	 *   nome nuovo.
	 *
	 * ⛔ E' OPZIONALE: chi non lo collega non puo' servire §7.6, e `rcp.c`
	 *    risponde `ERRORE_PROTOCOLLO`? ⚠ NO — risponde congedando lo stesso con
	 *    `0x10` e scrivendo nel registro che la sessione non e' stata toccata.
	 *    «Il client ha sbagliato» e «questo server non sa farlo» sono due fatti
	 *    diversi, e punire il client per il secondo sarebbe punire chi non ha
	 *    sbagliato niente. */
	void (*termina_sessione)(void *ctx);
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

/* ⛔⭐ §5.3 — «il client e' ancora li'»: la chiama il TRASPORTO dopo ogni
 *     pacchetto DECIFRATO E AUTENTICATO, e da lei dipende l'orologio dei trenta
 *     secondi.  ⚠ Non dall'ultimo byte di RCP: quello e' l'orologio della
 *     *inattivita' dell'utente*, che e' di trenta MINUTI e non di trenta
 *     secondi.  La ragione lunga — e la misura che l'ha imposta — sta sul campo
 *     `ultima_vita` in `rcp.c`. */
void rcp_segno_di_vita(rcp_sessione *s, uint64_t ora_ms);

/* ⛔ Azzera il registro delle sessioni attive.  Serve SOLO al banco, fra una
 * prova e l'altra: in un server vero non lo chiama nessuno. */
void rcp_azzera_registro_sessioni(void);

/* ========================================================================= */
/* ⭐ IL CANALE VIDEO — `RCP.md` §2.5, §5.1, §5.2, §6.2                       */
/*                                                                           */
/* ⛔ PERCHE' STA QUI E NON IN UN MODULO SUO                                  */
/*                                                                           */
/* Sette delle undici regole del canale video non parlano dei 28 byte: parlano */
/* dello **stato della sessione**.  «Nessuno stream prima di aver spedito     */
/* `SESSIONE`» (§2.5) e' lo stato; «`largh.`/`altezza` valgono la tela in     */
/* vigore» (§6.2) e' la tela concessa da `SESSIONE` o dall'ultimo `TELA`;     */
/* «`codec` DEVE essere quello negoziato» e' §4.3; «il primo fotogramma DEVE  */
/* essere una chiave» (§5.2) e' il primo **dopo `SESSIONE`**; e               */
/* `RICHIEDI_CHIAVE` arriva sul canale di controllo.                          */
/*                                                                           */
/* ⇒ Un `video.c` a parte dovrebbe **ricopiarsi** quello stato, e due copie   */
/*   di uno stato divergono: e' la stessa ragione per cui `RCP.md` §0 esiste, */
/*   applicata dentro un programma solo.  ⭐ E ha un secondo effetto, che si  */
/*   vede nel `Makefile`: **zero righe da aggiungere**, perche' `rcp.c` e'    */
/*   gia' compilato e gia' confrontato con `banchi/rcp/` a ogni costruzione.  */
/*                                                                           */
/* ⛔ E QUEL CHE QUESTO MODULO NON FA, DICHIARATO: non guarda **dentro** i    */
/*    byte del codec.  §5.2 vuole che la chiave sia una chiave **vera** —     */
/*    VPS/SPS/PPS davanti all'IDR — e quella meta' la puo' giudicare solo chi */
/*    conosce HEVC/AV1.  Qui si dichiara invece di farla credere coperta.     */

/* Gli esiti di `rcp_video_apri()` e di `rcp_video_spedisci()`.
 * ⛔ Sono SETTE e non due, perche' i fatti sono sette: chi chiama deve poter
 *    distinguere «ricodifica piu' piccolo» da «mandami una chiave» da «non
 *    hai ancora spedito `SESSIONE`».  Un solo `false` li metterebbe sotto la
 *    stessa etichetta, che e' la forma d'errore E2. */
enum {
	RCP_VIDEO_SPEDITO = 0,
	/* i quattro ganci non ci sono: questo server non ha un canale video */
	RCP_VIDEO_NIENTE_CANALE,
	/* ⛔ §2.5 / invariante I3: `SESSIONE` non e' ancora partita */
	RCP_VIDEO_PRIMA_DI_SESSIONE,
	/* ⛔ §5.2: ci vuole una CHIAVE — il primo dopo `SESSIONE`, il primo alla
	 * misura nuova dopo un `TELA`, o quella che il client ha chiesto */
	RCP_VIDEO_SERVE_UNA_CHIAVE,
	/* ⛔ §6.2: oltre i 16 MiB.  Si RICODIFICA a qualita' inferiore — non si
	 * spedisce, e non e' partito un byte */
	RCP_VIDEO_TROPPO_GRANDE,
	/* non si e' potuto aprire uno stream adesso: non e' partito niente */
	RCP_VIDEO_STREAM_NON_APERTO,
	/* la scrittura si e' rotta a meta': lo stream e' stato AZZERATO (§6.2), e
	 * il client lo trattera' come un buco — mai come un fotogramma corto */
	RCP_VIDEO_ROTTO_A_META,
	/* c'e' gia' un fotogramma aperto su questa sessione: si finisce o si
	 * abbandona quello, prima */
	RCP_VIDEO_GIA_APERTO,
};

/* ⛔ APRE IL FOTOGRAMMA e ci scrive i **28 byte** di §6.2.
 *
 * `chiave`      §5.2: `0x0301` se vero, `0x0302` se falso.
 * `lunghezza`   quanti byte di DATI seguiranno.  ⛔ Si dichiara **prima**, e
 *               non e' una comodita': §6.2 dice che «il tetto vincola prima di
 *               tutto chi spedisce», e un tetto che si controllasse mentre i
 *               byte escono avrebbe gia' spedito i primi 16 MiB.  Chi codifica
 *               la lunghezza dell'access unit ce l'ha.
 * `istante_us`  microsecondi dell'orologio **monotono del server** alla
 *               cattura (§6.2).  ⚠ Non e' un'ora.
 * `input`       l'identificatore dell'ultimo input iniettato prima della
 *               cattura, 0 se nessuno (§6.2, §7.3).
 * `ora_ms`      l'orologio della sessione, come per `rcp_ricevi()`.  ⛔ E' un
 *               parametro a parte e NON si ricava da `istante_us`: quello e'
 *               l'orologio della cattura, e che i due siano lo stesso e'
 *               probabile e non scritto da nessuna parte.  Serve ai 200 ms di
 *               §5.2 (l'eccezione 5 di §3).
 *
 * ⛔ E QUEL CHE **NON** SI PASSA E' IL PUNTO: `largh.`, `altezza`, `codec` e
 *    `numero` non sono parametri.  Li mette questo modulo, dalla tela in
 *    vigore (§4.5, §7.1), dalla negoziazione di §4.3 e dal proprio contatore
 *    (§6.2).  ⭐ Cosi' le tre regole non si possono violare **per costruzione**
 *    invece che per disciplina di chi chiama — che e' l'invariante I7 letta da
 *    dentro: la protezione sta nel programma, non in una riga che si puo'
 *    perdere. */
int rcp_video_apri(rcp_sessione *s, bool chiave, size_t lunghezza,
                   uint64_t istante_us, uint32_t input, uint64_t ora_ms);

/* Scrive un pezzo dei dati del fotogramma aperto.  ⛔ Se non entrano, lo
 * stream viene AZZERATO qui dentro (§6.2) e si restituisce
 * `RCP_VIDEO_ROTTO_A_META`: un fotogramma a meta' chiuso con FIN sarebbe un
 * fotogramma completo per chi riceve. */
int rcp_video_pezzo(rcp_sessione *s, const uint8_t *dati, size_t len);

/* ⛔ §6.2: chiude con **FIN**, e solo se i `lunghezza` byte dichiarati sono
 * usciti tutti.  Se ne mancano, azzera e restituisce `RCP_VIDEO_ROTTO_A_META`:
 * «FIN» e' un'affermazione, non un modo di chiudere. */
int rcp_video_finisci(rcp_sessione *s);

/* ⛔ §5.1: abbandona il fotogramma aperto con `RESET_STREAM`, perche' ne e'
 * gia' partito uno piu' recente.  ⛔ E §5.2 vieta di abbandonare una
 * **chiave**: qui si rifiuta e si restituisce `false` — «abbandonare la cura
 * non e' una cura».  ⛔ Ogni abbandono finisce nel registro (§5.1): «un
 * fotogramma perso in silenzio e uno abbandonato di proposito hanno lo stesso
 * aspetto dal lato che riceve». */
bool rcp_video_abbandona(rcp_sessione *s, const char *perche);

/* ⛔⭐ §5.1 — L'ABBANDONO DI UN FOTOGRAMMA GIA' CHIUSO CON FIN MA ANCORA IN
 *     CODA, cioe' **la scena che §5.1 descrive davvero**: «il server PUO'
 *     chiamare `RESET_STREAM` su un fotogramma che non serve piu' — perche' ne
 *     e' gia' partito uno piu' recente — e i byte non ancora spediti non
 *     partono affatto».
 *
 * ⛔ Non e' la stessa cosa di `rcp_video_abbandona()`, e le due non si possono
 *    fondere: quella abbandona il fotogramma **aperto**, a cui manca ancora un
 *    pezzo da scrivere; questa abbandona uno **finito**, che per RCP e' gia'
 *    partito e per il trasporto e' ancora fermo in coda.  Chi lo sa e' solo chi
 *    tiene la coda; chi deve scrivere la riga, contare e riaccendere il debito
 *    della chiave e' solo questo modulo.  ⇒ Il taglio passa di qui.
 *
 * `chiave` lo passa chi chiama perche' §5.2 vieta l'abbandono di una chiave
 * **anche da valle**: qui si rifiuta, si scrive, e si restituisce `false`.
 * `byte_non_usciti` va nella riga: «l'ho buttato prima di spendere banda» e
 * «l'avevo gia' quasi spedito» sono due fatti diversi. */
bool rcp_video_abbandonato_a_valle(rcp_sessione *s, uint32_t numero, bool chiave,
                                   size_t byte_non_usciti, const char *perche);

/* ⛔ §2.3 — la riga obbligatoria di quando lo stream **non si apre**: «e in
 * tutt'e due i casi si scrive nel registro».  La chiama `rcp_video_apri()` da
 * se'; e' qui perche' un banco possa nominarla. */
void rcp_video_niente_credito(rcp_sessione *s, bool chiave, uint64_t restano);

/* Quanti fotogrammi questa sessione ha spedito e quanti ne ha abbandonati.
 * ⛔ I due numeri insieme, sempre: «zero abbandonati» detto da solo non
 * distingue una linea che porta da un canale che non ha mai spedito niente. */
void rcp_video_conti(const rcp_sessione *s, uint32_t *spediti,
                     uint32_t *abbandonati);

/* La comodita': apre, scrive e chiude in una chiamata.  ⛔ Il tetto dei 16 MiB
 * si applica PRIMA di aprire lo stream, quindi su un fotogramma troppo grande
 * non parte un byte e non si apre niente. */
int rcp_video_spedisci(rcp_sessione *s, bool chiave, const uint8_t *dati,
                       size_t len, uint64_t istante_us, uint32_t input,
                       uint64_t ora_ms);

/* ⛔ §7.1 — si e' appena risposto `TELA(ADATTATA, lar, alt)`: da qui in poi la
 * tela **in vigore** e' questa, e §6.2 ci lega `largh.`/`altezza` di ogni
 * fotogramma successivo.
 *
 * ⛔ E se la misura e' cambiata DAVVERO apre il debito di §5.2: il primo
 *    fotogramma alla misura nuova DEVE essere una chiave.  ⚠ Se la misura
 *    **non** cambia il debito NON si apre — §7.1 fa rispondere `TELA` anche a
 *    un `ADATTA_TELA` che chiede la misura in vigore, e aprire il debito li'
 *    fermerebbe il video su una sessione sana ogni volta che l'utente
 *    trascina una finestra e la rimette dov'era.
 *
 * ⚠ Chi risponde `TELA` non e' questo modulo: la risposta vuole un
 *   compositore che sappia ridimensionare, e `ADATTA_TELA` non e' ancora
 *   servito (vedi il registro di `rcp_ricevi`).  Questa funzione esiste
 *   perche' il giorno in cui lo sara', la regola di §6.2 stia **in un posto
 *   solo** — qui — invece di essere ricopiata accanto a chi manda il `TELA`. */
/* ⛔⭐⭐ LA MISURA AMMESSA PER LA TELA — §7.1, e sta QUI perche' a doverla
 *      applicare e' chi legge `ADATTA_TELA` dal filo.
 *
 * ⛔⛔ IL TETTO NON LO METTE NESSUN ALTRO, e sopra il tetto non c'e' un errore:
 *     c'e' una **morte silenziosa**.  `[M]` 14 agosto 2026, misurato sui
 *     compositori veri:
 *
 *       · oltre **16384** per lato `gnome-shell` MUORE («Failed to create
 *         texture 2d») — e 16386 e' DENTRO il `MAX_SIZE` che Mutter
 *         **dichiara**, cioe' il limite dichiarato mente;
 *       · su labwc `32768x32768` uccide il compositore con **zero righe di
 *         registro**, anche in modo prolisso.
 *
 * ⇒ Con la tela a misura fissa nessun client poteva arrivarci.  Da
 *   `DECISIONI.md` §5.0-sexies la misura la CHIEDE il client ⇒ un client
 *   qualunque potrebbe spegnere la sessione di chi lo ospita, e la guardia
 *   diventa obbligatoria.
 *
 * ⛔⭐⭐ E I LIMITI SONO QUELLI DI §4.5, PER LATO — corretti la notte del 15
 *      agosto 2026, refutando, e la prima stesura aveva **inventato i suoi**.
 *
 *      Diceva 200..8192 su tutt'e due i lati, con l'`[S]` di MS-RDPEDISP
 *      accanto.  ⛔ Ma `RCP.md` §4.5 e' NORMATIVO e dice un'altra cosa —
 *      *«larghezza e altezza della tela DEVONO stare fra 320x240 e 7680x4320»* —
 *      e `ATTACCA` la applicava gia'.  ⇒ Erano due regole sullo stesso numero in
 *      due posti, cioe' precisamente quel che il riquadro in fondo a `cattura.h`
 *      dichiara di voler evitare.
 *
 * ⚠ E la divergenza era **irraggiungibile** finche' `ADATTA_TELA` rispondeva
 *   sempre `COMPOSITORE_INCAPACE`: e' diventata viva la notte in cui la catena
 *   e' stata scritta.  Il caso concreto e' il bordo inferiore della finestra
 *   tirato su: `ADATTA_TELA(1600, 230)` veniva concessa, e la stessa misura
 *   veniva poi RIFIUTATA da `ATTACCA` al ri-attacco.
 *
 * ⛔ E la PARITA' e' NOSTRA, non dei compositori: `[M]` labwc concede anche le
 *   misure dispari, ed e' il nostro 4:2:0 a rifiutarle
 *   (`src/codificatore.c:1373`).  Si tronca in GIU' e si DICE, con `TELA` che
 *   riporta la misura vera.
 *
 * `fuori_l`/`fuori_a` ricevono la misura ammessa piu' vicina (troncata al pari).
 * Ritorna `false` se la richiesta e' fuori dai limiti: allora si risponde
 * `TELA(RIFIUTATA, MISURA_FUORI_LIMITI)` e **non** si aggiusta in silenzio. */
#define RCP_TELA_L_MINIMA 320u
#define RCP_TELA_L_MASSIMA 7680u
#define RCP_TELA_A_MINIMA 240u
#define RCP_TELA_A_MASSIMA 4320u
bool rcp_misura_ammessa(uint32_t larghezza, uint32_t altezza, uint32_t *fuori_l,
                        uint32_t *fuori_a);

void rcp_tela_adattata(rcp_sessione *s, uint32_t lar, uint32_t alt);

/* ⛔⭐⭐ QUANTO SI ASPETTA IL FOTOGRAMMA CHE DIMOSTRA IL CAMBIO — §7.1.
 *
 * ⚠ NON e' il tempo del ridimensionamento: `[M]` 14 agosto 2026 quello e' **41,6
 *   ms** su Mutter e **5,1 ms** su labwc.  E' il fondo oltre il quale si smette
 *   di aspettare e si RISPONDE lo stesso, perche' §7.1 dice *«a ogni
 *   `ADATTA_TELA` il server DEVE rispondere con un `TELA`, riuscito o no.  Un
 *   silenzio lascia il client ad aspettare per sempre»* — e §6.2 gli fa
 *   TRATTENERE i fotogrammi finche' quella risposta non arriva.
 *
 * ⛔ Tre secondi e non trecento millisecondi, e la ragione e' misurata: su un
 *    desktop FERMO il fotogramma nuovo arriva perche' la rinegoziazione stessa
 *    lo fa arrivare, ⚠ ma fra la richiesta e i pixel c'e' un confine di
 *    processo, un compositore e — se il palco e' caduto — un rimontaggio.  Un
 *    fondo troppo corto direbbe `NON_ORA` a un cambio che stava riuscendo, e il
 *    client mostrerebbe «adatta il desktop» come spento su un server che sa
 *    farlo.
 * ⚠ E il prezzo del fondo troppo lungo lo paga la memoria del client (la coda
 *   dei trattenuti di §6.2): per questo esiste un fondo, e non «si aspetta». */
#define RCP_TELA_ATTESA_MS 3000u

/* ⛔ Ogni quanto si RICHIEDE al palco di venire alla tela in vigore, quando ne
 *    ha una sua.  Raddoppia a ogni tentativo a vuoto fino al massimo.
 * ⚠ Non e' il tempo del ridimensionamento (`[M]` 41,6 ms su Mutter): e' il passo
 *   con cui si insiste, e cresce perche' il caso «non si muove» esiste. */
#define RCP_TELA_RICHIAMO_MS 500u
#define RCP_TELA_RICHIAMO_MAX_MS 8000u

/* ⭐⭐ LA RISPOSTA DEL PALCO — l'altra meta' del gancio `ritela`: la domanda esce
 *     di la', la risposta rientra di qui.  La porta il FIGLIO, che e' l'unico a
 *     sapere che cosa il compositore ha davvero fatto.
 *
 * ⛔⭐ PERCHE' PORTA **DUE** MISURE, e non basta quella nuova: `voluta_*` dice a
 *     quale richiesta risponde.  ⚠ Senza, due `ADATTA_TELA` incatenate — cioe'
 *     un utente che trascina il bordo della finestra — facevano prendere il
 *     fotogramma della PRIMA per la risposta della SECONDA, e il desktop si
 *     assestava sulla misura sbagliata **con i conti dei messaggi in ordine**.
 *
 * ⛔ `avuta_l == 0` = «il palco non ce l'ha fatta»: si risponde `NON_ORA`
 *    subito, invece di far scadere il fondo di `RCP_TELA_ATTESA_MS` per una
 *    notizia che c'e' gia'.
 *
 * ⛔⛔ E QUEL CHE NON FA, perche' era il difetto piu' grave della prima stesura:
 *     **non manda mai un `TELA` che nessuno ha chiesto.**  §6.2 dice che il
 *     client trattiene una misura mai annunciata solo finche' ha una
 *     `ADATTA_TELA` senza risposta; senza, e' `ERRORE_PROTOCOLLO` — e il
 *     fotogramma, che viaggia su uno stream suo, puo' arrivare **prima** del
 *     `TELA` che lo giustificherebbe.  ⇒ Quando il palco e' altrove di suo, gli
 *     si RICHIEDE la tela in vigore con un'attesa che cresce, e non si adotta
 *     niente. */
void rcp_tela_dal_palco(rcp_sessione *s, uint32_t voluta_l, uint32_t voluta_a,
                        uint32_t avuta_l, uint32_t avuta_a, uint64_t ora_ms);

/* ⛔ C'e' un'`ADATTA_TELA` girata al palco e non ancora risposta?  ⚠ Serve a chi
 * vede i fotogrammi per sapere se una misura inattesa e' una corsa legittima o
 * un fatto nuovo — e al banco, per leggere lo stato invece di dedurlo dai
 * tempi. */
bool rcp_tela_in_volo(const rcp_sessione *s, uint32_t *lar, uint32_t *alt);

/* ⭐⭐ «IL PALCO NON C'E' ANCORA»: il fondo di §7.1 si RIMANDA — 16 agosto 2026.
 *
 * ⛔ IL DIFETTO CHE CURA, misurato tre volte in una mattina: dopo un logout la
 *    sessione grafica non c'e' piu', e il login successivo la fa nascere.  Il
 *    client chiede la sua tela subito; il palco monta cinque secondi dopo — ⛔ ma
 *    il fondo di `RCP_TELA_ATTESA_MS` scatta a tre, e da quel momento la
 *    richiesta e' CHIUSA.  Quando il palco arriva alla misura giusta, per questo
 *    modulo non risponde piu' a niente: lo si rimanda alla tela in vigore, e
 *    l'utente guarda un desktop piu' piccolo della finestra — le BANDE NERE.
 *
 * ⚠ E non e' «alzare il timeout»: e' smettere di DEDURRE.  Il figlio sa se il
 *   palco non c'e' ancora, e adesso lo dice (`LEZIONI.md` §7.5).  Il fondo
 *   resta a tre secondi per tutti i casi in cui nessuno ha promesso niente.
 *
 * `true` se la richiesta in volo era proprio quella e il fondo e' stato
 * rimandato.  ⛔ Non manda niente sul filo: sposta solo una scadenza. */
bool rcp_tela_rimanda(rcp_sessione *s, uint32_t voluta_l, uint32_t voluta_a,
                      uint64_t ora_ms);

/* Per il registro, per il banco e per chi cattura.  ⛔ `false` quando la tela
 * non c'e' ancora, che NON e' «0x0» (§6.0: niente valori sentinella). */
bool rcp_tela_in_vigore(const rcp_sessione *s, uint32_t *lar, uint32_t *alt);
/* §4.3/§6.2: 1 = HEVC, 2 = AV1.  ⛔ `0` = non ancora negoziato. */
uint8_t rcp_codec_negoziato(const rcp_sessione *s);
/* ⛔ §5.2: «il prossimo fotogramma deve essere una chiave?».  La chiede chi
 * codifica, perche' e' lui che decide il tipo di fotogramma. */
bool rcp_video_serve_chiave(const rcp_sessione *s);
/* Il `numero` (§6.2) dell'ultimo fotogramma spedito.  ⛔ `0` vuol dire
 * «nessuno», ed e' il significato che §6.2 e §7.1 danno allo zero. */
uint32_t rcp_video_ultimo_numero(const rcp_sessione *s);

/* ========================================================================= */
/* ⭐ IL CANALE DI INPUT — `RCP.md` §2.5, §3, §6.1, §7.1, §7.3               */
/*                                                                           */
/* ⛔ PERCHE' STA QUI E NON IN UN MODULO SUO — la stessa ragione del video.   */
/*                                                                           */
/* Delle regole di §7.3 quasi nessuna parla dei venti byte del messaggio:    */
/* parlano dello **stato della sessione**.  «Lo stream di input si apre dopo */
/* aver ricevuto `SESSIONE`, ed e' uno solo» e' §2.5; «le coordinate stanno  */
/* dentro la tela» e' la tela concessa da `SESSIONE` (§4.5) o l'ultima di    */
/* `TELA` (§7.1); «il secondo di grazia» e' il MOMENTO di quel `TELA`; e     */
/* l'`id` che questo canale porta e' lo stesso numero che §6.2 fa tornare    */
/* indietro nel campo `input` di ogni fotogramma.                            */
/*                                                                           */
/* ⇒ Un `input_filo.c` a parte dovrebbe ricopiarsi quello stato, e due copie */
/*   di uno stato divergono.                                                 */
/*                                                                           */
/* ⛔ E QUEL CHE QUESTO MODULO NON FA, DICHIARATO: non conosce `libei`, non   */
/*    conosce `xkbcommon`, non sa che cosa sia una disposizione di tastiera e */
/*    non tiene il conto di che cosa e' premuto.  Decodifica, CONVALIDA e     */
/*    consegna ai ganci qui sopra; l'altra meta' e' di `src/input.c`.         */

/* ⛔ Byte arrivati sullo **stream di input** (§2.5: unidirezionale, aperto dal
 *    client, **uno solo**, dopo `SESSIONE`, e tenuto aperto).
 *
 * `stream` e' l'identificatore che usa l'ospite — lo stesso numero che i ganci
 * `video_*` si scambiano.  ⛔ Serve a una cosa sola, e non e' un lusso: §2.5
 * dice «**uno solo**», e senza un identificatore questo modulo non puo'
 * distinguere il secondo stream di input dalla continuazione del primo.  ⚠ Chi
 * ospita non lo puo' giudicare al posto nostro: vede gli stream ma non sa che
 * cosa sia «di input» finche' non ha letto i primi due byte del carico, e la
 * regola di §2.5 e' di questo modulo insieme a tutte le altre.
 *
 * Restituisce `false` se la sessione e' finita (per congedo o per violazione),
 * esattamente come `rcp_ricevi()`.
 *
 * ⛔ E l'orologio del silenzio (§5.3) si azzera anche QUI: i byte dell'input
 *    sono byte del client come gli altri, e un utente che per trenta secondi
 *    non fa che muovere il mouse **non e' silenzioso**.  Senza questa riga
 *    perderebbe il posto mentre sta usando il desktop. */
bool rcp_ricevi_input(rcp_sessione *s, int64_t stream, const uint8_t *dati,
                      size_t len, uint64_t ora_ms);

/* ⭐ §6.2, campo `input`: «l'identificatore dell'ultimo input **iniettato**
 *    prima della cattura; 0 se nessuno».
 *
 * ⛔ **INIETTATO**, non «ricevuto», e la differenza si vede su ogni messaggio
 *    che il compositore rifiuta o che una disposizione non sa produrre: quel
 *    che il fotogramma promette e' che l'effetto di quell'input e' gia' nella
 *    scena, e di un input non iniettato non c'e' nessun effetto da vedere.
 *    ⇒ Questo numero avanza solo quando il gancio ha risposto 0.
 *
 * ⚠ Lo legge CHI CATTURA, nell'istante della cattura, e lo passa a
 *   `rcp_video_apri()`.  ⛔ Non lo mette `rcp_video_apri()` da se', e non e'
 *   una dimenticanza: «l'ultimo iniettato **prima della cattura**» e' un fatto
 *   dell'istante della cattura, e quello lo conosce solo chi cattura — fra la
 *   cattura e la chiamata passa tutta la codifica.  Prenderlo qui direbbe
 *   «l'ultimo iniettato prima della SPEDIZIONE», che e' un numero piu' alto e
 *   una promessa piu' grande di quella che il fotogramma puo' mantenere. */
uint32_t rcp_input_ultimo_iniettato(const rcp_sessione *s);

/* L'ultimo `id` **accettato** sul canale — iniettato o no.  ⛔ Per il registro e
 * per il banco: insieme al precedente distingue «il compositore non ha preso
 * niente» da «non e' arrivato niente», che e' `LEZIONI.md` §1.9 regola 1 sul
 * campo dove costa di piu' (il sintomo di tutt'e due e' «il desktop non
 * risponde»). */
uint32_t rcp_input_ultimo_id(const rcp_sessione *s);

/* ⛔ §7.1 — la versione di `rcp_tela_adattata()` che sa **quando**, e apre il
 *    SECONDO DI GRAZIA: «dopo aver mandato `TELA(ADATTATA)` il server DEVE
 *    accettare per un secondo coordinate di input valide sulla tela
 *    PRECEDENTE, saturandole alla nuova e scrivendolo nel registro; passato
 *    quel secondo, sono `ERRORE_PROTOCOLLO`».  E' la terza eccezione dichiarata
 *    a §3.
 *
 * ⚠ `rcp_tela_adattata()` resta, fa tutto il resto e **non apre la grazia**:
 *   non ha un orologio da cui farla partire.  Il ripiego si DICHIARA
 *   (`CODER.md` §4.2) e lo dichiara una riga di registro, non questo commento. */
void rcp_tela_adattata_ora(rcp_sessione *s, uint32_t lar, uint32_t alt,
                           uint64_t ora_ms);

/* ========================================================================= */
/* ⭐ IL CURSORE — `RCP.md` §7.2, §5.5, §5, §6.1                             */
/*                                                                           */
/* ⛔ PERCHE' I PARAMETRI SONO SCALARI E NON UN `const CursoreForma *`.       */
/*                                                                           */
/* `src/cursore.h` definisce `CursoreForma` ed e' il contratto giusto — ma    */
/* `rcp.c` esiste in DUE cartelle e il `Makefile` (variabile `GEMELLATI`)     */
/* pretende che combacino byte per byte; la seconda copia la porta            */
/* `banchi/01-b3-rcp-innesta.py` dentro `examples/` di ngtcp2, e quel file    */
/* elenca TRE nomi: `rcp.c`, `rcp.h`, `autenticazione.c`.  ⇒ Un              */
/* `#include "cursore.h"` qui **non compila l'innesto**, cioe' spegne B3, B5, */
/* B6, B8 e B11 in un colpo solo.  E' la stessa ragione dei ganci dell'input, */
/* e la cura e' la stessa: i campi passano come scalari, e l'adattatore di    */
/* sei righe che scarta `CursoreForma` sta dove `cursore.h` puo' essere       */
/* incluso — cioe' dalla parte del coordinatore.                             */
/*                                                                           */
/* ⛔ E QUEL CHE QUESTA FUNZIONE **NON** CONTROLLA, DICHIARATO: i limiti di   */
/*    §5.5 — 256 per lato, il punto attivo dentro l'immagine, `0×0` con       */
/*    `0,0` per il nascosto, e «una sola delle due a zero e'                  */
/*    ERRORE_PROTOCOLLO» — li fa rispettare `src/cursore.c`.  Qui non si      */
/*    ricontrollano: due controlli sulla stessa regola in due posti diventano */
/*    due regole diverse il giorno in cui una cambia.                        */

/* Spedisce `CURSORE_FORMA` (§7.2) sul canale di controllo (§5).
 *
 * `larghezza`/`altezza`  ⛔ `0` e `0` insieme = cursore NASCOSTO (§5.5).
 * `attivo_x`/`attivo_y`  il punto che «punta»; `0,0` se nascosto.
 * `immagine`             `larghezza × altezza × 4` byte, BGRA PREMOLTIPLICATO.
 *                        ⛔ `NULL` e' lecito **solo** se non ci sono byte da
 *                        mandare.  ⚠ Si COPIA qui dentro: quando questa
 *                        funzione torna, il chiamante puo' riusare il buffer —
 *                        ed e' quel che `cursore.h` pretende, perche' li'
 *                        l'immagine «vive fino al richiamo successivo».
 * `immagine_n`           quanti byte ci sono DAVVERO dietro `immagine`.
 *
 * ⛔⭐ `immagine_n` NON e' ridondante, ed e' la ragione per cui questa firma non
 *     prende solo la misura: §7.2 impone che la lunghezza del messaggio valga
 *     **esattamente** `8 + larghezza × altezza × 4`, e senza sapere quanti byte
 *     esistono davvero questa funzione ne leggerebbe `larghezza × altezza × 4`
 *     **sulla fiducia** — cioe' farebbe, dal lato del mittente, precisamente il
 *     «leggo quel che c'e' e vado avanti» che §7.2 nomina.  Il cursore fatto di
 *     memoria altrui lo confezionerebbe il server.
 *
 * ⛔ Restituisce `0` se il messaggio E' PARTITO, `-1` se non e' partito — e in
 *    quel caso il perche' e' nel registro, sempre.  ⚠ Nel dubbio NON si manda:
 *    §7.2 fa rilevare la lunghezza sbagliata a CHI RICEVE, quindi un messaggio
 *    storto spedito da qui fa chiudere la sessione **alla pagina** e il registro
 *    del server non ne saprebbe niente.  Un cursore che non si aggiorna e'
 *    brutto; una sessione che cade e' rotta (`SPECIFICHE.md` §8.3).
 *
 * ⛔⛔ DAL THREAD DEL CICLO, MAI DA QUELLO DI TEMPO REALE DELLA CATTURA.
 *     `cattura.c` chiama `CursoreArrivata` sul thread di PipeWire
 *     (`cursore_rimbalzo()`, e il riquadro del ciclo in `cattura.h`); questo
 *     modulo non ha nessun lucchetto e `manda` scrive nella coda del trasporto.
 *     Chi cuce i due DEVE far passare la forma per il ciclo — e nel prodotto ci
 *     passa gia', perche' la cattura sta nel FIGLIO e la sessione nel padre. */
int rcp_cursore_forma(rcp_sessione *s, uint16_t larghezza, uint16_t altezza,
                      int16_t attivo_x, int16_t attivo_y,
                      const uint8_t *immagine, size_t immagine_n);

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
