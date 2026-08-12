/*
 * aiutante.h — ⭐ IL PROCESSO CHE INTERROGA PAM AL POSTO DEL FILO UNICO.
 *
 * ---------------------------------------------------------------------------
 * ⛔ PERCHE' ESISTE, CON IL NUMERO ACCANTO
 *
 * `DECISIONI.md` §1.10, 11 agosto 2026, dall'utente.  Il server gira in un
 * ciclo `poll` solo (`main.c`) e la verifica PAM **blocca quel filo**: `[M]`
 * B8, sera dell'11 agosto, **da 1,0 a 2,2 secondi per tentativo** (mediane
 * 2123 · 2198 · 1086 ms) — e ⭐ **il ritardo lo mette PAM, non noi**: +1034 ms
 * oltre il secondo fisso sui respinti contro +84 ms sugli ammessi, che e' la
 * firma di `pam_faildelay`.
 *
 * ⛔ Fino alla fase 1 il sintomo era «l'ultimo dei dieci aspetta dieci
 *    secondi»: sgradevole e circoscritto.  ⛔ Dalla fase 2 in poi diventa
 *    **lo schermo di tutti quelli collegati che si pianta per uno o due
 *    secondi ogni volta che qualcun altro entra** — e chi lo vedra' dara' la
 *    colpa al video, perche' e' li' che si vede.  E' la forma «il sintomo non
 *    nomina la causa» di `LEZIONI.md` §1.6, e curarla adesso significa non
 *    farla nascere.
 *
 * ---------------------------------------------------------------------------
 * ⛔⭐ UN PROCESSO, NON UN FILO — ed e' la decisione dell'utente, non una
 *     preferenza di stile
 *
 * §1.10: *«con un processo aiutante, non con un filo: PAM non e' affidabilmente
 * rientrante, e un thread porterebbe guai suoi dentro la cura di un problema di
 * concorrenza»*.
 *
 * ⭐ E qui si va un passo oltre, perche' costa dieci righe: **ogni transazione
 *    PAM vive in un processo che ne fa UNA SOLA e poi muore**.  Da cui la
 *    forma a tre piani:
 *
 *      il server        non chiama mai PAM.  Scrive una richiesta su un socket
 *                       e torna al `poll` — che e' tutto il punto;
 *      lo smistatore    un figlio, acceso una volta all'avvio.  Non chiama mai
 *                       PAM nemmeno lui: legge una richiesta e forca;
 *      il nipote        chiama PAM UNA volta, scrive l'esito, esce.
 *
 * ⛔ La rientranza di PAM cosi' non e' «gestita»: **non e' in gioco**.  Nessun
 *    processo che tocca `libpam` la tocca due volte, e i moduli di PAM — che
 *    sono codice altrui, caricato a runtime, con dentro `getpwnam`, socket
 *    verso `nscd`, `dlopen` — non condividono niente con nessuno.
 *
 * ⭐ E il secondo guadagno, che il filo unico non aveva: **dieci che entrano
 *    insieme non fanno la fila**, perche' i nipoti sono dieci processi.
 *
 * ---------------------------------------------------------------------------
 * ⛔⭐ L'INVARIANTE I3, E COME SI FA IN MODO CHE IL FALLIMENTO SIA UN «NO»
 *
 * I3 (`CODER.md` §2): *la guardia parte da negato.  Chi non passa dal
 * validatore non riceve un pixel e non comanda nulla.*  ⛔ Un aiutante che
 * rispondesse «si'» per un messaggio smarrito, un tempo scaduto o un processo
 * morto sarebbe I3 violata, ed e' il difetto peggiore che questo lavoro possa
 * produrre.  Le sette strade per cui qualcosa puo' andare storto, e dove
 * ciascuna sbuca:
 *
 *   1. l'aiutante non si e' acceso        `aiutante_chiedi` -> false -> NO
 *   2. il socket e' pieno / EAGAIN         `aiutante_chiedi` -> false -> NO
 *   3. troppe pratiche in volo (> 16)      `aiutante_chiedi` -> false -> NO
 *   4. lo smistatore e' morto (EOF)        tutte le pratiche in volo -> NO
 *   5. il nipote e' morto senza rispondere la pratica scade         -> NO
 *   6. la risposta e' corta o storpiata    si scarta                -> poi (5)
 *   7. la risposta porta un byte che non e' esattamente 1 -> NO
 *
 * ⛔ **Non c'e' nessuna strada che porti a `true` senza un `PAM_SUCCESS` su
 *    tutt'e due i passi di `rcp_autentica()`**: il `true` nasce in un solo
 *    punto del programma, ed e' il byte `1` scritto dal nipote dopo aver
 *    ricevuto quel `PAM_SUCCESS`.  Ogni altra combinazione di byte, ogni
 *    lunghezza diversa e ogni silenzio sono un «no».
 *
 * ⚠ E il SOCKET E' `SOCK_SEQPACKET`, non `SOCK_STREAM`: con i messaggi
 *   delimitati dal nucleo una richiesta non puo' arrivare a meta', e una
 *   risposta non puo' fondersi con quella di un altro nipote.  ⛔ Con uno
 *   stream sarebbe stato necessario un inquadramento nostro — cioe' un pezzo
 *   di codice in cui un difetto produce «la risposta di un altro», che e' I3
 *   violata da un errore di parsing.
 *
 * ---------------------------------------------------------------------------
 * ⚠ E LA PAROLA D'ORDINE PASSA DI QUI
 *
 * `RCP.md` §4.4: «la parola d'ordine sta in chiaro nella memoria di chi la
 * riceve, va azzerata appena PAM ha risposto, e non deve comparire in nessun
 * registro».  ⛔ Questo modulo aggiunge **due copie** a quelle che R9.8 ha gia'
 * censito — il messaggio nel buffer del mittente e quello nel buffer del
 * destinatario — e le azzera tutt'e due appena servite.  Il socket e' una
 * coppia anonima creata da `socketpair()`: non ha un nome nel filesystem, non
 * ci si puo' collegare da fuori, e muore con i due processi.
 */
