/*
 * appunti.h — LA CUCITURA degli appunti: dal desktop al filo, e ritorno.
 *
 * ⛔ QUESTO FILE E' DEL COORDINATORE, come `input.h`, e per la stessa ragione
 *    scritta la': il difetto sta FRA due pezzi «ciascuno corretto per conto
 *    suo», e le cuciture senza proprietario non le guarda nessun banco.
 *
 * Chi legge questo file:
 *   · `appunti.c` — attua queste funzioni su **Mutter**, sulla sessione
 *                   `RemoteDesktop` che `mutter.c` ha gia' aperto.  ⛔ NON
 *                   conosce ne' QUIC ne' il formato dei messaggi;
 *   · `figlio.c`  — ⭐ **cuce i due**: include questo file, scrive gli
 *                   adattatori e li fa viaggiare sul socket verso il padre,
 *                   dove `rcp.c` li traduce in §7.4.
 *
 * ---------------------------------------------------------------------------
 * ⛔ SOLO TESTO, E NON E' UNA RINUNCIA — `DECISIONI.md` §5-ter.1
 *
 * *«Per la clipboard ho idea precisa: solo testo»* (utente, 9 agosto 2026), e
 * confermato il 17.  Niente immagini, niente file, niente formati ricchi.  ⚠ v1
 * portava anche `text/html` e le immagini (`fondamenta/remotix-c/src/scambio.c`): qui
 * non ci sono **di proposito**, e chi le rimettesse dovrebbe prima riaprire
 * §5-ter.1 e `RCP.md` §7.4 — che non ha nemmeno un campo per dire il tipo.
 *
 * ⇒ Da cui la forma di questo file: non si scambiano elenchi di tipi MIME con
 *   chi cuce, si scambia **testo**.  I tipi vivono qui dentro e in nessun altro
 *   posto (`TIPI_TESTO`).
 *
 * ---------------------------------------------------------------------------
 * ⛔⛔ LA CLIPBOARD E' DEL COMPOSITORE, NON DELLA SESSIONE REMOTA
 *
 * `STUDI.md` §gnome §10 `[R]`, 9 agosto 2026, che ha **corretto** quel che
 * `LEZIONI.md` diceva prima: e' `MetaSelection`, cioe' di Mutter.  Della
 * sessione `RemoteDesktop` e' soltanto **la porta** (`EnableClipboard`).
 *
 * ⭐ E la conseguenza e' un regalo per il banco: la sponda X11 di Mutter e'
 *    **incondizionata nei due versi**, zero controlli sul fuoco ⇒ `xclip`
 *    funziona **senza una nostra sessione**, e il banco degli appunti ha un
 *    arbitro esterno invece di far parlare fra loro due pezzi nostri
 *    (`PIANO.md` §0.4, `fasi/07-audio-e-appunti.md` §2.4).
 *
 * ---------------------------------------------------------------------------
 * ⛔ LE TRE TRAPPOLE DI MUTTER, e sono tutte e tre disinnescate in `appunti.c`
 *
 *   1. `DisableClipboard` e' **a senso unico** (Mutter 48.7): stacca il gestore
 *      e azzera la sorgente ma NON rimette a falso `is_clipboard_enabled`, e da
 *      li' in poi `EnableClipboard` risponde «Already enabled» e gli annunci
 *      non tornano piu'.  ⇒ **non si chiama mai**: per lasciare la clipboard si
 *      usa `SetSelection` **senza** `mime-types`;
 *   2. la firma di `mime-types` e' **asimmetrica**: `as` in ingresso ai metodi,
 *      `(as)` in uscita dal segnale.  Chi legge col tipo sbagliato ottiene
 *      `NULL` **senza errore** — cioe' gli appunti funzionano in un verso solo
 *      e nel registro non compare niente che lo spieghi;
 *   3. il gestore interno degli appunti tiene **un solo tipo MIME**, quindi
 *      quando l'applicazione che ha copiato muore ne resta uno: si prova
 *      **tutta la fila**, non solo il primo.
 *
 * ⛔ E la quarta, che non e' di Mutter ma del ritorno: `SelectionOwnerChanged`
 *    arriva **anche dopo una NOSTRA `SetSelection`**, con `session-is-owner` a
 *    vero.  Trattarlo come una copia nuova vuol dire annunciare al client quel
 *    che il client ci ha appena annunciato, e da li' i due lati si rincorrono.
 *
 * ---------------------------------------------------------------------------
 * ⛔⛔ IL CONTRATTO DEL THREAD, e questo file ne ha uno SUO
 *
 * GDBus consegna i segnali al contesto predefinito del thread che ha
 * **sottoscritto**, e nessun thread di REMOTIX fa girare un ciclo GLib: quello
 * del figlio aspetta descrittori, quello di PipeWire e' suo.  ⇒ `appunti.c`
 * apre un contesto privato e lo fa girare su un thread dedicato.
 *
 * ⇒ **Le due richiamate qui sotto girano su QUEL thread**, non sul ciclo del
 *   figlio.  Chi le riceve **si accodi e torni**: sono libere di scrivere sul
 *   socket verso il padre (`send` su un SEQPACKET e' atomico per messaggio),
 *   ⛔ ma NON di toccare `libei`, che `input.h` dichiara non rientrante.
 */
