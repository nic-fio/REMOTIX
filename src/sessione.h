/*
 * sessione — la sessione grafica GNOME: REMOTIX la fa NASCERE, e la fa nascere
 * CON UN MONITOR.  Non si limita a trovarla, e non si limita a farla viva.
 *
 * ---------------------------------------------------------------------------
 * ⛔ PERCHE' QUESTO FILE ESISTE IN V2, E PERCHE' NON E' UNA COPIA DI QUELLO DI v1
 *
 * `fondamenta/remotix-c/src/sessione.c:671` e':
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
 * ⛔ E in headless Mutter mette `needs_outputs = false` (`STUDI.md` §gnome §3.1):
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
 * `fondamenta/banco/provision-server.sh`, cioe' una riga in `/etc/systemd/user/` su un
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
/* ⛔ E la SECONDA unita' da aspettare: quando una sessione GNOME finisce, GNOME
 * RIAVVIA il bus di sessione con questa.  Una sessione nuova avviata mentre gira
 * nasce su un bus che sta per essere sostituito — e muore senza scrivere niente
 * (`[M]` 16 agosto 2026: il suo registro resta a zero byte). */
#define SESSIONE_UNITA_DBUS "gnome-session-restart-dbus.service"

/*
 * ⭐ FASE 12 — IL SECONDO DESKTOP: PLASMA.  `fasi/12-kde.md`, incremento 1.
 *
 * ✅ `DECISIONI.md` §4.6-duodetricies: **un desktop per macchina**, e il
 *    server lo riconosce da quel che e' installato.  ⛔ La scelta fra piu'
 *    desktop e' rimandata (`MASTERPLAN.md` M5).
 *
 * ⚠ Le stesse tre cose di GNOME, con i nomi di Plasma — ⛔ non un'eccezione:
 *   la FUNZIONE e' la stessa (la sessione nasce, si riconosce, finisce), cambia
 *   **come** la si chiede.  `startplasma-wayland` non lancia KWin: fa partire
 *   `plasma-kwin_wayland.service`, il cui `ExecStart` si sovrascrive col drop-in
 *   (`STUDI.md` §kde §6.1-§6.2), esattamente come l'unita' della Shell.
 */
#define SESSIONE_COMANDO_KDE "exec startplasma-wayland"
#define SESSIONE_UNITA_KWIN "plasma-kwin_wayland.service"
#define SESSIONE_UNITA_PLASMA "plasma-workspace.target"

/*
 * ⭐ FASE 13 — IL TERZO DESKTOP: XFCE.  `fasi/13-xfce.md`, incremento 1.
 *
 * ⛔⛔ E QUI CADE LA FORMA DEI PRIMI DUE, non si ripete.  GNOME porta Mutter e
 *     KDE porta KWin; **XFCE non porta un compositore**: su Wayland si appoggia
 *     a `labwc`, della famiglia `wlroots` (`STUDI.md` §xfce §1).
 *
 * ⇒ Le conseguenze che cambiano il codice, e non sono di stile:
 *
 *   1. ⛔ **Non c'e' nessuna unita' systemd d'utente da scavalcare.**  Su GNOME
 *      si riscrive l'`ExecStart` di `org.gnome.Shell@wayland.service`, su KDE
 *      quello di `plasma-kwin_wayland.service`; qui il compositore è un
 *      processo che avviamo noi, e `scrivi_dropin()` **non ha oggetto**.
 *   2. ⛔ **La misura NON entra nella nascita.**  `[M]` 20 set 2026, dentro
 *      `rete11-xfce`: l'uscita nasce `HEADLESS-1 1280x720`, cablata, e nessun
 *      protocollo ne crea una della misura voluta.  La misura si da' **dopo**,
 *      da cliente Wayland (`zwlr_output_manager_v1` v4, che c'e').
 *   3. ⭐ **La riga di avvio deve contenere `labwc` E `--session`**, e non per
 *      gusto: `xfce4-session` legge `XFCE4_SESSION_COMPOSITOR` e, se non ci
 *      trova tutt'e due, al logout esegue `loginctl terminate-session ''` —
 *      cioe' ammazza **la sessione logind di REMOTIX** (`STUDI.md` §xfce §9.2).
 *      ⇒ `--session` fa anche il lavoro buono: rende `xfce4-session` il client
 *        primario di labwc, quindi quando esce lui **labwc termina da se'**.
 */
