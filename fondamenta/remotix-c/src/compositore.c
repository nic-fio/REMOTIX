#include "compositore.h"

#include <gio/gio.h>
#include <string.h>

#include "kwin.h"
#include "mutter.h"
#include "registro.h"
#include "sessione.h"

struct Compositore
{
	TipoCompositore tipo;
	MutterSessione *mutter;
	KwinSessione *kwin;
};

const char *compositore_nome(TipoCompositore tipo)
{
	switch (tipo)
	{
		case COMPOSITORE_MUTTER:
			return "Mutter";
		case COMPOSITORE_KWIN:
			return "KWin";
		default:
			return "automatico";
	}
}

gboolean compositore_tipo_da_nome(const char *nome, TipoCompositore *fuori)
{
	if (!nome || !g_ascii_strcasecmp(nome, "auto"))
		*fuori = COMPOSITORE_AUTO;
	else if (!g_ascii_strcasecmp(nome, "mutter") || !g_ascii_strcasecmp(nome, "gnome"))
		*fuori = COMPOSITORE_MUTTER;
	else if (!g_ascii_strcasecmp(nome, "kwin") || !g_ascii_strcasecmp(nome, "kde") ||
	         !g_ascii_strcasecmp(nome, "plasma"))
		*fuori = COMPOSITORE_KWIN;
	else
		return FALSE;
	return TRUE;
}

/* C'e' qualcuno con questo nome sul bus di sessione? */
static gboolean risponde(GDBusConnection *bus, const char *nome)
{
	g_autoptr(GVariant) risposta = g_dbus_connection_call_sync(
	    bus, "org.freedesktop.DBus", "/org/freedesktop/DBus", "org.freedesktop.DBus",
	    "NameHasOwner", g_variant_new("(s)", nome), G_VARIANT_TYPE("(b)"), G_DBUS_CALL_FLAGS_NONE,
	    2000, NULL, NULL);
	gboolean c_e = FALSE;

	if (risposta)
		g_variant_get(risposta, "(b)", &c_e);
	return c_e;
}

/*
 * Chi c'e', chiesto invece che dedotto.
 *
 * ⛔ NON SI GUARDA `XDG_CURRENT_DESKTOP`, e non e' pignoleria: quella variabile
 *    dice che cosa il desktop DICHIARA di essere, e nel nostro caso l'ambiente
 *    lo componiamo noi — quindi risponderebbe quel che ci siamo scritti da
 *    soli.  Il fatto e' chi risponde sul bus.
 *
 * L'ordine conta poco perche' i due nomi non coesistono, ma KWin va provato per
 * primo: su una macchina che ha entrambi i pacchetti installati e' la sessione
 * viva a rispondere, e una sessione Plasma non registra nulla di GNOME.
 */
TipoCompositore compositore_riconosci(TipoCompositore preferito)
{
	g_autoptr(GDBusConnection) bus = NULL;

	if (preferito != COMPOSITORE_AUTO)
	{
		diagnostica("compositore imposto: %s", compositore_nome(preferito));
		return preferito;
	}

	bus = sessione_bus(NULL);
	if (!bus)
	{
		avviso("nessun bus di sessione: presumo Mutter");
		return COMPOSITORE_MUTTER;
	}

	if (risponde(bus, "org.kde.KWin"))
		return COMPOSITORE_KWIN;
	if (risponde(bus, "org.gnome.Mutter.ScreenCast"))
		return COMPOSITORE_MUTTER;

	/*
	 * Nessuno dei due risponde: la sessione grafica non c'e' ancora.  E' il caso
	 * NORMALE al primo collegamento, perche' e' REMOTIX ad avviarla; si sceglie
	 * dal comando con cui la si avviera', che e' l'unica informazione che c'e'.
	 */
	{
		const char *comando = g_getenv("REMOTIX_SESSIONE");

		if (comando && strstr(comando, "plasma"))
			return COMPOSITORE_KWIN;
	}
	return COMPOSITORE_MUTTER;
}

