/* budget.h — ⭐⭐⭐ IL BUDGET DI COMPOSIZIONE, fase 10 (25 agosto 2026).
 *
 * ─────────────────────────────────────────────────────────────────────────────
 * ⛔ IL DIFETTO CHE QUESTO MODULO CURA
 * ─────────────────────────────────────────────────────────────────────────────
 *
 * Fino a oggi il prodotto **non aveva un budget: accettava tutti e affamava
 * tutti insieme**.  `[M]` `fasi/10-…md` §S.2: sulla scena satura l'undicesimo
 * entra con **`negati 0`**, e la prima sessione passa da **39,60 a 0,96
 * fot/s** — il **−97,6 %** — con **104 rossi appaiati** contro l'invariante
 * **I1** (*«il ritmo cala solo su misura, e mai staccare»*) e contro
 * `DECISIONI.md` §4.6-bis.
 *
 * ⭐ Il metro della fase l'ha posto il regista (`DECISIONI.md` §4.6-septies):
 *    *«sei RDP su un'integrata modesta non e' un cattivo risultato»* ⇒ **la
 *    fase non deve far entrare dieci: deve FERMARSI DOVE SI DEVE, DICENDOLO.**
 *
 * ─────────────────────────────────────────────────────────────────────────────
 * ⛔ 1 · LA GRANDEZZA E' LA **COMPOSIZIONE**, NON LA CODIFICA
 * ─────────────────────────────────────────────────────────────────────────────
 *
 * `DECISIONI.md` §4.6 dice *«il limite vero lo pone il codificatore, e si
 * misura in pixel al secondo»*.  ⛔ `[M]` **Su questo ferro non e' vero**
 * (§6.11, §6.15):
 *
 *   | dove cede            | `[M]`                                          |
 *   |----------------------|------------------------------------------------|
 *   | il codificatore nudo | **1,86 Gpixel/s** in H.264 · 2,33 in HEVC      |
 *   | ⭐ **la composizione** | ⛔ **0,97 Gpixel/s** — la META', ed e' `rcs0` |
 *
 * ⛔ E a saturare `rcs0` e' **`gnome-shell` al 99,5 %**, mentre `remotix` sta a
 *    **0,00 %**: il collo e' una cosa che **non e' nostra**, e che il budget
 *    puo' solo **contare**, non ridurre.
 *
 * ⇒ La moneta e' il **PIXEL COMPOSTO**, e si dimostra: `[M]` §6.9 — ai
 *   cedimenti i Mpixel/s coincidono entro lo **0,6 %** al variare della tela,
 *   mentre i fotogrammi/s differiscono del **74,9 %**.
 *
 * ⛔ E NON si conta `us_codifica` — il numero che il primo disegno (§3.2)
 *    proponeva come «il costo vero»: `[M]` §6.9 e' un **RITARDO, non un
 *    COSTO**, la sua curva ha un termine fisso venticinque volte quello vero, e
 *    tararci sopra **sopravvaluterebbe una tela 480p di due volte**.
 *
 * ⭐ E gli ingredienti erano gia' tutti in mano al padre: `deposita_fotogramma()`
 *    (`main.c`) riceve **ogni** fotogramma con larghezza, altezza, istante e
 *    byte, e il figlio lo chiama **senza guardie** su «qualcuno guarda»
 *    ⇒ ⭐⭐ **il padre vede anche i FANTASMI** — le sessioni che codificano
 *    senza che nessuno guardi (§3.2), che costano alla GPU quanto le altre e
 *    che un conto tenuto sui posti RCP **non vedrebbe**.
 *    ⇒ Non serviva nessun canale nuovo fra padre e figlio: serviva **un
 *      accumulatore**, ed e' questo modulo.
 *
 * ─────────────────────────────────────────────────────────────────────────────
 * ⛔⛔ 2 · PRIMA DEI PIXEL SI GUARDA IL **RITARDO**
 * ─────────────────────────────────────────────────────────────────────────────
 *
 * `[M]` §6.9: a otto sessioni il totale consegnato e' **26,6 Mpixel/s contro
 * 480** ⇒ il conto sui pixel direbbe *«c'e' posto per altre cinque»*
 * **mentre tutti stanno a 1,5 fot/s**.  ⛔ **Dopo il dirupo il consegnato
 * CROLLA, e un budget che guardi solo i pixel mente proprio quando serve.**
 *
 * ⇒ C'e' una porta prima della somma, e la soglia e' **misurata, non scelta**:
 *   `[M]` i gradini sani stanno a **≤ 13,1 ms**, quelli rotti a **≥ 39,9 ms**,
 *   ⭐ **nessuna sovrapposizione** ⇒ la soglia e' la loro **media geometrica**,
 *   **22,9 ms**.  Una sessione che consegna poco **con 600 ms di ritardo** e'
 *   *strozzata*, non *ferma* — e sono due fatti che il solo consegnato non
 *   distingue (`LEZIONI.md` §1.31, §1.34: il meccanismo accanto al sintomo, e
 *   qui il meccanismo e' il RITARDO, non le chiavi, che `[M]` restano a **zero**
 *   anche dentro il crollo, 0 su 8 741).
 *
 * ⚠ E LE DUE COSE CHE QUESTA SOGLIA **NON** E':
 *   · **non e' universale**: e' di **quella scena** (1080p H.264, desktop GNOME
 *     veri, su i5-13500T + UHD 730).  Su un altro ferro va rimisurata;
 *   · **non e' la grandezza del meccanismo**: il ritardo che il padre misura e'
 *     un **maggiorante** del tempo di ritenuta del buffer del compositore —
 *     prudente nel verso giusto, ma non la stessa cosa.
 *   ⛔ E la seconda meta' del metro **non attraversa il confine di processo**:
 *     la «pista di decollo» del compositore vale `(buffer_distinti − 2) × 16,67
 *     ms`, e `buffer_distinti` (`cattura.h`) vive **nel figlio**.  §6.9 tiene
 *     la piu' prudente fra la misura e la pista; qui si ha la sola misura, e lo
 *     si dichiara invece di far finta che siano la stessa cosa.
 *
 * ─────────────────────────────────────────────────────────────────────────────
 * ⛔⛔ 3 · LA RISERVA — e il RISVEGLIO, che e' la falla vera
 * ─────────────────────────────────────────────────────────────────────────────
 *
 * `[M]` §6.16: otto sessioni **ferme** ammesse quando costavano `[M]` **0,01 %
 * l'una** si accendono **in 19 ms** e chiedono **8 × 14,4 = 115 %**, piu' il
 * titolare: ⛔⛔ **il 130 % di un motore che ne ha 100.**  Chi stava lavorando
 * perde il **95,9 %** del ritmo e il suo ritardo fa **×78** (9,7 → 756 ms).
 *
 * ⛔ **E il regolatore della fase 9 non lo puo' rimediare**: vive nel padre e
 *    ferma fotogrammi **gia' composti e gia' codificati** (§3.2) — cioe' agisce
 *    dopo che il costo di GPU e' gia' stato pagato.
 *
 * ⇒ ⭐ **La riserva e' la sola difesa.**  La domanda di chi e' dentro non e'
 *   quel che consegna adesso: e' **il piu' grande fra quel che consegna e una
 *   frazione `F` del suo caso peggiore** (la sua tela al ritmo massimo di
 *   questo ferro).  Una sessione ferma non costa zero: costa la sua riserva.
 *
 * `[M]` §6.9, sui dati della salita a undici:
 *
 *   | regola          | falsi NO | falsi SI' | tetto sature | tetto ferme  |
 *   |-----------------|----------|-----------|--------------|--------------|
 *   | `F = 0`         |    0     |     0     |      6       | ⛔ illimitato |
 *   | ⭐ **`F = 0,5`** |  **0**   |   **0**   |    **6**     | ⭐ **10**     |
 *   | `F = 1`         |    1     |     0     |      5       |      6       |
 *
 * ⭐ **Il DIECI di `SPECIFICHE.md` §5.5 ritrovato per MISURA invece che per
 *    promessa** — e lo sforamento da risveglio passa da **1 640×** a **2×**.
 * ⭐ `F = 0` e' la regola «consegnato», `F = 1` e' la regola «peggiore»: **e' la
 *    stessa regola con la manopola in mano al regista** (`--riserva`).
 *
 * ─────────────────────────────────────────────────────────────────────────────
 * ⛔ 4 · IL MARGINE SI SCRIVE DAI DUE LATI, E I DUE ERRORI NON COSTANO UGUALE
 * ─────────────────────────────────────────────────────────────────────────────
 *
 * `LEZIONI.md` §1.33:
 *
 *   **falso NO**   dice «non regge» e reggeva ⇒ **un utente rifiutato per
 *                  niente**.  Costa **un utente**.
 *   **falso SI'**  dice «regge» e non reggeva ⇒ ⛔⛔ **affama chi stava
 *                  lavorando**, e viola **I1**.  Costa **tutti**.
 *
 * `[M]` §6.9: il margine misurato e' **+1,65 %** sopra la domanda piu' alta che
 * ha retto e **−13,7 %** sotto la piu' bassa che ha ceduto ⇒ ⭐ **il margine dal
 * lato che affama tutti e' OTTO VOLTE quello dal lato che costa un utente**, ed
 * e' il verso giusto.  ⇒ Ogni ripiego di questo modulo va nel verso
 * **scomodo**: quel che non si sa si conta al **caso peggiore**.
 *
 * ⛔ E «non ho misurato» non e' «zero» (`CODER.md`): una sessione appena nata
 *    che non ha ancora consegnato niente **non costa zero** — costa il suo caso
 *    peggiore, finche' non si sa.
 *
 * ─────────────────────────────────────────────────────────────────────────────
 * ⛔ 5 · IL BUDGET NON SI AUTO-TARA, E NASCE SPENTO
 * ─────────────────────────────────────────────────────────────────────────────
 *
 * `[M]` §6.9: **prima che la macchina abbia ceduto una volta, la capacita' che
 * si e' letta e' un LIMITE INFERIORE, non un soffitto** — e' *«il punto in cui
 * si e' smesso di provare»*.  ⇒ ⛔ **Il prodotto non deve dedurre da se' il
 * proprio soffitto**: o glielo si da' con `--budget-mpixel-s N`, o **non c'e'
 * budget**.  Un soffitto dedotto da una salita che non ha mai fatto cedere la
 * macchina rifiuterebbe utenti per un numero che nessuno ha verificato.
 *
 * ⭐ E per `CODER.md` **I6** — *cio' che cambia quel che l'utente VEDE resta
 *    dietro un interruttore spento finche' non l'ha guardato* — il budget nasce
 *    **SPENTO** (`--budget-mpixel-s 0`).  Questo modulo **acquista una
 *    funzione**, non cura un difetto d'aspetto: un utente respinto e' la cosa
 *    piu' visibile che un server possa fare, e non si accende da se'.
 */
