/*
 * 04-b26-cursore.c — IL BANCO DELL'ANELLO A6 della fase 4.
 *
 * ⛔ Scritto PRIMA di credere alla cura, e sono **DUE DOMANDE DISTINTE**:
 *
 *   1. ⛔ **il cursore non e' dentro l'immagine** — si guarda un FOTOGRAMMA, e
 *      lo strumento che lo guarda deve saper vedere un cursore che c'e' di
 *      sicuro, o «non l'ho visto» e «non so guardare» hanno lo stesso aspetto
 *      (`CODER.md` §3.10).  Il controllo positivo lo fa `04-b26-guarda.py`
 *      **con la forma vera arrivata in banda laterale**, non con un disegno
 *      inventato;
 *
 *   2. ⛔ **la forma arriva in banda laterale** — quante `CURSORE_FORMA`, con
 *      quale serie, e ⛔ **verificato dal lato che riceve**: questo programma
 *      SERIALIZZA il messaggio come lo scriverebbe `rcp.c` (`RCP.md` §7.2) e ne
 *      deposita i BYTE, che `04-b26-guarda.py` rilegge e misura.  Il registro di
 *      chi manda non e' una prova (`CODER.md` §3.8).
 *
 * ===========================================================================
 * ⛔⛔ E LA PRIMA COSA CHE IL BANCO DEVE FAR VEDERE E' IL **DIFETTO**, non la cura
 *
 * `gnome.md` §1.1 punto 6 e' `[R]`: *«chiediamo `cursor-mode=2` (metadato) ma
 * non chiediamo il metadato ⇒ il cursore non arriva affatto»*.  ⛔ Un banco che
 * nasce verde non ha mai visto il difetto (`CODER.md` §3.4).  ⇒ Tre modi, e i
 * primi due sono **la stessa sonda con una riga di differenza**:
 *
 *   --sonda-senza   la sonda chiede SOLO `SPA_META_Header` e `SPA_META_VideoDamage`,
 *                   che e' l'elenco che `src/cattura.c` aveva fino al 14 agosto
 *                   2026.  ⇒ ATTESO: `SPA_META_Cursor` assente su OGNI buffer,
 *                   zero `CURSORE_FORMA`.  **Questo e' il difetto, misurato.**
 *
 *   --sonda-con     la STESSA sonda con in piu' `SPA_META_Cursor`.
 *                   ⇒ ATTESO: il metadato c'e'.  ⛔ **Questo e' il controllo
 *                   positivo dello strumento**: prova che la sonda sa vedere un
 *                   metadato quando c'e', quindi che lo zero di sopra e' uno
 *                   zero e non una cecita'.
 *
 *   --prodotto      la catena vera: `src/cattura.c` + `src/cursore.c`, con
 *                   `cattura_cursore()`.  ⇒ ATTESO: le stesse forme della sonda,
 *                   piu' i FOTOGRAMMI per la domanda 1.
 *
 * ⚠ Le due sonde non duplicano `cattura.c`: hanno un consumatore PipeWire loro,
 *   minimo, che non guarda nemmeno i pixel.  ⛔ E' voluto — uno strumento che
 *   condivide il codice con la cosa misurata non e' uno strumento.
 *
 * ===========================================================================
 * ⛔ IL PUNTATORE LO MUOVE IL BANCO, e senza non si misura niente
 *
 * `[R]` `meta-screen-cast-virtual-stream-src.c:538`: Mutter riempie il metadato
 * solo se `should_cursor_metadata_be_set()`, cioe' **puntatore visibile E dentro
 * il flusso**.  Su una sessione senza nessuno che tocchi niente il puntatore non
 * e' visibile ⇒ `id = 0` ⇒ NASCOSTO.  ⇒ Il banco muove il puntatore da se', con
 * `NotifyPointerMotionAbsolute`, e ⭐ le due posizioni servono a tutt'e due le
 * domande: la forma cambia stato, e i due fotogrammi si confrontano.
 *
 * ⚠ NON usa `libei` (che e' dell'anello A4): la via D-Bus e' del banco, e vale
 *   `CODER.md` §3.6 — si chiama la sola cosa che serve, da fuori.
 *
 * ===========================================================================
 *   cc -o 04-b26-cursore 04-b26-cursore.c ../src/cattura.c ../src/cursore.c \
 *      ../src/mutter.c ../src/registro.c $(pkg-config --cflags --libs \
 *      gio-2.0 libpipewire-0.3 libdrm) -I../src -D_GNU_SOURCE
 *
 * ⛔ GIRA COME L'UTENTE `prova`, dentro la sua sessione (bus di sessione suo).
 */
#include "cattura.h"
#include "cursore.h"
#include "registro.h"

#include <gio/gio.h>
#include <pipewire/pipewire.h>
#include <spa/buffer/meta.h>
#include <spa/param/video/format-utils.h>

#include <inttypes.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define NOME_REMOTE "org.gnome.Mutter.RemoteDesktop"
#define PERCORSO_REMOTE "/org/gnome/Mutter/RemoteDesktop"
#define IFACE_REMOTE "org.gnome.Mutter.RemoteDesktop"
#define IFACE_REMOTE_SESSIONE "org.gnome.Mutter.RemoteDesktop.Session"
#define NOME_SCREENCAST "org.gnome.Mutter.ScreenCast"
#define PERCORSO_SCREENCAST "/org/gnome/Mutter/ScreenCast"
#define IFACE_SCREENCAST "org.gnome.Mutter.ScreenCast"
#define IFACE_SC_SESSIONE "org.gnome.Mutter.ScreenCast.Session"
#define IFACE_SC_FLUSSO "org.gnome.Mutter.ScreenCast.Stream"
#define CURSORE_METADATO 2u
#define ATTESA_CHIAMATA_MS 15000
#define ATTESA_NODO_MS 10000

#define LARGHEZZA 1920u
#define ALTEZZA 1080u

/* ⛔ Le due posizioni del puntatore: lontane fra loro, lontane dalla barra in
 *    alto (l'orologio si muove da solo) e dalla dock in basso.  Il confronto fra
 *    i due fotogrammi vale solo se il resto dello schermo sta fermo. */
#define A_X 400
#define A_Y 400
#define B_X 1400
#define B_Y 400

/* ------------------------------------------------------------------ *
 *  Quel che si raccoglie
 * ------------------------------------------------------------------ */

