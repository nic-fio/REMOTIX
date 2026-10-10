/*
 * appunti_kde — the clipboard on KDE Plasma, behind the same door as
 * `appunti.h`.  Clipboard users do not call it: they call `appunti_*()`, and
 * `appunti.c` passes here when the stage is KWin's (`appunti_apri_kde()`).
 *
 * ⛔ CARRIED OVER FROM v1's `fondamenta/remotix-c/src/appunti_wlr.c` (796 lines),
 *    green on 8 August 2026 in both directions with «àèìòù» (`STUDI.md` §kde): the
 *    Wayland protocol `zwlr_data_control_manager_v1` (KWin 6.3.6 does not have
 *    `ext_data_control_v1`), which KWin does **not** put behind the
 *    `.desktop` gate (`wayland_server.cpp:386`).
 * ⭐ The shape is that of `appunti.c` and NOT that of v1: TEXT ONLY
 *    (`DECISIONI.md` §5-ter.1), read here and handed over already read, the same
 *    ceiling (`APPUNTI_TETTO`), the same row of types, the same memory
 *    of the last text.
 */
#ifndef REMOTIX_APPUNTI_KDE_H
#define REMOTIX_APPUNTI_KDE_H

#include "appunti.h"

typedef struct AppuntiKde AppuntiKde;

AppuntiKde *appunti_kde_apri(GError **sbaglio);
/* ⭐ PHASE 13 — the same protocol on labwc (XFCE): `zwlr_data_control_manager_v1`
 *    belongs to wlroots, and there we are in its home (`STUDI.md` §xfce §8).  Only
 *    the compositor's name in the log lines changes. */
AppuntiKde *appunti_kde_apri_wlroots(GError **sbaglio);
void appunti_kde_chiudi(AppuntiKde *appunti);
void appunti_kde_ascolta(AppuntiKde *appunti, AppuntiSuTesto su_testo,
                         AppuntiSuRichiesta su_richiesta, void *dati);
char *appunti_kde_ultimo_testo(AppuntiKde *appunti, size_t *byte);
void appunti_kde_leggi_adesso(AppuntiKde *appunti);
gboolean appunti_kde_offri(AppuntiKde *appunti, GError **sbaglio);
void appunti_kde_rispondi(AppuntiKde *appunti, uint32_t serial, const char *testo,
                          size_t byte);

#endif