/* ⚠ La riga si scrive UNA volta e si usa DUE: come comando (con `exec`) e
 *   dentro `XFCE4_SESSION_COMPOSITOR` (senza).  ⛔ Scriverla due volte vorrebbe
 *   dire poterle far divergere, e divergendo scatterebbe la trappola del
 *   logout senza che nessuna riga lo dica. */
#define SESSIONE_RIGA_XFCE "labwc --session xfce4-session"
#define SESSIONE_COMANDO_XFCE "exec " SESSIONE_RIGA_XFCE
/* ⛔ Il processo del compositore, per nome: su XFCE la guardia contro la
 *    seconda sessione non puo' chiedere a systemd — vedi `unita_inattiva()`. */
#define SESSIONE_PROCESSO_XFCE "labwc"
/* Il gestore di sessione sul bus D'UTENTE — `[M]` 20 set 2026: compare li', non
 * su un bus privato, perche' `labwc` lo avviamo noi senza `dbus-run-session`.
 * ⚠ Il nome non è l'interfaccia: `org.xfce.Session.Manager` (con un punto in
 * piu') — `STUDI.md` §xfce §9.5. */
#define SESSIONE_BUS_XFCE "org.xfce.SessionManager"

/*
 * ⭐ FASE 14 — IL QUARTO DESKTOP: LXQt.  Incremento 1, «si riconosce, nasce e
 *    si vede».  La fonte è `STUDI.md` §lxqt, e dove parla il sorgente upstream
 *    lo si cita con l'indirizzo.
 *
 * ⛔⛔ SU TRIXIE LA SESSIONE WAYLAND DI LXQt NON È IMPACCHETTATA: manca il
 *     lanciatore (`lxqt-wayland-session`, `startlxqtwayland`), non il codice
 *     (`STUDI.md` §lxqt §1).  ⇒ Il lanciatore lo facciamo noi, e la forma è
 *     quella del lanciatore upstream coetaneo di LXQt 2.1 — tag 0.1.1 —
 *     `[R]` https://raw.githubusercontent.com/lxqt/lxqt-wayland-session/0.1.1/startlxqtwayland.in
 *     (ramo `labwc`):
 *
 *         exec labwc -C $XDG_CONFIG_HOME/labwc -S lxqt-session
 *
 *   con UNA differenza voluta: la cartella di `-C` è NOSTRA (sotto
 *   `XDG_RUNTIME_DIR`), non quella dell'utente — lo script upstream ci copia
 *   una volta sola un `autostart` che lancia `swayidle … wlopm --off` a 5
 *   minuti, e la copia è **permanente** (`STUDI.md` §lxqt §6.2).
 *   ⭐ `-C` basta da solo: con `-C` labwc guarda **solo** quella cartella
 *   (`[R]` labwc 0.8.3 `src/common/dir.c:151-157`).
 *
 * ⚠ La stessa forma di XFCE, e per la stessa ragione: `-S` (= `--session`)
 *   rende `lxqt-session` il client primario di labwc ⇒ quando esce lui, labwc
 *   termina.  ✅ E la trappola di XFCE qui non c'è: `lxqt-session` non chiama
 *   `loginctl terminate-session` (`STUDI.md` §lxqt §3.3, `[✗]`).
 *
 * ⚠ La riga intera non è una costante, al contrario di XFCE: la cartella di
 *   `-C` sta sotto `XDG_RUNTIME_DIR` e si compone in `avvia()`.  Qui ci sono
 *   i due pezzi che non cambiano.
 */