#ifndef REMOTIX_APPUNTI_H
#define REMOTIX_APPUNTI_H

#include <gio/gio.h>
#include <glib.h>
#include <stddef.h>
#include <stdint.h>

/* ⭐ L'area del registro di questo modulo.  Sta qui e non in `registro.h` per
 *    la stessa ragione di `REG_FIGLIO`: e' del figlio, e `registro.h` e'
 *    condiviso col padre. */
#define REG_APPUNTI "appunti"

/* ⛔ Il tetto di `RCP.md` §5.4, e vive QUI perche' il testo piu' grande non
 *    dev'essere ne' spedito ne' annunciato — cioe' la decisione si prende
 *    **prima** di attraversare il socket, dove il testo ancora esiste intero.
 *
 * ⚠ Un milione tondo, NON 1 MiB: `RCP.md` §5.4 sceglie 1 000 000 proprio
 *   perche' il messaggio che lo porta ha dieci byte di inquadratura, e un tetto
 *   uguale a quello del messaggio (§6.1, 1 MiB) renderebbe **illegale il testo
 *   grande esattamente quanto il tetto**.
 *
 * ⛔ E oltre il tetto NON SI TRONCA: §5.4 lo vieta con la ragione scritta —
 *    «un testo troncato incollato in un terminale e' peggio di un testo
 *    mancante».  Non si annuncia affatto, e si scrive nel registro. */
#define APPUNTI_TETTO 1000000u

typedef struct Appunti Appunti;

/*
 * ⭐ «LA SESSIONE HA COPIATO DEL TESTO», ed e' gia' letto e gia' convalidato.
 *
 * ⛔ Il testo arriva GIA' LETTO, e non e' una comodita': l'annuncio di §7.4
 *    porta `u32 lunghezza`, e nessuno puo' dire quanto e' lungo un testo senza
 *    averlo letto.  ⇒ Il «si annuncia e poi si tira» del protocollo vive sul
 *    FILO, dove serve; da questa parte il testo c'e' gia'.
 *
 * ⛔ E se il testo supera `APPUNTI_TETTO` questa richiamata NON viene chiamata
 *    affatto (§5.4: «non si annuncia»), e la riga sta nel registro.  ⚠ Cosi'
 *    «non e' stato copiato niente» e «era troppo grande» non hanno la stessa
 *    faccia — `CODER.md` §3.10.
 *
 * `testo` e' UTF-8 valido, terminato da zero, e vale SOLO dentro la chiamata.
 * Gira sul thread degli appunti.
 */
typedef void (*AppuntiSuTesto)(const char *testo, size_t byte, void *dati);

