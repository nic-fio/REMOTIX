/*
 * sessione — la sessione grafica GNOME: REMOTIX la fa NASCERE, e la fa nascere
 * CON UN MONITOR.  Non si limita a trovarla, e non si limita a farla viva.
 *
 * ---------------------------------------------------------------------------
 * ⛔ PERCHE' QUESTO FILE ESISTE IN V2, E PERCHE' NON E' UNA COPIA DI QUELLO DI v1
 *
 * `v1/remotix-c/src/sessione.c:671` e':
 *
 *     if (tipo == COMPOSITORE_KWIN && !scrivi_dropin(larghezza, altezza, sbaglio))
 *
 * cioe' il monitor virtuale si scrive **solo per KWin**.  `sessione_assicura()`
 * riceve `larghezza` e `altezza` (righe 650-651) e sul ramo GNOME **non le legge
 * nessuno**: la misura del desktop entra nella funzione e si perde in silenzio.
 * E' la forma d'errore **E3** — una funzione fa MENO di quel che il suo nome
 * promette: si chiama «assicura» e per GNOME non assicura la cosa senza cui non
 * c'e' niente da catturare.
 *
 * ⛔ E in headless Mutter mette `needs_outputs = false` (`gnome.md` §3.1):
 *    senza `--virtual-monitor` la sessione parte **viva, completa e nera**.
 *    Viva vuol dire proprio viva — `IsSessionRunning` risponde `true`,
 *    cinquanta nomi sul bus, Nautilus e il Terminale accesi — e manca una cosa
 *    sola, che manca in silenzio.
 *
 * ⭐ Non e' un timore: `[M]` 12 agosto 2026, la sessione GNOME viva su NIC-OS
 *    **da due giorni** era esattamente quella, e nessuno se n'era accorto
 *    (`fasi/rapporti/F2-1-sessione.md`, `fasi/rapporti/D4-sessione-nera.md`).
 *    Una cattura puntata li' avrebbe misurato zero fotogrammi e mandato a
 *    cercare il difetto dentro PipeWire.
 *
 * ---------------------------------------------------------------------------
 * ⛔ L'INVARIANTE CHE QUESTO FILE PAGA — **I7** (`CODER.md` §2)
 *
 *     «La protezione di un difetto noto sta nel programma, non in una riga di
 *      configurazione che si puo' perdere.»
 *
 * Fino al 12 agosto 2026 il monitor virtuale di GNOME lo metteva
 * `v1/banco/provision-server.sh`, cioe' una riga in `/etc/systemd/user/` su un
 * rootfs che vive in RAM.  Quella riga si e' persa — e la macchina e' stata nera
 * due giorni.  D4 l'ha rimessa, ⛔ **ma una riga rimessa e' ancora una riga che
 * si puo' perdere**: qui il monitor lo chiede il PROGRAMMA, a ogni nascita di
 * sessione, e verifica di essere stato obbedito.
 *
 * ---------------------------------------------------------------------------
 * ⛔ LE DUE DOMANDE CHE NON SONO UNA SOLA
 *
 *     «la sessione e' VIVA?»   e   «la sessione HA UN MONITOR?»
 *
 * Il difetto e' rimasto invisibile due giorni perche' se ne faceva **una sola**
 * — quella che rispondeva di si'.  Da cui `sessione_stato()`, che ha un numero
 * per stato, e `sessione_assicura()`, che aspetta **il monitor** e non la
 * vitalita'.
 *
 * ---------------------------------------------------------------------------
 * ⛔ E LE DUE REGOLE PAGATE CARE CHE ARRIVANO DA v1 INTATTE
 *
 *   - L'AMBIENTE SI COMPONE, NON SI EREDITA (`CODER.md` §4.5).  Chi avvia la
 *     sessione le regala tutto il proprio ambiente, comprese le variabili che
 *     non c'entrano nulla, e da li' la sessione lo ridistribuisce al gestore
 *     systemd dell'utente e all'attivazione D-Bus, dove SOPRAVVIVE al
 *     compositore.  Una `LC_ALL=C` arrivata per sbaglio da una shell SSH ha
 *     impedito a TUTTE le applicazioni di aprirsi, e il sintomo non diceva
 *     «manca una variabile»: diceva «le applicazioni non partono».
 *   - LA VITALITA' SI ACCERTA SENZA INTERPRETARE LA RISPOSTA.  `sessione_viva()`
 *     guarda solo che la risposta ARRIVI: dichiarare il tipo di ritorno di
 *     `GetCurrentState` significherebbe che la vitalita' della sessione dipende
 *     dall'esattezza di quella dichiarazione, e la prima stesura in Rust
 *     falliva cosi' — la sessione era partita e REMOTIX la dava per morta.
 *     ⭐ `sessione_stato()` invece la risposta la LEGGE, e quando non ha la
 *        forma che sa leggere dice «non ho potuto leggere» (5) e **mai** «zero
 *        monitor» (1): «vuoto» e «proibito» hanno lo stesso aspetto, ed e' la
 *        forma d'errore **E8**.
 */