#ifndef REMOTIX_AIUTANTE_H
#define REMOTIX_AIUTANTE_H

#include <stdbool.h>
#include <stdint.h>

typedef struct aiutante aiutante;

/* ⛔ Si accende PRESTO, e la ragione e' che il figlio eredita i descrittori:
 *    acceso dopo `trasporto_apri()` si porterebbe dietro il socket UDP e
 *    l'ascoltatore TCP, e la porta resterebbe occupata da lui anche dopo la
 *    morte del server.  ⚠ Restituisce NULL se non si e' potuto accendere, e
 *    chi chiama DEVE poter distinguere «acceso» da «non acceso»: senza
 *    aiutante ogni autenticazione e' un NO. */
aiutante *aiutante_accendi(void);

/* Chiude il socket e manda `SIGTERM` allo smistatore. */
void aiutante_spegni(aiutante *a);

/* Il descrittore da mettere nel `poll`, o -1 se l'aiutante e' spento/morto. */
int aiutante_descrittore(const aiutante *a);

/* ⛔ Chiede la verifica e TORNA SUBITO.  `true` = la domanda e' partita e una
 * risposta arrivera' (o scadra'); `false` = **non e' partita**, e chi chiama
 * deve trattarlo come un «no» immediato.
 * `pratica` esce con il numero con cui la risposta si riconoscera'. */
bool aiutante_chiedi(aiutante *a, const char *utente, const char *parola,
                     uint64_t ora_ms, uint64_t *pratica);

/* Legge le risposte pronte e le consegna una per una.  Da chiamare quando il
 * descrittore e' leggibile.
 * ⛔ Se lo smistatore e' morto, consegna un «no» per ogni pratica in volo:
 *    una pratica senza risposta e' un'attesa che nessuno chiude. */
void aiutante_muovi(aiutante *a,
                    void (*consegna)(void *ctx, uint64_t pratica, bool ammesso),
                    void *ctx);

/* ⛔ Fa scadere le pratiche troppo vecchie, consegnando un «no».  E' la rete di
 * sicurezza del caso 5: un nipote ucciso a meta' non scrive niente, e senza
 * questa chiamata la sessione resterebbe in `attesa-verdetto` per sempre. */
void aiutante_scaduti(aiutante *a, uint64_t ora_ms,
                      void (*consegna)(void *ctx, uint64_t pratica, bool ammesso),
                      void *ctx);

/* Quante pratiche sono in volo.  Per il registro. */
int aiutante_in_volo(const aiutante *a);

#endif
