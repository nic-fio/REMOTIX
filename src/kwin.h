/*
 * kwin — the stage on KDE Plasma: the screen stream requested from KWin.
 *
 * ⛔ CARRIED OVER FROM v1's `fondamenta/remotix-c/src/kwin.c` (822 lines), not
 *    copied: what stays here is ⭐ **capture** — the Wayland protocol
 *    `zkde_screencast_unstable_v1` (version 5 on KWin 6.3.6) which, asked
 *    on the `Virtual-0` output, answers with the number of a PipeWire node.  From
 *    the node onwards the road is GNOME's: `cattura_avvia(nodo)`.
 *    ⭐ And the INPUT channel (increment 3): `org.kde.KWin.EIS.RemoteDesktop.
 *    connectToEIS(7)` ⇒ a libei descriptor, the same kind of channel that
 *    Mutter gives with `ConnectToEIS` — `input.c` does not see the difference.
 *    ⚠ v1's lock state (`org_kde_kwin_keystate`) is NOT here.
 *
 * Its role is that of `mutter.h` on GNOME, and the choice between the two is made by
 * `sessione_desktop()` ONCE per process — no second way of
 * recognising the desktop.
 *
 * ⛔ THE GATE.  KWin announces `zkde_screencast_unstable_v1` ONLY to a
 *    client whose executable (`/proc/<pid>/exe`, canonical) is in the `Exec=` of
 *    a `.desktop` that declares it in `X-KDE-Wayland-Interfaces`.  `[M]` 18 Sep
 *    2026 in the `kde` box: without that file the global is NOT there (58 others
 *    are), with the file it is — even when written with the session already live.
 *    ⇒ The file is shipped by the PACKAGE (phase 17, §6.5-bis; up to phase 16 the
 *    server wrote it).  At startup the server only VERIFIES it
 *    (`kwin_verifica_permesso()`) against the path of the running
 *    binary: the child is an `execve` of the same binary, so it is the child
 *    that KWin recognises.
 */
#pragma once

#include <glib.h>
#include <stdbool.h>
#include <stdint.h>

typedef struct KwinSessione KwinSessione;

/* Connects to the user's compositor, finds the output, asks for the stream and
 * waits for the PipeWire node (at most 5 s).  NULL with `sbaglio` set — and
 * if the gate is closed, `sbaglio` says which of the two causes to look at. */
KwinSessione *kwin_apri(GError **sbaglio);

uint32_t kwin_nodo(const KwinSessione *sessione);
void kwin_misura(const KwinSessione *sessione, uint32_t *larghezza, uint32_t *altezza);
const char *kwin_nome_uscita(const KwinSessione *sessione);
/* How many outputs the compositor announced (with a mode). */
unsigned kwin_quante_uscite(const KwinSessione *sessione);
bool kwin_chiuso(const KwinSessione *sessione);

/* The input channel: KWin's EIS descriptor, requested the first time it is
 * needed and then kept here (like `mutter_eis_fd()`: whoever uses it `dup`s it).
 * -1 with `sbaglio` set. */
int kwin_eis_fd(KwinSessione *sessione, GError **sbaglio);
/* The healing: the old context is detached (with the token) and a new one is
 * requested.  Same shape as `mutter_eis_riattacca()`. */
int kwin_eis_riattacca(KwinSessione *sessione, GError **sbaglio);
void kwin_chiudi(KwinSessione *sessione);

/* The `.desktop` that opens the gate, owned by the PACKAGE, at
 * `/usr/share/applications/org.kde.remotix.desktop`: it checks that it exists,
 * that `Exec=` leads to the running binary and that it declares
 * `zkde_screencast_unstable_v1`.  ⛔ It is never written.  false with `perche`
 * set, starting with the code (RX-KDE-001/002/003) and stating the remedy. */
bool kwin_verifica_permesso(char *perche, size_t quanto);

/* The keyboard layout negotiated with the client (`it`, `de(neo)`):
 * written to `kxkbrc` in the session folder and announced to KWin with the
 * signal `org.kde.keyboard /Layouts reloadConfig`.  ⚠ "Requested", not "in
 * force": that is told by the new keymap arriving from EIS.  -1 with `sbaglio`. */
int kwin_disposizione(const char *nome, GError **sbaglio);

/* The user's Wayland socket: `WAYLAND_DISPLAY` if it answers, otherwise the
 * first `wayland-N` in `XDG_RUNTIME_DIR` that answers (the child is born with
 * an environment built from scratch).  The clipboard uses it too (`appunti_kde.c`). */
struct wl_display;
struct wl_display *kwin_display_apri(char *quale, size_t quanto);