typedef struct
{
	FILE *jsonl;
	FILE *filo; /* ⭐ I BYTE, come li scriverebbe `rcp.c` */
	const char *cartella;
	const char *modo;
	const char *momento; /* a che punto del copione siamo */

	guint64 forme;
	guint64 nascosti;
	guint64 violazioni;
} Ascolto;

static void jsonl(Ascolto *a, const char *fmt, ...) __attribute__((format(printf, 2, 3)));

static void jsonl(Ascolto *a, const char *fmt, ...)
{
	va_list ap;

	if (!a->jsonl)
		return;
	va_start(ap, fmt);
	vfprintf(a->jsonl, fmt, ap);
	va_end(ap);
	fputc('\n', a->jsonl);
	fflush(a->jsonl);
}

/* ------------------------------------------------------------------ *
 *  ⭐ IL LATO CHE RICEVE — la forma diventa BYTE, e i byte si controllano
 * ------------------------------------------------------------------ */

/*
 * `RCP.md` §7.2, alla lettera:
 *
 *   u16 larghezza · u16 altezza · i16 attivo_x · i16 attivo_y · immagine
 *   ⛔ la lunghezza DEVE valere esattamente `8 + larghezza x altezza x 4`
 *   ⛔ larghezza e altezza NON DEVONO superare 256
 *
 * ⚠ Davanti a ogni messaggio il banco mette **quattro byte di lunghezza suoi**,
 *   che NON sono l'inquadratura di `RCP.md` §6.1: servono solo a rileggere il
 *   deposito, e il file che li rilegge lo dichiara.  L'ordine dei byte e' quello
 *   di rete, come sul filo vero.
 */
static void metti16(uint8_t *dove, uint16_t v)
{
	dove[0] = (uint8_t) (v >> 8);
	dove[1] = (uint8_t) (v & 0xFF);
}

static int forma_arrivata(void *chi, const CursoreForma *f)
{
	Ascolto *a = chi;
	uint8_t testa[8];
	uint8_t quattro[4];
	uint64_t lunghezza;
	uint64_t pixel = (uint64_t) f->larghezza * (uint64_t) f->altezza * 4u;
	int nascosto = (f->larghezza == 0 && f->altezza == 0);
	int guai = 0;

	a->forme++;
	if (nascosto)
		a->nascosti++;

	/* --- i controlli di RCP, fatti QUI: e' il lato che riceve ----------- */
	if (f->larghezza > 256 || f->altezza > 256)
		guai |= 1; /* ⛔ ERRORE_PROTOCOLLO dall'altra parte */
	if ((f->larghezza == 0) != (f->altezza == 0))
		guai |= 2; /* ⛔ §5.5: una sola delle due a zero */
	if (nascosto && (f->attivo_x != 0 || f->attivo_y != 0))
		guai |= 4; /* ⛔ §5.5: nascosto ⇒ punto attivo 0,0 */
	if (!nascosto && (f->attivo_x < 0 || f->attivo_x >= (int16_t) f->larghezza ||
	                  f->attivo_y < 0 || f->attivo_y >= (int16_t) f->altezza))
		guai |= 8; /* ⛔ §5.5: il punto attivo sta DENTRO l'immagine */
	if (!nascosto && !f->immagine)
		guai |= 16; /* ⛔ misura non nulla e nessun pixel */
	if (nascosto && f->immagine)
		guai |= 32; /* ⛔ nascosto con dei pixel appresso */
	if (guai)
		a->violazioni++;

	/* --- i byte, e la lunghezza che DEVE tornare ------------------------ */
	lunghezza = 8u + pixel;
	metti16(testa + 0, f->larghezza);
	metti16(testa + 2, f->altezza);
	metti16(testa + 4, (uint16_t) f->attivo_x);
	metti16(testa + 6, (uint16_t) f->attivo_y);

	if (a->filo)
	{
		quattro[0] = (uint8_t) (lunghezza >> 24);
		quattro[1] = (uint8_t) (lunghezza >> 16);
		quattro[2] = (uint8_t) (lunghezza >> 8);
		quattro[3] = (uint8_t) (lunghezza & 0xFF);
		fwrite(quattro, 1, 4, a->filo);
		fwrite(testa, 1, 8, a->filo);
		if (!nascosto && f->immagine)
			fwrite(f->immagine, 1, (size_t) pixel, a->filo);
		fflush(a->filo);
	}

	/* --- e l'immagine grezza, per il controllo positivo del fotogramma --- */
	if (!nascosto && f->immagine && a->cartella)
	{
		char percorso[512];
		FILE *g;

		snprintf(percorso, sizeof percorso, "%s/forma-%03u.bgra", a->cartella,
		         (unsigned) f->serie);
		g = fopen(percorso, "wb");
		if (g)
		{
			fwrite(f->immagine, 1, (size_t) pixel, g);
			fclose(g);
		}
	}

	jsonl(a,
	      "{\"cosa\":\"CURSORE_FORMA\",\"modo\":\"%s\",\"momento\":\"%s\",\"serie\":%u,"
	      "\"larghezza\":%u,\"altezza\":%u,\"attivo_x\":%d,\"attivo_y\":%d,"
	      "\"nascosto\":%s,\"lunghezza\":%" PRIu64 ",\"lunghezza_attesa\":%" PRIu64 ","
	      "\"violazioni\":%d}",
	      a->modo, a->momento, (unsigned) f->serie, (unsigned) f->larghezza,
	      (unsigned) f->altezza, (int) f->attivo_x, (int) f->attivo_y, nascosto ? "true" : "false",
	      lunghezza, 8u + pixel, guai);

	/* ⛔ Si ACCETTA anche quel che viola: il banco misura, non censura.  Un -1
	 *    qui farebbe sparire dal deposito proprio i messaggi da guardare. */
	return 0;
}

/* ------------------------------------------------------------------ *
 *  ⭐ IL PALCO — la sequenza D-Bus, e il banco se la fa DA SE'
 * ------------------------------------------------------------------ *
 *
 * ⛔⛔ E NON E' PER SFIZIO: `[M]` 14 agosto 2026, primo giro del banco.
 *
 *    Mutter lega la sessione RemoteDesktop al **peer D-Bus** che l'ha creata.
 *    `src/mutter.c` apre una connessione PRIVATA (`bus_di_sessione`, e ha le sue
 *    ragioni: `g_bus_get_sync` porterebbe via il processo al logout), e quella
 *    connessione non la espone.  ⇒ Un banco che apra il palco con `mutter_apri`
 *    e poi muova il puntatore da una connessione sua si prende
 *    `org.freedesktop.DBus.Error.AccessDenied` su OGNI movimento — misurato, e
 *    il primo giro e' finito con 40 movimenti rifiutati e **un solo buffer**.
 *
 * ⭐ E il rimedio e' anche la cosa giusta: `src/mutter.c` e' dell'anello A4, che
 *    lo sta cambiando adesso.  Un banco che ci si appoggia misura il codice di
 *    un altro mentre gliela cambiano sotto.  Qui la sequenza e' del banco, e
 *    ricalca `src/mutter.c` passo per passo — ⛔ l'ordine non ammette permute.
 */

