/*
 * figlio.h — ⭐ UN PROCESSO PER UTENTE, CHE GIRA COME LUI E TIENE IL PALCO.
 *
 * ---------------------------------------------------------------------------
 * ⛔ PERCHE' ESISTE, CON LA MISURA ACCANTO
 *
 * `DECISIONI.md` §1.10-bis, 12 agosto 2026, dall'utente, davanti alla misura
 * del montaggio della fase 2 (`fasi/rapporti/P2-6-montaggio.md` §5.4):
 *
 *   `[M]` ⛔ **root non si collega al bus di sessione dell'utente**
 *         sudo env XDG_RUNTIME_DIR=/run/user/1000 \
 *              DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus \
 *              gdbus call --session --dest org.gnome.Mutter.ScreenCast …
 *         → «Error connecting: The connection is closed», uscita 1
 *
 *   `[M]` ⛔ **solo root puo' verificare con PAM la parola d'ordine di un
 *         altro**: `pam_unix` fuori da root passa da `unix_chkpwd`, che
 *         verifica solo la parola di CHI LO INVOCA.
 *
 * ⇒ Le due cose **non stanno nello stesso processo**, e non e' un dettaglio di
 *   implementazione: senza bus non c'e' cattura, senza root non c'e'
 *   autenticazione.  Il server resta **privilegiato**, e per ogni utente
 *   ammesso genera un **figlio che gira come lui**, che tiene il suo bus di
 *   sessione, la sua cattura e i suoi dispositivi.
 *
 * ---------------------------------------------------------------------------
 * ⭐ E' L'AIUTANTE DI §1.10 AL CONTRARIO — la stessa regola, un mestiere per
 *    processo.  ⛔ MA TRE COSE SONO DIVERSE, E VANNO DETTE PRIMA
 *
 * L'aiutante (`aiutante.h`) e' un figlio **meno** privilegiato del padre che fa
 * la cosa che blocca; questo e' un figlio **diversamente** privilegiato che fa
 * la cosa che il padre non puo' fare.  Da cui:
 *
 *   1. ⛔ **NON si puo' accendere presto.**  L'aiutante nasce prima di
 *      `trasporto_apri()` apposta, perche' un `fork()` regala al figlio tutti i
 *      descrittori e un aiutante acceso dopo si porterebbe dietro la porta.  Il
 *      figlio nasce **quando un utente e' stato ammesso**, cioe' per forza dopo
 *      gli ascoltatori.  ⇒ Quel che l'aiutante compra con il MOMENTO, questo lo
 *      compra con `close_range()`: appena nato chiude **tutto** tranne i tre
 *      standard e il proprio socket, e il banco lo legge da `/proc/<pid>/fd` —
 *      non lo deduce.
 *
 *   2. ⛔ **L'identita' non e' una promessa del codice: e' un fatto del
 *      nucleo.**  Un aiutante che risponde «si'» per un messaggio smarrito e'
 *      I3 violata e si vede; un figlio che gira **come l'utente sbagliato** e'
 *      I3 violata **in modo invisibile** — i pixel arrivano, sono bellissimi, e
 *      sono di un altro.  ⇒ Il socket del padre ha `SO_PASSCRED`, e il nucleo
 *      timbra **ogni messaggio** con pid/uid/gid **veri** del mittente
 *      (`SCM_CREDENTIALS`).  Il padre li confronta con l'uid che ha risolto dal
 *      nome dell'utente della sessione RCP **a ogni messaggio**, non
 *      all'apertura.  ⭐ E' il numero di pratica dell'aiutante, con un notaio:
 *      la pratica la scriviamo noi, le credenziali le scrive il nucleo, e un
 *      processo non privilegiato **non puo' dichiararne di false**.
 *
 *   3. ⛔ **Sopravvive al distacco** (invariante I4).  L'aiutante e' senza
 *      memoria — una transazione e muore.  Questo e' il PALCO: cattura,
 *      monitor virtuale, dispositivi.  ⚠ Chi muore quando cade la rete non e'
 *      lui: il figlio muore quando muore il server (`PR_SET_PDEATHSIG` **e**
 *      l'EOF sul socket, due strade indipendenti perche' la prima si perde
 *      quando cambiano le credenziali).
 *
 * ---------------------------------------------------------------------------
 * ⛔ GLI INVARIANTI, E DOVE SI LEGGE CHE SONO RISPETTATI
 *
 * | I3 | la guardia parte da negato | ogni strada che non porti a un messaggio
 * |    |                            | firmato dal nucleo con l'uid ATTESO e'
 * |    |                            | un no: `credenziali_combaciano()`, e non
 * |    |                            | c'e' un secondo posto che dica di si'   |
 * | I4 | il palco e' della sessione | nessuna riga di questo file lega la vita
 * |    |                            | di un figlio a una connessione: si
 * |    |                            | muore per `figli_spegni()` e basta      |
 * | I2 | una sessione per utente    | `figli_assicura()` cerca PRIMA di
 * |    |                            | generare: due connessioni dello stesso
 * |    |                            | utente trovano lo stesso figlio         |
 * | I7 | la protezione sta nel      | il calo di privilegio si VERIFICA con
 * |    | programma                  | `getresuid()` — chiesto al nucleo — e un
 * |    |                            | figlio che non e' sceso davvero esce    |
 *
 * ---------------------------------------------------------------------------
 * ⛔ E QUEL CHE QUESTO FILE NON FA, DICHIARATO INVECE CHE SCOPERTO
 *
 *   · **non fa nascere una sessione grafica**.  Se l'utente ammesso non ha un
 *     `/run/user/<uid>` — cioe' non e' mai entrato su quella macchina — il
 *     figlio lo DICE e resta senza palco.  Farla nascere vuole
 *     `pam_open_session` (cioe' `pam_systemd`, che crea la sessione logind e
 *     la cartella di runtime), ed e' la decisione del login vero: non di qui;
 *   · **non spedisce niente sul filo**.  Consegna i byte al padre, che e'
 *     l'unico che ha le connessioni;
 *   · **non guarda dentro i byte del codec**: quello e' del codificatore.
 */
