/*
 * wlr_input.c — la tastiera e il puntatore virtuali su wlroots.  Il perché e la
 * divisione del lavoro con `input.c` stanno in `wlr_input.h`.
 *
 * ⛔⛔ LE CINQUE TRAPPOLE SILENZIOSE di `STUDI.md` §xfce §7.2, e dove stanno qui:
 *
 *   1. la rotella vuole scatti da ±1, non ±120      → `wlr_input_rotella()`
 *   2. `value` non deve mai essere 0                → idem: si manda solo con
 *                                                      almeno uno scatto
 *   3. senza `frame` non arriva niente              → `cornice()` dopo OGNI
 *                                                      gesto del puntatore
 *   4. i modificatori li mandiamo noi, sempre       → `manda_modificatori()`
 *   5. `wlr_pointer_finish()` non rilascia i pulsanti → `wlr_input_chiudi()`
 *
 * ⚠ Tutte e cinque sono `[R]` nello studio (wlroots 0.18.2, labwc 0.8.3, le
 *   versioni di Trixie).  ⭐ `[M]` 21 set 2026 SUL PORTATILE — labwc 0.8.3
 *   headless in una cartella privata, testimone `banchi/06-b33-testimone.c`,
 *   ⛔ NON la macchina di prova e NON una sessione XFCE intera:
 *     · Maiusc+A: il testimone vede `MODIFICATORI premuti 1` PRIMA del tasto 30;
 *       la lettera `@` (us) arriva come Maiusc + tasto 3;
 *     · BlocMaiusc ripetuto tre volte: blocca UNA volta, la seconda pressione
 *       vera sblocca;
 *     · rotella +120 dal client ⇒ `v120 -120`, `valore -15` (su); +60 +60 ⇒ uno
 *       scatto solo; orizzontale +120 ⇒ `+120`;
 *     · puntatore 640,360 e 1279,719 esatti; 5000,5000 saturato; tela 1920×1080
 *       su uscita 1280×720 ⇒ 480,270 arriva a 320,180 (la proporzione tiene);
 *     · doppio `press` + un `release` ⇒ il testimone vede UNA coppia;
 *     · disposizione `de` ⇒ keymap nuova al testimone e `z` sul tasto 21;
 *     · chiusura con Ctrl e sinistro giù ⇒ il testimone vede i due rilasci.
 *   ⚠ Quel che NON è misurato: una sessione XFCE vera (pannello, applicazioni
 *     GTK che guardano la cornice), le scorciatoie di labwc (§7.5), e il
 *     percorso intero dal browser.
 */
#include "wlr_input.h"

#include "registro.h"

#include "virtual-keyboard-unstable-v1-client-protocol.h"
#include "wlr-virtual-pointer-unstable-v1-client-protocol.h"

#include <errno.h>
#include <gio/gio.h>
#include <poll.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>
#include <wayland-client.h>
#include <xkbcommon/xkbcommon.h>

/* ⚠ La stessa area di `input.c`: chi legge il registro cerca l'input sotto una
 *   parola sola, non sotto il nome del modulo che lo trasporta. */
#define AREA "input"

/* ⛔ Il tetto dei codici, lo stesso di `input.c` (`MAX_TASTO`/`MAX_BOTTONE`):
 *    evdev arriva fino a `KEY_MAX` = 0x2ff. */
#define MAX_CODICE 0x300u

/*
 * ⭐ Il valore di uno scatto.  wayvnc usa **15.0**, «valore magico misurato con
 *    `wev`» (§7.2 trappola 2), ed è il passo che libinput dà a una rotella
 *    vera: le applicazioni che guardano il `value` e non il `discrete` scorrono
 *    come con un mouse.  ⛔ Mai zero: con `value == 0` wlroots manda un
 *    `axis_stop` e lo scatto sparisce (`wlr_seat_pointer.c:369-391`).
 */
#define VALORE_SCATTO 15.0

/* ⚠ Il tetto delle attese sincrone (apertura, riattacco).  Chi le fa è il ciclo
 *   del figlio: un compositore muto non deve fermarlo più di così. */
#define ATTESA_US (2 * G_USEC_PER_SEC)

struct WlrInput {
	struct wl_display *display;
	struct wl_registry *registry;
	struct wl_seat *seat;
	struct wl_output *uscita;
	struct zwp_virtual_keyboard_manager_v1 *gestore_tastiera;
	struct zwlr_virtual_pointer_manager_v1 *gestore_puntatore;
	uint32_t versione_puntatore;

	struct zwp_virtual_keyboard_v1 *tastiera;
	struct zwlr_virtual_pointer_v1 *puntatore;

	/* ⭐ La SPIA: una `wl_keyboard` presa una volta sola, per farsi consegnare
	 *    la keymap della sessione (§7.4) — e poi rilasciata. */
	struct wl_keyboard *spia;
	char *keymap_sessione;
	size_t keymap_sessione_len;

	/* ⛔ La keymap IN VIGORE sulla nostra tastiera, e lo stato che la segue. */
	struct xkb_context *ctx;
	struct xkb_keymap *keymap;
	struct xkb_state *stato;
	char *keymap_testo; /* con lo zero finale; `keymap_len` senza */
	size_t keymap_len;
	char *keymap_origine;
	bool keymap_mandata;

	/* L'ultimo stato dei modificatori MANDATO — per non rimandarlo uguale. */
	uint32_t mod_giu, mod_agganciati, mod_bloccati, gruppo;