#ifndef BUDGET_H
#define BUDGET_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

/* ⛔⭐ IL RITMO MASSIMO PER SESSIONE — `[M]` **39,54 fot/s**, e non e' una
 *     scelta: e' quel che **una sessione da sola** ha consegnato su questo
 *     ferro, primo gradino della salita a undici (§6.9, `10-b99-misure.jsonl`,
 *     scena `satura`, 1920×1080, H.264, i5-13500T · Intel UHD 730 `renderD128`,
 *     cure della fase 9 accese).
 *
 * ⛔⛔ E' IL SECONDO NUMERO DELLA MACCHINA, e si misura **insieme** al primo:
 *      `--budget-mpixel-s` dice **quanto lavoro** la macchina regge, questo dice
 *      **quanto ne chiede una sessione sola quando spinge**.  ⇒ Chi porta il
 *      prodotto su un altro ferro e ne muove uno **rimisura anche l'altro**, o
 *      la riserva diventa una frazione di un caso peggiore che non e' di quella
 *      macchina.  ⚠ Non ha un'opzione apposta perche' la fase ne ha volute
 *      **tre** e nessuna di piu' (§8.1); il valore in vigore finisce nella riga
 *      d'avvio insieme agli altri, cosi' non e' un numero nascosto.
 *
 * ⚠ E si usa SOLO per il caso peggiore, mai per il consegnato: il consegnato si
 *   MISURA, fotogramma per fotogramma, e non si stima mai. */
