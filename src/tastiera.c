/*
 * tastiera.c — DALLA LETTERA AL MARTELLETTO.  Anello A5 della fase 4.
 *
 * ⛔ Il contratto sta in `tastiera.h`, che e' del coordinatore: qui si ATTUA,
 *    non si cambia la cucitura.
 *
 * ---------------------------------------------------------------------------
 * IL PROBLEMA, in una riga
 *
 * Sul filo le lettere viaggiano come lettere (`SPECIFICHE.md` §7.3,
 * `DECISIONI.md` §5-bis.6), ma `libei` — l'unico modo di iniettare input in un
 * compositore Wayland — non accetta lettere: accetta POSIZIONI, e a decidere
 * che lettera sia e' il compositore, guardando la disposizione.  Questo file fa
 * il giro all'incontrario.
 *
 * ---------------------------------------------------------------------------
 * ⭐ CHE COSA SI E' RIUSATO DA v1, E CHE COSA NO
 *
 * `fondamenta/remotix-c/src/tastiera.c` faceva gia' questo giro (372 righe, xkbcommon),
 * e la sua struttura e' quella di qui: si scandisce la disposizione tasto per
 * tasto e livello per livello, e si cerca chi produce il simbolo voluto.  Tre
 * cose sono cambiate, e ciascuna per una ragione MISURATA il 14 agosto 2026:
 *
 *  1. ⛔ **i modificatori non si indovinano piu'.**  v1 aveva la regoletta
 *     «livello 1 = Maiusc, livello 2 = AltGr, livello 3 = tutt'e due»
 *     (`fondamenta/.../tastiera.c:251`).  E' vera per le disposizioni ordinarie e falsa
 *     per le altre.  ⭐ `[M]` 14 agosto 2026, misurato su `de(neo)`:
 *
 *       U+00E4 «ä» ⇒ 46                 (nessun modificatore)
 *       U+2192 «→» ⇒ 43 + 77
 *       U+03B1 «α» ⇒ 42 + 43 + 32
 *       U+221A «√» ⇒ 100 + 43 + 17      ⛔ DUE modificatori di livello
 *
 *     ⛔ Due cose che la regoletta di v1 avrebbe sbagliato: su `de(neo)` il
 *        tasto del terzo livello e' il **43** (`<BKSL>`), non il 100 che v1
 *        aveva scritto in testa al file; e il quinto livello non lo nomina
 *        affatto.  Qui la risposta la da' `xkb_keymap_key_get_mods_for_level()`,
 *        cioe' la disposizione stessa.
 *
 *     ⭐ E la stessa misura risponde alla domanda che il contratto pone senza
 *        dirlo — **quattro posizioni bastano?**  Il caso peggiore che si e'
 *        trovato ne usa **tre** (due modificatori piu' il tasto): `de(neo)` e'
 *        la disposizione con piu' livelli che il sistema porti, e ne avanza una;
 *
 *  2. ⛔ **quale TASTO sia un modificatore non si scrive a mano.**  v1 aveva
 *     `#define KEY_LEFTSHIFT 42` e `KEY_RIGHTALT 100` in testa al file.  Qui si
 *     CHIEDE alla disposizione: si preme ogni tasto su una `xkb_state` e si
 *     guarda quale modificatore si accende.  Una tabella scritta a mano e' una
 *     tabella che sbaglia in silenzio quando la disposizione e' insolita;
 *
 *  3. ⛔ **il confronto e' sul CARATTERE, non sul keysym.**  v1 traduceva il
 *     carattere in keysym con `xkb_utf32_to_keysym()` e cercava QUEL keysym.
 *     Ma lo stesso carattere ha due forme di keysym — quella storica
 *     (`XKB_KEY_eacute` = 0x00E9) e quella Unicode (0x010000E9) — e una
 *     disposizione puo' usare l'una o l'altra: cercando una forma sola si
 *     dichiara «non producibile» un carattere che sta li'.  Qui si confronta
 *     `xkb_keysym_to_utf32(simbolo) == carattere`, che copre tutt'e due.
 *
 * ⚠ E una cosa di v1 NON e' stata riportata, perche' non e' di questo file: il
 *   conto di che cosa e' premuto e il rilascio al distacco.  In V2 quello sta
 *   in `input.c` (`input_rilascia_tutto()`, `input.h:98`), e tenerne due copie
 *   sarebbe la forma d'errore «due misure sotto la stessa etichetta».
 *
 * ---------------------------------------------------------------------------
 * ⛔⛔ LA TRAPPOLA CHE QUESTO FILE ESISTE PER NON AVERE
 *
 * Se la disposizione chiesta non si carica e si ripiega su `us` senza dirlo, il
 * sintomo che l'utente descrive e' **«scrive le lettere sbagliate»**, e nessuno
 * lo collega alla disposizione: si va a cercare il difetto nel protocollo, nel
 * browser, nella tastiera del telefono.  `CODER.md` §4.2 — degradare, non
 * fallire, MA IL RIPIEGO SI DICHIARA.  Qui il ripiego non c'e' affatto:
 *
 *   · `[M]` 14 agosto 2026 — `xkbcommon` 1.7.0 **non ripiega da se'**: chiesta
 *     una disposizione che non esiste, `xkb_keymap_new_from_names()` ritorna
 *     NULL e scrive `[XKB-338] Couldn't find file "symbols/..."`.  Il ripiego
 *     poteva metterlo solo il nostro codice, e non c'e';
 *   · ⚠ ma quelle righe **finiscono su stderr e basta**, e chi chiama vede solo
 *     un NULL senza motivo.  ⇒ Qui il registro di `xkbcommon` viene DIROTTATO
 *     (`xkb_context_set_log_fn`) e il primo errore diventa il testo di
 *     `*errore`.  Chi legge il registro trova il motivo, non un NULL;
 *   · ⛔ e `tastiera_disposizione()` porta dentro il nome che la disposizione
 *     COMPILATA da' di se' — «it [Italian]», «us [English (US)]».  Se un giorno
 *     un ripiego entrasse da qualche altra parte, si vedrebbe **nel registro**
 *     come «it [English (US)]», che e' una riga che si legge da sola.
 *
 * `banchi/04-b25-tastiera.c` guarda tutt'e tre, e `banchi/04-b25-lancia.sh` gli
 * mette davanti un'implementazione che ripiega apposta, per certificare che il
 * banco lo vedrebbe.
 */