	/* ⛔ Quel che QUESTO dispositivo ha premuto: serve a scartare i doppioni.
	 *    ⚠ Non è il conto di `RCP.md` §11: quello è di `input.c`. */
	uint8_t tasti_giu[MAX_CODICE / 8];
	uint8_t bottoni_giu[MAX_CODICE / 8];

	/* ⛔ Gli accumulatori della rotella, uno per asse: i mezzi scatti non si
	 *    perdono, si sommano al prossimo (weston fa lo stesso, §7.2). */
	int32_t resto_verticale, resto_orizzontale;

	bool caduto;
	bool caduta_detta;
};

/* ------------------------------------------------------------------------- */

static bool bit(const uint8_t *m, uint32_t n)
{
	return (m[n / 8u] & (uint8_t)(1u << (n % 8u))) != 0;
}

static void metti_bit(uint8_t *m, uint32_t n, bool acceso)
{
	if (acceso)
		m[n / 8u] |= (uint8_t)(1u << (n % 8u));
	else
		m[n / 8u] &= (uint8_t)~(1u << (n % 8u));
}

/* ⚠ Il tempo del protocollo è in millisecondi e può girare: è un'etichetta per
 *   le applicazioni, non un orologio su cui si fanno conti. */
static uint32_t ora_ms(void)
{
	return (uint32_t)(g_get_monotonic_time() / 1000);
}

/*
 * ⛔ IL FILO CADUTO SI DICE UNA VOLTA, E CON LA CAUSA.  Un errore di protocollo
 *    (il nostro: `no_keymap`, un asse sbagliato) e un compositore morto hanno
 *    lo stesso sintomo — la connessione non risponde più — e la differenza la
 *    sa solo `wl_display_get_protocol_error()`.
 */
static void segna_caduta(WlrInput *w, const char *dove)
{
	const struct wl_interface *interfaccia = NULL;
	uint32_t id = 0;
	uint32_t codice = 0;
	int err;

	w->caduto = true;
	if (w->caduta_detta)
		return;
	w->caduta_detta = true;

	err = w->display ? wl_display_get_error(w->display) : 0;
	if (err == EPROTO)
		codice = wl_display_get_protocol_error(w->display, &interfaccia, &id);
	if (err == EPROTO)
		registro_dice(AREA,
		              "⛔⛔ wlroots: il compositore ha CHIUSO la connessione dell'input "
		              "per un ERRORE DI PROTOCOLLO nostro (%s, oggetto %s@%u, codice %u) — "
		              "è un difetto di REMOTIX, non del desktop.  ⚠ Da adesso i tasti "
		              "rimasti giù li rilascia il compositore, i PULSANTI no (§7.2 n.5)",
		              dove, interfaccia ? interfaccia->name : "?", id, codice);
	else
		registro_dice(AREA,
		              "⛔ wlroots: la connessione dell'input è CADUTA (%s: %s) — il "
		              "compositore se n'è andato o ha chiuso il socket",
		              dove, err ? g_strerror(err) : "senza errore dichiarato");
}

/*
 * ⛔ Si spedisce SUBITO: le richieste Wayland restano nel buffer del client
 *    finché qualcuno non fa `flush`, e un tasto nel buffer è latenza regalata
 *    all'utente — proprio sul percorso che `CODER.md` §1-bis misura.
 * ⚠ `EAGAIN` non è una caduta: il socket è pieno, e il prossimo giro di
 *   `wlr_input_gira()` riprova.
 */
static int spedisci(WlrInput *w)
{
	if (wl_display_flush(w->display) < 0 && errno != EAGAIN) {
		segna_caduta(w, "flush");
		return -1;
	}
	return 0;
}

/*
 * Un giro della pompa con scadenza — la stessa forma di `pompa()` in
 * `wlroots.c`, e per la stessa ragione: `wl_display_roundtrip()` aspetta senza
 * tetto, e un compositore muto fermerebbe il figlio per sempre.
 */
static bool pompa(WlrInput *w, gint64 scadenza)
{
	struct pollfd pfd;
	gint64 resta;
	int r;

	while (wl_display_prepare_read(w->display) != 0) {
		if (wl_display_dispatch_pending(w->display) < 0) {
			segna_caduta(w, "dispatch_pending");
			return false;
		}
	}
	if (wl_display_flush(w->display) < 0 && errno != EAGAIN) {
		wl_display_cancel_read(w->display);
		segna_caduta(w, "flush");
		return false;
	}
	resta = (scadenza - g_get_monotonic_time()) / 1000;
	if (resta < 0)
		resta = 0;
	pfd.fd = wl_display_get_fd(w->display);
	pfd.events = POLLIN;
	pfd.revents = 0;
	r = poll(&pfd, 1, (int)resta);
	if (r <= 0) {
		wl_display_cancel_read(w->display);
		if (r < 0 && errno != EINTR) {
			segna_caduta(w, "poll");
			return false;
		}
		return true;
	}
	if (wl_display_read_events(w->display) < 0) {
		segna_caduta(w, "read_events");
		return false;
	}
	if (wl_display_dispatch_pending(w->display) < 0) {
		segna_caduta(w, "dispatch");
		return false;
	}
	return true;
}

static void sincronia_fatta(void *dati, struct wl_callback *cb, uint32_t x)
{
	bool *fatto = dati;

	*fatto = true;
	wl_callback_destroy(cb);
}

static const struct wl_callback_listener ASCOLTO_SINCRONIA = {
	.done = sincronia_fatta,
};