#define SESSIONE_MARCATORE_LXQT "lxqt-session"
#define SESSIONE_PRIMARIO_LXQT "lxqt-session"
/* ⭐ Il nome sul bus D'UTENTE, e anche l'oggetto e l'interfaccia del logout:
 *    `[R]` lxqt-session 2.1.1 `sessionapplication.cpp:48-49` (servizio e
 *    `/LXQtSession`), `sessiondbusadaptor.h` (interfaccia `org.lxqt.session`)
 *    — https://raw.githubusercontent.com/lxqt/lxqt-session/2.1.1/lxqt-session/src/sessiondbusadaptor.h
 * ⚠ Il nome compare nel COSTRUTTORE: «c'è il nome» non vuol dire «desktop su»
 *   (`STUDI.md` §lxqt §3.4).  Vedi `sessione_viva()`. */
#define SESSIONE_BUS_LXQT "org.lxqt.session"

/*
 * ⛔⛔ E IL QUARTO VALORE NON E' UN DESKTOP: E' L'ONESTA'.
 *
 * Fino alla fase 12 una macchina che non aveva ne' GNOME ne' KDE veniva
 * dichiarata **GNOME per ripiego**, e il prodotto provava ad avviare
 * `gnome-session` che li' non esiste.  `[M]` 20 set 2026, `rete11-xfce`: il
 * guasto non arrivava dove ci si aspetta — `scrivi_dropin()` rileggeva
 * l'`ExecStart` di un'unita' inesistente, otteneva il vuoto, e scriveva
 * «**un altro drop-in vince sul mio**»; poi la cattura accusava «**Mutter non
 * espone RemoteDesktop**».  ⇒ Due innocenti accusati, e la causa vera —
 * *GNOME non c'e'* — scritta una volta sola, all'avvio del server, dove il
 * banco non la legge.
 *
 * ⭐ Con «un desktop per macchina» (`DECISIONI.md` §0.6) quel ripiego era
 *   **l'unico posto in cui il prodotto poteva sbagliare desktop, e sbagliava in
 *   silenzio**.  ⇒ Non si aggiunge XFCE all'elenco lasciandolo li': si toglie.
 *   Altrimenti il giorno di LXQt si ripete identico.
 *
 * ⚠ I numeri vanno IN CODA: `SessioneDesktop` viaggia come `uint32_t` fra il
 *   padre e il figlio, e spostare 0 o 1 romperebbe quel confine.
 */
typedef enum {
	SESSIONE_DESKTOP_GNOME = 0,
	SESSIONE_DESKTOP_KDE = 1,
	SESSIONE_DESKTOP_XFCE = 2,
	SESSIONE_DESKTOP_NESSUNO = 3,
	/* ⭐ FASE 14 — IN CODA, per la regola qui sopra: 0..3 restano quelli. */
	SESSIONE_DESKTOP_LXQT = 4,
} SessioneDesktop;