/*
 * ⭐ «LA SESSIONE VUOLE INCOLLARE quel che ha il client»: si chieda al client,
 *    e quando la risposta arriva si chiami `appunti_rispondi` con questo
 *    `serial`.
 *
 * ⛔⛔ VA RISPOSTO SEMPRE, anche fallendo, e anche se il client non risponde
 *      mai.  Un `SelectionTransfer` lasciato senza risposta lascia
 *      l'applicazione che sta incollando in attesa **a tempo indeterminato**, e
 *      quel che l'utente vede e' **un desktop che si e' piantato** — un difetto
 *      che nessuno collega agli appunti.
 * ⇒ Chi cuce tiene un fondo di tempo e risponde `NULL` allo scadere.
 *
 * Gira sul thread degli appunti.
 */
typedef void (*AppuntiSuRichiesta)(uint32_t serial, void *dati);

/*
 * Accende gli appunti sulla sessione di controllo indicata, e li accende **una
 * volta per sessione grafica**.
 *
 * ⛔ NON SI SPENGONO MAI — vedi la trappola 1 in testa.  `appunti_chiudi`
 *    smonta quel che e' nostro (thread, contesto, sottoscrizioni) e **non
 *    chiama `DisableClipboard`**: chiudendo la sessione di controllo se ne va
 *    tutto insieme, che e' il modo pulito.
 *
 * ⭐ E si accende con opzioni VUOTE, di proposito: cosi' Mutter non ci fa
 *    proprietari di niente e ci racconta subito chi lo e' adesso, con un
 *    `SelectionOwnerChanged` che arriva **immediatamente**.  ⛔ E' la riga che
 *    fa ritrovare gli appunti a chi si RICOLLEGA: quel segnale arriva solo
 *    quando il proprietario **cambia**, e a una riconnessione non cambia
 *    niente (`STUDI.md` §gnome §10 — «era la nostra ricetta a perderlo»).
 */
Appunti *appunti_apri(GDBusConnection *bus, const char *percorso_controllo,
                      GError **sbaglio);
void appunti_chiudi(Appunti *appunti);

/* Chi ascolta le due richiamate.  Con richiamate a NULL si smette di
 * ascoltare, e la chiamata **aspetta** che nessuna richiamata sia in corso. */
void appunti_ascolta(Appunti *appunti, AppuntiSuTesto su_testo,
                     AppuntiSuRichiesta su_richiesta, void *dati);

/*
 * ⭐ L'ultimo testo che la SESSIONE ha copiato, o NULL.
 *
 * ⛔ E' QUI CHE CHI SI RICOLLEGA RITROVA GLI APPUNTI, ed e' qui e non nel
 *    canale **proprio perche' deve sopravvivere alla connessione** — come tutto
 *    il resto del palco (invariante I4).
 *
 * Restituisce una copia da liberare con `g_free`; `byte` — se non NULL —
 * riceve quanti byte ha.
 */
char *appunti_ultimo_testo(Appunti *appunti, size_t *byte);

/*
 * «IL CLIENT HA COPIATO DEL TESTO»: da adesso la sessione puo' chiederlo, e lo
 * chiedera' con la richiamata `AppuntiSuRichiesta`.
 *
 * ⛔ NON porta il testo, e non e' una dimenticanza: e' il «si annuncia e poi si
 *    tira» di §7.4 applicato di qua.  Chi copia un documento intero sul
 *    telefono non lo spedisce a nessuno finche' qualcuno non incolla.
 */
/* ⭐ Legge ADESSO la selezione della sessione e la consegna alla richiamata:
 *    Mutter non racconta a una sessione nuova chi possiede la selezione, e
 *    senza questa chiamata la clipboard del desktop si perde al collegamento.
 *    Vedi il riquadro in `appunti.c`. */
void appunti_leggi_adesso(Appunti *appunti);

gboolean appunti_offri(Appunti *appunti, GError **sbaglio);

/*
 * Risponde a una richiesta della sessione.  Con `testo` NULL dichiara di non
 * avere quel che era stato chiesto — ⛔ **che e' comunque una risposta**, ed e'
 * quella che sblocca chi sta incollando.
 *
 * ⛔ ASPETTA: apre un descrittore e ci scrive dentro.  Va chiamata da un thread
 *    che puo' permetterselo.
 */
void appunti_rispondi(Appunti *appunti, uint32_t serial, const char *testo,
                      size_t byte);

#endif