/* Un `roundtrip` con il tetto.  false = caduto o scaduto. */
static bool sincronizza(WlrInput *w, gint64 scadenza)
{
	bool fatto = false;
	struct wl_callback *cb = wl_display_sync(w->display);

	wl_callback_add_listener(cb, &ASCOLTO_SINCRONIA, &fatto);
	while (!fatto) {
		if (!pompa(w, scadenza)) {
			wl_callback_destroy(cb);
			return false;
		}
		if (!fatto && g_get_monotonic_time() >= scadenza) {
			/* ⚠ La callback resta viva e arriverà a un `fatto` che non esiste
			 *   più: le si toglie l'ascoltatore distruggendola. */
			wl_callback_destroy(cb);
			return false;
		}
	}
	return true;
}

/* ------------------------------------------------------------------------- */
/* La spia: la keymap della sessione, copiata dal filo (§7.4). */

static void spia_keymap(void *dati, struct wl_keyboard *k, uint32_t formato, int32_t fd,
                        uint32_t misura)
{
	WlrInput *w = dati;
	void *mappa;

	/* ⛔ Il descrittore è NOSTRO appena arriva, e si chiude su ogni strada: la
	 *    keymap labwc la rimanda a ogni cambio di tastiera, e un descrittore
	 *    perso a ogni tasto finisce i descrittori del figlio in un'ora. */
	if (formato != WL_KEYBOARD_KEYMAP_FORMAT_XKB_V1 || misura == 0 || w->keymap_sessione) {
		close(fd);
		return;
	}
	mappa = mmap(NULL, misura, PROT_READ, MAP_PRIVATE, fd, 0);
	close(fd);
	if (mappa == MAP_FAILED)
		return;
	/* ⚠ Il testo è terminato dallo zero DENTRO `misura` (è il protocollo), ma
	 *   non ci si fida: si copia e si termina noi. */
	w->keymap_sessione = g_malloc0(misura + 1);
	memcpy(w->keymap_sessione, mappa, misura);
	w->keymap_sessione_len = strnlen(w->keymap_sessione, misura);
	munmap(mappa, misura);
}

static void spia_entra(void *d, struct wl_keyboard *k, uint32_t s, struct wl_surface *sf,
                       struct wl_array *tasti) {}
static void spia_esce(void *d, struct wl_keyboard *k, uint32_t s, struct wl_surface *sf) {}
static void spia_tasto(void *d, struct wl_keyboard *k, uint32_t s, uint32_t t, uint32_t c,
                       uint32_t st) {}
/* ⚠ Qui arriverebbero i LUCCHETTI veri (§7.3: labwc li manda a tutti, anche
 *   senza fuoco).  ⛔ Non si leggono in questo incremento, ed è detto: la spia
 *   si rilascia subito, e l'anello di retroazione coi nostri `modifiers` che
 *   §7.3 teme non si apre nemmeno. */
static void spia_modificatori(void *d, struct wl_keyboard *k, uint32_t s, uint32_t g,
                              uint32_t a, uint32_t b, uint32_t gr) {}
static void spia_ripetizione(void *d, struct wl_keyboard *k, int32_t r, int32_t ri) {}

static const struct wl_keyboard_listener ASCOLTO_SPIA = {
	.keymap = spia_keymap,
	.enter = spia_entra,
	.leave = spia_esce,
	.key = spia_tasto,
	.modifiers = spia_modificatori,
	.repeat_info = spia_ripetizione,
};

static void seat_capacita(void *dati, struct wl_seat *s, uint32_t capacita)
{
	WlrInput *w = dati;

	/* ⚠ Una volta sola: dopo che la nostra tastiera virtuale esiste, il seat
	 *   ridice le sue capacità, e una seconda spia leggerebbe la NOSTRA keymap
	 *   credendola della sessione. */
	if ((capacita & WL_SEAT_CAPABILITY_KEYBOARD) && !w->spia && !w->keymap_sessione &&
	    !w->tastiera) {
		w->spia = wl_seat_get_keyboard(s);
		wl_keyboard_add_listener(w->spia, &ASCOLTO_SPIA, w);
	}
}

static void seat_nome(void *d, struct wl_seat *s, const char *nome) {}

static const struct wl_seat_listener ASCOLTO_SEAT = {
	.capabilities = seat_capacita,
	.name = seat_nome,
};

static void spia_via(WlrInput *w)
{
	if (!w->spia)
		return;
	/* ⚠ `release` esiste da wl_seat v3; prima c'è solo la distruzione lato
	 *   client, e il compositore continua a mandare eventi a un oggetto che
	 *   `libwayland` scarta (chiudendone i descrittori). */
	if (wl_keyboard_get_version(w->spia) >= WL_KEYBOARD_RELEASE_SINCE_VERSION)
		wl_keyboard_release(w->spia);
	else
		wl_keyboard_destroy(w->spia);
	w->spia = NULL;
}

/* ------------------------------------------------------------------------- */
/* I global. */

