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
/* ⛔⭐ `chiave` E' ARRIVATO CON LA FASE 3, E NON E' UN CAMPO IN PIU'.
 *
 *     Fino alla fase 2 chi riceveva marcava `chiave = true` **per
 *     costruzione**, perche' il fotogramma era uno solo e per forza una
 *     chiave.  ⛔ Con la predizione fra fotogrammi quella riga diventa **una
 *     bugia sul filo**: §6.2 scrive quel valore nel campo `tipo`, e un delta
 *     marcato `0x0301` fa riconfigurare al client un decodificatore su
 *     un'immagine che non si decodifica da sola.  ⇒ Qui viaggia quel che il
 *     codificatore ha LETTO dal flusso, non quel che si spera. */
/* ⭐⭐ E `input` E' ARRIVATO CON LA FASE 4, per la stessa ragione per cui
 *     `chiave` era arrivato con la 3: senza, il campo `input` di §6.2 sarebbe
 *     **0 per costruzione** — ed e' esattamente quel che era, `input = 0` in
 *     953 fotogrammi su 953 (`README.md`, 13 agosto 2026).
 *
 * ⛔ E lo riempie il FIGLIO, non il padre: solo lui sa che cosa il compositore
 *    ha davvero preso, e in che istante ha catturato.  Riempirlo qui direbbe
 *    «l'ultimo input spedito al palco», che e' un numero piu' alto e farebbe
 *    misurare all'anello del ritardo un ritardo piu' corto del vero — in nostro
 *    favore, che e' la direzione in cui non si sbaglia mai per caso. */
typedef void (*FiglioDeposito)(void *ctx, const char *utente, uid_t uid,
                               uint8_t codec, bool chiave, const uint8_t *dati,
                               size_t byte, uint32_t larghezza,
                               uint32_t altezza, uint64_t istante_us,
                               uint32_t input);

/* ⛔ Un figlio se n'e' andato.  Serve al padre per lasciare quel che era suo —
 * per esempio il deposito del video, che oggi e' di PROCESSO (vedi il riquadro
 * di `video_forse()` in `webtransport.c`): un deposito che sopravvive al figlio
 * che lo ha riempito e' l'immagine di un utente che resta in casa. */
typedef void (*FiglioCongedo)(void *ctx, const char *utente, uid_t uid);

/* ⭐⭐ FASE 4 — LA FORMA DEL CURSORE, e attraversa il confine nel verso opposto
 *     all'input: il metadato arriva da PipeWire (cioe' nel figlio) e il canale
 *     `CURSORE_FORMA` (`RCP.md` §7.2) vive nel padre.
 *
 * ⛔ `immagine` e' BGRA premoltiplicato, `larghezza x altezza x 4` byte, e vive
 *    SOLO dentro la chiamata: chi la vuole tenere la copia.
 * ⛔ `0x0` con `immagine` NULL = **cursore nascosto** (§5.5), e va consegnato
 *    come messaggio: e' l'unico modo che il client ha di sapere che il
 *    puntatore e' sparito, invece di disegnare l'ultima forma per sempre.
 * ⚠ La POSIZIONE non passa di qui e non passa da nessuna parte in questo verso:
 *   e' del client, che disegna il puntatore da se' (`SPECIFICHE.md` §7.1). */
typedef void (*FiglioCursore)(void *ctx, const char *utente, uid_t uid,
                              uint16_t larghezza, uint16_t altezza,
                              int16_t attivo_x, int16_t attivo_y,
                              const uint8_t *immagine, size_t byte);

/* ⭐⭐ §7.1 — LA RISPOSTA ALLA TELA, e attraversa il confine nel verso del
 *     cursore: la domanda esce con `figli_ritela()`, la risposta rientra di qui.
 *
 * ⛔ PERCHE' NON BASTAVA GUARDARE I FOTOGRAMMI, che e' quel che faceva la prima
 *    stesura di questa catena: dal fotogramma si vede che la misura e' cambiata,
 *    ⚠ ma non si vede **a quale richiesta risponde** — e i tre casi che non si
 *    distinguono guardando i pixel sono tutti frequenti:
 *
 *      · il palco ha GIA' quella misura ⇒ non arrivera' nessun fotogramma nuovo,
 *        e chi aspetta aspetterebbe il fondo dei tre secondi per niente;
 *      · il palco non c'e' o non ce l'ha fatta ⇒ il fatto e' noto SUBITO, di la';
 *      · due richieste incatenate — l'utente che trascina il bordo — ⇒ il
 *        fotogramma della PRIMA verrebbe preso per la risposta della SECONDA, e
 *        il desktop si assesterebbe sulla misura sbagliata **senza che nessun
 *        conto se ne accorgesse**.
 *
 * `voluta_*`  la misura che era stata chiesta al palco: serve a riconoscere la
 *             richiesta, non a dichiarare un esito.
 * `avuta_*`   quel che il palco ha davvero.  ⛔ `0x0` = **non ce l'ha fatta**, ed
 *             e' un fatto diverso da «ci sta provando» (`CODER.md` §3.10).
 *
 * ⚠ E arriva anche quando nessuno aveva chiesto niente: il palco puo' cambiare
 *   misura da se' (un rimontaggio dopo una caduta della sessione grafica).  Chi
 *   riceve decide che farne — qui si riferisce un fatto. */