#ifndef REMOTIX_FIGLIO_H
#define REMOTIX_FIGLIO_H

#include <poll.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <sys/types.h>

/* ⛔ L'area del registro sta QUI e non in `registro.h`: quel file non e' di
 *    questo mandato, e `registro_dice()` prende una stringa qualunque.  ⚠ Il
 *    giorno in cui `registro.h` si potra' toccare, questa riga va li' accanto
 *    alle altre — com'e' successo a `REG_SESSIONE`, che ha vissuto in
 *    `sessione.h` fino al 12 agosto 2026. */
#define REG_FIGLIO "figlio"

typedef struct figli figli;

/* ⛔ Come il padre riceve un fotogramma dal figlio.  ⚠ `utente` e `uid` ci
 * sono TUTT'E DUE apposta: il nome e' quello con cui la sessione RCP ha chiesto
 * di entrare, l'uid e' quello che il **nucleo** ha timbrato sul messaggio, e
 * chi consegna deve poter rifiutare se i due si sono scollati. */
typedef void (*FiglioDeposito)(void *ctx, const char *utente, uid_t uid,
                               uint8_t codec, const uint8_t *dati, size_t byte,
                               uint32_t larghezza, uint32_t altezza,
                               uint64_t istante_us);

/* ⛔ Un figlio se n'e' andato.  Serve al padre per lasciare quel che era suo —
 * per esempio il deposito del video, che oggi e' di PROCESSO (vedi il riquadro
 * di `video_forse()` in `webtransport.c`): un deposito che sopravvive al figlio
 * che lo ha riempito e' l'immagine di un utente che resta in casa. */
typedef void (*FiglioCongedo)(void *ctx, const char *utente, uid_t uid);

/* Accende la tabella dei figli.  ⛔ Non genera niente: qui non si sa ancora
 * chi entrera'.
 *
 * `tela_l`/`tela_a`  la misura con cui il figlio aprira' cattura e codifica —
 *                    la stessa costante di `main.c`, passata invece che
 *                    ricopiata (`P2-1-sessione.md` §6.3: «o fra due settimane
 *                    saranno tre posti»).
 * `dir_rilievo`      dove il figlio scrive il crudo e i flussi, o NULL.
 *                    ⚠ Ci scrive **il figlio**, cioe' l'utente: se la cartella
 *                    non e' sua, il rilievo non esce e la riga lo dice. */
figli *figli_accendi(uint32_t tela_l, uint32_t tela_a, const char *dir_rilievo,
                     FiglioDeposito deposita, FiglioCongedo congeda, void *ctx);

/* ⛔ Spegne tutti i figli e aspetta che siano morti.  ⚠ ASPETTA, e va detto:
 * sta **dopo** l'ultimo giro del ciclo `poll`, come `aiutante_spegni()` —
 * `CODER.md` §4.4 vieta l'attesa DENTRO il ciclo, non dopo. */
void figli_spegni(figli *f);