static void registro_global(void *dati, struct wl_registry *reg, uint32_t nome,
                            const char *interfaccia, uint32_t versione)
{
	WlrInput *w = dati;

	if (g_strcmp0(interfaccia, wl_seat_interface.name) == 0) {
		/* ⛔ Il PRIMO seat.  labwc ne ha uno (`seat0`) e non crea
		 *    `ext_transient_seat_v1` (§7.6): si inietta in quello
		 *    dell'utente, e su XFCE non c'è scelta. */
		if (!w->seat) {
			uint32_t v = versione < 5 ? versione : 5;

			w->seat = wl_registry_bind(reg, nome, &wl_seat_interface, v);
			wl_seat_add_listener(w->seat, &ASCOLTO_SEAT, w);
		}
	} else if (g_strcmp0(interfaccia, wl_output_interface.name) == 0) {
		/* ⚠ La PRIMA uscita, come `wlroots.c`: è quella che si cattura, ed è
		 *   quella su cui si chiede di mappare il puntatore. */
		if (!w->uscita)
			w->uscita = wl_registry_bind(reg, nome, &wl_output_interface, 1);
	} else if (g_strcmp0(interfaccia, zwp_virtual_keyboard_manager_v1_interface.name) == 0) {
		w->gestore_tastiera =
			wl_registry_bind(reg, nome, &zwp_virtual_keyboard_manager_v1_interface, 1);
	} else if (g_strcmp0(interfaccia, zwlr_virtual_pointer_manager_v1_interface.name) == 0) {
		uint32_t v = versione < 2 ? versione : 2;

		w->versione_puntatore = v;
		w->gestore_puntatore =
			wl_registry_bind(reg, nome, &zwlr_virtual_pointer_manager_v1_interface, v);
	}
}

static void registro_via(void *d, struct wl_registry *r, uint32_t nome) {}

static const struct wl_registry_listener ASCOLTO_REGISTRO = {
	.global = registro_global,
	.global_remove = registro_via,
};

/* ------------------------------------------------------------------------- */
/* La keymap e i modificatori. */

/*
 * ⛔⛔ I MODIFICATORI — la trappola 4, ed è quella dove si sbaglia in silenzio.
 *
 * `[R]` `wlr_virtual_keyboard_v1.c:92`: wlroots costruisce l'evento del tasto
 * con `update_state = false`, cioè **non** aggiorna il suo `xkb_state`.  ⇒ Il
 * Maiusc premuto arriva alle applicazioni come tasto, ma lo stato dei
 * modificatori resta zero: **Shift+A dà `a`**, Ctrl+C non copia, e nessun
 * errore da nessuna parte.
 *
 * ⇒ Lo stato lo teniamo NOI, con un `xkb_state` sulla stessa keymap che abbiamo
 *   mandato, e dopo ogni tasto si manda `modifiers` se è cambiato.  ⭐ È la
 *   forma di wayvnc: tasto prima, modificatori dopo — l'applicazione vede
 *   «premuto Maiusc» e poi «adesso Maiusc è giù», come con una tastiera vera.
 *
 * ⚠ `forza`: dopo una keymap nuova si manda comunque, perché il compositore ha
 *   appena buttato il suo stato e il nostro «ultimo mandato» non vale più.
 */
static void manda_modificatori(WlrInput *w, bool forza)
{
	uint32_t giu, agganciati, bloccati, gruppo;

	if (!w->stato || !w->tastiera)
		return;
	giu = xkb_state_serialize_mods(w->stato, XKB_STATE_MODS_DEPRESSED);
	agganciati = xkb_state_serialize_mods(w->stato, XKB_STATE_MODS_LATCHED);
	bloccati = xkb_state_serialize_mods(w->stato, XKB_STATE_MODS_LOCKED);
	gruppo = xkb_state_serialize_layout(w->stato, XKB_STATE_LAYOUT_EFFECTIVE);
	if (!forza && giu == w->mod_giu && agganciati == w->mod_agganciati &&
	    bloccati == w->mod_bloccati && gruppo == w->gruppo)
		return;
	w->mod_giu = giu;
	w->mod_agganciati = agganciati;
	w->mod_bloccati = bloccati;
	w->gruppo = gruppo;
	zwp_virtual_keyboard_v1_modifiers(w->tastiera, giu, agganciati, bloccati, gruppo);
}

/*
 * Manda `km` come keymap della nostra tastiera, e rifà lo stato su di lei.
 *
 * ⛔ Il testo che si manda è `xkb_keymap_get_as_string()` della keymap GIÀ
 *    COMPILATA, con lo zero finale dentro la misura: wlroots la rilegge con
 *    `xkb_keymap_new_from_string()`, che vuole il terminatore — e una keymap che
 *    non si compila dall'altra parte non torna un errore gentile, chiude la
 *    connessione.
 */
