/*
 * kwin — il palco su KDE Plasma: il flusso dello schermo chiesto a KWin.
 *
 * ⛔ RIPORTATO DA `fondamenta/remotix-c/src/kwin.c` di v1 (822 righe), e non
 *    ricopiato: qui resta ⭐ **la cattura** — il protocollo Wayland
 *    `zkde_screencast_unstable_v1` (versione 5 su KWin 6.3.6) che, chiesto
 *    sull'uscita `Virtual-0`, risponde col numero di un nodo PipeWire.  Dal nodo
 *    in poi la strada e' quella di GNOME: `cattura_avvia(nodo)`.
 *    ⚠ L'input (`org.kde.KWin.EIS.RemoteDesktop.connectToEIS`) e lo stato dei
 *    lucchetti (`org_kde_kwin_keystate`) sono di v1 e NON sono qui: sono
 *    l'incremento 3 della fase 12 (`fasi/12-kde.md`).
 *
 * Il ruolo e' quello di `mutter.h` su GNOME, e la scelta fra i due la fa
 * `sessione_desktop()` UNA volta per processo — nessun secondo modo di
 * riconoscere il desktop.
 *
 * ⛔ IL CANCELLO.  KWin annuncia `zkde_screencast_unstable_v1` SOLO a un
 *    client il cui eseguibile (`/proc/<pid>/exe`, canonico) sta nell'`Exec=` di
 *    un `.desktop` che lo dichiara in `X-KDE-Wayland-Interfaces`.  `[M]` 18 set
 *    2026 nella scatola `kde`: senza quel file il global NON c'e' (58 altri
 *    si'), con il file c'e' — anche scritto a sessione gia' viva.
 *    ⇒ Il file lo scrive il server all'avvio (`kwin_scrivi_permesso()`), col
 *    percorso del binario che sta girando: il figlio e' un `execve` dello
 *    stesso binario, quindi e' lui che KWin riconosce.
 */
#pragma once

#include <glib.h>
#include <stdbool.h>
#include <stdint.h>

typedef struct KwinSessione KwinSessione;

/* Si collega al compositore dell'utente, trova l'uscita, chiede il flusso e
 * aspetta il nodo PipeWire (al massimo 5 s).  NULL con `sbaglio` scritto — e
 * se il cancello e' chiuso, `sbaglio` dice quale delle due cause guardare. */
KwinSessione *kwin_apri(GError **sbaglio);

uint32_t kwin_nodo(const KwinSessione *sessione);
void kwin_misura(const KwinSessione *sessione, uint32_t *larghezza, uint32_t *altezza);
const char *kwin_nome_uscita(const KwinSessione *sessione);
/* Quante uscite ha annunciato il compositore (con un modo). */
unsigned kwin_quante_uscite(const KwinSessione *sessione);
bool kwin_chiuso(const KwinSessione *sessione);
void kwin_chiudi(KwinSessione *sessione);

/* Il `.desktop` che apre il cancello, scritto dal SERVER (root) all'avvio in
 * `/usr/share/applications/org.kde.remotix.desktop`, con `Exec=` sul binario
 * che sta girando.  false con `perche` scritto. */
bool kwin_scrivi_permesso(char *perche, size_t quanto);
