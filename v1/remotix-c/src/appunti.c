/*
 * appunti — la porta unica verso la clipboard della sessione.
 *
 * Stessa forma di `compositore.c`: qui non c'e' logica, c'e' lo smistamento
 * verso le due implementazioni.  Il perche' di ogni scelta sta in `appunti.h`;
 * le due strade sono `appunti_mutter.c` (D-Bus, sulla sessione di controllo) e
 * `appunti_wlr.c` (`zwlr_data_control_manager_v1`, con una connessione Wayland
 * propria).
 *
 * ⭐ LE DUE STRADE NON SONO DUE VERSIONI DELLA STESSA COSA.  Su Mutter la
 *    clipboard **appartiene alla sessione remota**: senza sessione di controllo
 *    non esiste, e la si accende con `EnableClipboard`.  Su KWin appartiene al
 *    **compositore**: c'e' sempre, non chiede permessi, e continuerebbe a
 *    esistere anche se REMOTIX non ci fosse.  E' la stessa differenza di fondo
 *    che `compositore.h` descrive per la misura dello schermo — chi possiede la
 *    cosa non e' lo stesso — e per questo la porta ha due parametri che valgono
 *    per una sola delle due.
 */
#include "appunti.h"

#include "appunti_mutter.h"
#include "appunti_wlr.h"
#include "registro.h"

struct Appunti
{
	TipoCompositore tipo;
	AppuntiMutter *mutter;
	AppuntiWlr *wlr;
};

Appunti *appunti_apri(TipoCompositore tipo, GDBusConnection *bus, const char *percorso_controllo,
                      GError **sbaglio)
{
	Appunti *appunti = g_new0(Appunti, 1);

	appunti->tipo = tipo;
	if (tipo == COMPOSITORE_KWIN)
	{
		appunti->wlr = appunti_wlr_apri(sbaglio);
		if (!appunti->wlr)
			goto guasto;
	}
	else
	{
		appunti->mutter = appunti_mutter_apri(bus, percorso_controllo, sbaglio);
		if (!appunti->mutter)
			goto guasto;
	}
	return appunti;

guasto:
	g_free(appunti);
	return NULL;
}

void appunti_chiudi(Appunti *appunti)
{
	if (!appunti)
		return;
	g_clear_pointer(&appunti->wlr, appunti_wlr_chiudi);
	g_clear_pointer(&appunti->mutter, appunti_mutter_chiudi);
	g_free(appunti);
}

GStrv appunti_ultimi_tipi(Appunti *appunti)
{
	if (!appunti)
		return NULL;
	return appunti->wlr ? appunti_wlr_ultimi_tipi(appunti->wlr)
	                    : appunti_mutter_ultimi_tipi(appunti->mutter);
}

void appunti_ascolta(Appunti *appunti, AppuntiSuOfferta su_offerta, AppuntiSuRichiesta su_richiesta,
                     gpointer dati)
{
	if (!appunti)
		return;
	if (appunti->wlr)
		appunti_wlr_ascolta(appunti->wlr, su_offerta, su_richiesta, dati);
	else
		appunti_mutter_ascolta(appunti->mutter, su_offerta, su_richiesta, dati);
}

gboolean appunti_offri(Appunti *appunti, const char *const *mime, GError **sbaglio)
{
	if (!appunti)
	{
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_NOT_INITIALIZED, "appunti non aperti");
		return FALSE;
	}
	return appunti->wlr ? appunti_wlr_offri(appunti->wlr, mime, sbaglio)
	                    : appunti_mutter_offri(appunti->mutter, mime, sbaglio);
}

GBytes *appunti_leggi(Appunti *appunti, const char *mime, GError **sbaglio)
{
	if (!appunti)
	{
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_NOT_INITIALIZED, "appunti non aperti");
		return NULL;
	}
	return appunti->wlr ? appunti_wlr_leggi(appunti->wlr, mime, sbaglio)
	                    : appunti_mutter_leggi(appunti->mutter, mime, sbaglio);
}

void appunti_rispondi(Appunti *appunti, guint32 serial, GBytes *dati)
{
	if (!appunti)
		return;
	if (appunti->wlr)
		appunti_wlr_rispondi(appunti->wlr, serial, dati);
	else
		appunti_mutter_rispondi(appunti->mutter, serial, dati);
}