static int metti_keymap(WlrInput *w, struct xkb_keymap *km, const char *origine,
                        GError **sbaglio)
{
	char *testo;
	size_t len;
	int fd;
	struct xkb_state *stato;

	if (w->caduto || !w->tastiera) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_BROKEN_PIPE,
		            "la connessione dell'input è caduta: la keymap non ha dove andare");
		xkb_keymap_unref(km);
		return -1;
	}
	testo = xkb_keymap_get_as_string(km, XKB_KEYMAP_FORMAT_TEXT_V1);
	stato = xkb_state_new(km);
	if (!testo || !stato) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_FAILED,
		            "xkbcommon non ha serializzato la keymap «%s»", origine);
		free(testo);
		if (stato)
			xkb_state_unref(stato);
		xkb_keymap_unref(km);
		return -1;
	}
	len = strlen(testo);

	fd = memfd_create("remotix-keymap", MFD_CLOEXEC);
	if (fd < 0 || write(fd, testo, len + 1) != (ssize_t)(len + 1)) {
		g_set_error(sbaglio, G_IO_ERROR, g_io_error_from_errno(errno),
		            "la keymap non si scrive nel memfd: %s", g_strerror(errno));
		if (fd >= 0)
			close(fd);
		free(testo);
		xkb_state_unref(stato);
		xkb_keymap_unref(km);
		return -1;
	}
	/* ⚠ `libwayland` duplica il descrittore mentre impacchetta la richiesta:
	 *   il nostro si chiude subito dopo, e non è una doppia chiusura. */
	zwp_virtual_keyboard_v1_keymap(w->tastiera, WL_KEYBOARD_KEYMAP_FORMAT_XKB_V1, fd,
	                               (uint32_t)(len + 1));
	close(fd);

	/* ⛔ Lo stato nuovo RIPRENDE i tasti che risultano ancora giù — come fa
	 *    wlroots dalla sua parte (`wlr_keyboard_set_keymap`).  Chi chiama li ha
	 *    già rilasciati, e di norma non ce n'è nessuno; ma se il rilascio non
	 *    fosse partito, uno stato vergine direbbe «Maiusc su» a un compositore
	 *    che lo tiene giù. */
	for (uint32_t c = 0; c < MAX_CODICE; c++)
		if (bit(w->tasti_giu, c))
			xkb_state_update_key(stato, c + 8, XKB_KEY_DOWN);

	if (w->stato)
		xkb_state_unref(w->stato);
	if (w->keymap)
		xkb_keymap_unref(w->keymap);
	w->stato = stato;
	w->keymap = km;
	free(w->keymap_testo);
	w->keymap_testo = testo;
	w->keymap_len = len;
	g_free(w->keymap_origine);
	w->keymap_origine = g_strdup(origine);
	w->keymap_mandata = true;

	manda_modificatori(w, true);
	return spedisci(w);
}

/*
 * `de(neo)` → layout `de`, variante `neo`.  ⛔ La stessa forma di `RCP.md` §4.5
 * che `tastiera.c` accetta; e i caratteri si controllano, perché questa stringa
 * arriva dal filo.
 */
static bool separa_nome(const char *nome, char *layout, size_t nl, char *variante, size_t nv)
{
	const char *par = strchr(nome, '(');
	size_t ll = par ? (size_t)(par - nome) : strlen(nome);
	size_t lv = 0;

	for (const char *c = nome; *c; c++)
		if (!g_ascii_isalnum(*c) && *c != '_' && *c != '-' && *c != '(' && *c != ')')
			return false;
	if (ll == 0 || ll >= nl)
		return false;
	memcpy(layout, nome, ll);
	layout[ll] = 0;
	variante[0] = 0;
	if (par) {
		const char *chiusa = strchr(par + 1, ')');

		if (!chiusa || chiusa[1] != 0)
			return false;
		lv = (size_t)(chiusa - par - 1);
		if (lv >= nv)
			return false;
		memcpy(variante, par + 1, lv);
		variante[lv] = 0;
	}
	return true;
}

int wlr_input_keymap_da_nome(WlrInput *w, const char *nome, GError **sbaglio)
{
	char layout[72], variante[72];
	struct xkb_rule_names nomi;
	struct xkb_keymap *km;

	g_return_val_if_fail(w != NULL && nome != NULL, -1);

	if (!separa_nome(nome, layout, sizeof layout, variante, sizeof variante)) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_INVALID_ARGUMENT,
		            "«%.64s» non è un nome di disposizione XKB (RCP.md §4.5)", nome);
		return -1;
	}
	/* ⚠ Tutti e cinque i campi, come `tastiera.c`: un campo NULL lo riempie
	 *   l'ambiente (`XKB_DEFAULT_*`), e la disposizione CHIESTA non deve
	 *   dipendere da chi ha avviato il servizio. */
	nomi.rules = "evdev";
	nomi.model = "pc105";
	nomi.layout = layout;
	nomi.variant = variante;
	nomi.options = "";
	km = xkb_keymap_new_from_names(w->ctx, &nomi, XKB_KEYMAP_COMPILE_NO_FLAGS);
	if (!km) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_NOT_FOUND,
		            "xkbcommon non compila la disposizione «%s»", nome);
		return -1;
	}
	return metti_keymap(w, km, nome, sbaglio);
}

int wlr_input_keymap_da_testo(WlrInput *w, const char *testo, size_t lunghezza,
                              const char *origine, GError **sbaglio)
{
	struct xkb_keymap *km;

	g_return_val_if_fail(w != NULL && testo != NULL, -1);
	km = xkb_keymap_new_from_buffer(w->ctx, testo, lunghezza, XKB_KEYMAP_FORMAT_TEXT_V1,
	                                XKB_KEYMAP_COMPILE_NO_FLAGS);
	if (!km) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_INVALID_DATA,
		            "la keymap «%s» non si compila", origine ? origine : "?");
		return -1;
	}
	return metti_keymap(w, km, origine ? origine : "?", sbaglio);
}

const char *wlr_input_keymap(const WlrInput *w, size_t *lunghezza)
{
	if (lunghezza)
		*lunghezza = w && w->keymap_testo ? w->keymap_len : 0;
	return w ? w->keymap_testo : NULL;
}

const char *wlr_input_keymap_origine(const WlrInput *w)
{
	return w && w->keymap_origine ? w->keymap_origine : "nessuna";
}

/* ------------------------------------------------------------------------- */

