#include "tastiera.h"

#include <freerdp/input.h>
#include <winpr/input.h>
#include <xkbcommon/xkbcommon.h>

#include "registro.h"

/* Codici evdev, da `linux/input-event-codes.h`. */
#define KEY_LEFTSHIFT 42
#define KEY_RIGHTALT 100

/* Gli scancode dei due tasti che compongono la sequenza del Pausa. */
#define SCANCODE_CTRL 0x1D
#define SCANCODE_NUMLOCK 0x45

/* XKB numera i tasti a partire da 8; evdev da 0. */
#define XKB_A_EVDEV(k) ((uint32_t) (k) - 8)

/* Un carattere Unicode premuto per via Unicode, e cio' che gli è servito. */
typedef struct
{
	uint32_t evdev;
	uint32_t modificatori[TASTIERA_MODIFICATORI_MAX];
	guint n_modificatori;
} TastoUnicode;

struct Tastiera
{
	/* evdev → presente = premuto.  Le posizioni fisiche. */
	GHashTable *premuti;
	/* codepoint → TastoUnicode.  Tenuta a parte perché il rilascio arriva
	 * come carattere, non come posizione. */
	GHashTable *premuti_unicode;

	struct xkb_context *xkb;
	struct xkb_keymap *keymap;
	xkb_layout_index_t gruppo;

	/* La macchina a quattro stati del tasto Pausa. */
	guint stato_pausa;
};

Tastiera *tastiera_nuova(void)
{
	Tastiera *tastiera = g_new0(Tastiera, 1);

	tastiera->premuti = g_hash_table_new(g_direct_hash, g_direct_equal);
	tastiera->premuti_unicode = g_hash_table_new_full(g_direct_hash, g_direct_equal, NULL, g_free);
	tastiera->xkb = xkb_context_new(XKB_CONTEXT_NO_FLAGS);
	if (!tastiera->xkb)
		avviso("contesto xkbcommon non creato: il percorso Unicode non funzionera'");
	return tastiera;
}

void tastiera_libera(Tastiera *tastiera)
{
	if (!tastiera)
		return;
	g_clear_pointer(&tastiera->premuti, g_hash_table_unref);
	g_clear_pointer(&tastiera->premuti_unicode, g_hash_table_unref);
	if (tastiera->keymap)
		xkb_keymap_unref(tastiera->keymap);
	if (tastiera->xkb)
		xkb_context_unref(tastiera->xkb);
	g_free(tastiera);
}

gboolean tastiera_keymap(Tastiera *tastiera, const char *xkb, gsize lunghezza)
{
	struct xkb_keymap *nuova;

	if (!tastiera->xkb)
		return FALSE;

	nuova = xkb_keymap_new_from_buffer(tastiera->xkb, xkb, lunghezza, XKB_KEYMAP_FORMAT_TEXT_V1,
	                                   XKB_KEYMAP_COMPILE_NO_FLAGS);
	if (!nuova)
	{
		avviso("la disposizione consegnata dalla sessione non si compila");
		return FALSE;
	}

	if (tastiera->keymap)
		xkb_keymap_unref(tastiera->keymap);
	tastiera->keymap = nuova;

	/*
	 * Si dichiara quale disposizione è: è la risposta alla questione aperta
	 * n.7, e va scritta nel registro perché è l'informazione che serve quando
	 * l'utente dice «i simboli non corrispondono».
	 */
	{
		xkb_layout_index_t n = xkb_keymap_num_layouts(tastiera->keymap);
		g_autoptr(GString) nomi = g_string_new(NULL);

		for (xkb_layout_index_t i = 0; i < n; i++)
		{
			const char *nome = xkb_keymap_layout_get_name(tastiera->keymap, i);
			g_string_append_printf(nomi, "%s%s", i ? ", " : "", nome ? nome : "?");
		}
		informazione("disposizione della sessione letta da libei: %s", nomi->str);
	}
	return TRUE;
}

gboolean tastiera_ha_keymap(const Tastiera *tastiera)
{
	return tastiera->keymap != NULL;
}

void tastiera_gruppo(Tastiera *tastiera, uint32_t gruppo)
{
	tastiera->gruppo = gruppo;
}

/* ------------------------------------------------------------------ *
 * Posizioni fisiche
 * ------------------------------------------------------------------ */