/* ⛔⭐ SI CHIAMA QUANDO PAM HA DETTO SI', E NON UN ISTANTE PRIMA (invariante
 *     I3).  Un figlio che nascesse su `CREDENZIALI` girerebbe come un utente
 *     che non ha ancora dimostrato di essere lui.
 *
 * ⛔ I2 — «una sola sessione grafica per utente»: se il figlio di
 *    quell'utente c'e' gia' e risponde ancora, questa funzione **non ne genera
 *    un secondo** e restituisce `true` lo stesso.  Due connessioni dello stesso
 *    utente vedono lo stesso palco, che e' precisamente quel che I4 dice.
 *
 * ⛔ `false` vuol dire «non c'e' nessun figlio per quell'utente», e chi chiama
 *    non deve trattarlo come «forse»: nessun palco, nessun pixel.  Le strade
 *    che portano qui sono elencate in `figlio.c`, funzione `figli_assicura`. */
bool figli_assicura(figli *f, const char *utente);

/* I descrittori da mettere nel `poll`.  Restituisce quanti ne ha scritti. */
size_t figli_descrittori(figli *f, struct pollfd *fds, size_t max);

/* ⛔ Legge quel che i figli hanno da dire, verificando le credenziali del
 * nucleo **su ogni messaggio**.  ⚠ Si chiama anche quando nessun descrittore e'
 * leggibile: qui dentro scadono le attese e si raccolgono i morti, e una
 * scadenza che aspetta un byte e' una scadenza che non scatta mai — la lezione
 * di `regola_battito`, pagata l'11 agosto con B6 e ripagata dall'aiutante. */
void figli_muovi(figli *f, struct pollfd *fds, size_t n, uint64_t ora_ms);

/* Quanti figli sono vivi adesso.  Per il registro e per il banco. */
int figli_quanti(const figli *f);

/* ⛔ Per il banco: il pid del figlio di quell'utente, o -1.  ⚠ Serve a
 * `banchi/02-figlio-*` per chiedere al NUCLEO chi e' quel processo
 * (`/proc/<pid>/status`) invece di dedurlo da `pgrep`, che troverebbe anche i
 * figli dei server degli altri banchi. */
pid_t figli_pid_di(const figli *f, const char *utente);

/* ⛔⭐ CHIEDE AL FIGLIO DI QUELL'UTENTE DI RIMANDARE IL SUO FOTOGRAMMA.
 *
 *     ⚠ Serve perche' il deposito del video, in `webtransport.c`, e' **uno per
 *     PROCESSO**: quando entra un altro utente il padre lo svuota (o
 *     consegnerebbe a lui i pixel del primo), e il primo — che il suo figlio ce
 *     l'ha ancora vivo — deve poterselo far rimandare.
 *
 * ⛔ Il figlio rimanda **lo stesso** fotogramma, non uno nuovo: la fase 2 e'
 *    un'immagine ferma, e ricatturare qui consegnerebbe due immagini diverse
 *    sotto la stessa etichetta.
 *
 * `false` = non c'e' nessun figlio per quell'utente, o la domanda non e'
 * partita — e allora quella sessione non vedra' niente, dichiarato. */
bool figli_chiedi_palco(figli *f, const char *utente);

/* ⛔⭐ RICHIEDE A OGNI FIGLIO «CHI SEI», al massimo una volta ogni minuto.
 *
 *     ⚠ Serve perche' «verificato a ogni messaggio» sia una protezione anche
 *     quando i messaggi non ci sono: un figlio che ha consegnato il suo
 *     fotogramma e poi tace resterebbe verificato **una volta sola, all'inizio**
 *     — cioe' esattamente quel che §1.10-bis vieta.  ⭐ La risposta ripassa da
 *     `credenziali_combaciano()` come tutte le altre, e un figlio che nel
 *     frattempo non fosse piu' quell'uid verrebbe abbattuto li'.
 *
 * ⚠ La riga dell'esito OK sta nella parlantina (`registro_dettaglio`): una al
 *   minuto per figlio riempirebbe il registro di verde.  Il disaccordo, no:
 *   quello si scrive sempre. */
void figli_ricontrolla(figli *f, uint64_t ora_ms);

/* ⛔⭐ L'INGRESSO DEL FIGLIO — `main.c` ci arriva come PRIMA cosa, quando
 *     `argv[1]` e' `--figlio-interno`, e non torna mai.
 *
 *     ⚠ E' una riga di comando INTERNA: la scrive `figli_assicura()` e la legge
 *     `figlio_vive()`.  Chi la battesse a mano otterrebbe un processo che parla
 *     su un descrittore 3 che non esiste, e morirebbe li' — non c'e' niente da
 *     guadagnarci, perche' il figlio non ha nessun privilegio da regalare: e'
 *     l'utente stesso. */
void figlio_vive(int argc, char **argv);

#endif