WlrInput *wlr_input_apri(GError **sbaglio)
{
	WlrInput *w = g_new0(WlrInput, 1);
	const char *nome = g_getenv("WAYLAND_DISPLAY");
	gint64 scadenza;
	g_autoptr(GError) sb_keymap = NULL;
	int esito;

	w->display = wl_display_connect(nome);
	if (!w->display && !nome) {
		/* ⚠ La stessa ricerca di `wlr_apri()`: il figlio non eredita
		 *   `WAYLAND_DISPLAY` dal compositore che ha appena fatto nascere. */
		for (int i = 0; i < 10 && !w->display; i++) {
			g_autofree char *tenta = g_strdup_printf("wayland-%d", i);

			w->display = wl_display_connect(tenta);
		}
	}
	if (!w->display) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_NOT_FOUND,
		            "nessun compositore Wayland raggiungibile in XDG_RUNTIME_DIR=%s",
		            g_getenv("XDG_RUNTIME_DIR") ?: "(non impostata)");
		wlr_input_chiudi(w);
		return NULL;
	}
	w->ctx = xkb_context_new(XKB_CONTEXT_NO_FLAGS);
	if (!w->ctx) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_FAILED, "contesto xkbcommon non creato");
		wlr_input_chiudi(w);
		return NULL;
	}

	w->registry = wl_display_get_registry(w->display);
	wl_registry_add_listener(w->registry, &ASCOLTO_REGISTRO, w);

	/* ⚠ TRE giri: i global; le capacità del seat (che chiedono la spia); la
	 *   keymap che la spia riceve.  Con un tetto solo per tutti e tre. */
	scadenza = g_get_monotonic_time() + ATTESA_US;
	if (!sincronizza(w, scadenza) || !sincronizza(w, scadenza)) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_TIMED_OUT,
		            "il compositore non ha risposto all'elenco dei global entro %d s",
		            (int)(ATTESA_US / G_USEC_PER_SEC));
		wlr_input_chiudi(w);
		return NULL;
	}
	if (w->spia)
		(void)sincronizza(w, scadenza); /* ⚠ senza keymap si va avanti: sotto c'è il ripiego */
	spia_via(w);

	if (!w->seat || !w->gestore_tastiera || !w->gestore_puntatore) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_NOT_SUPPORTED,
		            "il compositore non annuncia %s%s%s: su questo desktop l'input non "
		            "passa di qui",
		            w->seat ? "" : "wl_seat ",
		            w->gestore_tastiera ? "" : "zwp_virtual_keyboard_manager_v1 ",
		            w->gestore_puntatore ? "" : "zwlr_virtual_pointer_manager_v1");
		wlr_input_chiudi(w);
		return NULL;
	}

	w->tastiera = zwp_virtual_keyboard_manager_v1_create_virtual_keyboard(w->gestore_tastiera,
	                                                                       w->seat);
	/*
	 * ⭐ Il puntatore si LEGA ALL'USCITA quando il manager è v2: le coordinate
	 *    assolute allora sono relative a lei, e non allo spazio di tutte le
	 *    uscite.  ⚠ Con un'uscita sola è la stessa cosa; con due, senza questo,
	 *    il puntatore finirebbe spalmato su entrambe.  `[?]` Che labwc onori
	 *    l'uscita suggerita (`wlr_cursor_map_input_to_output`) è letto nello
	 *    studio, non misurato.
	 */
	if (w->versione_puntatore >= 2 && w->uscita)
		w->puntatore = zwlr_virtual_pointer_manager_v1_create_virtual_pointer_with_output(
			w->gestore_puntatore, w->seat, w->uscita);
	else
		w->puntatore = zwlr_virtual_pointer_manager_v1_create_virtual_pointer(
			w->gestore_puntatore, w->seat);

	/* ⛔ La keymap PRIMA di qualunque tasto — e quindi prima di tornare. */
	if (w->keymap_sessione)
		esito = wlr_input_keymap_da_testo(w, w->keymap_sessione, w->keymap_sessione_len,
		                                  "sessione", &sb_keymap);
	else
		esito = -1;
	if (esito != 0) {
		/*
		 * ⚠ IL RIPIEGO, DICHIARATO: la sessione non ci ha dato la sua keymap
		 *   (`[M]` succede su labwc headless: senza una tastiera vera il seat
		 *   dichiara capacità 0 e la spia non nasce — `wlr_input.h`).  Allora la
		 *   compone `xkbcommon` dall'ambiente del figlio (`XKB_DEFAULT_*`, o
		 *   `us`).  ⛔ Può NON essere la disposizione della sessione: la
		 *   disposizione negoziata col client (`input_disposizione()`), che
		 *   arriva subito dopo l'apertura, la sostituisce.
		 */
		struct xkb_rule_names vuoti = { 0 };
		struct xkb_keymap *km;

		if (sb_keymap)
			registro_dice(AREA, "⚠ wlroots: la keymap della sessione non si usa (%s)",
			              sb_keymap->message);
		g_clear_error(&sb_keymap);
		km = xkb_keymap_new_from_names(w->ctx, &vuoti, XKB_KEYMAP_COMPILE_NO_FLAGS);
		if (!km || metti_keymap(w, km, "ambiente", &sb_keymap) != 0) {
			g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_FAILED,
			            "nessuna keymap da presentare alla tastiera virtuale (%s): senza, "
			            "il primo tasto chiuderebbe la connessione (no_keymap)",
			            sb_keymap ? sb_keymap->message : "xkbcommon non compone nemmeno "
			                                             "quella dell'ambiente");
			wlr_input_chiudi(w);
			return NULL;
		}
		registro_dice(AREA,
		              "⚠ RIPIEGO DICHIARATO: la sessione non ha consegnato la sua keymap — "
		              "presento quella dell'AMBIENTE (disposizione «%s»).  ⛔ Può non essere "
		              "quella della sessione: la corregge la disposizione negoziata col client",
		              xkb_keymap_layout_get_name(w->keymap, 0) ?: "senza nome");
	}

	/* ⛔ E si controlla che il compositore abbia accettato tutto: un errore di
	 *    protocollo arriva DOPO la richiesta, e senza questo giro lo si
	 *    scoprirebbe al primo tasto dell'utente. */
	if (!sincronizza(w, g_get_monotonic_time() + ATTESA_US) || w->caduto) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_BROKEN_PIPE,
		            "il compositore non ha accettato i dispositivi virtuali (il registro "
		            "dice perché)");
		wlr_input_chiudi(w);
		return NULL;
	}

	registro_dice(AREA,
	              "⭐ wlroots: tastiera e puntatore virtuali creati (puntatore v%u%s), keymap "
	              "dalla %s, %zu byte",
	              w->versione_puntatore,
	              w->versione_puntatore >= 2 && w->uscita ? ", legato all'uscita" : "",
	              w->keymap_origine, w->keymap_len);
	return w;
}

