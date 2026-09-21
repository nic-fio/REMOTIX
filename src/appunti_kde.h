/*
 * appunti_kde — gli appunti su KDE Plasma, dietro la stessa porta di
 * `appunti.h`.  Chi usa gli appunti non lo chiama: chiama `appunti_*()`, e
 * `appunti.c` passa qui quando il palco e' di KWin (`appunti_apri_kde()`).
 *
 * ⛔ RIPORTATO DA `fondamenta/remotix-c/src/appunti_wlr.c` di v1 (796 righe),
 *    verde l'8 agosto 2026 nei due versi con «àèìòù» (`STUDI.md` §kde): il
 *    protocollo Wayland `zwlr_data_control_manager_v1` (KWin 6.3.6 non ha
 *    `ext_data_control_v1`), che KWin **non** mette dietro il cancello del
 *    `.desktop` (`wayland_server.cpp:386`).
 * ⭐ La forma e' quella di `appunti.c` e NON quella di v1: SOLO TESTO
 *    (`DECISIONI.md` §5-ter.1), letto qui e consegnato gia' letto, lo stesso
 *    tetto (`APPUNTI_TETTO`), la stessa fila dei tipi, la stessa memoria
 *    dell'ultimo testo.
 */
#ifndef REMOTIX_APPUNTI_KDE_H
#define REMOTIX_APPUNTI_KDE_H

#include "appunti.h"

typedef struct AppuntiKde AppuntiKde;

AppuntiKde *appunti_kde_apri(GError **sbaglio);
/* ⭐ FASE 13 — lo stesso protocollo su labwc (XFCE): `zwlr_data_control_manager_v1`
 *    e' di wlroots, e li' siamo in casa sua (`STUDI.md` §xfce §8).  Cambia solo
 *    il nome del compositore nelle righe di registro. */
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
