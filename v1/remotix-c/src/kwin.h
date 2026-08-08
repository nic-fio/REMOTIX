/*
 * kwin — la cattura su KDE Plasma, che non passa da D-Bus ma dal protocollo
 * Wayland.
 *
 * E' l'equivalente di `mutter.c` per l'altro compositore, e la differenza di
 * forma e' totale: su GNOME la cattura si chiede con una sequenza di cinque
 * chiamate D-Bus che non ammette permute, qui con UNA richiesta Wayland.  Su
 * KWin non esiste alcun servizio D-Bus di screencast — cercato in tutto
 * l'albero della 6.3.6, non c'e' (`kde.md` §16): la cattura passa dal
 * protocollo, punto.
 *
 * ⛔ IL PROTOCOLLO E' DIETRO UN PERMESSO, ED E' LA PRIMA COSA DA SAPERE.
 *
 *    `zkde_screencast_unstable_v1` sta nella lista nera del filtro dei global
 *    di KWin (`wayland_server.cpp:129-136`): a un client qualunque il global
 *    NON VIENE NEMMENO ANNUNCIATO, e il sintomo e' «questo compositore non ha
 *    il protocollo» — non un errore, un'assenza.
 *
 *    Il cancello si apre con un file `.desktop` installato che dichiari
 *    `X-KDE-Wayland-Interfaces=zkde_screencast_unstable_v1` e il cui primo
 *    token di `Exec=`, canonicalizzato, coincida con il nostro
 *    `/proc/self/exe`.  Nessun dialogo, mai: e' il meccanismo con cui si
 *    autorizzano il portale di KDE, `krfb-virtualmonitor` e **KRdp**, il server
 *    RDP di KDE (`kde.md` §3.2 e §12.0).  Lo installa `--installa-desktop`.
 *
 * ⛔ E DIPENDE DA UNA VARIABILE D'AMBIENTE CHE NESSUNO DOCUMENTA:
 *    `XDG_MENU_PREFIX=plasma-` NELL'AMBIENTE DI KWIN.  Senza, l'indice dei
 *    servizi di KDE si costruisce VUOTO — `kbuildsycoca6` non trova
 *    `applications.menu`, che su Debian non esiste — e KWin non trova nessun
 *    `.desktop`, nemmeno quelli di sistema.  In una sessione Plasma la mette
 *    `startplasma`; in un ambiente composto da noi va messa a mano.  [M, 7
 *    agosto 2026, dopo cinque prove negate con il file scritto giusto —
 *    `kde.md` §3.3-bis, `LEZIONI.md` §1.10]
 *
 * ⛔ E LA MISURA NON LA DECIDIAMO NOI.  Con il backend `--virtual` — l'unico
 *    praticabile, perche' `--drm` da una sessione senza seat non parte
 *    (`kde.md` §5.2) — `stream_virtual_output` NON FUNZIONA: `VirtualBackend`
 *    non sa creare uscite a richiesta e KWin risponde «Could not find output».
 *    Si cattura quindi l'uscita che il compositore ha gia', della misura con
 *    cui e' stato avviato, e quella misura si LEGGE invece di imporla.  Il
 *    ridimensionamento arriva in KWin 6.8, per negoziazione PipeWire — cioe'
 *    con il codice della nostra fase 6 (`kde.md` §8.2).
 */
#pragma once

#include <glib.h>
#include <stdint.h>

typedef struct KwinSessione KwinSessione;

/*
 * Apre il flusso di cattura e restituisce la sessione, con il nodo PipeWire
 * gia' annunciato.
 *
 * Non prende una misura: quella la porta l'uscita, e si legge con
 * `kwin_misura`.  Chi chiama deve adattarvisi, non il contrario.
 */
KwinSessione *kwin_apri(GError **sbaglio);

/* Il nodo PipeWire da cui leggere i fotogrammi. */
uint32_t kwin_nodo(const KwinSessione *sessione);

/*
 * La misura dell'uscita catturata, in PIXEL.
 *
 * E' quella del modo corrente del `wl_output`, non una nostra richiesta: su
 * KWin il desktop e' grande quanto il compositore l'ha fatto.
 */
void kwin_misura(const KwinSessione *sessione, uint32_t *larghezza, uint32_t *altezza);

/* Il nome dell'uscita catturata, per il registro e per le diagnosi. */
const char *kwin_nome_uscita(const KwinSessione *sessione);