typedef struct
{
	GDBusConnection *bus;
	char *controllo; /* RemoteDesktop.Session  */
	char *flusso;    /* ScreenCast.Stream      */
	uint32_t nodo;
} Palco;

static GVariant *chiama(GDBusConnection *bus, const char *nome, const char *percorso,
                        const char *interfaccia, const char *metodo, GVariant *argomenti,
                        const GVariantType *tipo, GError **sbaglio)
{
	return g_dbus_connection_call_sync(bus, nome, percorso, interfaccia, metodo, argomenti, tipo,
	                                   G_DBUS_CALL_FLAGS_NONE, ATTESA_CHIAMATA_MS, NULL, sbaglio);
}

static void su_nodo(GDBusConnection *bus, const char *mittente, const char *percorso,
                    const char *interfaccia, const char *segnale, GVariant *parametri,
                    gpointer dati)
{
	if (g_variant_is_of_type(parametri, G_VARIANT_TYPE("(u)")))
		g_variant_get(parametri, "(u)", (uint32_t *) dati);
}

static gboolean sveglia(gpointer dati)
{
	return G_SOURCE_CONTINUE;
}

static Palco *palco_apri(uint32_t modo_cursore, GError **sbaglio)
{
	Palco *p = g_new0(Palco, 1);
	g_autofree char *indirizzo = NULL;
	g_autofree char *id_controllo = NULL;
	GVariantBuilder proprieta;
	GMainContext *contesto;
	GSource *battito;
	guint sottoscrizione;
	gint64 scadenza;

	indirizzo = g_dbus_address_get_for_bus_sync(G_BUS_TYPE_SESSION, NULL, sbaglio);
	if (!indirizzo)
		goto guasto;
	p->bus = g_dbus_connection_new_for_address_sync(indirizzo,
	                                                G_DBUS_CONNECTION_FLAGS_AUTHENTICATION_CLIENT |
	                                                    G_DBUS_CONNECTION_FLAGS_MESSAGE_BUS_CONNECTION,
	                                                NULL, NULL, sbaglio);
	if (!p->bus)
		goto guasto;
	g_dbus_connection_set_exit_on_close(p->bus, FALSE);

	/* --- 1. il controllo, creato e NON avviato --------------------------- */
	{
		g_autoptr(GVariant) r = chiama(p->bus, NOME_REMOTE, PERCORSO_REMOTE, IFACE_REMOTE,
		                               "CreateSession", NULL, G_VARIANT_TYPE("(o)"), sbaglio);
		if (!r)
			goto guasto;
		g_variant_get(r, "(o)", &p->controllo);
	}
	{
		g_autoptr(GVariant) r =
		    chiama(p->bus, NOME_REMOTE, p->controllo, "org.freedesktop.DBus.Properties", "Get",
		           g_variant_new("(ss)", IFACE_REMOTE_SESSIONE, "SessionId"),
		           G_VARIANT_TYPE("(v)"), sbaglio);
		g_autoptr(GVariant) v = NULL;
		if (!r)
			goto guasto;
		g_variant_get(r, "(v)", &v);
		id_controllo = g_variant_dup_string(v, NULL);
	}

	/* --- 2. la cattura, registrata sul controllo non ancora avviato ------ */
	g_variant_builder_init(&proprieta, G_VARIANT_TYPE("a{sv}"));
	g_variant_builder_add(&proprieta, "{sv}", "remote-desktop-session-id",
	                      g_variant_new_string(id_controllo));
	g_variant_builder_add(&proprieta, "{sv}", "disable-animations", g_variant_new_boolean(TRUE));
	{
		g_autoptr(GVariant) r =
		    chiama(p->bus, NOME_SCREENCAST, PERCORSO_SCREENCAST, IFACE_SCREENCAST, "CreateSession",
		           g_variant_new("(a{sv})", &proprieta), G_VARIANT_TYPE("(o)"), sbaglio);
		char *cattura_percorso = NULL;

		if (!r)
			goto guasto;
		g_variant_get(r, "(o)", &cattura_percorso);

		/* --- 3. ADESSO si avvia il controllo, non prima ------------------ */
		{
			g_autoptr(GVariant) r2 = chiama(p->bus, NOME_REMOTE, p->controllo,
			                                IFACE_REMOTE_SESSIONE, "Start", NULL, NULL, sbaglio);
			if (!r2)
			{
				g_free(cattura_percorso);
				goto guasto;
			}
		}

		/* --- 4. il monitor virtuale, con `cursor-mode = 2` (METADATO) ---- */
		g_variant_builder_init(&proprieta, G_VARIANT_TYPE("a{sv}"));
		g_variant_builder_add(&proprieta, "{sv}", "cursor-mode",
		                      g_variant_new_uint32(modo_cursore));
		g_variant_builder_add(&proprieta, "{sv}", "is-platform", g_variant_new_boolean(TRUE));
		{
			g_autofree char *mappa = g_uuid_string_random();
			g_autoptr(GVariant) r3 = chiama(p->bus, NOME_SCREENCAST, cattura_percorso,
			                                IFACE_SC_SESSIONE, "RecordVirtual",
			                                g_variant_new("(a{sv})", &proprieta),
			                                G_VARIANT_TYPE("(o)"), sbaglio);
			if (!r3)
			{
				g_free(cattura_percorso);
				goto guasto;
			}
			g_variant_get(r3, "(o)", &p->flusso);
			(void) mappa;
		}
		g_free(cattura_percorso);
	}

	/* --- 5. ci si iscrive PRIMA di `Stream.Start`, o l'annuncio e' gia' passato */
	contesto = g_main_context_new();
	g_main_context_push_thread_default(contesto);
	sottoscrizione =
	    g_dbus_connection_signal_subscribe(p->bus, NULL, IFACE_SC_FLUSSO, "PipeWireStreamAdded",
	                                       p->flusso, NULL, G_DBUS_SIGNAL_FLAGS_NONE, su_nodo,
	                                       &p->nodo, NULL);
	{
		g_autoptr(GVariant) r =
		    chiama(p->bus, NOME_SCREENCAST, p->flusso, IFACE_SC_FLUSSO, "Start", NULL, NULL,
		           sbaglio);
		if (!r)
		{
			g_dbus_connection_signal_unsubscribe(p->bus, sottoscrizione);
			g_main_context_pop_thread_default(contesto);
			g_main_context_unref(contesto);
			goto guasto;
		}
	}
	battito = g_timeout_source_new(50);
	g_source_set_callback(battito, sveglia, NULL, NULL);
	g_source_attach(battito, contesto);
	scadenza = g_get_monotonic_time() + (gint64) ATTESA_NODO_MS * 1000;
	while (p->nodo == 0 && g_get_monotonic_time() < scadenza)
		g_main_context_iteration(contesto, TRUE);
	g_source_destroy(battito);
	g_source_unref(battito);
	g_dbus_connection_signal_unsubscribe(p->bus, sottoscrizione);
	g_main_context_pop_thread_default(contesto);
	g_main_context_unref(contesto);

	if (p->nodo == 0)
	{
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_TIMED_OUT, "nessun nodo PipeWire annunciato");
		goto guasto;
	}
	return p;

