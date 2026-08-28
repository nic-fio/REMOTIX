/*
 * appunti_mutter — gli appunti come li espone Mutter: sulla sessione di
 * controllo, in D-Bus.
 *
 * L'interfaccia e le trappole sono documentate in `appunti.h`, che e' la porta:
 * qui c'e' solo la dichiarazione di quel che `appunti.c` chiama.  Il perche' di
 * ogni scelta — l'eco di `SelectionOwnerChanged`, il thread proprio per i
 * segnali, il fatto che gli appunti non si spengano mai — sta li' e non si
 * duplica.
 */
#pragma once

#include <gio/gio.h>
#include <glib.h>

#include "appunti.h"

typedef struct AppuntiMutter AppuntiMutter;

AppuntiMutter *appunti_mutter_apri(GDBusConnection *bus, const char *percorso_controllo,
                                   GError **sbaglio);
void appunti_mutter_chiudi(AppuntiMutter *appunti);
GStrv appunti_mutter_ultimi_tipi(AppuntiMutter *appunti);
void appunti_mutter_ascolta(AppuntiMutter *appunti, AppuntiSuOfferta su_offerta,
                            AppuntiSuRichiesta su_richiesta, gpointer dati);
gboolean appunti_mutter_offri(AppuntiMutter *appunti, const char *const *mime, GError **sbaglio);
GBytes *appunti_mutter_leggi(AppuntiMutter *appunti, const char *mime, GError **sbaglio);
void appunti_mutter_rispondi(AppuntiMutter *appunti, guint32 serial, GBytes *dati);
