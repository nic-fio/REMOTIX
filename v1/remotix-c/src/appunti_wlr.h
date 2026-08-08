/*
 * appunti_wlr — gli appunti presi con `zwlr_data_control_manager_v1`.
 *
 * L'interfaccia e' quella di `appunti.h`, che resta la porta; qui c'e' solo la
 * dichiarazione di quel che `appunti.c` chiama.
 *
 * ⭐ IL NOME DICE «WLR» E NON «KWIN», E NON E' UN DETTAGLIO.  Il protocollo e' di
 *    wlroots — KWin lo implementa (`wayland_server.cpp:386`), ma lo implementano
 *    anche Sway, Hyprland e tutto quel che sta su wlroots, cioe' i compositori
 *    di XFCE e LXQt che il §3.8 di `SPECIFICA.md` mette nella terza famiglia.
 *    Questo file e' quindi gia' scritto per due dei tre compositori, e chi apre
 *    wlroots non deve rifarlo.
 *
 * ⚠ Su KWin 6.3.6 `ext_data_control_v1` — il successore standardizzato — NON
 *   esiste (`kde.md` §9).  Quando esistera' cambieranno i nomi generati, non la
 *   forma: il posto dove metterlo e' questo.
 */
#pragma once

#include <glib.h>

#include "appunti.h"

typedef struct AppuntiWlr AppuntiWlr;

AppuntiWlr *appunti_wlr_apri(GError **sbaglio);
void appunti_wlr_chiudi(AppuntiWlr *appunti);
GStrv appunti_wlr_ultimi_tipi(AppuntiWlr *appunti);
void appunti_wlr_ascolta(AppuntiWlr *appunti, AppuntiSuOfferta su_offerta,
                         AppuntiSuRichiesta su_richiesta, gpointer dati);
gboolean appunti_wlr_offri(AppuntiWlr *appunti, const char *const *mime, GError **sbaglio);
GBytes *appunti_wlr_leggi(AppuntiWlr *appunti, const char *mime, GError **sbaglio);
void appunti_wlr_rispondi(AppuntiWlr *appunti, guint32 serial, GBytes *dati);