Compositore *compositore_apri(TipoCompositore tipo, GError **sbaglio)
{
	Compositore *comp = g_new0(Compositore, 1);

	comp->tipo = tipo;
	switch (tipo)
	{
		case COMPOSITORE_KWIN:
			comp->kwin = kwin_apri(sbaglio);
			if (!comp->kwin)
				goto guasto;
			break;
		default:
			comp->tipo = COMPOSITORE_MUTTER;
			comp->mutter = mutter_apri(sbaglio);
			if (!comp->mutter)
				goto guasto;
			break;
	}
	return comp;

guasto:
	g_free(comp);
	return NULL;
}

TipoCompositore compositore_tipo(const Compositore *comp)
{
	return comp ? comp->tipo : COMPOSITORE_AUTO;
}

uint32_t compositore_nodo(const Compositore *comp)
{
	if (!comp)
		return 0;
	return comp->kwin ? kwin_nodo(comp->kwin) : mutter_nodo(comp->mutter);
}

void compositore_misura_imposta(const Compositore *comp, uint32_t *larghezza, uint32_t *altezza)
{
	*larghezza = 0;
	*altezza = 0;
	if (comp && comp->kwin)
		kwin_misura(comp->kwin, larghezza, altezza);
}

int compositore_prendi_fd_eis(Compositore *comp)
{
	if (!comp)
		return -1;
	if (comp->mutter)
		return mutter_prendi_fd_eis(comp->mutter);
	return kwin_prendi_fd_eis(comp->kwin);
}

void compositore_lucchetti_ascolta(Compositore *comp, CompositoreLucchetti su_cambio, gpointer dati)
{
	if (!comp)
		return;
	if (comp->kwin)
	{
		kwin_lucchetti_ascolta(comp->kwin, su_cambio, dati);
		return;
	}
	/*
	 * Su Mutter non serve: lo stato vero arriva da libei con
	 * `EI_EVENT_KEYBOARD_MODIFIERS`, ed e' una delle quattro cose per cui libei
	 * fu scelto al posto dei metodi `Notify*` (§5.8 di SPECIFICA.md).  E' KWin
	 * l'eccezione: li' quell'evento non arriva mai, perche'
	 * `eis_device_keyboard_send_xkb_modifiers` non e' chiamato da nessuna parte.
	 */
}

const char *compositore_mapping_id(const Compositore *comp)
{
	if (comp && comp->mutter)
		return mutter_mapping_id(comp->mutter);
	return NULL;
}

const char *compositore_percorso_controllo(const Compositore *comp)
{
	if (comp && comp->mutter)
		return mutter_percorso_controllo(comp->mutter);
	return NULL;
}

gboolean compositore_finito(const Compositore *comp)
{
	if (!comp)
		return TRUE;
	if (comp->kwin)
		return kwin_chiuso(comp->kwin);
	return FALSE;
}

gboolean compositore_cursore_nell_immagine(TipoCompositore tipo)
{
	/*
	 * ⛔ FALSO ANCHE SU KWIN, ADESSO — e la ragione non e' che il cursore sia
	 *    uscito dall'immagine: e' che dentro l'immagine e' TRASPARENTE.
	 *    `sessione.c` gli mette un tema con un cursore 1x1 ad alfa zero, quindi
	 *    quel che KWin compone non si vede e il puntatore torna a essere quello
	 *    del client, come su Mutter.
	 *
	 * ⚠ Il che rende questa funzione sempre falsa.  Resta scritta, e con essa il
	 *   ragionamento, perche' il giorno in cui un compositore disegnasse il
	 *   cursore nell'immagine SENZA lasciarci cambiare il tema, la risposta e'
	 *   qui e non va ritrovata da capo: nascondere quello del client con
	 *   `SYSPTR_NULL`, pagando la latenza del video.
	 */
	(void) tipo;
	return FALSE;
}

void compositore_chiudi(Compositore *comp)
{
	if (!comp)
		return;
	g_clear_pointer(&comp->kwin, kwin_chiudi);
	g_clear_pointer(&comp->mutter, mutter_chiudi);
	g_free(comp);
}