#ifndef REMOTIX_SESSIONE_H
#define REMOTIX_SESSIONE_H

#include <gio/gio.h>
#include <glib.h>
#include <stdbool.h>
#include <stdint.h>

/* ⭐ `REG_SESSIONE` sta in `registro.h` accanto alle altre aree, dal 12 agosto
 *    2026: e' l'unica riga che il montaggio ha tolto da questo file, ed e' la
 *    riga che §6.2 di `P2-1-sessione.md` chiedeva di portare li'. */

/*
 * Come si avvia la sessione, e su quale unita' si scrive il monitor.
 *
 * ⛔ Il comando e' la parte FACILE.  Quel che decide se il compositore nasce con
 *    qualcosa da catturare e' la sovrascrittura dell'`ExecStart` dell'unita'
 *    della Shell: `gnome-session` NON lancia `gnome-shell`, fa partire l'unita'
 *    d'utente `org.gnome.Shell@wayland.service`, il cui `ExecStart` e' fisso.
 */
#define SESSIONE_COMANDO_GNOME "exec gnome-session --session=gnome"
#define SESSIONE_UNITA_SHELL "org.gnome.Shell@wayland.service"
#define SESSIONE_UNITA_GESTORE "gnome-session-manager@gnome.service"

/*
 * ⛔ IL MONITOR SI SCEGLIE PER NOME, E IL NOME E' QUESTO.
 *
 * `[M]` 12 agosto 2026: su questa macchina sono stati visti **due** monitor
 * virtuali insieme, e **entrambi 1920x1080@60**:
 *
 *     Meta-0   MetaVirtualMonitor      0x00       ← il nostro, --virtual-monitor
 *     Meta-1   Virtual remote monitor  0x000001   ← creato da Mutter per se'
 *
 * ⭐ Stessa identica misura: chi li distinguesse per risoluzione o per indice
 *    non distinguerebbe niente.  Li distingue **il nome del prodotto**, che
 *    Mutter mette al monitor persistente chiesto con `--virtual-monitor`
 *    (`meta-context-main.c:592-597` `[R]`) contro quello che si crea da se' per
 *    uno ScreenCast virtuale (`meta-screen-cast-virtual-stream-src.c:606-609`
 *    `[R]`).  E' `CODER.md` §3.9 alla lettera: *chiedi il componente per nome, e
 *    verifica che abbia obbedito*.
 */
#define SESSIONE_PRODOTTO_CHIESTO "MetaVirtualMonitor"

/*
 * ⛔ I NUMERI DI STATO, E SONO GLI STESSI DEL BANCO.
 *
 * Sono, uno per uno, le uscite di `banchi/02-sessione-stato.py` (0-5), e la
 * coincidenza e' voluta: il prodotto e il banco che lo giudica devono dire la
 * stessa parola per la stessa cosa, o il rapporto fra i due numeri va tradotto
 * a mano da qualcuno, e chi traduce sbaglia.
 *
 * ⚠ Il banco ha due numeri in piu' che qui non ci sono, e la divisione e'
 *   dichiarata invece che subita:
 *     6 DISACCORDO      riga di comando e bus non dicono lo stesso   ← E1
 *     7 SHELL NON VUOTA gnome-session ripartito in una shell di login
 *   Il **6** il prodotto lo previene invece di misurarlo: scrive il drop-in e
 *   rilegge l'`ExecStart` IN VIGORE prima di avviare (necessario), poi chiede al
 *   bus quanti monitor ci sono davvero (sufficiente).  Il **7** non puo'
 *   accadere: l'ambiente lo compone questo file, e `SHELL` la mette vuota di sua
 *   mano.  ⛔ Che il prodotto non possa produrre uno stato non toglie al banco
 *   il dovere di saperlo vedere: quei due numeri restano suoi.
 */