gboolean tastiera_evdev(uint16_t flags, uint8_t scancode, uint32_t *evdev)
{
	DWORD completo;
	DWORD vkcode;
	DWORD keycode;

	/* La catena di §6.1, nell'ordine: il flag «esteso» va applicato DUE volte,
	 * allo scancode prima e al codice virtuale poi. */
	completo = (flags & KBD_FLAGS_EXTENDED) ? ((DWORD) scancode | KBDEXT) : (DWORD) scancode;
	vkcode = GetVirtualKeyCodeFromVirtualScanCode(completo, WINPR_KBD_TYPE_IBM_ENHANCED);
	if (vkcode == 0)
		return FALSE;
	if (flags & KBD_FLAGS_EXTENDED)
		vkcode |= KBDEXT;

	keycode = GetKeycodeFromVirtualKeyCode(vkcode, WINPR_KEYCODE_TYPE_EVDEV);
	if (keycode == 0)
		return FALSE;

	*evdev = keycode;
	return TRUE;
}

/* ------------------------------------------------------------------ *
 * Il tasto Pausa
 * ------------------------------------------------------------------ */
EsitoPausa tastiera_pausa(Tastiera *tastiera, uint16_t flags, uint8_t scancode, gboolean premuto)
{
	gboolean e1 = (flags & KBD_FLAGS_EXTENDED1) != 0;

	switch (tastiera->stato_pausa)
	{
		case 0:
			if (e1 && scancode == SCANCODE_CTRL && premuto)
			{
				tastiera->stato_pausa = 1;
				return PAUSA_INGOIA;
			}
			return PAUSA_ESTRANEO;
		case 1:
			if (scancode == SCANCODE_NUMLOCK && premuto)
			{
				tastiera->stato_pausa = 2;
				return PAUSA_INGOIA;
			}
			break;
		case 2:
			if (scancode == SCANCODE_CTRL && !premuto)
			{
				tastiera->stato_pausa = 3;
				return PAUSA_INGOIA;
			}
			break;
		case 3:
			if (scancode == SCANCODE_NUMLOCK && !premuto)
			{
				tastiera->stato_pausa = 0;
				return PAUSA_EMETTI;
			}
			break;
		default:
			break;
	}

	/* La sequenza si è rotta: si torna in attesa e questo evento si tratta
	 * normalmente.  Quelli già ingoiati sono persi, ed è il prezzo — lo paga
	 * anche il riferimento. */
	tastiera->stato_pausa = 0;
	return PAUSA_ESTRANEO;
}

/* ------------------------------------------------------------------ *
 * Il conto dei tasti premuti
 * ------------------------------------------------------------------ */
gboolean tastiera_registra(Tastiera *tastiera, uint32_t evdev, gboolean premuto)
{
	gpointer chiave = GUINT_TO_POINTER(evdev);

	if (premuto)
	{
		if (g_hash_table_contains(tastiera->premuti, chiave))
		{
			traccia("pressione ripetuta di %u: scartata", evdev);
			return FALSE;
		}
		g_hash_table_add(tastiera->premuti, chiave);
		return TRUE;
	}

	if (!g_hash_table_remove(tastiera->premuti, chiave))
	{
		traccia("rilascio non appaiato di %u: scartato", evdev);
		return FALSE;
	}
	return TRUE;
}

/* ------------------------------------------------------------------ *
 * Il percorso Unicode
 * ------------------------------------------------------------------ */
static gboolean cerca_tasto(struct xkb_keymap *keymap, xkb_layout_index_t gruppo,
                            xkb_keysym_t voluto, xkb_keycode_t *fuori, xkb_level_index_t *livello)
{
	xkb_keycode_t minimo = xkb_keymap_min_keycode(keymap);
	xkb_keycode_t massimo = xkb_keymap_max_keycode(keymap);

	for (xkb_keycode_t tasto = minimo; tasto <= massimo; tasto++)
	{
		xkb_level_index_t livelli = xkb_keymap_num_levels_for_key(keymap, tasto, gruppo);

		for (xkb_level_index_t l = 0; l < livelli; l++)
		{
			const xkb_keysym_t *simboli = NULL;
			int quanti = xkb_keymap_key_get_syms_by_level(keymap, tasto, gruppo, l, &simboli);

			for (int i = 0; i < quanti; i++)
			{
				if (simboli[i] == voluto)
				{
					*fuori = tasto;
					*livello = l;
					return TRUE;
				}
			}
		}
	}
	return FALSE;
}

/* Il livello si raggiunge tenendo premuti dei modificatori: Maiusc per il 1,
 * AltGr per il 2, entrambi per il 3.  E' quel che fa il riferimento. */
static void modificatori_del_livello(xkb_level_index_t livello, uint32_t *modificatori,
                                     guint *quanti)
{
	*quanti = 0;
	if (livello == 1 || livello == 3)
		modificatori[(*quanti)++] = KEY_LEFTSHIFT;
	if (livello == 2 || livello == 3)
		modificatori[(*quanti)++] = KEY_RIGHTALT;
}