guasto:
	if (p->bus)
		g_object_unref(p->bus);
	g_free(p->controllo);
	g_free(p->flusso);
	g_free(p);
	return NULL;
}

static void palco_chiudi(Palco *p)
{
	if (!p)
		return;
	/* ⛔ Si chiude fermando il CONTROLLO: una cattura associata rifiuta di
	 *    fermarsi da sola («Must be stopped from remote desktop session»). */
	if (p->controllo)
	{
		g_autoptr(GVariant) r =
		    chiama(p->bus, NOME_REMOTE, p->controllo, IFACE_REMOTE_SESSIONE, "Stop", NULL, NULL,
		           NULL);
		(void) r;
	}
	g_object_unref(p->bus);
	g_free(p->controllo);
	g_free(p->flusso);
	g_free(p);
}

/* ------------------------------------------------------------------ *
 *  Il puntatore, mosso dal banco
 * ------------------------------------------------------------------ */

static gboolean muovi(Palco *p, double x, double y)
{
	GError *sbaglio = NULL;
	GVariant *risposta;
	static int detto = 0;

	risposta = g_dbus_connection_call_sync(
	    p->bus, NOME_REMOTE, p->controllo, IFACE_REMOTE_SESSIONE, "NotifyPointerMotionAbsolute",
	    g_variant_new("(sdd)", p->flusso, x, y), NULL, G_DBUS_CALL_FLAGS_NONE, 5000, NULL,
	    &sbaglio);
	if (!risposta)
	{
		/* ⛔ Si dice UNA volta: quaranta righe uguali nascondono il resto. */
		if (!detto)
		{
			detto = 1;
			fprintf(stderr, "  NO  il puntatore NON si muove: %s\n", sbaglio->message);
		}
		g_error_free(sbaglio);
		return FALSE;
	}
	g_variant_unref(risposta);
	return TRUE;
}

/*
 * ⛔ IL TOCCO SERVE A NASCONDERE IL PUNTATORE, e non e' una stranezza:
 *    `[R]` `meta-backend.c:1170` — un evento di **touchscreen** mette
 *    `pointer_visible = FALSE`.  E' l'unico modo che il banco ha di far dire a
 *    Mutter `id = 0` a comando, cioe' di far comparire lo stato NASCOSTO invece
 *    di sperarlo.
 */
static gboolean tocca(Palco *p, double x, double y)
{
	GError *sbaglio = NULL;
	GVariant *r;

	r = g_dbus_connection_call_sync(p->bus, NOME_REMOTE, p->controllo, IFACE_REMOTE_SESSIONE,
	                                "NotifyTouchDown", g_variant_new("(sudd)", p->flusso, 0u, x, y),
	                                NULL, G_DBUS_CALL_FLAGS_NONE, 5000, NULL, &sbaglio);
	if (!r)
	{
		fprintf(stderr, "  NO  il tocco non passa: %s\n", sbaglio->message);
		g_error_free(sbaglio);
		return FALSE;
	}
	g_variant_unref(r);
	r = g_dbus_connection_call_sync(p->bus, NOME_REMOTE, p->controllo, IFACE_REMOTE_SESSIONE,
	                                "NotifyTouchUp", g_variant_new("(u)", 0u), NULL,
	                                G_DBUS_CALL_FLAGS_NONE, 5000, NULL, NULL);
	if (r)
		g_variant_unref(r);
	return TRUE;
}

/*
 * ⚠ La scena si dichiara e si muove: qui la «scena» e' la FORMA del puntatore, e
 *   l'unico modo di farla cambiare a comando e' far ricaricare lo sprite.
 *   L'uscita si guarda: un `gsettings` che fallisce in silenzio produrrebbe un
 *   banco che misura «la forma non cambia mai» su una causa sbagliata.
 */
static void esegui(const char *comando)
{
	GError *sbaglio = NULL;
	int stato = 0;

	if (!g_spawn_command_line_sync(comando, NULL, NULL, &stato, &sbaglio))
	{
		fprintf(stderr, "  NO  «%s» non parte: %s\n", comando, sbaglio->message);
		g_error_free(sbaglio);
		return;
	}
	if (stato != 0)
		fprintf(stderr, "  NO  «%s» e uscito %d\n", comando, stato);
	else
		printf("  --  scena: %s\n", comando);
}

/*
 * ⛔⛔ LA ZONA DI COLORE NOTO — e serve a DUE cose, non a una.
 *
 * `[M]` 14 agosto 2026, secondo giro del banco: sul monitor che montiamo noi
 * ⛔ **non arriva un fotogramma nuovo per minuti interi**.  La cadenza e' `0/1`
 * («mandami un fotogramma quando cambia qualcosa», `cattura.h` regola 3) e su un
 * monitor virtuale fermo non cambia niente — nemmeno muovendo il puntatore, ne'
 * in modo METADATA (dove il puntatore non e' nei pixel per costruzione) ne' in
 * modo EMBEDDED.  ⇒ `cattura_prendi` tornava ZERO, che e' uno zero LEGITTIMO e
 * non un guasto — e il banco restava senza fotogrammi da guardare.
 *
 * ⭐ La cura e' la stessa cosa che la fase chiede: **un fondo di colore noto**.
 *    Si toglie l'immagine di sfondo e si mette una tinta piatta:
 *
 *      1. ogni cambio di tinta RIDIPINGE lo schermo ⇒ arriva un fotogramma vero,
 *         a comando (`CODER.md` §3.2: la scena si dichiara e si muove);
 *      2. il fotogramma che ne esce ha, attorno al puntatore, ⛔ **un colore che
 *         sappiamo**: la domanda «il cursore e' nell'immagine?» diventa «questo
 *         riquadro e' ancora tutto di quel colore?», che non ha bisogno di
 *         confronti fra scatti.
 *
 * ⚠ Le due tinte differiscono di UNO su un canale: bastano a far ridipingere e
 *   non a far cambiare il giudizio (la soglia del giudice e' 8).
 * ⛔ E si RIMETTE com'era in fondo al giro: la sessione di `prova` e' di tutti.
 */