typedef enum {
	SESSIONE_SANA = 0,          /* un monitor solo, del nome e della misura chiesti */
	SESSIONE_NERA = 1,          /* viva, e ZERO monitor — il guasto M9 di gnome.md §13 */
	SESSIONE_MISURA_ALTRA = 2,  /* un monitor, ma non della misura chiesta */
	SESSIONE_SCELTO_DA_SE = 3,  /* prodotto diverso da quello chiesto, o piu' d'uno ← E2 */
	SESSIONE_MORTA = 4,         /* nessun compositore: il bus non risponde */
	SESSIONE_NON_LETTA = 5,     /* non ho POTUTO leggere: negata o illeggibile ← E8 */
} SessioneStato;

/* La marca a parole, con le stesse parole del banco. */
const char *sessione_marca(SessioneStato stato);

/* Il monitor come lo dichiara Mutter, per chi deve catturarlo per NOME. */
typedef struct {
	char connettore[64]; /* «Meta-0» */
	char fornitore[64];  /* «MetaVendor» */
	char prodotto[64];   /* «MetaVirtualMonitor» — e' questo che si guarda */
	char seriale[64];    /* «0x00» */
	uint32_t larghezza;
	uint32_t altezza;
	double refresh;
	unsigned quanti; /* quanti monitor c'erano in tutto: 2 e' gia' un difetto */
} SessioneMonitor;

/*
 * L'UNICO modo lecito di prendere il bus di sessione.
 *
 * ⛔ Non si chiama mai `g_bus_get_sync(G_BUS_TYPE_SESSION, ...)` direttamente.
 *
 * GIO, sulla connessione al bus di SESSIONE, tiene acceso «exit-on-close»: se
 * il bus si chiude, la libreria chiama `raise(SIGTERM)` per conto nostro.  Al
 * logout `dbus.service` dell'utente si ferma — e ha un colpevole con nome e
 * riga, `gnome-session-ctl.c:130-133` fa `StopUnit("dbus.service")`
 * (`gnome.md` §3.3) — e REMOTIX moriva li': non ucciso da systemd ne' da
 * nessun altro, ma da se stesso.  La pila che lo dimostra e' del 4 agosto 2026.
 * Per il bus di SISTEMA il difetto non esiste: quello resta.
 *
 * Restituisce un riferimento nuovo, o NULL con `sbaglio` scritto.
 */
GDBusConnection *sessione_bus(GError **sbaglio);

/*
 * C'e' un compositore che risponde?
 *
 * ⚠ E' la domanda DEBOLE, ed e' qui apposta perche' si veda che e' debole: una
 *   sessione nera risponde «si'».  Chi deve sapere se c'e' qualcosa da
 *   catturare chiama `sessione_stato()`.
 */
bool sessione_viva(void);

/*
 * In che stato e' la sessione, con la misura CHIESTA accanto.
 *
 * `scelto` (facoltativo) riceve il monitor trovato — o il primo dei molti,
 * quando sono molti — perche' chi cattura possa nominarlo invece di dedurlo.
 *
 * ⛔ Non tocca niente: si puo' chiamare in qualunque momento, e non fa male a
 *    nessuno.  ⚠ In particolare NON si chiede `org.gnome.Shell.Screenshot`, che
 *    su una sessione a zero monitor fa tentare a Mutter una texture 0x0
 *    (`cogl_texture_2d_new_with_size: assertion 'width >= 1' failed`), fa morire
 *    `gnome-shell` e, con `OnFailure=gnome-session-shutdown.target` e
 *    `Restart=no`, **porta via tutta la sessione** `[M]` 12 ago 2026.  ⇒ Quel
 *    controllo **distrugge la cosa che sta controllando**, e lo fa **solo nel
 *    caso guasto**: verde quando e' sana, macerie quando e' nera.
 */
SessioneStato sessione_stato(uint32_t larghezza, uint32_t altezza, SessioneMonitor *scelto);

