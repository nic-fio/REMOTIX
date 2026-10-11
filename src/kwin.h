/*
 * kwin — the stage on KDE Plasma: the screen stream requested from KWin.
 *
 * ⛔ CARRIED OVER FROM v1's `fondamenta/remotix-c/src/kwin.c` (822 lines), not
 *    copied: what stays here is ⭐ **capture** — the Wayland protocol
 *    `zkde_screencast_unstable_v1` (version 5 on KWin 6.3.6) which, asked
 *    on the `Virtual-0` output, answers with the number of a PipeWire node.  From
 *    the node onwards the road is GNOME's: `capture_start(node)`.
 *    ⭐ And the INPUT channel (increment 3): `org.kde.KWin.EIS.RemoteDesktop.
 *    connectToEIS(7)` ⇒ a libei descriptor, the same kind of channel that
 *    Mutter gives with `ConnectToEIS` — `input.c` does not see the difference.
 *    ⚠ v1's lock state (`org_kde_kwin_keystate`) is NOT here.
 *
 * Its role is that of `mutter.h` on GNOME, and the choice between the two is made by
 * `desktop_session()` ONCE per process — no second way of
 * recognising the desktop.
 *
 * ⛔ THE GATE.  KWin announces `zkde_screencast_unstable_v1` ONLY to a
 *    client whose executable (`/proc/<pid>/exe`, canonical) is in the `Exec=` of
 *    a `.desktop` that declares it in `X-KDE-Wayland-Interfaces`.  `[M]` 18 Sep
 *    2026 in the `kde` box: without that file the global is NOT there (58 others
 *    are), with the file it is — even when written with the session already live.
 *    ⇒ The file is shipped by the PACKAGE (phase 17, §6.5-bis; up to phase 16 the
 *    server wrote it).  At startup the server only VERIFIES it
 *    (`kwin_check_permission()`) against the path of the running
 *    binary: the child is an `execve` of the same binary, so it is the child
 *    that KWin recognises.
 */
#pragma once

#include <glib.h>
#include <stdbool.h>
#include <stdint.h>

typedef struct KwinSession KwinSession;

/* Connects to the user's compositor, finds the output, asks for the stream and
 * waits for the PipeWire node (at most 5 s).  NULL with `mistake` set — and
 * if the gate is closed, `mistake` says which of the two causes to look at. */
KwinSession *kwin_open(GError **mistake);

uint32_t kwin_node(const KwinSession *session);
void kwin_measure(const KwinSession *session, uint32_t *width, uint32_t *height);
const char *kwin_output_name(const KwinSession *session);
/* How many outputs the compositor announced (with a mode). */
unsigned kwin_output_count(const KwinSession *session);
bool kwin_closed(const KwinSession *session);

/* The input channel: KWin's EIS descriptor, requested the first time it is
 * needed and then kept here (like `mutter_eis_fd()`: whoever uses it `dup`s it).
 * -1 with `mistake` set. */
int kwin_eis_fd(KwinSession *session, GError **mistake);
/* The healing: the old context is detached (with the token) and a new one is
 * requested.  Same shape as `mutter_eis_reattach()`. */
int kwin_eis_reattach(KwinSession *session, GError **mistake);
void kwin_close(KwinSession *session);

/* The `.desktop` that opens the gate, owned by the PACKAGE, at
 * `/usr/share/applications/org.kde.remotix.desktop`: it checks that it exists,
 * that `Exec=` leads to the running binary and that it declares
 * `zkde_screencast_unstable_v1`.  ⛔ It is never written.  false with `why`
 * set, starting with the code (RX-KDE-001/002/003) and stating the remedy. */
bool kwin_check_permission(char *why, size_t how_much);

/* The keyboard layout negotiated with the client (`it`, `de(neo)`):
 * written to `kxkbrc` in the session folder and announced to KWin with the
 * signal `org.kde.keyboard /Layouts reloadConfig`.  ⚠ "Requested", not "in
 * force": that is told by the new keymap arriving from EIS.  -1 with `mistake`. */
int kwin_layout(const char *name, GError **mistake);

/* The user's Wayland socket: `WAYLAND_DISPLAY` if it answers, otherwise the
 * first `wayland-N` in `XDG_RUNTIME_DIR` that answers (the child is born with
 * an environment built from scratch).  The clipboard uses it too (`appunti_kde.c`). */
struct wl_display;
struct wl_display *kwin_display_open(char *which, size_t how_much);

/* ------------------------------------------------------------------ *
 * ⭐⭐ THE NESTED KWIN — the desktop takes the window's size at REATTACH
 *      on KDE too (`DECISIONI.md` §10.40, 11 Oct 2026).
 *
 * ⛔ THE WALL: KWin ≤ 6.7 with `--virtual` cannot change the size of its
 *    output, nor create a second one (`VirtualBackend` does not override
 *    `createVirtualOutput()`: `stream_virtual_output` answers «Could not
 *    find output», `STUDI.md` §kde §8.1, `[M]` M7a/M11).  Restarting KWin
 *    with another size kills every non-Qt program (`[M]` 10 Oct 2026:
 *    Firefox and a GTK editor died at the first restart).
 * ⭐ THE ROAD: KWin is born NESTED (`--wayland-display`), as a full-screen
 *    window inside a labwc without a screen that lives in a folder of its
 *    own.  KWin's `WaylandOutput::resize()` follows the size of its window
 *    (`[R]` KWin 6.3.6 `wayland_output.cpp`, `handleConfigure`), and the
 *    window follows labwc's output, whose size `zwlr_output_manager_v1`
 *    changes (the XFCE/LXQt road).  ⇒ To change the size of the desktop is
 *    to change the size of labwc's output: no program is restarted.
 *    ⚠ It is one road for every KWin: on 6.8 it stays the same.
 * ------------------------------------------------------------------ */

/* The command-line mode: `remotix --kwin-nested W H NODE -- <kwin_wayland_wrapper> args`.
 * It is the `ExecStart` of `plasma-kwin_wayland.service` (`sessione.c`,
 * `write_dropin()`): it starts labwc at W×H, waits for it, and becomes
 * (`execvp`) the KWin wrapper with `--wayland-display` added.  NODE is the
 * render node for labwc, `pixman` for drawing in memory, `-` to let wlroots
 * choose.  It returns only on failure. */
int kwin_nested_alive(int argc, char **argv);

/* The host's display: `$XDG_RUNTIME_DIR/remotix-kwin-host/wayland-0`
 * (g_free).  NULL without `XDG_RUNTIME_DIR`. */
char *kwin_host_display(void);

/* Changes the size of the host's output to W×H, and waits (at most
 * `wait_s`) until KWin's output says W×H.  FALSE with `mistake` set when
 * there is no host (a session born before this road: the old fallback holds)
 * or the size did not arrive. */
bool kwin_host_resize(uint32_t width, uint32_t height, double wait_s,
                        GError **mistake);

/* Is there a host to talk to?  (The socket exists and accepts.) */
bool kwin_host_exists(void);


/* ⛔ Before mounting the capture: KWin's output must already have the HOST's size.
 *    At birth labwc configures KWin's window more than once (`[M]` 11 Oct 2026,
 *    Leap 16: first 3822x2036, then full screen 3824x2064), and a capture asked
 *    in between offers a size KWin's stream no longer has — the card route
 *    refused, and the stage fell back to copying in memory for the whole session.
 *    TRUE at once when there is no host. */
bool kwin_host_settle(double wait_s, GError **mistake);