int wlr_input_descrittore(WlrInput *w)
{
	if (!w || w->caduto || !w->display)
		return -1;
	return wl_display_get_fd(w->display);
}

bool wlr_input_caduto(const WlrInput *w)
{
	return !w || w->caduto;
}

int wlr_input_gira(WlrInput *w)
{
	struct pollfd pfd;
	int n;

	if (!w || w->caduto)
		return -1;
	/* ⛔ Non si aspetta MAI: è il ciclo del figlio che chiama, e questa è la
	 *    sua rete di sicurezza a ogni giro — `poll` con zero. */
	while (wl_display_prepare_read(w->display) != 0) {
		if (wl_display_dispatch_pending(w->display) < 0) {
			segna_caduta(w, "dispatch_pending");
			return -1;
		}
	}
	if (wl_display_flush(w->display) < 0 && errno != EAGAIN) {
		wl_display_cancel_read(w->display);
		segna_caduta(w, "flush");
		return -1;
	}
	pfd.fd = wl_display_get_fd(w->display);
	pfd.events = POLLIN;
	pfd.revents = 0;
	if (poll(&pfd, 1, 0) > 0) {
		if (wl_display_read_events(w->display) < 0) {
			segna_caduta(w, "read_events");
			return -1;
		}
	} else {
		wl_display_cancel_read(w->display);
	}
	n = wl_display_dispatch_pending(w->display);
	if (n < 0) {
		segna_caduta(w, "dispatch");
		return -1;
	}
	return n;
}

/* ------------------------------------------------------------------------- */
/* I gesti. */

int wlr_input_tasto(WlrInput *w, uint16_t codice, bool premuto)
{
	if (!w || w->caduto || !w->tastiera || codice >= MAX_CODICE)
		return -1;
	/* ⛔ `no_keymap`: senza keymap il tasto è un errore di protocollo, e un
	 *    errore di protocollo chiude la connessione intera. */
	if (!w->keymap_mandata)
		return -1;
	if (bit(w->tasti_giu, codice) == premuto)
		return 0; /* doppione: vedi `wlr_input.h` */

	zwp_virtual_keyboard_v1_key(w->tastiera, ora_ms(), codice,
	                            premuto ? WL_KEYBOARD_KEY_STATE_PRESSED
	                                    : WL_KEYBOARD_KEY_STATE_RELEASED);
	metti_bit(w->tasti_giu, codice, premuto);
	/* ⚠ L'offset evdev → XKB è 8 in tutt'e due i versi (§7.1). */
	xkb_state_update_key(w->stato, (xkb_keycode_t)codice + 8, premuto ? XKB_KEY_DOWN : XKB_KEY_UP);
	manda_modificatori(w, false);
	return spedisci(w);
}

/*
 * ⛔ `frame` DOPO OGNI gesto del puntatore (trappola 3): wlroots tiene gli assi
 *    in sospeso finché non arriva, e le applicazioni raccolgono gli eventi per
 *    cornice — un clic senza cornice è un clic che l'applicazione non ha ancora
 *    finito di ricevere.
 */
static int cornice(WlrInput *w)
{
	zwlr_virtual_pointer_v1_frame(w->puntatore);
	return spedisci(w);
}

int wlr_input_assoluto(WlrInput *w, uint32_t x, uint32_t y, uint32_t l, uint32_t a)
{
	if (!w || w->caduto || !w->puntatore || l == 0 || a == 0)
		return -1;
	/*
	 * ⚠ Le coordinate le ha già saturate `rcp.c` sulla sua tela; qui si satura
	 *   di nuovo sull'ESTENSIONE, perché fra un `ADATTA_TELA` e il `input_ritela`
	 *   che lo segue le due possono differire per un fotogramma.  ⭐ E il
	 *   protocollo è NORMALIZZATO (wlroots divide per l'estensione): se l'uscita
	 *   cambia misura sotto di noi, il punto resta nella stessa proporzione
	 *   invece di uscire dallo schermo.
	 */
	if (x >= l)
		x = l - 1;
	if (y >= a)
		y = a - 1;
	zwlr_virtual_pointer_v1_motion_absolute(w->puntatore, ora_ms(), x, y, l, a);
	return cornice(w);
}

int wlr_input_pulsante(WlrInput *w, uint16_t codice, bool premuto)
{
	if (!w || w->caduto || !w->puntatore || codice >= MAX_CODICE)
		return -1;
	if (bit(w->bottoni_giu, codice) == premuto)
		return 0; /* doppione: il seat conterebbe due pressioni */
	zwlr_virtual_pointer_v1_button(w->puntatore, ora_ms(), codice,
	                               premuto ? WL_POINTER_BUTTON_STATE_PRESSED
	                                       : WL_POINTER_BUTTON_STATE_RELEASED);
	metti_bit(w->bottoni_giu, codice, premuto);
	return cornice(w);
}