gboolean tastiera_unicode_premi(Tastiera *tastiera, uint32_t codepoint, uint32_t *evdev,
                                uint32_t *modificatori, guint *n_modificatori)
{
	gpointer chiave = GUINT_TO_POINTER(codepoint);
	xkb_keysym_t simbolo;
	xkb_keycode_t tasto;
	xkb_level_index_t livello;
	TastoUnicode *voce;

	if (!tastiera->keymap)
	{
		traccia("carattere U+%04X senza disposizione: scartato", codepoint);
		return FALSE;
	}
	if (g_hash_table_contains(tastiera->premuti_unicode, chiave))
	{
		traccia("carattere U+%04X gia' premuto: scartato", codepoint);
		return FALSE;
	}

	simbolo = xkb_utf32_to_keysym(codepoint);
	if (simbolo == XKB_KEY_NoSymbol)
		return FALSE;
	if (!cerca_tasto(tastiera->keymap, tastiera->gruppo, simbolo, &tasto, &livello))
	{
		/* Non è un difetto: la disposizione della sessione può semplicemente
		 * non avere quel carattere su nessun tasto. */
		diagnostica("nessun tasto produce U+%04X nella disposizione della sessione", codepoint);
		return FALSE;
	}

	voce = g_new0(TastoUnicode, 1);
	voce->evdev = XKB_A_EVDEV(tasto);
	modificatori_del_livello(livello, voce->modificatori, &voce->n_modificatori);
	g_hash_table_insert(tastiera->premuti_unicode, chiave, voce);

	*evdev = voce->evdev;
	*n_modificatori = voce->n_modificatori;
	for (guint i = 0; i < voce->n_modificatori; i++)
		modificatori[i] = voce->modificatori[i];
	return TRUE;
}

gboolean tastiera_unicode_rilascia(Tastiera *tastiera, uint32_t codepoint, uint32_t *evdev,
                                   uint32_t *modificatori, guint *n_modificatori)
{
	gpointer chiave = GUINT_TO_POINTER(codepoint);
	TastoUnicode *voce = g_hash_table_lookup(tastiera->premuti_unicode, chiave);

	if (!voce)
		return FALSE;

	*evdev = voce->evdev;
	*n_modificatori = voce->n_modificatori;
	for (guint i = 0; i < voce->n_modificatori; i++)
		modificatori[i] = voce->modificatori[i];

	g_hash_table_remove(tastiera->premuti_unicode, chiave);
	return TRUE;
}

gboolean tastiera_lucchetti(const Tastiera *tastiera, uint32_t bloccati, gboolean *maiuscole,
                            gboolean *numeri)
{
	xkb_mod_index_t maiusc, num;

	if (!tastiera->keymap)
		return FALSE;

	maiusc = xkb_keymap_mod_get_index(tastiera->keymap, XKB_MOD_NAME_CAPS);
	/* Il BlocNum non ha un nome canonico in xkbcommon: nelle disposizioni
	 * ordinarie è «Mod2», ed è così che lo cercano tutti. */
	num = xkb_keymap_mod_get_index(tastiera->keymap, "Mod2");
	if (maiusc == XKB_MOD_INVALID || num == XKB_MOD_INVALID)
		return FALSE;

	*maiuscole = (bloccati & (1u << maiusc)) != 0;
	*numeri = (bloccati & (1u << num)) != 0;
	return TRUE;
}

/* ------------------------------------------------------------------ *
 * Il rilascio di tutto
 * ------------------------------------------------------------------ */
GArray *tastiera_svuota(Tastiera *tastiera)
{
	GArray *codici = g_array_new(FALSE, FALSE, sizeof(uint32_t));
	GHashTableIter giro;
	gpointer chiave, valore;

	g_hash_table_iter_init(&giro, tastiera->premuti);
	while (g_hash_table_iter_next(&giro, &chiave, NULL))
	{
		uint32_t evdev = GPOINTER_TO_UINT(chiave);
		g_array_append_val(codici, evdev);
	}
	g_hash_table_remove_all(tastiera->premuti);

	g_hash_table_iter_init(&giro, tastiera->premuti_unicode);
	while (g_hash_table_iter_next(&giro, &chiave, &valore))
	{
		TastoUnicode *voce = valore;

		g_array_append_val(codici, voce->evdev);
		for (guint i = 0; i < voce->n_modificatori; i++)
			g_array_append_val(codici, voce->modificatori[i]);
	}
	g_hash_table_remove_all(tastiera->premuti_unicode);

	tastiera->stato_pausa = 0;
	return codici;
}