#include "tastiera.h"

#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <xkbcommon/xkbcommon.h>
#include <xkbcommon/xkbcommon-names.h>

#include "registro.h"

/*
 * ⚠ L'area del registro sta qui e non in `registro.h`: quel file lo condividono
 *   dieci anelli che scrivono nello stesso momento, e una riga aggiunta li'
 *   dentro sarebbe una collisione garantita.  Da unire a `registro.h` quando la
 *   fase chiude — e' una cucitura, e le cuciture le tiene il coordinatore.
 */
#define REG_TASTIERA "tastiera"

/* XKB numera i tasti a partire da 8, evdev da 0 (`RCP.md` §7.3). */
#define EVDEV_DA_XKB(k) ((uint16_t)((k) - 8))

/* Quanti modificatori puo' avere una disposizione.  xkbcommon ne ammette 32. */
#define MAX_MOD 32

struct tastiera
{
	struct xkb_context *ctx;
	struct xkb_keymap *keymap;
	xkb_layout_index_t gruppo;

	/* «it [Italian]»: il chiesto e il compilato nella stessa riga. */
	char nome[192];

	/*
	 * ⛔ modificatore → tasto che lo accende, CHIESTO alla disposizione e non
	 *    scritto a mano.  0 = nessun tasto lo accende da solo.
	 */
	uint16_t tasto_del_mod[MAX_MOD];
	xkb_mod_index_t n_mod;

	/* I due lucchetti, che NON si usano mai per fare una lettera: vedi sotto. */
	xkb_mod_index_t mod_maiuscole, mod_numeri;

	/* Il dirottamento del registro di xkbcommon, durante la compilazione. */
	char primo_errore[256];
	int errori;

	/*
	 * ⭐⭐ DI CHI E' LA RIGA — 27 agosto 2026, il rosso di C9.
	 *
	 * ⛔ Questo modulo scrive righe d'area `tastiera` da DUE processi di specie
	 *    diversa (`registro.h`), e finora le trattava allo stesso modo:
	 *
	 *      · nel FIGLIO va gia' bene: `registro_identita()` e' posata
	 *        all'`exec` e ogni riga del processo la porta;
	 *      · nel PADRE no: `tastiera_apri()` lo chiama `webtransport.c` per
	 *        rispondere a «questa disposizione esiste?» durante l'ATTACCA, e
	 *        li' un processo solo serve TUTTE le sessioni.
	 *
	 * `[M]` 26 agosto 2026, maglia C9, due inquilini vivi insieme: le righe
	 *      «modificatore N: si preferisce…» e «disposizione in vigore: …»
	 *      uscivano DUE VOLTE, identiche parola per parola, ⛔ e non c'era modo
	 *      di dire quale fosse di chi.
	 *
	 * ⇒ Il nome lo porta la TASTIERA, per tutta la durata dell'apertura: cosi'
	 *   lo vedono anche le righe che escono da `xkb_parla()`, che non ha altro
	 *   in mano che questa struttura.
	 * ⚠ Vuoto e' la verita' quando non si sa: `registro.c` allora ripiega
	 *   sull'identita' di PROCESSO, che nel figlio e' quella giusta.  ⇒ La
	 *   `calloc()` lascia questo campo com'e', e la strada del figlio non
	 *   cambia di una virgola.
	 */
	char chi[REG_IDENTITA_MAX + 1];
};

/* ------------------------------------------------------------------ *
 * Il registro di xkbcommon, dirottato
 * ------------------------------------------------------------------ */
static void xkb_parla(struct xkb_context *ctx, enum xkb_log_level livello, const char *fmt,
                      va_list ap)
{
	Tastiera *t = xkb_context_get_user_data(ctx);
	char riga[256];
	size_t n;

	if (!t)
		return;
	vsnprintf(riga, sizeof riga, fmt, ap);
	/* xkbcommon manda la riga con l'a capo in fondo: qui darebbe fastidio. */
	n = strlen(riga);
	while (n && (riga[n - 1] == '\n' || riga[n - 1] == '\r'))
		riga[--n] = 0;

	if (livello <= XKB_LOG_LEVEL_ERROR)
	{
		t->errori++;
		if (!t->primo_errore[0])
			snprintf(t->primo_errore, sizeof t->primo_errore, "%s", riga);
		registro_dettaglio_di(REG_TASTIERA, t->chi, "xkbcommon: %s", riga);
	}
	else
		registro_dettaglio_di(REG_TASTIERA, t->chi, "xkbcommon (avviso): %s", riga);
}

/* ------------------------------------------------------------------ *
 * La forma della stringa — `RCP.md` §4.5
 *
 * ⛔ Non e' pignoleria, ed e' l'unico controllo di questo file che protegge
 *    qualcosa di piu' di una lettera storta: la stringa finisce dentro la
 *    macchina degli `include` di XKB, che apre file per nome.  Un
 *    «../../qualcosa» arriverebbe li' dentro.
 *
 * ⚠ E `RCP.md` §4.5 vuole i due guasti DISTINTI — forma sbagliata e'
 *   `ERRORE_PROTOCOLLO`, disposizione ben formata ma sconosciuta e'
 *   `SESSIONE_NON_SERVIBILE`.  Il contratto di `tastiera.h` da' un solo canale
 *   d'uscita (NULL + testo), quindi i due si distinguono dal PREFISSO del
 *   testo: «forma:» oppure «sconosciuta:».  ⇒ E' una delle cuciture che il
 *   rapporto chiede al coordinatore.
 * ------------------------------------------------------------------ */