#define TINTA_A "#3465a4"
#define TINTA_B "#3465a5"

static void scena_sfondo(const char *colore)
{
	char comando[256];

	esegui("gsettings set org.gnome.desktop.background picture-uri ''");
	esegui("gsettings set org.gnome.desktop.background picture-uri-dark ''");
	esegui("gsettings set org.gnome.desktop.background color-shading-type solid");
	snprintf(comando, sizeof comando,
	         "gsettings set org.gnome.desktop.background primary-color '%s'", colore);
	esegui(comando);
}

static void scena_rimetti(void)
{
	esegui("gsettings reset org.gnome.desktop.background picture-uri");
	esegui("gsettings reset org.gnome.desktop.background picture-uri-dark");
	esegui("gsettings reset org.gnome.desktop.background color-shading-type");
	esegui("gsettings reset org.gnome.desktop.background primary-color");
	esegui("gsettings reset org.gnome.desktop.interface cursor-size");
}

/* ------------------------------------------------------------------ *
 *  Il fotogramma, depositato come PPM
 * ------------------------------------------------------------------ */

/* ⚠ BGRx/BGRA in memoria ⇒ P6 vuole R,G,B: i byte si voltano qui, e lo stride si
 *   LEGGE dal fotogramma (regola 1 di `cattura.h`), non si ricalcola. */
static gboolean deposita_ppm(const CatturaFermo *fermo, const char *percorso)
{
	FILE *g = fopen(percorso, "wb");
	uint8_t *riga;
	uint32_t y, x;

	if (!g)
		return FALSE;
	fprintf(g, "P6\n%u %u\n255\n", fermo->larghezza, fermo->altezza);
	riga = malloc((size_t) fermo->larghezza * 3u);
	if (!riga)
	{
		fclose(g);
		return FALSE;
	}
	for (y = 0; y < fermo->altezza; y++)
	{
		const uint8_t *dentro = fermo->pixel + (size_t) y * fermo->stride;

		for (x = 0; x < fermo->larghezza; x++)
		{
			riga[x * 3 + 0] = dentro[x * 4 + 2];
			riga[x * 3 + 1] = dentro[x * 4 + 1];
			riga[x * 3 + 2] = dentro[x * 4 + 0];
		}
		fwrite(riga, 1, (size_t) fermo->larghezza * 3u, g);
	}
	free(riga);
	fclose(g);
	return TRUE;
}

/* ------------------------------------------------------------------ *
 *  ⭐ LA SONDA — un consumatore PipeWire tutto suo, che non guarda i pixel
 * ------------------------------------------------------------------ */

typedef struct
{
	struct pw_thread_loop *ciclo;
	struct pw_context *contesto;
	struct pw_core *nucleo;
	struct pw_stream *flusso;
	struct spa_hook gancio;

	gboolean chiedi_il_cursore; /* ⛔ L'UNICA differenza fra le due sonde */
	Cursore *cursore;

	guint64 buffer;
	guint64 con_metadato;
	guint64 senza_metadato;
	guint32 byte_metadato;
	gboolean attiva;
} Sonda;

static void sonda_stato(void *dati, enum pw_stream_state vecchio, enum pw_stream_state nuovo,
                        const char *errore)
{
	Sonda *s = dati;

	s->attiva = (nuovo == PW_STREAM_STATE_STREAMING);
	if (errore)
		fprintf(stderr, "  --  sonda: %s\n", errore);
	pw_thread_loop_signal(s->ciclo, false);
}

static void sonda_parametri(void *dati, uint32_t id, const struct spa_pod *param)
{
	Sonda *s = dati;
	uint8_t spazio[1024];
	struct spa_pod_builder b = SPA_POD_BUILDER_INIT(spazio, sizeof spazio);
	const struct spa_pod *p[4];
	uint32_t quanti = 0;

	if (!param || id != SPA_PARAM_Format)
		return;

	p[quanti++] = spa_pod_builder_add_object(
	    &b, SPA_TYPE_OBJECT_ParamBuffers, SPA_PARAM_Buffers, SPA_PARAM_BUFFERS_buffers,
	    SPA_POD_CHOICE_RANGE_Int(4, 2, 8), SPA_PARAM_BUFFERS_dataType,
	    SPA_POD_CHOICE_FLAGS_Int((1 << SPA_DATA_MemFd) | (1 << SPA_DATA_MemPtr)));

	/*
	 * ⛔ QUESTE DUE RIGHE SONO L'ELENCO CHE `src/cattura.c` AVEVA FINO AL
	 *    14 AGOSTO 2026 (righe 355-364), e stanno qui perche' il difetto si
	 *    riproduce, non si racconta.
	 */
	p[quanti++] = spa_pod_builder_add_object(&b, SPA_TYPE_OBJECT_ParamMeta, SPA_PARAM_Meta,
	                                         SPA_PARAM_META_type, SPA_POD_Id(SPA_META_Header),
	                                         SPA_PARAM_META_size,
	                                         SPA_POD_Int(sizeof(struct spa_meta_header)));
	p[quanti++] = spa_pod_builder_add_object(
	    &b, SPA_TYPE_OBJECT_ParamMeta, SPA_PARAM_Meta, SPA_PARAM_META_type,
	    SPA_POD_Id(SPA_META_VideoDamage), SPA_PARAM_META_size,
	    SPA_POD_CHOICE_RANGE_Int(sizeof(struct spa_meta_region) * 4,
	                             sizeof(struct spa_meta_region) * 1,
	                             sizeof(struct spa_meta_region) * 16));

	/* ⭐ E QUESTA E' LA CURA — l'unica riga di differenza fra i due modi. */
	if (s->chiedi_il_cursore)
	{
		int grande = (int) (sizeof(struct spa_meta_cursor) + sizeof(struct spa_meta_bitmap) +
		                    384 * 384 * 4);
		int piccolo =
		    (int) (sizeof(struct spa_meta_cursor) + sizeof(struct spa_meta_bitmap) + 1 * 1 * 4);

		p[quanti++] = spa_pod_builder_add_object(
		    &b, SPA_TYPE_OBJECT_ParamMeta, SPA_PARAM_Meta, SPA_PARAM_META_type,
		    SPA_POD_Id(SPA_META_Cursor), SPA_PARAM_META_size,
		    SPA_POD_CHOICE_RANGE_Int(grande, piccolo, grande));
	}

	pw_stream_update_params(s->flusso, p, quanti);
	pw_thread_loop_signal(s->ciclo, false);
}