/* Vero se KWin ha chiuso il flusso per conto suo (uscita disabilitata,
 * PipeWire caduto, sessione finita). */
gboolean kwin_chiuso(const KwinSessione *sessione);

/*
 * Il descrittore di libei, chiesto a KWin con UNA chiamata D-Bus.
 *
 * ⛔ E NON C'E' NESSUN CONTROLLO DI PERMESSO.  `org.kde.KWin.EIS.RemoteDesktop`
 *    e' registrato con `ExportAllInvokables` senza filtro
 *    (`kwin/src/plugins/eis/eisbackend.cpp:70`): nessun pid, nessun `.desktop`,
 *    nessun dialogo.  In tutto KWin 6.3.6 l'unico oggetto D-Bus protetto e'
 *    `ScreenShot2` (`kde.md` §3.4).  Misurato il 7 agosto 2026:
 *    `connectToEIS(7)` da una shell SSH qualunque risponde `(handle 0, 1)`.
 *
 *    Per un servizio non presidiato e' meglio di GNOME — niente sessione da
 *    creare, niente portale — ma va trattato come **una porta che puo'
 *    chiudersi**: l'errore D-Bus e' un caso normale, non un difetto, e chi lo
 *    riceve degrada a sola visione invece di non partire.
 *
 * La maschera e' quella del portale xdg: tastiera 1, puntatore 2, tocco 4.
 *
 * La chiamata CONSEGNA il descrittore: da qui in poi e' di chi l'ha preso,
 * perche' libei dichiara di prenderselo e di chiuderlo lui.  Vale -1 se KWin
 * non l'ha concesso.
 */
int kwin_prendi_fd_eis(KwinSessione *sessione);

/*
 * Lo stato vero dei tasti a scatto, che su KWin NON arriva da libei.
 *
 * ⛔ `eis_device_keyboard_send_xkb_modifiers` non e' chiamato da nessuna parte
 *    in KWin (`kde.md` §7.2, cercato: assente).  L'evento
 *    `EI_EVENT_KEYBOARD_MODIFIERS` su cui poggia la riconciliazione scritta per
 *    GNOME quindi **non arriva mai**, e chi non se ne accorge crede di aver
 *    scritto una funzione che invece non gira.
 *
 *    Il ripiego e' un protocollo a parte, `org_kde_kwin_keystate`, che da' lo
 *    stato con notifica spontanea.  Su KDE costa poco davvero — la connessione
 *    Wayland c'e' gia' per la cattura — e il prezzo e' un nome in piu' nel
 *    `.desktop`, che `--installa-desktop` scrive gia'.  E' la decisione
 *    dell'utente dell'8 agosto 2026.
 *
 * La richiamata gira sul thread della pompa: chi la scrive accodi e basta.
 */
typedef void (*KwinLucchetti)(gboolean maiusc, gboolean num, gpointer dati);

void kwin_lucchetti_ascolta(KwinSessione *sessione, KwinLucchetti su_cambio, gpointer dati);

void kwin_chiudi(KwinSessione *sessione);

/*
 * Scrive il file `.desktop` che apre il cancello della cattura, con `Exec=`
 * puntato al binario vero — cioe' a `/proc/self/exe` canonicalizzato.
 *
 * ⛔ NON SI ESEGUE COME ROOT: `/proc/<pid>/exe` di un processo di altro uid non
 *    e' leggibile da KWin, `executablePath()` torna vuoto e il permesso e'
 *    negato (`kde.md` §3.3).  E `Exec=` deve nominare il binario, non un
 *    lanciatore di shell: il confronto e' sul percorso canonico.
 */
gboolean kwin_installa_desktop(GError **sbaglio);

/*
 * Il socket del compositore Wayland, aperto.
 *
 * ⛔ NON SI PUO' RICORDARE: al riavvio della sessione il numero CAMBIA — il
 *    socket e' il primo `wayland-N` libero (`kde.md` §6.6).  Si prende
 *    `WAYLAND_DISPLAY` se c'e', altrimenti si provano in ordine, perche' un
 *    servizio avviato da systemd o da una shell SSH quella variabile non ce l'ha.
 *
 * ⚠ Sta qui perche' qui e' nata, ma NON e' specifica di KWin: la usa anche
 *   `appunti_wlr.c`, che domani servira' wlroots.  Duplicarla significherebbe
 *   avere due ricette che divergono.
 *
 * `quale` riceve il nome del socket, da liberare con `g_free`.
 */
struct wl_display *kwin_display_apri(char **quale);