typedef void (*FiglioTela)(void *ctx, const char *utente, uid_t uid,
                           uint32_t voluta_l, uint32_t voluta_a, uint32_t avuta_l,
                           uint32_t avuta_a);

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
/* ⭐⭐ §7.6 — «LA SESSIONE GRAFICA DI QUEST'UTENTE E' FINITA», e non gliel'ha
 *     chiesto nessun client: l'utente ha scelto «Esci…» dal menu del desktop.
 *
 * ⛔ E' il gemello di `TERMINA_SESSIONE` visto dall'altro verso: la' l'ordine
 *    arriva dal filo, qui il fatto arriva dal desktop.  ⚠ In tutt'e due i casi
 *    chi guarda deve ricevere `0x10 SESSIONE_TERMINATA` — e non i trenta
 *    secondi del silenzio seguiti da «errore di rete», che e' quel che
 *    succederebbe tacendo (rilievo B-7).
 *
 * ⚠ Si registra a parte invece di allungare `figli_accendi()`: quella firma ha
 *   gia' quattro richiami, e un quinto parametro in una riga di sei non lo
 *   legge piu' nessuno. */
typedef void (*FiglioSessioneFinita)(void *ctx, const char *utente, uid_t uid);
void figli_gancio_sessione_finita(figli *f, FiglioSessioneFinita fn, void *ctx);

figli *figli_accendi(uint32_t tela_l, uint32_t tela_a, const char *dir_rilievo,
                     FiglioDeposito deposita, FiglioCongedo congeda,
                     FiglioCursore cursore, FiglioTela tela, void *ctx);

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

/* ⛔⭐ FASE 3 — «CATTURA DI CONTINUO», E «QUESTA DEV'ESSERE UNA CHIAVE».
 *
 *     E' la meta' padre della cucitura che alla fase 2 non esisteva:
 *     `codificatore_chiedi_chiave()` non aveva **nessun chiamante nel
 *     prodotto**, quindi un `RICHIEDI_CHIAVE` del client accendeva un `bool` in
 *     `rcp.c` e non produceva nessuna chiave — e con `chiavi_ogni = 0` (GOP
 *     infinito) dopo la prima chiave non ne arrivava mai piu' una.
 *
 * `codec`  1 = HEVC, 2 = AV1, e ⛔ **0 = smetti di catturare**.  Non e' un
 *          sentinella implicito: e' il valore che §4.3/§6.2 danno a «nessun
 *          codec negoziato», e qui vuol dire la stessa cosa — nessuno guarda.
 * `chiave` §5.2: il prossimo fotogramma di quel codec DEVE essere una chiave.
 *
 * ⚠ Chi decide non e' questo file e non e' `main.c`: e' `webtransport.c`, che
 *   sa quando `SESSIONE` e' partita e quando §5.2 apre il debito.  `main.c` fa
 *   da ponte perche' e' l'unico che conosce tutt'e due i lati. */
bool figli_video(figli *f, const char *utente, uint8_t codec, bool chiave);

/* ⭐⭐ FASE 4 — L'INPUT ATTRAVERSA IL CONFINE DI PROCESSO.
 *
 * ⛔ La ragione e' un fatto dell'architettura, non una scelta: `libei` parla
 *    con la sessione grafica dell'utente, e quella sessione ce l'ha **il
 *    figlio**; QUIC, RCP e i byte del client stanno nel **padre**.  ⇒ Fra il
 *    tasto premuto nel browser e il tasto premuto sul desktop c'e' un confine
 *    di processo, e questa e' la funzione che lo attraversa.
 *
 * ⚠ Chi decide non e' questo file: e' `rcp.c`, che ha gia' convalidato il
 *   messaggio secondo `RCP.md` §7.3 — intervalli, surrogati, coordinate sulla
 *   tela, `id` crescente.  ⛔ Qui NON si riconvalida e NON si trasforma niente:
 *   due controlli sullo stesso valore in due posti diventano due regole diverse
 *   il giorno in cui una delle due cambia.
 *
 * ⛔ E IL SEGNO DELLA ROTELLA NON SI TOCCA NEMMENO QUI: si inverte una volta
 *    sola, dentro `input_rotella()` (`src/input.h`, `RCP.md` §7.3).
 *
 * `id`      §7.3, l'identificatore del messaggio.  ⭐ E' quel che torna nel
 *           campo `input` dei fotogrammi (§6.2) — ma **solo se il compositore
 *           lo prende**: il figlio avanza il suo contatore quando l'iniezione
 *           e' riuscita, non quando la richiesta e' partita.
 * `codice`  evdev (`BTN_LEFT` = 0x110, `KEY_A` = 30), per pulsante e posizione.
 * `a`/`b`   puntatore: `x`/`y` sulla tela · rotella: gli assi in unita' da 120
 *           · lettera: il valore scalare Unicode in `a` · ritela: la tela nuova.
 *
 * `false` = non c'e' nessun figlio per quell'utente, o la richiesta non e'
 * partita — ⛔ e allora quell'input non e' arrivato al desktop, il che si
 * DICHIARA nel registro invece di essere taciuto (`CODER.md` §4.2). */