static void sonda_processo(void *dati)
{
	Sonda *s = dati;
	struct pw_buffer *pacco = pw_stream_dequeue_buffer(s->flusso);
	struct spa_meta *meta;

	if (!pacco)
		return;
	s->buffer++;

	meta = spa_buffer_find_meta(pacco->buffer, SPA_META_Cursor);
	if (!meta || !meta->data)
		s->senza_metadato++;
	else
	{
		s->con_metadato++;
		s->byte_metadato = meta->size;
		if (s->cursore)
			cursore_metadato(s->cursore, meta->data, meta->size);
	}
	pw_stream_queue_buffer(s->flusso, pacco);
}

static const struct pw_stream_events sonda_eventi = {
	PW_VERSION_STREAM_EVENTS,
	.state_changed = sonda_stato,
	.param_changed = sonda_parametri,
	.process = sonda_processo,
};

static Sonda *sonda_avvia(uint32_t nodo, gboolean chiedi_il_cursore, Cursore *cursore)
{
	Sonda *s = calloc(1, sizeof *s);
	uint8_t spazio[1024];
	struct spa_pod_builder b = SPA_POD_BUILDER_INIT(spazio, sizeof spazio);
	const struct spa_pod *p[1];
	struct spa_rectangle misura = SPA_RECTANGLE(LARGHEZZA, ALTEZZA);
	struct spa_fraction zero = SPA_FRACTION(0, 1);
	struct spa_fraction uno = SPA_FRACTION(1, 1);
	struct spa_fraction sessanta = SPA_FRACTION(60, 1);

	if (!s)
		return NULL;
	s->chiedi_il_cursore = chiedi_il_cursore;
	s->cursore = cursore;

	pw_init(NULL, NULL);
	s->ciclo = pw_thread_loop_new("b26-sonda", NULL);
	s->contesto = pw_context_new(pw_thread_loop_get_loop(s->ciclo), NULL, 0);
	pw_thread_loop_lock(s->ciclo);
	if (pw_thread_loop_start(s->ciclo) < 0)
		goto guasto;
	s->nucleo = pw_context_connect(s->contesto, NULL, 0);
	if (!s->nucleo)
		goto guasto;
	s->flusso = pw_stream_new(s->nucleo, "remotix-b26-sonda", NULL);
	if (!s->flusso)
		goto guasto;
	pw_stream_add_listener(s->flusso, &s->gancio, &sonda_eventi, s);

	p[0] = spa_pod_builder_add_object(
	    &b, SPA_TYPE_OBJECT_Format, SPA_PARAM_EnumFormat, SPA_FORMAT_mediaType,
	    SPA_POD_Id(SPA_MEDIA_TYPE_video), SPA_FORMAT_mediaSubtype,
	    SPA_POD_Id(SPA_MEDIA_SUBTYPE_raw), SPA_FORMAT_VIDEO_format,
	    SPA_POD_CHOICE_ENUM_Id(3, SPA_VIDEO_FORMAT_BGRx, SPA_VIDEO_FORMAT_BGRx,
	                           SPA_VIDEO_FORMAT_BGRA),
	    SPA_FORMAT_VIDEO_size, SPA_POD_Rectangle(&misura), SPA_FORMAT_VIDEO_framerate,
	    SPA_POD_Fraction(&zero), SPA_FORMAT_VIDEO_maxFramerate,
	    SPA_POD_CHOICE_RANGE_Fraction(&sessanta, &uno, &sessanta));

	if (pw_stream_connect(s->flusso, PW_DIRECTION_INPUT, nodo,
	                      PW_STREAM_FLAG_AUTOCONNECT | PW_STREAM_FLAG_MAP_BUFFERS, p, 1) < 0)
		goto guasto;
	pw_thread_loop_unlock(s->ciclo);
	return s;

guasto:
	pw_thread_loop_unlock(s->ciclo);
	fprintf(stderr, "  NO  la sonda non parte\n");
	free(s);
	return NULL;
}

static void sonda_ferma(Sonda *s)
{
	if (!s)
		return;
	pw_thread_loop_stop(s->ciclo);
	if (s->flusso)
		pw_stream_destroy(s->flusso);
	if (s->nucleo)
		pw_core_disconnect(s->nucleo);
	pw_context_destroy(s->contesto);
	pw_thread_loop_destroy(s->ciclo);
	free(s);
}

/* ------------------------------------------------------------------ *
 *  Il copione
 * ------------------------------------------------------------------ */

static void aspetta(double secondi)
{
	g_usleep((gulong) (secondi * 1000000.0));
}