static int carattere_ammesso(char c)
{
	return (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || (c >= '0' && c <= '9') ||
	       c == '_' || c == '-';
}

static int forma_valida(const char *s, char *layout, size_t nl, char *variante, size_t nv)
{
	const char *par = strchr(s, '(');
	size_t len_l;

	if (!*s || strlen(s) > 64)
		return 0;

	len_l = par ? (size_t)(par - s) : strlen(s);
	if (len_l == 0 || len_l >= nl)
		return 0;
	for (size_t i = 0; i < len_l; i++)
		if (!carattere_ammesso(s[i]))
			return 0;
	memcpy(layout, s, len_l);
	layout[len_l] = 0;

	variante[0] = 0;
	if (!par)
		return 1;

	{
		const char *chiusa = strchr(par + 1, ')');
		size_t len_v;

		if (!chiusa || chiusa[1] != 0)
			return 0;
		len_v = (size_t)(chiusa - par - 1);
		if (len_v == 0 || len_v >= nv)
			return 0;
		for (size_t i = 0; i < len_v; i++)
			if (!carattere_ammesso(par[1 + i]))
				return 0;
		memcpy(variante, par + 1, len_v);
		variante[len_v] = 0;
	}
	return 1;
}

/* ------------------------------------------------------------------ *
 * ⛔ QUALE TASTO ACCENDE QUALE MODIFICATORE — chiesto, non scritto a mano
 *
 * Si preme ogni tasto della disposizione su una macchina a stati e si guarda
 * quale modificatore si accende.  Se se ne accende esattamente uno, quel tasto
 * e' il modo di ottenerlo.  E' `CODER.md` §3.9 applicata a una tabella: quando
 * un componente puo' rispondere, non si indovina.
 *
 * ⚠ Si tiene il PRIMO tasto che lo accende, e i tasti si scandiscono in ordine
 *   crescente: viene il sinistro prima del destro, che e' l'abitudine di tutti.
 *
 * ---------------------------------------------------------------------------
 * ⛔⛔ E POI C'E' LA PREFERENZA, CHE E' NATA DA UNA MISURA — `[M]` 14 ago 2026
 *
 * La scansione qui sopra, da sola, sceglieva per l'AltGr italiano il codice
 * evdev **84**.  E' una scelta LEGALE — nel file `keycodes/evdev` di XKB il
 * tasto `<LVL3>` sta al codice 92, cioe' evdev 84, e porta `ISO_Level3_Shift`
 * — e il banco la dichiarava verde, perche' battendola esce davvero la «@».
 *
 * ⛔ Ma **evdev 84 e' un buco**: in `linux/input-event-codes.h` fra `KEY_KPDOT`
 *    (83) e `KEY_ZENKAKUHANKAKU` (85) NON C'E' NIENTE — nessuna tastiera al
 *    mondo puo' emettere quel codice.  Funziona perche' il compositore lo
 *    risolve sulla SUA copia della disposizione, ed e' esattamente la forma di
 *    difetto che questo progetto teme: regge finche' i due lati hanno la stessa
 *    tabella, e il giorno che non ce l'hanno smette **senza un errore**.
 *
 * ⇒ Da cui la preferenza: fra i tasti che accendono LO STESSO modificatore, si
 *   sceglie quello che una tastiera vera ha davvero (`<RALT>` = evdev 100).
 *
 * ⚠ E si noti che cosa NON e': non e' la tabella scritta a mano di v1 —
 *   «AltGr e' il tasto 100» — che sbaglia in silenzio sulle disposizioni
 *   insolite.  E' una PREFERENZA fra risposte tutte ottenute chiedendo alla
 *   disposizione: se `ISO_Level3_Shift` stesse altrove, la scansione lo
 *   troverebbe lo stesso e la preferenza non troverebbe niente da preferire.
 * ------------------------------------------------------------------ */
static const uint16_t TASTI_DI_UNA_TASTIERA_VERA[] = {
	42,  /* KEY_LEFTSHIFT */
	54,  /* KEY_RIGHTSHIFT */
	29,  /* KEY_LEFTCTRL */
	97,  /* KEY_RIGHTCTRL */
	56,  /* KEY_LEFTALT */
	100, /* KEY_RIGHTALT — l'AltGr */
	125, /* KEY_LEFTMETA */
	126, /* KEY_RIGHTMETA */
};

/* Quale modificatore accende questo tasto, se ne accende esattamente uno? */
static int un_solo_modificatore(struct xkb_keymap *km, xkb_keycode_t k, int *quale)
{
	struct xkb_state *st = xkb_state_new(km);
	xkb_mod_mask_t attivi;

	if (!st)
		return 0;
	xkb_state_update_key(st, k, XKB_KEY_DOWN);
	attivi = xkb_state_serialize_mods(st, XKB_STATE_MODS_EFFECTIVE);
	xkb_state_unref(st);

	if (!attivi || (attivi & (attivi - 1)) != 0)
		return 0;
	*quale = __builtin_ctz(attivi);
	return 1;
}

static void impara_i_modificatori(Tastiera *t)
{
	xkb_keycode_t min = xkb_keymap_min_keycode(t->keymap);
	xkb_keycode_t max = xkb_keymap_max_keycode(t->keymap);
	uint8_t gia_preferito[MAX_MOD] = {0};
	size_t i;

	t->n_mod = xkb_keymap_num_mods(t->keymap);
	if (t->n_mod > MAX_MOD)
		t->n_mod = MAX_MOD;

	/* 1. si chiede alla disposizione, tasto per tasto. */
	for (xkb_keycode_t k = min; k <= max; k++)
	{
		int quale;
		if (k < 8 || !un_solo_modificatore(t->keymap, k, &quale))
			continue;
		if (quale < (int)t->n_mod && !t->tasto_del_mod[quale])
			t->tasto_del_mod[quale] = EVDEV_DA_XKB(k);
	}

	/*
	 * 2. e poi la preferenza, sopra le risposte gia' ottenute.
	 *
	 * ⚠ `gia_preferito` non e' una precauzione teorica: senza, la lista veniva
	 *   percorsa fino in fondo e per il Maiusc vinceva **il destro** (evdev 54),
	 *   perche' era l'ultimo dei due a passare di qui.  Funzionava — il banco
	 *   diceva verde — ma un registro che dice «Maiusc destro» dove ogni mano
	 *   usa il sinistro e' una riga che fa perdere mezz'ora a chi la legge.
	 *   ⇒ Vince il PRIMO della lista, che e' l'ordine in cui si scrive a mano.
	 */
	for (i = 0; i < sizeof TASTI_DI_UNA_TASTIERA_VERA / sizeof *TASTI_DI_UNA_TASTIERA_VERA; i++)
	{
		uint16_t evdev = TASTI_DI_UNA_TASTIERA_VERA[i];
		xkb_keycode_t k = (xkb_keycode_t)evdev + 8;
		int quale;

		if (k < min || k > max)
			continue;
		if (!un_solo_modificatore(t->keymap, k, &quale))
			continue;
		if (quale >= (int)t->n_mod)
			continue;
		if (gia_preferito[quale] || t->tasto_del_mod[quale] == evdev)
		{
			gia_preferito[quale] = 1;
			continue;
		}
		registro_dettaglio_di(REG_TASTIERA, t->chi,
		                      "modificatore %d: si preferisce il tasto %u a %u (una tastiera "
		                      "vera ha il primo)",
		                      quale, evdev, t->tasto_del_mod[quale]);
		t->tasto_del_mod[quale] = evdev;
		gia_preferito[quale] = 1;
	}
}

/* ------------------------------------------------------------------ *
 * L'apertura
 * ------------------------------------------------------------------ */
Tastiera *tastiera_apri(const char *disposizione, char **errore)
{
	/* ⚠ `NULL` e' la verita' per chi non serve una sessione sola: le righe
	 *   usciranno con l'identita' di PROCESSO, se c'e' (il figlio), e mute se
	 *   non c'e'.  ⛔ Chi non sa tace (`registro.h`). */
	return tastiera_apri_per(disposizione, NULL, errore);
}

Tastiera *tastiera_apri_per(const char *disposizione, const char *chi, char **errore)
{
	Tastiera *t;
	char layout[72], variante[72];
	struct xkb_rule_names nomi;
	const char *chiesta = disposizione ? disposizione : "(quella della sessione)";

	if (errore)
		*errore = NULL;

	t = calloc(1, sizeof *t);
	if (!t)
		return NULL;
	t->mod_maiuscole = XKB_MOD_INVALID;
	t->mod_numeri = XKB_MOD_INVALID;
	/* ⭐ Il nome si posa PRIMA di qualunque riga: la prima che puo' uscire e'
	 *   quella della forma mal formata, tre righe piu' sotto. */
	if (chi && *chi)
		snprintf(t->chi, sizeof t->chi, "%s", chi);

	if (disposizione &&
	    !forma_valida(disposizione, layout, sizeof layout, variante, sizeof variante))
	{
		/* ⛔ `RCP.md` §4.5: questo e' ERRORE_PROTOCOLLO, non SESSIONE_NON_SERVIBILE. */
		registro_dice_di(REG_TASTIERA, t->chi,
		                 "disposizione mal formata, rifiutata senza nemmeno provarci: %.64s",
		                 disposizione);
		if (errore)
			*errore = strdup("forma: non e' un nome di disposizione XKB (RCP.md §4.5)");
		free(t);
		return NULL;
	}

	t->ctx = xkb_context_new(XKB_CONTEXT_NO_FLAGS);
	if (!t->ctx)
	{
		registro_dice_di(REG_TASTIERA, t->chi, "contesto xkbcommon non creato");
		if (errore)
			*errore = strdup("xkbcommon: contesto non creato");
		free(t);
		return NULL;
	}
	xkb_context_set_user_data(t->ctx, t);
	xkb_context_set_log_fn(t->ctx, xkb_parla);
	xkb_context_set_log_level(t->ctx, XKB_LOG_LEVEL_WARNING);

	/*
	 * ⚠ Tutti e cinque i campi si dichiarano, e NULL non va bene: per ogni
	 *   campo NULL `xkbcommon` sostituisce la variabile d'ambiente
	 *   `XKB_DEFAULT_*` e poi un valore di compilazione.  Un
	 *   `XKB_DEFAULT_VARIANT` ereditato dall'ambiente di chi ha avviato il
	 *   servizio cambierebbe la disposizione della sessione senza che nessuno
	 *   l'abbia chiesto — ed e' `CODER.md` §4.5, l'ambiente che si compone e
	 *   non si eredita.
	 *
	 * ⛔ L'eccezione voluta: `disposizione == NULL` vuol dire «quella in vigore
	 *    nella sessione», e li' l'ambiente E' la risposta.  Allora si lascia
	 *    decidere a `xkbcommon` — e lo si SCRIVE nel registro, perche' e' un
	 *    caso in cui non sappiamo che cosa abbiamo caricato finche' non ce lo
	 *    facciamo dire.
	 */
	if (disposizione)
	{
		nomi.rules = "evdev";
		nomi.model = "pc105";
		nomi.layout = layout;
		nomi.variant = variante;
		nomi.options = "";
	}
	else
	{
		nomi.rules = NULL;
		nomi.model = NULL;
		nomi.layout = NULL;
		nomi.variant = NULL;
		nomi.options = NULL;
	}

	t->keymap = xkb_keymap_new_from_names(t->ctx, &nomi, XKB_KEYMAP_COMPILE_NO_FLAGS);
	if (!t->keymap)
	{
		/*
		 * ⛔ QUI STAVA IL RIPIEGO, E NON C'E'.  La tentazione e' una riga: «se
		 *    non si compila, riprova con us».  Il servizio andrebbe avanti —
		 *    `CODER.md` §4.2 lo chiede — ma scrivendo le lettere sbagliate per
		 *    sempre, senza che nessuno sappia perche'.  ⇒ La degradazione
		 *    morbida di `DECISIONI.md` §5-bis.7 e' un'altra cosa: la sessione
		 *    tiene la disposizione che ha gia', e questo lo decide CHI CHIAMA,
		 *    che sa se una sessione c'e' o no.  Qui si fallisce e si dice.
		 */
		const char *perche =
			t->primo_errore[0] ? t->primo_errore : "xkbcommon non ha detto perche'";

		registro_dice_di(REG_TASTIERA, t->chi,
		                 "disposizione «%s» NON caricata, e non si ripiega su nessun'altra: %s",
		                 chiesta, perche);
		if (errore)
		{
			/*
			 * ⛔ La misura sta LARGA APPOSTA.  Questo testo E' il modo in cui il
			 *    ripiego si dichiara, e un messaggio troncato e' un ripiego
			 *    dichiarato a meta': il nome della disposizione (fino a 64 byte,
			 *    `RCP.md` §4.5) piu' la riga di `xkbcommon` (fino a 255) non
			 *    stanno in 320.  ⚠ Rilievo del costruttore del coordinatore, 14
			 *    agosto 2026: gcc lo diceva, e diceva bene.
			 */
			char msg[448];
			snprintf(msg, sizeof msg, "sconosciuta: la disposizione «%s» non si compila (%s)",
			         chiesta, perche);
			*errore = strdup(msg);
		}
		xkb_context_unref(t->ctx);
		free(t);
		return NULL;
	}

	t->gruppo = 0;
	snprintf(t->nome, sizeof t->nome, "%s [%s]", disposizione ? disposizione : "predefinita",
	         xkb_keymap_layout_get_name(t->keymap, t->gruppo)
	             ? xkb_keymap_layout_get_name(t->keymap, t->gruppo)
	             : "senza nome");

	impara_i_modificatori(t);
	t->mod_maiuscole = xkb_keymap_mod_get_index(t->keymap, XKB_MOD_NAME_CAPS);
	t->mod_numeri = xkb_keymap_mod_get_index(t->keymap, XKB_MOD_NAME_NUM);

	/*
	 * ⚠ Se `xkb_keymap_num_layouts()` ne desse piu' d'uno la stringa avrebbe
	 *   nominato piu' disposizioni: `RCP.md` §4.5 non lo permette, ma se un
	 *   giorno lo permettesse (`DECISIONI.md` §5-bis.7 lo tiene aperto) qui si
	 *   userebbe solo la prima, in silenzio.  ⇒ Si dichiara subito.
	 */
	if (xkb_keymap_num_layouts(t->keymap) > 1)
		registro_dice_di(REG_TASTIERA, t->chi,
		                 "disposizione «%s»: la sessione ne porta %u, si usa SOLO la prima",
		                 chiesta, xkb_keymap_num_layouts(t->keymap));

	registro_dice_di(REG_TASTIERA, t->chi, "disposizione in vigore: %s", t->nome);
	return t;
}

/* ------------------------------------------------------------------ *
 * ⛔⛔ LA DISPOSIZIONE COME LA CONSEGNA LA SESSIONE
 *
 * ⭐ Questa funzione e' nata da un rifiuto del mandato, accolto il 14 agosto
 *    2026.  Il contratto diceva `tastiera_apri("it")` — compila una
 *    disposizione dal nome che il client ha negoziato — e poggiava su un
 *    presupposto che nessuno aveva misurato: **che la disposizione che
 *    compiliamo noi sia la stessa con cui il compositore interpretera' i codici
 *    che gli mandiamo.**
 *
 * ⛔ Non lo e', e non lo decidiamo noi: la disposizione della sessione la
 *    sceglie GNOME, e `libei` ce la CONSEGNA col dispositivo tastiera.  Il
 *    danno, in concreto — sessione `it`, client che ha negoziato `us`, l'utente
 *    scrive `[`:
 *
 *      · su `us` la `[` sta sul tasto 26, da sola;
 *      · su `it` sul tasto 26 c'e' la «e` », e la `[` vuole l'AltGr.
 *
 *    ⇒ Mandiamo «26» e sullo schermo compare **«è»**.  Non un carattere
 *      mancante: UN CARATTERE DIVERSO, che `RCP.md` §7.3 vieta.
 *
 * ⚠ E rende falsa la frase di `DECISIONI.md` §5-bis.7 — «una disposizione
 *   vecchia non produce mai caratteri sbagliati, al massimo rende
 *   irraggiungibili un paio di accenti».  Quella frase e' vera **solo** se si
 *   usa la keymap della sessione.  Con la nostra, i caratteri sbagliati escono.
 * ------------------------------------------------------------------ */

/*
 * ⛔ IL CONFRONTO E' SU QUEL CHE LE DUE DISPOSIZIONI **FANNO**, NON SU COME SI
 *    CHIAMANO — ed e' una scelta, non un dettaglio.
 *
 * La strada corta era confrontare i nomi dei gruppi: «Italian» contro «English
 * (US)».  ⭐ `[M]` 14 agosto 2026 il nome **sopravvive** alla serializzazione e
 * al ritorno (`it` → serializzata → ricompilata → ancora «Italian»), quindi
 * avrebbe funzionato.  ⚠ Ma A4 ha misurato che la keymap che Mutter consegna
 * porta `xkb_symbols "(unnamed)"`: il nome della SEZIONE non c'e'.  Il nome del
 * GRUPPO e' un'altra cosa e c'e' — ma sono due campi diversi in un file che non
 * scriviamo noi, e appendere a un'etichetta la riga che dichiara il ripiego
 * significa che il giorno che l'etichetta manca **si grida al ripiego a ogni
 * connessione**.  Un falso allarme su questa riga vale quanto un silenzio.
 *
 * ⇒ Due disposizioni sono la stessa se **producono gli stessi caratteri sugli
 *   stessi tasti**.  E' indipendente dai nomi, e misura la cosa che conta.
 *
 * ---------------------------------------------------------------------------
 * ⛔⛔ E SI CONFRONTANO SOLO I TASTI CHE FANNO UN CARATTERE — misurato, non scelto
 *
 * La prima stesura confrontava **tutto**, e ⛔ **gridava al ripiego anche quando
 * le due disposizioni erano la stessa**.  `[M]` 14 agosto 2026: una keymap `it`
 * serializzata e ricompilata — cioe' il giro esatto che fa la nostra, da Mutter
 * a noi — torna indietro con **due keysym in meno**, su due tasti soli:
 *
 *     tasto evdev 610  XF86KbdInputAssistPrevgroup  ⇒ sparito
 *     tasto evdev 611  XF86KbdInputAssistNextgroup  ⇒ sparito
 *
 * Sono due tasti che **non fanno nessun carattere** e che nessuna tastiera in
 * commercio ha.  ⇒ Con il confronto totale, la riga «RIPIEGO DICHIARATO»
 * sarebbe uscita **a ogni connessione**, compresa quella in cui va tutto bene.
 * Un falso allarme su questa riga vale quanto un silenzio: chi legge il registro
 * impara a saltarla, ed e' finita la sua utilita'.
 *
 * ⚠ E non l'ha trovato il banco — il banco era verde, perche' guardava la
 *   lettera che usciva e la lettera usciva giusta.  L'ho trovato **leggendo il
 *   registro**.  ⇒ Adesso il banco guarda anche la riga (`04-b25-tastiera.c`,
 *   `prova_dichiarazione`), che e' l'unica parte di questo lavoro che l'utente
 *   vedra' quando qualcosa non torna.
 *
 * ⇒ Si confrontano i tasti che producono un carattere.  Due disposizioni che
 *   differiscono solo sui tasti multimediali sono la stessa disposizione **per
 *   quel che questo file fa**, e dirlo sarebbe rumore.
 */
static int fanno_la_stessa_cosa(struct xkb_keymap *a, xkb_layout_index_t ga,
                                struct xkb_keymap *b, xkb_layout_index_t gb)
{
	xkb_keycode_t min = xkb_keymap_min_keycode(a);
	xkb_keycode_t max = xkb_keymap_max_keycode(a);

	if (xkb_keymap_min_keycode(b) > min)
		min = xkb_keymap_min_keycode(b);
	if (xkb_keymap_max_keycode(b) < max)
		max = xkb_keymap_max_keycode(b);

	for (xkb_keycode_t k = min; k <= max; k++)
	{
		xkb_level_index_t na = xkb_keymap_num_levels_for_key(a, k, ga);
		xkb_level_index_t nb = xkb_keymap_num_levels_for_key(b, k, gb);
		xkb_level_index_t quanti = na > nb ? na : nb;

		for (xkb_level_index_t l = 0; l < quanti; l++)
		{
			const xkb_keysym_t *sa = NULL, *sb = NULL;
			int qa = l < na ? xkb_keymap_key_get_syms_by_level(a, k, ga, l, &sa) : 0;
			int qb = l < nb ? xkb_keymap_key_get_syms_by_level(b, k, gb, l, &sb) : 0;
			/* il carattere che quel tasto, a quel livello, fa uscire — 0 = nessuno */
			uint32_t ca = qa > 0 ? xkb_keysym_to_utf32(sa[0]) : 0;
			uint32_t cb = qb > 0 ? xkb_keysym_to_utf32(sb[0]) : 0;

			if (ca != cb)
				return 0;
		}
	}
	return 1;
}

Tastiera *tastiera_apri_da_keymap(const char *testo, size_t lunghezza, const char *negoziata,
                                  char **errore)
{
	Tastiera *t;
	const char *suo;

	if (errore)
		*errore = NULL;

	/*
	 * ⚠ `ei_keymap_get_size()` conta il NUL finale, e chi legge il descrittore
	 *   ne mette uno suo: la lunghezza puo' arrivare con dei NUL in coda.  Si
	 *   tolgono qui, una volta, invece di sperare che il compilatore di
	 *   `xkbcommon` li digerisca — e' l'unica riga che sta fra un descrittore
	 *   altrui e il nostro compilatore.
	 */
	while (lunghezza > 0 && testo && testo[lunghezza - 1] == '\0')
		lunghezza--;

	if (!testo || lunghezza == 0)
	{
		registro_dice(REG_TASTIERA,
		              "la sessione non ha consegnato nessuna disposizione: le LETTERE non si "
		              "possono scrivere");
		if (errore)
			*errore = strdup("sessione: nessuna keymap consegnata da libei");
		return NULL;
	}

	t = calloc(1, sizeof *t);
	if (!t)
		return NULL;
	t->mod_maiuscole = XKB_MOD_INVALID;
	t->mod_numeri = XKB_MOD_INVALID;

	t->ctx = xkb_context_new(XKB_CONTEXT_NO_FLAGS);
	if (!t->ctx)
	{
		registro_dice(REG_TASTIERA, "contesto xkbcommon non creato");
		if (errore)
			*errore = strdup("xkbcommon: contesto non creato");
		free(t);
		return NULL;
	}
	xkb_context_set_user_data(t->ctx, t);
	xkb_context_set_log_fn(t->ctx, xkb_parla);
	xkb_context_set_log_level(t->ctx, XKB_LOG_LEVEL_WARNING);

	t->keymap = xkb_keymap_new_from_buffer(t->ctx, testo, lunghezza, XKB_KEYMAP_FORMAT_TEXT_V1,
	                                       XKB_KEYMAP_COMPILE_NO_FLAGS);
	if (!t->keymap)
	{
		const char *perche =
			t->primo_errore[0] ? t->primo_errore : "xkbcommon non ha detto perche'";

		registro_dice(REG_TASTIERA,
		              "la disposizione consegnata dalla sessione (%zu byte) non si compila: %s",
		              lunghezza, perche);
		if (errore)
		{
			char msg[448];
			snprintf(msg, sizeof msg, "sessione: la keymap di libei non si compila (%s)", perche);
			*errore = strdup(msg);
		}
		xkb_context_unref(t->ctx);
		free(t);
		return NULL;
	}

	t->gruppo = 0;
	suo = xkb_keymap_layout_get_name(t->keymap, t->gruppo);
	snprintf(t->nome, sizeof t->nome, "%s [%s]", negoziata ? negoziata : "della sessione",
	         suo && *suo ? suo : "senza nome");

	impara_i_modificatori(t);
	t->mod_maiuscole = xkb_keymap_mod_get_index(t->keymap, XKB_MOD_NAME_CAPS);
	t->mod_numeri = xkb_keymap_mod_get_index(t->keymap, XKB_MOD_NAME_NUM);

	if (xkb_keymap_num_layouts(t->keymap) > 1)
		registro_dice(REG_TASTIERA,
		              "la sessione porta %u disposizioni: si usa SOLO la prima (%s)",
		              xkb_keymap_num_layouts(t->keymap), suo && *suo ? suo : "senza nome");

	/*
	 * ⛔ IL CONFRONTO, E LA DICHIARAZIONE.  Non si cambia niente — quella della
	 *    sessione VINCE sempre, perche' e' quella che il compositore applica —
	 *    ma se non e' quella che il client ha chiesto **si scrive**, altrimenti
	 *    l'utente vedra' un paio di accenti irraggiungibili senza sapere
	 *    perche' (`CODER.md` §4.2).
	 */
	if (negoziata)
	{
		Tastiera *chiesta = tastiera_apri(negoziata, NULL);

		if (!chiesta)
			registro_dice(REG_TASTIERA,
			              "⚠ il client ha negoziato «%s», che questo sistema non conosce: si usa "
			              "quella della sessione (%s)",
			              negoziata, suo && *suo ? suo : "senza nome");
		else if (!fanno_la_stessa_cosa(t->keymap, t->gruppo, chiesta->keymap, chiesta->gruppo))
			registro_dice(REG_TASTIERA,
			              "⛔ RIPIEGO DICHIARATO: il client ha negoziato «%s», la sessione ha "
			              "un'ALTRA disposizione (%s) e si usa QUELLA — con l'altra uscirebbero "
			              "lettere sbagliate. Qualche carattere restera' irraggiungibile "
			              "(DECISIONI.md §5-bis.7)",
			              negoziata, suo && *suo ? suo : "senza nome");
		else
			registro_dettaglio(REG_TASTIERA, "la sessione ha proprio «%s»: niente da dichiarare",
			                   negoziata);
		tastiera_chiudi(chiesta);
	}

	registro_dice(REG_TASTIERA, "disposizione in vigore (consegnata dalla sessione): %s", t->nome);
	return t;
}

const char *tastiera_disposizione(Tastiera *t)
{
	return t ? t->nome : NULL;
}

/*
 * ⛔⭐ La domanda che evita di chiedere due volte la stessa disposizione — e
 *     che, soprattutto, evita di NON chiederla quando serve.
 *
 * ⚠ Il contratto in `tastiera.h` racconta il difetto che l'ha fatta nascere:
 *   una memoria di «quel che ho chiesto» al posto di «quel che c'e'».  Qui la
 *   risposta viene dalla keymap VERA, quella che `libei` ha consegnato, e si
 *   confronta con quel che la disposizione nominata FAREBBE — non col suo nome.
 *
 * ⛔ E si riusa `fanno_la_stessa_cosa()`, che e' gia' l'unico posto in cui
 *    questo confronto e' scritto: due confronti in due punti diventano due
 *    regole diverse il giorno in cui una cambia (forma E2).
 */
int tastiera_e_questa(Tastiera *t, const char *nome)
{
	Tastiera *altra;
	int uguali;

	if (!t || !t->keymap || !nome || !*nome)
		return -1;

	/* ⚠ `NULL` come canale d'errore: qui non interessa PERCHE' non si compila —
	 *   se non si compila, la domanda non ha risposta, e -1 lo dice. */
	altra = tastiera_apri(nome, NULL);
	if (!altra)
		return -1;

	uguali = fanno_la_stessa_cosa(t->keymap, t->gruppo, altra->keymap, altra->gruppo);
	tastiera_chiudi(altra);
	return uguali ? 1 : 0;
}

void tastiera_chiudi(Tastiera *t)
{
	if (!t)
		return;
	if (t->keymap)
		xkb_keymap_unref(t->keymap);
	if (t->ctx)
		xkb_context_unref(t->ctx);
	free(t);
}

/* ------------------------------------------------------------------ *
 * La scelta della strada
 * ------------------------------------------------------------------ */

/*
 * Da una maschera di modificatori ai tasti da premere.  Ritorna 0 se questa
 * maschera NON e' percorribile, e sono due i casi:
 *
 *  1. ⛔ **chiede un lucchetto**.  `xkb_keymap_key_get_mods_for_level()` per una
 *     lettera risponde «Maiusc, OPPURE BlocMaiusc»: sono tutt'e due modi di
 *     arrivare alla maiuscola.  Ma premere il BlocMaiusc CAMBIA LA SESSIONE —
 *     resta acceso dopo, e la lettera dopo esce maiuscola per conto suo.  Un
 *     modificatore si tiene premuto e si rilascia; un lucchetto no.  ⇒ Le
 *     maschere che nominano BlocMaiusc o BlocNum si scartano: c'e' sempre
 *     l'altra strada;
 *  2. chiede un modificatore che in questa disposizione nessun tasto accende.
 */
static int tasti_della_maschera(Tastiera *t, xkb_mod_mask_t maschera,
                                uint16_t fuori[TASTIERA_MAX_POSIZIONI], size_t *quanti)
{
	*quanti = 0;
	for (xkb_mod_index_t i = 0; i < t->n_mod; i++)
	{
		if (!(maschera & (1u << i)))
			continue;
		if (i == t->mod_maiuscole || i == t->mod_numeri)
			return 0;
		if (!t->tasto_del_mod[i])
			return 0;
		if (*quanti + 1 >= TASTIERA_MAX_POSIZIONI) /* +1: il tasto vero */
			return 0;
		fuori[(*quanti)++] = t->tasto_del_mod[i];
	}
	return 1;
}

int tastiera_posizioni_per(Tastiera *t, uint32_t carattere,
                           uint16_t codici[TASTIERA_MAX_POSIZIONI], size_t *n)
{
	xkb_keycode_t min, max;
	uint16_t migliori[TASTIERA_MAX_POSIZIONI];
	size_t migliori_n = 0;
	int trovato = 0;

	if (!t || !t->keymap || !codici || !n)
		return -1;
	*n = 0;

	/*
	 * ⛔ Fuori intervallo e surrogati NON sono «non producibili»: sono un
	 *    errore di protocollo (`RCP.md` §7.3), e vanno distinti — se tornassero
	 *    0 il chiamante scriverebbe nel registro «l'utente ha chiesto un
	 *    carattere che la disposizione non ha», che e' falso.
	 */
	if (carattere > 0x10FFFF || (carattere >= 0xD800 && carattere <= 0xDFFF))
	{
		registro_dice(REG_TASTIERA, "carattere U+%X fuori dai valori scalari Unicode: rifiutato",
		              carattere);
		return -1;
	}

	min = xkb_keymap_min_keycode(t->keymap);
	max = xkb_keymap_max_keycode(t->keymap);

	for (xkb_keycode_t k = min; k <= max && !(trovato && migliori_n == 1); k++)
	{
		xkb_level_index_t livelli = xkb_keymap_num_levels_for_key(t->keymap, k, t->gruppo);

		if (k < 8)
			continue; /* non avrebbe un codice evdev */

		for (xkb_level_index_t l = 0; l < livelli; l++)
		{
			const xkb_keysym_t *simboli = NULL;
			int quanti_simboli;
			int e_lui = 0;
			xkb_mod_mask_t maschere[8];
			size_t quante_maschere;

			quanti_simboli = xkb_keymap_key_get_syms_by_level(t->keymap, k, t->gruppo, l,
			                                                  &simboli);
			for (int i = 0; i < quanti_simboli; i++)
			{
				/*
				 * ⛔ Il confronto e' sul CARATTERE, non sul keysym: lo stesso
				 *    carattere ha la forma storica e quella Unicode, e una
				 *    disposizione puo' portare l'una o l'altra.
				 */
				uint32_t prodotto = xkb_keysym_to_utf32(simboli[i]);
				if (prodotto && prodotto == carattere)
				{
					e_lui = 1;
					break;
				}
			}
			if (!e_lui)
				continue;

			quante_maschere = xkb_keymap_key_get_mods_for_level(t->keymap, k, t->gruppo, l,
			                                                    maschere,
			                                                    sizeof maschere / sizeof *maschere);
			if (quante_maschere == 0 && l == 0)
			{
				maschere[0] = 0;
				quante_maschere = 1;
			}

			for (size_t m = 0; m < quante_maschere; m++)
			{
				uint16_t via[TASTIERA_MAX_POSIZIONI];
				size_t quanti_mod = 0;

				if (!tasti_della_maschera(t, maschere[m], via, &quanti_mod))
					continue;

				/*
				 * Si tiene la strada piu' corta: meno modificatori si premono,
				 * meno cose possono andare storte, ed e' anche quel che farebbe
				 * una mano.  A parita', vince il tasto piu' basso — che e' il
				 * criterio che tiene fuori il tastierino numerico dai numeri.
				 */
				if (trovato && quanti_mod + 1 >= migliori_n)
					continue;

				memcpy(migliori, via, quanti_mod * sizeof *via);
				migliori[quanti_mod] = EVDEV_DA_XKB(k);
				migliori_n = quanti_mod + 1;
				trovato = 1;
			}
		}
	}

	if (!trovato)
	{
		/*
		 * ⛔⛔ IL CASO CHE `RCP.md` §7.3 OBBLIGA A DICHIARARE: «se una LETTERA
		 *     non e' producibile nella disposizione della sessione, il server
		 *     DEVE scriverlo nel registro e NON DEVE mandare un carattere
		 *     diverso ne' tacere».  La riga sta qui e non nel chiamante perche'
		 *     qui si sa QUALE disposizione e' — che e' l'unica cosa che serve a
		 *     chi legge il registro sei ore dopo.
		 */
		registro_dice(REG_TASTIERA,
		              "U+%04X non e' producibile con la disposizione %s: NON mandato niente "
		              "(RCP.md §7.3)",
		              carattere, t->nome);
		return 0;
	}

	memcpy(codici, migliori, migliori_n * sizeof *migliori);
	*n = migliori_n;
	registro_dettaglio(REG_TASTIERA, "U+%04X ⇒ %zu posizioni, l'ultima e' %u", carattere,
	                   migliori_n, (unsigned)migliori[migliori_n - 1]);
	return 1;
}