/*
 * Si assicura che ci sia una sessione grafica CON UN MONITOR della misura
 * chiesta, facendola nascere se manca o se e' nera.
 *
 * Restituisce **lo stato del mondo quando ha finito**, non un si'/no: 0 e'
 * riuscito, e ogni altro numero dice in che modo non lo e'.  ⛔ Il perche' sta
 * nel registro, area «sessione»: non c'e' un `GError` da propagare perche' non
 * c'e' nessuno a cui propagarlo — chi chiama puo' solo dichiararlo e proseguire
 * con meno (`CODER.md` §4.2), ed e' quel che deve fare.
 *
 * `avviata` (facoltativo) dice se l'ha dovuta far nascere.
 *
 * ⛔ CHE COSA FA, CASO PER CASO — scritto qui perche' non si scopra dal codice:
 *
 *   SANA            non tocca niente.  Il palco appartiene alla sessione (I4)
 *   MORTA           scrive il drop-in, avvia, e ASPETTA IL MONITOR
 *   NERA            ⛔ scrive il drop-in e la fa RINASCERE, dichiarandolo forte.
 *                   Perche' e' lecito: un monitor vero ce l'avrebbe una sessione
 *                   locale, e una sessione a ZERO monitor puo' essere solo una
 *                   headless — cioe' nostra.  Non si porta via niente a nessuno
 *   MISURA_ALTRA    ⚠ DICHIARA e prosegue: c'e' qualcosa da catturare, e la
 *                   misura di una sessione gia' viva non si cambia a caldo
 *                   (`gnome.md` §8.2: `ensure_virtual_monitor` esce prima se la
 *                   misura non cambia — e che regga un cambio a caldo e' `[?]`)
 *   SCELTO_DA_SE    ⚠ DICHIARA, elenca TUTTI i monitor per nome, e prosegue.
 *                   Rifarla nascere non curerebbe niente: chi crea il monitor
 *                   di troppo e' uno ScreenCast di qualcun altro
 *   NON_LETTA       ⛔ NON TOCCA NIENTE.  «Non ho potuto leggere» non e' «non
 *                   c'e'» (E8), e una sessione buttata giu' per una lettura
 *                   fallita e' un danno fatto per un'ipotesi
 */
/* ⭐ Chiede la nascita della sessione grafica e TORNA SUBITO — fase 5.
 * Si avvia solo da `SESSIONE_MORTA`; a scoprire che c'e' ci pensa chi riprova.
 * ⛔ La usa il FIGLIO, che in un'attesa di 40 s smetterebbe di rispondere al
 *    padre.  Il perche' per intero sta sopra la funzione in `sessione.c`. */
bool sessione_fai_nascere(uint32_t larghezza, uint32_t altezza);

SessioneStato sessione_assicura(uint32_t larghezza, uint32_t altezza, bool *avviata);

/*
 * Termina la sessione grafica.  Vero se c'era e ora non c'e' piu'.
 *
 * # Perche' esiste
 *
 * Perche' «la sessione locale vince» (I2) non significa soltanto staccare il
 * client: se il compositore remoto restasse in piedi, l'utente che si siede
 * davanti alla macchina avrebbe **due sessioni grafiche a proprio nome** sullo
 * stesso `$XDG_RUNTIME_DIR`, e la seconda troverebbe `org.gnome.Shell` gia'
 * occupato.  Il difetto si vedrebbe dove nessuno lo cerca: sulla sessione
 * LOCALE che non parte.
 *
 * # Prima si chiede, poi si insiste
 *
 * `Logout(1)` e' l'uscita ordinata senza domande.  Ma puo' anche non succedere
 * nulla — un programma con modifiche non salvate ha il diritto di INIBIRE
 * l'uscita, e `Logout(1)` in quel caso mostra il dialogo, che in una sessione
 * non presidiata non chiude nessuno (`gnome.md` §3.2).  Dopo dieci secondi si
 * insiste con `Logout(2)`, **dichiarandolo nel registro**: e' una perdita
 * possibile di lavoro non salvato, e chi legge deve poterla ricostruire.
 *
 * ⛔ E si aspetta `inactive`, NON «diverso da active»: `is-active` passa per
 *    `deactivating`, e far ripartire una sessione li' dentro e' un'altra prima
 *    esecuzione (`fasi/00-ambiente.md`, difetto 4 della fase 0).
 */
bool sessione_termina(void);

#endif