int main(int argc, char **argv)
{
	const char *modo = argc > 1 ? argv[1] : "--prodotto";
	const char *cartella = argc > 2 ? argv[2] : ".";
	char percorso[512];
	Ascolto ascolto;
	Palco *palco;
	GError *sbaglio = NULL;
	Cursore *cursore_sonda = NULL;
	Sonda *sonda = NULL;
	Cattura *cattura = NULL;
	int uscita = 0;

	memset(&ascolto, 0, sizeof ascolto);
	ascolto.cartella = cartella;
	ascolto.modo = modo;
	ascolto.momento = "avvio";

	snprintf(percorso, sizeof percorso, "%s/esiti.jsonl", cartella);
	ascolto.jsonl = fopen(percorso, "w");
	snprintf(percorso, sizeof percorso, "%s/filo.bin", cartella);
	ascolto.filo = fopen(percorso, "wb");
	if (!ascolto.jsonl || !ascolto.filo)
	{
		fprintf(stderr, "  NO  non riesco a scrivere in %s\n", cartella);
		return 2;
	}

	printf("\n== 04-b26 — il cursore, modo %s ==\n", modo);

	/*
	 * ⛔⛔ IL MODO DEL CURSORE E' LA COSA MISURATA, quindi si DICHIARA:
	 *
	 *    --incorporato   `cursor-mode = 1` (EMBEDDED) ⇒ Mutter dipinge il
	 *                    puntatore DENTRO i pixel.  ⭐ E' il **controllo positivo
	 *                    della domanda 1, fatto sui pixel veri**: se il giudice
	 *                    non trovasse il cursore nemmeno qui, sarebbe cieco, e il
	 *                    «non c'e» dell'altro giro non varrebbe niente.
	 *    tutti gli altri `cursor-mode = 2` (METADATA), che e' quel che chiede il
	 *                    prodotto (`src/mutter.c:439`).
	 */
	palco = palco_apri(strcmp(modo, "--incorporato") == 0 ? 1u : CURSORE_METADATO, &sbaglio);
	if (!palco)
	{
		fprintf(stderr, "  NO  il palco non si apre: %s\n", sbaglio ? sbaglio->message : "?");
		return 2;
	}
	printf("  --  nodo PipeWire %u, flusso %s\n", palco->nodo, palco->flusso);

	if (strcmp(modo, "--prodotto") == 0 || strcmp(modo, "--incorporato") == 0)
	{
		cattura = cattura_avvia(palco->nodo, LARGHEZZA, ALTEZZA, 60,
		                        CATTURA_STRADA_MEMORIA, CATTURA_COLORE_BGRX, NULL, NULL, NULL,
		                        &sbaglio);
		if (!cattura)
		{
			fprintf(stderr, "  NO  la cattura non parte: %s\n", sbaglio->message);
			palco_chiudi(palco);
			return 2;
		}
		cattura_cursore(cattura, forma_arrivata, &ascolto);
	}
	else
	{
		cursore_sonda = cursore_apri(forma_arrivata, &ascolto);
		sonda = sonda_avvia(palco->nodo, strcmp(modo, "--sonda-con") == 0, cursore_sonda);
		if (!sonda)
		{
			palco_chiudi(palco);
			return 2;
		}
	}

	/* --- il flusso deve essere VIVO prima di misurare qualunque cosa ----- */
	aspetta(3.0);

	ascolto.momento = "prima-di-toccare";
	aspetta(2.0);

	/*
	 * ⛔⛔ MOMENTO 1 — SI COSTRINGE MUTTER A MANDARE LA FORMA, e senza questo
	 *     passo il banco misurerebbe uno schermo su cui la forma non arriva mai.
	 *
	 * `[R]` `meta-screen-cast-virtual-stream-src.c:135` e `:551`: la bitmap
	 * viaggia **solo** se `cursor_bitmap_invalid`, che nasce FALSO (l'oggetto e'
	 * azzerato) e diventa vero **soltanto** sul segnale `cursor-changed` del
	 * tracker.  ⇒ Su un flusso appena aperto arriva la POSIZIONE e basta, e la
	 * forma puo' non arrivare mai.
	 *
	 * ⭐ La scena si dichiara e si muove (`CODER.md` §3.2): cambiare
	 *    `org.gnome.desktop.interface cursor-size` fa ricaricare lo sprite del
	 *    puntatore ⇒ `cursor-changed` ⇒ la bitmap parte.  ⚠ E' una modifica alla
	 *    sessione di `prova`: si RIMETTE com'era in fondo al giro.
	 */
	ascolto.momento = "forma-1";
	esegui("gsettings set org.gnome.desktop.interface cursor-size 48");
	aspetta(2.5);

	/* --- MOMENTO A: il puntatore su una zona di COLORE NOTO -------------- */
	ascolto.momento = "punto-A";
	scena_sfondo(TINTA_A);
	aspetta(2.0);
	muovi(palco, A_X, A_Y);
	aspetta(1.5);
	/* ⛔ E ADESSO si ridipinge, o non arriva nessun fotogramma nuovo. */
	scena_sfondo(TINTA_B);
	jsonl(&ascolto, "{\"cosa\":\"tinta\",\"punto\":\"A\",\"colore\":\"%s\"}", TINTA_B);

	if (cattura)
	{
		CatturaFermo fermo;

		if (cattura_prendi(cattura, 5.0, &fermo, &sbaglio) == CATTURA_PRESA_FATTA)
		{
			snprintf(percorso, sizeof percorso, "%s/fotogramma-A.ppm", cartella);
			deposita_ppm(&fermo, percorso);
			jsonl(&ascolto,
			      "{\"cosa\":\"fotogramma\",\"punto\":\"A\",\"x\":%d,\"y\":%d,"
			      "\"larghezza\":%u,\"altezza\":%u,\"stride\":%u}",
			      A_X, A_Y, fermo.larghezza, fermo.altezza, fermo.stride);
			cattura_fermo_libera(&fermo);
		}
		else
			jsonl(&ascolto, "{\"cosa\":\"fotogramma\",\"punto\":\"A\",\"preso\":false}");
	}

	/* --- MOMENTO B: il puntatore altrove --------------------------------- */
	ascolto.momento = "punto-B";
	muovi(palco, B_X, B_Y);
	aspetta(1.5);
	scena_sfondo(TINTA_A);
	jsonl(&ascolto, "{\"cosa\":\"tinta\",\"punto\":\"B\",\"colore\":\"%s\"}", TINTA_A);

	if (cattura)
	{
		CatturaFermo fermo;

		if (cattura_prendi(cattura, 5.0, &fermo, &sbaglio) == CATTURA_PRESA_FATTA)
		{
			snprintf(percorso, sizeof percorso, "%s/fotogramma-B.ppm", cartella);
			deposita_ppm(&fermo, percorso);
			jsonl(&ascolto,
			      "{\"cosa\":\"fotogramma\",\"punto\":\"B\",\"x\":%d,\"y\":%d,"
			      "\"larghezza\":%u,\"altezza\":%u,\"stride\":%u}",
			      B_X, B_Y, fermo.larghezza, fermo.altezza, fermo.stride);
			cattura_fermo_libera(&fermo);
		}
		else
			jsonl(&ascolto, "{\"cosa\":\"fotogramma\",\"punto\":\"B\",\"preso\":false}");
	}

	/*
	 * ⭐ MOMENTO C — si continua a muovere il puntatore SENZA cambiargli forma.
	 *    ⛔ E' la domanda «non rimandi mille volte la stessa immagine?»: il
	 *       metadato arriva a OGNI buffer, e qui devono arrivare molti buffer e
	 *       zero `CURSORE_FORMA` nuove.
	 */
	ascolto.momento = "solo-movimento";
	{
		guint64 forme_prima = ascolto.forme;
		int i;

		for (i = 0; i < 40; i++)
		{
			muovi(palco, 600 + (i % 20) * 20, 500 + (i % 7) * 15);
			aspetta(0.1);
		}
		aspetta(1.0);
		jsonl(&ascolto,
		      "{\"cosa\":\"solo-movimento\",\"movimenti\":40,\"forme_nuove\":%" PRIu64 "}",
		      ascolto.forme - forme_prima);
	}

	/*
	 * ⭐⭐ MOMENTO D — NASCOSTO e RITORNO, che e' la trappola vera.
	 *
	 * `[R]` `meta-backend.c:1170`: un evento di **touchscreen** mette
	 * `pointer_visible = FALSE`, un evento di puntatore lo rimette a TRUE.  ⇒ Un
	 * tocco fa arrivare `id = 0` (NASCOSTO), e il movimento successivo fa tornare
	 * il puntatore.
	 *
	 * ⛔ E al ritorno Mutter manda `bitmap_offset = 0` — «la forma non e'
	 *    cambiata» — perche' la visibilita' NON invalida la bitmap.  Chi non
	 *    conservasse l'ultima forma lascerebbe il client senza puntatore **senza
	 *    nessun errore**.  Qui si misura che invece torna.
	 */
	ascolto.momento = "nascosto";
	{
		guint64 prima = ascolto.nascosti;

		tocca(palco, 900, 500);
		aspetta(2.0);
		jsonl(&ascolto, "{\"cosa\":\"tocco\",\"nascosti_nuovi\":%" PRIu64 "}",
		      ascolto.nascosti - prima);
	}

	ascolto.momento = "ritorno";
	{
		guint64 prima = ascolto.forme;

		muovi(palco, A_X, A_Y);
		aspetta(2.0);
		jsonl(&ascolto, "{\"cosa\":\"ritorno\",\"forme_nuove\":%" PRIu64 "}",
		      ascolto.forme - prima);
	}

	/*
	 * ⭐ MOMENTO E — una forma DIVERSA: se la deduplicazione fosse troppo zelante,
	 *    qui non arriverebbe niente.  ⛔ E' il rovescio della domanda 2-bis: si
	 *    verifica che «non rimanda sempre» non sia diventato «non manda mai».
	 */
	ascolto.momento = "forma-2";
	{
		guint64 prima = ascolto.forme;

		esegui("gsettings set org.gnome.desktop.interface cursor-size 32");
		aspetta(2.5);
		muovi(palco, B_X, B_Y);
		aspetta(1.5);
		jsonl(&ascolto, "{\"cosa\":\"forma-diversa\",\"forme_nuove\":%" PRIu64 "}",
		      ascolto.forme - prima);
	}

	/* ⛔ La scena si RIMETTE com'era: la sessione di `prova` e' di tutti. */
	scena_rimetti();

	/* --- i conteggi, che sono la meta' della risposta -------------------- */
	if (cattura)
	{
		CatturaConteggi c;

		cattura_conteggi(cattura, &c);
		jsonl(&ascolto,
		      "{\"cosa\":\"conteggi\",\"modo\":\"%s\",\"fotogrammi\":%" PRIu64
		      ",\"solo_cursore\":%" PRIu64 ",\"cursore_metadati\":%" PRIu64
		      ",\"cursore_assente\":%" PRIu64 ",\"cursore_malformati\":%" PRIu64
		      ",\"forme\":%" PRIu64 ",\"nascosti\":%" PRIu64 ",\"violazioni\":%" PRIu64 "}",
		      modo, c.arrivati, c.solo_cursore, c.cursore_metadati, c.cursore_assente,
		      c.cursore_malformati, ascolto.forme, ascolto.nascosti, ascolto.violazioni);
		printf("  --  fotogrammi %" PRIu64 ", metadati del cursore %" PRIu64 ", assenti %" PRIu64
		       ", CURSORE_FORMA %" PRIu64 "\n",
		       c.arrivati, c.cursore_metadati, c.cursore_assente, ascolto.forme);
	}
	else
	{
		jsonl(&ascolto,
		      "{\"cosa\":\"conteggi\",\"modo\":\"%s\",\"buffer\":%" PRIu64
		      ",\"cursore_metadati\":%" PRIu64 ",\"cursore_assente\":%" PRIu64
		      ",\"byte_metadato\":%u,\"forme\":%" PRIu64 ",\"nascosti\":%" PRIu64
		      ",\"violazioni\":%" PRIu64 "}",
		      modo, sonda->buffer, sonda->con_metadato, sonda->senza_metadato,
		      sonda->byte_metadato, ascolto.forme, ascolto.nascosti, ascolto.violazioni);
		printf("  --  buffer %" PRIu64 ", con metadato %" PRIu64 ", senza %" PRIu64
		       ", CURSORE_FORMA %" PRIu64 "\n",
		       sonda->buffer, sonda->con_metadato, sonda->senza_metadato, ascolto.forme);

		/*
		 * ⛔ IL VERDETTO DELLA SONDA, e sono TRE esiti non due (`CODER.md` §3.10):
		 *    zero metadati con dei buffer = il difetto;  zero buffer = non ho
		 *    guardato niente, e non e' uno zero.
		 */
		if (sonda->buffer == 0)
		{
			printf("  NO  ZERO BUFFER: non ho misurato niente — ⛔ NON e «il metadato non "
			       "arriva»\n");
			uscita = 3;
		}
		else if (!sonda->chiedi_il_cursore && sonda->con_metadato == 0)
			printf("  OK  il DIFETTO e riprodotto: %" PRIu64
			       " buffer, zero SPA_META_Cursor, zero CURSORE_FORMA\n",
			       sonda->buffer);
		else if (sonda->chiedi_il_cursore && sonda->con_metadato > 0)
			printf("  OK  controllo positivo: la sonda SA vedere il metadato (%" PRIu64
			       " buffer su %" PRIu64 ")\n",
			       sonda->con_metadato, sonda->buffer);
		else
		{
			printf("  NO  esito inatteso per il modo %s\n", modo);
			uscita = 4;
		}
	}

	if (ascolto.violazioni)
	{
		printf("  NO  ⛔ %" PRIu64 " CURSORE_FORMA violano RCP §7.2/§5.5\n", ascolto.violazioni);
		uscita = 5;
	}

	if (cattura)
		cattura_ferma(cattura);
	sonda_ferma(sonda);
	if (cursore_sonda)
		cursore_chiudi(cursore_sonda);
	palco_chiudi(palco);
	fclose(ascolto.jsonl);
	fclose(ascolto.filo);
	return uscita;
}