#define BUDGET_RITMO_MAX_FOT_S 39.54

/* ⛔⭐ LA SOGLIA DEL RITARDO — `[M]` **22,9 ms**, media geometrica fra i 13,1 ms
 *     peggiori dei gradini SANI e i 39,9 ms migliori di quelli ROTTI, che
 *     ⭐ **non si sovrappongono** (§6.9).  ⚠ E' di **quella scena**: vedi il
 *     riquadro in testa, punto 2. */
#define BUDGET_RITARDO_AFFANNO_MS 22.9

/* ⭐ La manopola di `--riserva`, e il suo predefinito misurato (§6.9): a 0,5 il
 *    predittore fa **0 falsi si' e 0 falsi no** sui dati che ci sono. */
#define BUDGET_RISERVA_PREDEFINITA 0.5

/* ⛔ La tolleranza sul confronto, e ha una ragione precisa: la capacita' e' il
 *    **culmine MISURATO**, cioe' uno stato che si e' visto reggere.
 *    Confrontarlo con `≤` nudo rifiuterebbe **proprio quello stato** appena
 *    l'aritmetica muove la terza cifra — un falso NO per arrotondamento.
 * ⭐ L'1 % e' la ripetibilita' dichiarata del metro (`[M]` ±0,6 %, §6.1), ed e'
 *    **diciassette volte piu' piccolo** del vuoto fra il culmine e il primo
 *    punto che ha ceduto (+17 %): il margine resta tutto dal lato prudente. */