/*
 * Quale desktop ha questa macchina — deciso UNA volta per processo.
 *
 * ⭐ È una RICERCA, non un arbitrato: `DECISIONI.md` §0.6 — una macchina, un
 *   desktop; le macchine con piu' desktop installati sono **fuori scopo**.
 *
 * L'ordine, e ogni riga ha la sua ragione:
 *
 *   1. `startplasma-wayland` **e non** `gnome-session`  → KDE
 *   2. tutti e due                                      → GNOME, e si DICHIARA
 *      ambiguo (fuori scopo: si sceglie e si dice, non si cura)
 *   3. `gnome-session`                                  → GNOME
 *   4. `xfce4-session`                                  → XFCE   ⭐ fase 13
 *      (e se c'è anche `lxqt-session`: XFCE, e si DICHIARA ambiguo — fase 14)
 *   5. `lxqt-session`                                   → LXQT   ⭐ fase 14
 *   6. nessuno                                          → **NESSUNO**, e non
 *      nasce niente — vedi il riquadro dell'enum
 *
 * ⚠ L'ordine NON è libero: i primi tre rami restano testualmente quelli della
 *   fase 12, quindi **nessuna macchina servita oggi cambia comportamento**.  Il
 *   ramo di XFCE si infila fra l'ultimo desktop conosciuto e il ripiego.
 * ⭐ E quello di LXQt DOPO XFCE, per la stessa ragione: una macchina con XFCE
 *   e LXQt insieme resta XFCE com'era ieri — cambia solo che adesso lo dice.
 *
 * ⛔ E il marcatore di XFCE è `xfce4-session`, **non `labwc`**: labwc è il
 *    compositore di FAMIGLIA, lo stesso che usa LXQt, e riconoscere su di lui
 *    confonderebbe due desktop diversi.  `labwc` resta una **precondizione**, e
 *    la sua assenza si dichiara alla nascita invece di scoprirla da un `exec`
 *    fallito.  ⭐ Fase 14: per LXQt, identico, il marcatore è `lxqt-session`.
 */
SessioneDesktop sessione_desktop(void);

/* La scelta a parole, con il perche' — per la riga di avvio del server. */
const char *sessione_desktop_spiega(void);

/*
 * ⭐ FASE 14 — LA FAMIGLIA, non il desktop: vero su XFCE **e** su LXQt.
 *
 * Cattura, input, appunti e rimontaggio non parlano col desktop: parlano col
 * COMPOSITORE, e per tutt'e due è labwc (`STUDI.md` §lxqt §5: «riuso
 * integrale»).  ⛔ Fino alla fase 13 `figlio.c` lo scriveva
 * `== SESSIONE_DESKTOP_XFCE` in cinque punti: con un quinto valore dell'enum
 * LXQt sarebbe caduto, tutto insieme e senza un avviso, nel ramo di GNOME/KDE.
 * ⇒ Chi chiede «wlroots?» chiede questo, e non un desktop.
 */
bool sessione_su_wlroots(void);

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
	SESSIONE_NERA = 1,          /* viva, e ZERO monitor — il guasto M9 di STUDI.md §gnome §13 */
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
 * (`STUDI.md` §gnome §3.3) — e REMOTIX moriva li': non ucciso da systemd ne' da
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
 *                   (`STUDI.md` §gnome §8.2: `ensure_virtual_monitor` esce prima se la
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

/* ⭐ Le impostazioni che la sessione deve avere PRIMA di nascere: le dodici
 * scorciatoie delle console virtuali (che in headless Mutter ingoia per
 * niente), la voce «Esci…» accesa, la sospensione automatica spenta, il
 * blocca-schermo del desktop spento.  ⛔ Le mette il PRODOTTO e non un file di
 * provisioning: invariante I7.  ⚠ Ogni schema si cerca prima — `g_settings_new`
 * su uno schema assente ABORTISCE il processo. */
void sessione_impostazioni(void);

/* ⭐ Dice al gestore di sessione che qualcuno sta lavorando: `SUSPEND|IDLE`,
 * ⛔ mai `LOGOUT`.  Restituisce il gettone, 0 se non e' andata.  ⚠ Non si
 * rilascia: vale quanto la sessione.  (`DECISIONI.md` §4.7, terza cintura.) */
guint32 sessione_inibisci(void);

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
 * non presidiata non chiude nessuno (`STUDI.md` §gnome §3.2).  Dopo dieci secondi si
 * insiste con `Logout(2)`, **dichiarandolo nel registro**: e' una perdita
 * possibile di lavoro non salvato, e chi legge deve poterla ricostruire.
 *
 * ⛔ E si aspetta `inactive`, NON «diverso da active»: `is-active` passa per
 *    `deactivating`, e far ripartire una sessione li' dentro e' un'altra prima
 *    esecuzione (`FASI.md` §00-ambiente, difetto 4 della fase 0).
 */
bool sessione_termina(void);

#endif
