/*
 * compositore — la porta unica verso chi possiede schermo e input.
 *
 * §3.8 di SPECIFICA.md dice che l'asse rilevante non e' il desktop ma il
 * COMPOSITORE, e che tre famiglie coprono tutto il panorama Wayland: Mutter
 * (GNOME, Cinnamon), KWin (Plasma), wlroots (XFCE, LXQt, Sway).  Qui c'e'
 * l'interfaccia che il palco usa, e sotto ci sono le implementazioni: `mutter.c`
 * e `kwin.c`.  wlroots arrivera' con il suo modulo, e non dovra' toccare niente
 * di quel che sta sopra.
 *
 * ⛔ QUEL CHE CAMBIA DAVVERO FRA I DUE NON E' LA STRADA, E' CHI DECIDE LA
 *    MISURA.
 *
 *    Su Mutter il monitor si CHIEDE — `RecordVirtual` non prende una misura, la
 *    risoluzione si concorda nella negoziazione PipeWire, ed e' la base su cui
 *    poggia la risoluzione dinamica della fase 6.
 *
 *    Su KWin no.  Il backend `--virtual` — l'unico praticabile, perche' `--drm`
 *    da una sessione senza seat non parte (`kde.md` §5.2) — non sa creare
 *    uscite a richiesta, e un output virtuale ha UN SOLO MODO, immutabile
 *    (`kde.md` §8.1).  La misura la porta il compositore, e noi ci adattiamo:
 *    e' la decisione dell'utente dell'8 agosto 2026 — «misura fissa alla
 *    connessione, l'immagine si scala nel client».
 *
 *    Il ridimensionamento vero arriva in KWin 6.8, e arriva **per negoziazione
 *    PipeWire** (`kwin!7932`, unita il 29 luglio 2026): cioe' con il codice che
 *    la fase 6 ha gia' scritto.  Per questo la richiesta si manda comunque, in
 *    quella forma — su Trixie il compositore risponde con la propria misura e
 *    noi la adottiamo, su 6.8 risponde con quella chiesta e si accende da se'.
 */
#pragma once

#include <glib.h>
#include <stdint.h>

typedef enum
{
	COMPOSITORE_AUTO,   /* si riconosce all'avvio */
	COMPOSITORE_MUTTER, /* GNOME, Cinnamon */
	COMPOSITORE_KWIN,   /* KDE Plasma */
} TipoCompositore;

typedef struct Compositore Compositore;

const char *compositore_nome(TipoCompositore tipo);
gboolean compositore_tipo_da_nome(const char *nome, TipoCompositore *fuori);

/*
 * Chi serve questa sessione.
 *
 * Si RILEVA, non si deduce dalla distribuzione (§2 di SPECIFICA.md): si chiede
 * al bus di sessione chi risponde.  `preferito` diverso da AUTO salta il
 * riconoscimento — serve al banco, e serve il giorno in cui due compositori
 * fossero raggiungibili insieme.
 */
TipoCompositore compositore_riconosci(TipoCompositore preferito);

/* Apre la cattura e restituisce la sessione, con il nodo PipeWire pronto. */
Compositore *compositore_apri(TipoCompositore tipo, GError **sbaglio);

TipoCompositore compositore_tipo(const Compositore *comp);
uint32_t compositore_nodo(const Compositore *comp);

/*
 * La misura che il compositore IMPONE, o 0×0 se la decidiamo noi.
 *
 * Zero significa «chiedi quella che vuoi alla cattura»: e' il caso di Mutter.
 * Un valore significa «il desktop e' grande cosi'»: e' il caso di KWin, e chi
 * chiama deve adattare la propria tela invece di insistere.
 */
void compositore_misura_imposta(const Compositore *comp, uint32_t *larghezza, uint32_t *altezza);

/*
 * Il descrittore di libei, o -1 se questo compositore non l'ha concesso.
 *
 * La chiamata lo CONSEGNA: da qui in poi e' di chi l'ha preso, perche' libei
 * dichiara di prenderselo e di chiuderlo lui.
 */