#define BUDGET_TOLLERANZA 0.01

/* ⛔ L'esito, e sono TRE.  ⚠ `BUDGET_NON_SO` non e' `BUDGET_NON_REGGE`: e' «non
 *    ho potuto misurare», e chi lo riceve **ammette** e scrive la riga.  Un
 *    budget che rifiutasse per non aver saputo misurare farebbe pagare
 *    all'utente un guasto nostro. */
enum budget_esito {
	BUDGET_REGGE,
	BUDGET_NON_REGGE,
	BUDGET_NON_SO,
};

/* ⭐ Si accende una volta sola, all'avvio, con i numeri della riga di comando.
 *
 *   `capacita_mpixel_s`  `--budget-mpixel-s`, **0 = SPENTO** (I6);
 *   `riserva`            `--riserva`, 0..1 (§6.9);
 *   `tela_l`, `tela_a`   la tela del palco, cioe' il **maggiorante** della tela
 *                        che una sessione qualunque potra' ottenere: serve come
 *                        ripiego dichiarato per chi non ha ancora consegnato
 *                        niente, e va nel verso scomodo. */
void budget_accendi(double capacita_mpixel_s, double riserva, uint32_t tela_l,
                    uint32_t tela_a);

/* ⛔ Quante caselle avra' la tabella degli inquilini — si chiama **prima** di
 *    `budget_accendi()`, col tetto delle sessioni in vigore.  ⚠ Dopo
 *    l'accensione non fa niente: la tabella e' gia' allocata, e cambiarne la
 *    misura a caldo vorrebbe dire perdere il consegnato di chi c'e'. */
void budget_caselle(int quante);

/* ⭐⭐ LA RIGA D'AVVIO, e si scrive **ACCESO E SPENTO**.
 *
 * ⛔ E porta i TRE valori in vigore col **nome dell'opzione accanto al
 *    numero** — `--budget-mpixel-s N`, `--tetto-sessioni N`, `--riserva F` —
 *    e non e' pignoleria di forma: chi legge il registro dopo un `0x06` deve
 *    poter sapere **su che numeri** quel no e' stato deciso, e un banco che
 *    tarasse il proprio oracolo su un numero diverso da quello in vigore
 *    produrrebbe falsi si' e falsi no **suoi**, non del prodotto.
 * ⚠ Il tetto arriva da fuori (`rcp_tetto()`) perche' non e' del budget: e' il
 *   limite amministrativo, e sta nella stessa riga solo perche' chi legge ha
 *   bisogno dei tre insieme. */