int wlr_input_rilascia_forzato(WlrInput *w, uint16_t codice)
{
	if (!w || w->caduto || !w->puntatore || codice >= MAX_CODICE)
		return -1;
	zwlr_virtual_pointer_v1_button(w->puntatore, ora_ms(), codice,
	                               WL_POINTER_BUTTON_STATE_RELEASED);
	metti_bit(w->bottoni_giu, codice, false);
	return cornice(w);
}

/*
 * ⛔ Unità da 120 → scatti interi, con l'accumulatore.
 *
 * La soglia è 60, cioè mezzo scatto, come su GNOME (`input.c`,
 * `UNITA_PER_DELTA`): 60 fa uno scatto e lascia -60 nell'accumulatore, e un
 * secondo 60 lo riporta a zero senza scattare.  ⇒ Due mezzi scatti fanno uno
 * scatto, uno solo ne fa uno — come l'utente si aspetta da una rotella fine.
 */
static int32_t scatti(int32_t *resto, int32_t unita)
{
	int32_t n = 0;

	*resto += unita;
	while (*resto >= 60) {
		n++;
		*resto -= 120;
	}
	while (*resto <= -60) {
		n--;
		*resto += 120;
	}
	return n;
}

int wlr_input_rotella(WlrInput *w, int32_t orizzontale, int32_t verticale)
{
	int32_t sv, so;

	if (!w || w->caduto || !w->puntatore)
		return -1;
	sv = scatti(&w->resto_verticale, verticale);
	so = scatti(&w->resto_orizzontale, orizzontale);
	if (sv == 0 && so == 0)
		return 0; /* ⛔ niente `value = 0`: trappola 2 */

	zwlr_virtual_pointer_v1_axis_source(w->puntatore, WL_POINTER_AXIS_SOURCE_WHEEL);
	/* ⛔ `discrete` in SCATTI, non in 120: wlroots moltiplica lui per 120
	 *    (`wlr_virtual_pointer_v1.c:183-184`, trappola 1). */
	if (sv)
		zwlr_virtual_pointer_v1_axis_discrete(w->puntatore, ora_ms(),
		                                      WL_POINTER_AXIS_VERTICAL_SCROLL,
		                                      wl_fixed_from_double(sv * VALORE_SCATTO), sv);
	if (so)
		zwlr_virtual_pointer_v1_axis_discrete(w->puntatore, ora_ms(),
		                                      WL_POINTER_AXIS_HORIZONTAL_SCROLL,
		                                      wl_fixed_from_double(so * VALORE_SCATTO), so);
	return cornice(w);
}

/* ------------------------------------------------------------------------- */

void wlr_input_chiudi(WlrInput *w)
{
	if (!w)
		return;

	if (w->display && !w->caduto) {
		/*
		 * ⛔⛔ LA TRAPPOLA 5: `wlr_pointer_finish()` NON rilascia i pulsanti
		 *     (`types/wlr_pointer.c:38-42`).  Distruggere il puntatore con il
		 *     sinistro giù lascia il desktop col sinistro giù.  ⇒ Si rilascia
		 *     qui, con la cornice, PRIMA di distruggere.
		 * ⚠ Di norma non c'è niente: `input_chiudi()` ha già rilasciato col
		 *   conto di `RCP.md` §11.  Questa è la rete sotto la rete.
		 * ⭐ La tastiera no: `wlr_keyboard_finish()` rilascia da sé (§7.2).
		 */
		if (w->puntatore)
			for (uint32_t c = 0; c < MAX_CODICE; c++)
				if (bit(w->bottoni_giu, c))
					(void)wlr_input_rilascia_forzato(w, (uint16_t)c);
		if (w->puntatore)
			zwlr_virtual_pointer_v1_destroy(w->puntatore);
		if (w->tastiera)
			zwp_virtual_keyboard_v1_destroy(w->tastiera);
		w->puntatore = NULL;
		w->tastiera = NULL;
		/* ⛔ `wl_display_disconnect()` NON spedisce quel che è in coda: senza
		 *    questo, il rilascio qui sopra resterebbe nel nostro buffer. */
		(void)wl_display_flush(w->display);
	}
	spia_via(w);
	if (w->puntatore)
		zwlr_virtual_pointer_v1_destroy(w->puntatore);
	if (w->tastiera)
		zwp_virtual_keyboard_v1_destroy(w->tastiera);
	if (w->gestore_puntatore)
		zwlr_virtual_pointer_manager_v1_destroy(w->gestore_puntatore);
	if (w->gestore_tastiera)
		zwp_virtual_keyboard_manager_v1_destroy(w->gestore_tastiera);
	if (w->uscita)
		wl_output_destroy(w->uscita);
	if (w->seat)
		wl_seat_destroy(w->seat);
	if (w->registry)
		wl_registry_destroy(w->registry);
	if (w->display)
		wl_display_disconnect(w->display);
	if (w->stato)
		xkb_state_unref(w->stato);
	if (w->keymap)
		xkb_keymap_unref(w->keymap);
	if (w->ctx)
		xkb_context_unref(w->ctx);
	free(w->keymap_testo);
	g_free(w->keymap_origine);
	g_free(w->keymap_sessione);
	g_free(w);
}