int compositore_prendi_fd_eis(Compositore *comp);

/*
 * Lo stato VERO dei tasti a scatto, per chi non lo consegna con l'input.
 *
 * Su Mutter non fa niente, e va bene: là lo stato arriva da libei con
 * `EI_EVENT_KEYBOARD_MODIFIERS`.  Su KWin quell'evento **non arriva mai**
 * (`kde.md` §7.2), e senza questa strada la riconciliazione di BlocMaiusc e
 * BlocNum sarebbe codice che non gira — che è peggio di codice che manca,
 * perché non lo si va a cercare.
 */
typedef void (*CompositoreLucchetti)(gboolean maiusc, gboolean num, gpointer dati);

void compositore_lucchetti_ascolta(Compositore *comp, CompositoreLucchetti su_cambio,
                                   gpointer dati);

/*
 * La chiave con cui si riconosce, fra le regioni che libei annuncia, quella del
 * nostro schermo.  NULL su KWin, che le regioni non le marca affatto
 * (`eis_region_set_mapping_id` non e' chiamato in tutto KWin, `kde.md` §7.2):
 * la' si cercano per GEOMETRIA.
 */
const char *compositore_mapping_id(const Compositore *comp);

/*
 * Il percorso della sessione di controllo, per chi vi appende gli appunti.
 * NULL su KWin: la clipboard non appartiene a una sessione, e si prende con
 * `zwlr_data_control_manager_v1` (`kde.md` §9).
 */
const char *compositore_percorso_controllo(const Compositore *comp);

/* Vero se il compositore ha chiuso la cattura per conto suo. */
gboolean compositore_finito(const Compositore *comp);

/*
 * Il compositore disegna il cursore DENTRO l'immagine che catturiamo?
 *
 * ⛔ SU KWIN CON `--virtual` SI, E NON C'E' MODO DI IMPEDIRGLIELO.
 *    [M, 8 agosto 2026, e l'ha visto l'utente: «e' quello di KDE che segue
 *    quello vero», cioe' due puntatori]
 *
 *    Il backend virtuale non ha un piano cursore hardware —
 *    `m_backend->cursorLayer(output)` non e' definito — quindi
 *    `compositor_wayland.cpp:573-608` ripiega sul cursore SOFTWARE, che e' un
 *    RenderLayer dipinto nello stesso framebuffer dell'uscita.  E
 *    `VirtualEglBackend::textureForOutput` restituisce proprio quel framebuffer
 *    (`virtual_egl_backend.cpp:187-194`): il cursore ci sta dentro.
 *
 *    ⚠ E il modo cursore dello screencast NON c'entra: «Metadata» governa se lo
 *      screencast ne AGGIUNGE uno, non se la scena ne contiene gia' uno.
 *      Chiedere «Hidden» non cambierebbe niente.
 *
 *    KWin lo mostra appena esiste un dispositivo di puntamento sul seat
 *    (`pointer_input.cpp:99-108`), e il nostro lo crea libei.  Non esiste alcuna
 *    leva — ne' protocollo ne' D-Bus — per dirgli di non disegnarlo: `hideCursor`
 *    e' interna e la chiama solo lui.
 *
 * Su Mutter no: la' il cursore resta fuori dall'immagine, e il puntatore che si
 * vede e' quello che il client disegna da se'.
 *
 * ⛔ Da cui la conseguenza, che e' l'unica cura possibile: dove il cursore e'
 *    nell'immagine, si dice al client di NASCONDERE il proprio, o se ne vedono
 *    due.  Il prezzo e' che il puntatore si muove alla latenza del VIDEO invece
 *    che a quella della rete — su una LAN e' un fotogramma.
 */
gboolean compositore_cursore_nell_immagine(TipoCompositore tipo);

void compositore_chiudi(Compositore *comp);