void budget_riga_avvio(int tetto_sessioni);

/* ⛔⭐ IL CONTO DEI NEGATI, e si scrive a OGNI verdetto — anche quando il
 *     budget e' SPENTO, ed e' proprio quello il caso che conta.
 *
 *     `[M]` §S.2: il difetto si legge in due parole — *«l'undicesimo entra con
 *     **`negati 0`**»*.  ⇒ Un banco deve poter leggere quel numero **a ogni
 *     gradino**, e leggerlo **zero** e' il fatto che prova **I6**: col budget
 *     spento il prodotto si comporta come ieri, e non nega nessuno.
 *
 * ⚠ I conti sono DUE e non uno: `negati` sono tutti i no detti a questa porta
 *   (tabella piena compresa), `negati_budget` sono i soli `0x06`.  Sommarli
 *   farebbe passare per capacita' un guasto di configurazione. */
void budget_riga_verdetto(const char *utente, bool ammesso, uint8_t motivo,
                          int tetto_sessioni, const char *perche);

bool budget_acceso(void);

/* ⭐⭐ L'ACCUMULATORE — si chiama per **ogni** fotogramma di **ogni** figlio, da
 *     `deposita_fotogramma()`.  ⛔ Senza guardie su «qualcuno guarda»: e'
 *     proprio cosi' che il conto vede i **fantasmi** di §3.2.
 *
 * `istante_us` e' il `CLOCK_MONOTONIC` timbrato **dal figlio all'istante della
 * cattura** — l'orologio e' di macchina, quindi confrontabile qui.  ⚠ Il
 * ritardo che ne esce e' *cattura → padre*, cioe' un **maggiorante** del tempo
 * di ritenuta: prudente nel verso giusto. */
void budget_deposita(const char *utente, uint32_t larghezza, uint32_t altezza,
                     uint64_t istante_us);

/* ⛔ Il conto si apre, si riempie con **chi e' dentro**, e si chiude con il
 *    verdetto sul nuovo.  ⚠ Tre chiamate e non una perche' «chi e' dentro» lo
 *    sa la tabella dei **palchi** (`figlio.c`), non questo modulo: legarli
 *    vorrebbe dire che il budget conosce i figli, e allora un giorno
 *    deciderebbe qualcosa su di loro. */
struct budget_conto {
	uint64_t ora_us;
	bool orologio;          /* ⛔ false = non ho letto l'ora: non giudico */
	double domanda;         /* Mpixel/s gia' impegnati */
	int quanti;
	/* ⛔ Il primo strozzato che si e' trovato: e' la porta del ritardo, e
	 *    chiude il conto **prima** della somma. */
	char strozzato[257];
	double strozzato_ms;
	/* ⚠ Quanti di quelli dentro sono stati contati al caso peggiore perche'
	 *   non avevano ancora consegnato: va nella riga, o il numero della domanda
	 *   sembra una misura quando e' un ripiego. */
	int al_peggiore;
};

void budget_conto_apri(struct budget_conto *c);
void budget_conto_dentro(struct budget_conto *c, const char *utente);

/* ⭐ Il verdetto sul nuovo.  `tela_l`/`tela_a` sono il **tetto** della tela che
 *    otterra' — `min(tela del palco, video.misura_massima del client)` — e la
 *    tela vera si decide solo a `SESSIONE`, cioe' dopo.  ⇒ Si conta il tetto:
 *    verso scomodo.
 *
 * `perche` riceve la frase che va nel **corpo del CONGEDO** e nel registro:
 * dev'essere leggibile da un utente, non da chi ha scritto il codice. */
enum budget_esito budget_conto_verdetto(struct budget_conto *c,
                                        const char *nuovo, uint32_t tela_l,
                                        uint32_t tela_a, char *perche,
                                        size_t perche_cap);

#endif /* BUDGET_H */