enum {
	FIGLI_INPUT_PUNTATORE = 1,
	FIGLI_INPUT_PULSANTE = 2,
	FIGLI_INPUT_ROTELLA = 3,
	FIGLI_INPUT_LETTERA = 4,
	FIGLI_INPUT_POSIZIONE = 5,
	/* ⛔⭐ «La regola col rapporto danno/costo piu' alto del documento»
	 *     (`RCP.md` §11): al distacco si rilascia TUTTO.  Un Ctrl rimasto giu'
	 *     in una sessione che sopravvive al client rende il desktop
	 *     inservibile al riattacco, e nessuno collega le due cose. */
	FIGLI_INPUT_RILASCIA_TUTTO = 6,
	/* ⛔ §7.1: la tela in vigore e' cambiata, rimappa la regione del puntatore
	 *    assoluto.  Senza, `rcp.c` satura sulla tela nuova e il palco resta
	 *    sulla vecchia — due lati con due verita' e nessun errore. */
	FIGLI_INPUT_RITELA = 7,
	/* ⭐ §7.6 di `RCP.md` — «l'utente ha chiesto di USCIRE».  ⛔ Non e' un
	 *    gesto e non si inietta: viaggia in questa busta per la stessa ragione
	 *    di `RITELA` — una sola busta fra padre e figlio, un solo ramo da
	 *    leggere — e come quella passa PRIMA della guardia dei gesti. */
	FIGLI_INPUT_TERMINA = 8
};

bool figli_input(figli *f, const char *utente, uint32_t id, uint8_t azione,
                 uint16_t codice, int premuto, int32_t a, int32_t b);

/* ⭐⭐ «LA TELA DEL SERVER PRENDE LA MISURA DELLA TELA DEL CLIENT» — la catena
 *     che il 14 agosto 2026 mancava, e con lei quattro sintomi (`DECISIONI.md`
 *     §5.0-sexies, `fasi/rapporti/F4-IN-12`):
 *
 *   · le bande nere laterali      le due tele combaciano ⇒ niente da impaginare
 *   · il testo interpolato        scala 1 ⇒ nessuno ricampiona l'immagine
 *   · il ri-attacco a misura       `[M]` Mutter cambia a caldo in 41,6 ms,
 *     diversa                      labwc in 5,1 ms
 *   · ⭐⭐ i 4 secondi fra login    `pw_stream_update_params()` E' un riavvio del
 *     e desktop                    flusso, e un riavvio CONSEGNA un buffer: su
 *                                  Wayland il compositore manda solo quando la
 *                                  scena cambia, e un desktop appena acceso e'
 *                                  fermo (`[M]` 4,4 s, 659 «attese a vuoto»)
 *
 * ⛔ Torna `true` quando la DOMANDA e' partita, ⚠ non quando la tela e'
 *    cambiata: fra le due c'e' un compositore che puo' concedere altro (§4.5),
 *    dire «riuscito» senza fare niente (`[M]` labwc) o non farcela.  ⇒ Chi
 *    aspetta l'esito lo legge nel FOTOGRAMMA: e' il primo che arriva alla misura
 *    nuova, e il campo `larghezza`/`altezza` di `FiglioDeposito` lo porta. */
/* ⭐ «TERMINA LA SESSIONE GRAFICA DI QUEST'UTENTE» — `RCP.md` §7.6, la seconda
 * delle due uscite di `DECISIONI.md` §4.1-ter.  ⛔ Non e' il distacco: qui i
 * programmi dell'utente si chiudono, e al prossimo attacco nasce una sessione
 * NUOVA.  `false` = non c'e' nessun figlio per quell'utente, o la domanda non e'
 * partita — e allora la sessione NON finira'. */
bool figli_termina_sessione(figli *f, const char *utente);

bool figli_ritela(figli *f, const char *utente, uint32_t larghezza,
                  uint32_t altezza);

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
