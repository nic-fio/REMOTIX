/*
 * appunti.c — gli appunti della SESSIONE, cioe' quelli di Mutter.
 *
 * ⛔ Le quattro trappole, il contratto del thread e la ragione del «solo testo»
 *    stanno in `appunti.h`, e non si ripetono qui: questo file le ATTUA, e ogni
 *    punto in cui una di esse morde e' segnato sul posto.
 *
 * ⭐ Discende da `fondamenta/remotix-c/src/appunti_mutter.c` (450 righe, misurato il 5
 *    agosto 2026 contro GNOME 48.7).  ⛔ Le differenze, tutte volute:
 *
 *      · **solo testo**: v1 scambiava elenchi di tipi MIME con chi cuce e
 *        portava anche immagini e `text/html` (`fondamenta/…/scambio.c`).  Qui i tipi
 *        vivono in `TIPI_TESTO` e non escono da questo file;
 *      · **si legge qui**, sul thread degli appunti, invece di consegnare i
 *        tipi e farsi richiamare: l'annuncio di §7.4 porta la lunghezza, e la
 *        lunghezza non si sa senza leggere;
 *      · **il tetto e la validita' UTF-8 si controllano qui**, dove il testo
 *        esiste ancora intero — non dopo aver attraversato un socket;
 *      · **si ricorda l'ultimo testo**, non l'ultimo elenco di tipi: e' quel
 *        che serve a chi si ricollega, ed e' gia' pronto da spedire.
 */
#include "appunti.h"

#include <gio/gunixfdlist.h>
#include <glib-unix.h>
#include <string.h>
#include <unistd.h>

#include "registro.h"

#define NOME_REMOTE "org.gnome.Mutter.RemoteDesktop"
#define IFACE_SESSIONE "org.gnome.Mutter.RemoteDesktop.Session"

#define ATTESA_CHIAMATA_MS 5000

/* Quanto si aspetta un blocco dal descrittore prima di dichiararlo perso: chi
 * scrive dall'altro capo puo' essere lento, ma non muto. */
#define ATTESA_LETTURA_MS 5000

/*
 * ⛔ LA FILA DEI TIPI, E SI PROVA TUTTA — trappola 3 di `appunti.h`.
 *
 * Il gestore interno degli appunti di Mutter tiene **un solo tipo MIME**:
 * quando l'applicazione che ha copiato muore, di tutto quel che aveva
 * annunciato ne resta uno, e non e' detto che sia il primo della nostra fila.
 * ⇒ Si chiede nell'ordine, e si prende il primo che consegna.
 *
 * ⚠ L'ordine non e' indifferente: il primo e' quello che dichiara la codifica,
 *   e gli altri due la sottintendono.  `text/plain` senza charset e' UTF-8 su
 *   Wayland per convenzione, ⛔ ma **si convalida lo stesso**: una convenzione
 *   non e' una garanzia, e un testo non-UTF-8 spedito come UTF-8 e' una
 *   violazione di §5.4 dalla nostra parte del filo.
 */
static const char *const TIPI_TESTO[] = {
	"text/plain;charset=utf-8",
	"UTF8_STRING",
	"text/plain",
	NULL,
};

struct Appunti
{
	GDBusConnection *bus;
	char *controllo;

	GMainContext *contesto;
	GMainLoop *ciclo;
	GThread *thread;

	/* ⛔ L'ultimo testo che la sessione ha copiato, tenuto QUI perche' deve
	 *    sopravvivere alla connessione: chi si ricollega non riceve nessun
	 *    segnale nuovo (`appunti.h`, `appunti_ultimo_testo`). */
	char *ultimo;
	size_t ultimo_byte;

	guint sottoscrizione_offerta;
	guint sottoscrizione_richiesta;

	/* Le richiamate e il loro proprietario.  Il lucchetto e' preso mentre una
	 * richiamata gira, cosi' `appunti_ascolta(NULL, NULL, NULL)` aspetta chi e'
	 * a meta' strada invece di liberargli il contesto sotto i piedi. */
	GMutex lucchetto;
	AppuntiSuTesto su_testo;
	AppuntiSuRichiesta su_richiesta;
	void *dati;
};

static GVariant *chiama(Appunti *appunti, const char *metodo, GVariant *argomenti,
                        const GVariantType *tipo, GError **sbaglio)
{
	return g_dbus_connection_call_sync(appunti->bus, NOME_REMOTE,
	                                   appunti->controllo, IFACE_SESSIONE,
	                                   metodo, argomenti, tipo,
	                                   G_DBUS_CALL_FLAGS_NONE,
	                                   ATTESA_CHIAMATA_MS, NULL, sbaglio);
}

/* Come sopra, ma la risposta porta un descrittore. */
static int chiama_per_descrittore(Appunti *appunti, const char *metodo,
                                  GVariant *argomenti, GError **sbaglio)
{
	g_autoptr(GUnixFDList) elenco = NULL;
	g_autoptr(GVariant) risposta = NULL;
	gint32 indice = -1;

	risposta = g_dbus_connection_call_with_unix_fd_list_sync(
	    appunti->bus, NOME_REMOTE, appunti->controllo, IFACE_SESSIONE, metodo,
	    argomenti, G_VARIANT_TYPE("(h)"), G_DBUS_CALL_FLAGS_NONE,
	    ATTESA_CHIAMATA_MS, NULL, &elenco, NULL, sbaglio);
	if (!risposta)
		return -1;

	g_variant_get(risposta, "(h)", &indice);
	return g_unix_fd_list_get(elenco, indice, sbaglio);
}

/* ------------------------------------------------------------------ *
 * Leggere il testo dalla sessione
 * ------------------------------------------------------------------ */

/* Legge un descrittore fino alla fine, con un tetto e senza restare appesa.
 *
 * ⛔ Il tetto e' quello di §5.4 **piu' uno**: leggendo esattamente
 *    `APPUNTI_TETTO` non si distingue «un testo grande quanto il tetto», che e'
 *    LECITO, da «un testo piu' grande», che va rifiutato.  Un byte in piu' e i
 *    due casi si separano.  ⚠ E' la stessa forma dell'1 000 000 contro 1 MiB di
 *    §5.4: un tetto che rende illegale il caso al limite non e' quel tetto. */
static GBytes *bevi_tutto(int fd, GError **sbaglio)
{
	GByteArray *raccolto = g_byte_array_new();
	guint8 pezzo[16384];

	while (TRUE)
	{
		GPollFD sonda = { .fd = fd, .events = G_IO_IN | G_IO_HUP | G_IO_ERR };
		gssize letti;

		if (g_poll(&sonda, 1, ATTESA_LETTURA_MS) <= 0)
		{
			g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_TIMED_OUT,
			            "chi doveva consegnare gli appunti non ha scritto "
			            "niente per %d ms",
			            ATTESA_LETTURA_MS);
			g_byte_array_free(raccolto, TRUE);
			return NULL;
		}

		letti = read(fd, pezzo, sizeof pezzo);
		if (letti == 0)
			break; /* fine */
		if (letti < 0)
		{
			if (errno == EINTR)
				continue;
			g_set_error(sbaglio, G_IO_ERROR, g_io_error_from_errno(errno),
			            "lettura degli appunti fallita: %s", g_strerror(errno));
			g_byte_array_free(raccolto, TRUE);
			return NULL;
		}

		if (raccolto->len + (guint)letti > APPUNTI_TETTO)
		{
			g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_NO_SPACE,
			            "appunti oltre il tetto di %u byte (§5.4): lasciati "
			            "dove sono, e NON troncati",
			            APPUNTI_TETTO);
			g_byte_array_free(raccolto, TRUE);
			return NULL;
		}
		g_byte_array_append(raccolto, pezzo, (guint)letti);
	}

	return g_byte_array_free_to_bytes(raccolto);
}

/*
 * Prova la fila di `TIPI_TESTO` e restituisce il primo testo che regge, gia'
 * convalidato.  NULL se non ce n'e' nessuno — e la ragione sta nel registro.
 *
 * ⛔ E le ragioni sono TRE e restano distinte: non c'era nessun tipo di testo ·
 *    c'era e la lettura e' fallita · c'era, si e' letto, e non era UTF-8 valido.
 *    Un `NULL` solo per tutt'e tre sarebbe `LEZIONI.md` §1.9 — «vuoto e
 *    proibito con la stessa faccia».
 */
static char *leggi_il_testo(Appunti *appunti, size_t *quanti)
{
	for (int i = 0; TIPI_TESTO[i]; i++)
	{
		g_autoptr(GError) sbaglio = NULL;
		g_autoptr(GBytes) dati = NULL;
		const char *inizio;
		gsize byte = 0;
		int fd;

		fd = chiama_per_descrittore(appunti, "SelectionRead",
		                            g_variant_new("(s)", TIPI_TESTO[i]),
		                            &sbaglio);
		if (fd < 0)
		{
			/* ⚠ In dettaglio e non in chiaro: la fila si prova apposta, e un
			 *   tipo che la sessione non ha e' l'esito NORMALE dei primi giri —
			 *   una riga per ciascuno coprirebbe il registro di rumore. */
			registro_dettaglio(REG_APPUNTI,
			                   "«%s» non si legge dalla sessione (%s): provo il "
			                   "prossimo tipo",
			                   TIPI_TESTO[i],
			                   sbaglio ? sbaglio->message : "senza dettaglio");
			continue;
		}

		dati = bevi_tutto(fd, &sbaglio);
		close(fd);
		if (!dati)
		{
			registro_dice(REG_APPUNTI,
			              "⛔ «%s»: la lettura non e' riuscita — %s",
			              TIPI_TESTO[i],
			              sbaglio ? sbaglio->message : "senza dettaglio");
			continue;
		}

		inizio = (const char *)g_bytes_get_data(dati, &byte);
		if (byte == 0)
		{
			/* ⚠ Zero byte NON e' un guasto: e' una clipboard svuotata, ed e'
			 *   esattamente quel che il banco fa all'inizio di ogni giro
			 *   (`LEZIONI.md` §2.3-quinquies).  Si dichiara e si va avanti. */
			registro_dettaglio(REG_APPUNTI,
			                   "«%s» ha consegnato zero byte: la clipboard e' "
			                   "vuota, non guasta",
			                   TIPI_TESTO[i]);
			continue;
		}

		/* ⛔ UTF-8 VALIDO, e si controlla QUI.  `RCP.md` §5.4: «il testo DEVE
		 *    essere UTF-8».  Spedirlo senza guardare vorrebbe dire mettere sul
		 *    filo una violazione **nostra**, e farla scoprire al client — che
		 *    per §3 dovrebbe chiudere la sessione.  ⇒ Il sintomo sarebbe «la
		 *    sessione cade quando copio da quel programma». */
		if (!g_utf8_validate_len(inizio, byte, NULL))
		{
			registro_dice(REG_APPUNTI,
			              "⛔ «%s» ha consegnato %zu byte che NON sono UTF-8 "
			              "valido: non si annuncia (§5.4).  ⚠ Non e' un difetto "
			              "nostro ne' del client — e' un programma che tiene "
			              "negli appunti byte che RCP/1 non sa portare",
			              TIPI_TESTO[i], (size_t)byte);
			continue;
		}

		/* ⛔ E NIENTE ZERI IN MEZZO.  Da qui in poi il testo viaggia come
		 *    stringa terminata da zero — nel socket verso il padre e in
		 *    `rcp.c` — e uno zero in mezzo lo taglierebbe **in silenzio**: quel
		 *    che si incolla sarebbe piu' corto di quel che si e' copiato, e
		 *    l'annuncio direbbe la lunghezza intera.  ⇒ Due verita' sulla
		 *    stessa cosa, che e' il difetto che §2.2 vieta con quelle parole. */
		if (memchr(inizio, 0, byte))
		{
			registro_dice(REG_APPUNTI,
			              "⛔ «%s»: %zu byte con uno zero in mezzo — non si "
			              "annuncia.  Troncare qui darebbe un testo piu' corto "
			              "dell'annuncio, cioe' un annuncio che mente",
			              TIPI_TESTO[i], (size_t)byte);
			continue;
		}

		registro_dettaglio(REG_APPUNTI, "letti %zu byte di «%s» dalla sessione",
		                   (size_t)byte, TIPI_TESTO[i]);
		if (quanti)
			*quanti = byte;
		return g_strndup(inizio, byte);
	}

	return NULL;
}

/* ------------------------------------------------------------------ *
 * I due segnali
 * ------------------------------------------------------------------ */
static void su_padrone_cambiato(GDBusConnection *bus, const char *mittente,
                                const char *percorso, const char *interfaccia,
                                const char *segnale, GVariant *parametri,
                                gpointer dati)
{
	Appunti *appunti = dati;
	g_autoptr(GVariant) opzioni = NULL;
	g_autoptr(GVariant) tipi = NULL;
	g_autofree const char **mime = NULL;
	g_autofree char *testo = NULL;
	gboolean nostro = FALSE;
	gboolean c_e_testo = FALSE;
	size_t byte = 0;

	(void)bus;
	(void)mittente;
	(void)percorso;
	(void)interfaccia;
	(void)segnale;

	g_variant_get(parametri, "(@a{sv})", &opzioni);

	/*
	 * ⛔ IL RITORNO SI RICONOSCE QUI, ed e' la prima cosa da guardare —
	 *    trappola 4 di `appunti.h`.  Senza queste tre righe si annuncerebbe al
	 *    client quel che il client ci ha appena dato, e i due lati si
	 *    rincorrerebbero senza fine.
	 * ⭐ E su GNOME e' **etichettato**, non da indovinare: `STUDI.md` §gnome §10
	 *    corregge la nostra vecchia riga che parlava di «un'euristica».
	 */
	if (g_variant_lookup(opzioni, "session-is-owner", "b", &nostro) && nostro)
	{
		registro_dettaglio(REG_APPUNTI,
		                   "e' il ritorno della nostra offerta, non una copia "
		                   "nuova: non si annuncia");
		return;
	}

	/*
	 * ⛔ NEL SEGNALE I TIPI STANNO DENTRO UNA TUPLA, E NEI METODI NO — trappola
	 *    2 di `appunti.h`, misurata il 5 agosto 2026 e costata una prova.
	 *
	 *    `SetSelection` vuole `mime-types` come `as`; `SelectionOwnerChanged` lo
	 *    consegna come `(as)`.  Chi legge `as` non trova niente e **torna in
	 *    silenzio**: gli appunti funzionano in un verso solo, e nel registro non
	 *    compare nulla che lo spieghi.
	 *
	 *    ⚠ Si accettano ENTRAMBE le forme, perche' quale delle due arrivi
	 *      dipende dalla versione di Mutter — e sbagliare costa un verso degli
	 *      appunti.  Lo aggira anche il riferimento (`grd-session.c`), il che
	 *      dice che non e' una nostra fantasia.
	 */
	tipi = g_variant_lookup_value(opzioni, "mime-types",
	                              G_VARIANT_TYPE_STRING_ARRAY);
	if (!tipi)
	{
		g_autoptr(GVariant) tupla =
		    g_variant_lookup_value(opzioni, "mime-types", G_VARIANT_TYPE("(as)"));

		if (tupla)
			tipi = g_variant_get_child_value(tupla, 0);
	}
	if (!tipi)
	{
		registro_dice(REG_APPUNTI,
		              "⛔ la sessione ha annunciato una copia senza tipi "
		              "leggibili: ne' `as` ne' `(as)`.  ⚠ Se e' una forma "
		              "terza, gli appunti da qui in poi vanno in un verso solo "
		              "e questa riga e' l'unico posto in cui si vede");
		return;
	}
	mime = g_variant_get_strv(tipi, NULL);

	/* ⛔ C'E' DEL TESTO FRA I TIPI?  E se non c'e', si dice CHE COSA c'era.
	 *
	 * ⚠ E' il caso normale di «ho copiato un'immagine»: non e' un guasto, ed e'
	 *   la riga che spiega all'utente perche' quella copia non e' arrivata sul
	 *   telefono.  Senza, il sintomo sarebbe «gli appunti a volte non
	 *   funzionano» — cioe' il difetto piu' caro da diagnosticare che ci sia. */
	for (int i = 0; mime && mime[i] && !c_e_testo; i++)
		for (int k = 0; TIPI_TESTO[k]; k++)
			if (g_ascii_strcasecmp(mime[i], TIPI_TESTO[k]) == 0)
			{
				c_e_testo = TRUE;
				break;
			}
	if (!c_e_testo)
	{
		g_autofree char *elenco = mime ? g_strjoinv(", ", (GStrv)mime) : NULL;

		registro_dice(REG_APPUNTI,
		              "la sessione ha copiato qualcosa che non e' testo (%s): "
		              "non si annuncia.  ⚠ `DECISIONI.md` §5-ter.1 — solo "
		              "testo, ed e' una decisione, non un limite tecnico",
		              elenco && *elenco ? elenco : "nessun tipo");
		return;
	}

	testo = leggi_il_testo(appunti, &byte);
	if (!testo)
	{
		/* ⚠ `leggi_il_testo` ha gia' scritto QUALE dei tre motivi era: qui si
		 *   dice soltanto che l'annuncio non parte, o «ho letto e ho taciuto»
		 *   avrebbe la faccia di «non e' successo niente». */
		registro_dice(REG_APPUNTI,
		              "⛔ la sessione ha copiato del testo ma non se n'e' potuto "
		              "leggere nessun tipo: niente annuncio al client");
		return;
	}

	g_mutex_lock(&appunti->lucchetto);
	g_free(appunti->ultimo);
	appunti->ultimo = g_strdup(testo);
	appunti->ultimo_byte = byte;
	if (appunti->su_testo)
		appunti->su_testo(testo, byte, appunti->dati);
	g_mutex_unlock(&appunti->lucchetto);
}

/*
 * ⛔⛔⭐ LA CLIPBOARD CHE C'ERA GIA', E CHE VA **CHIESTA** — 21 agosto 2026.
 *
 * ⚠ Qui accanto c'era scritto che `EnableClipboard` con opzioni vuote fa
 *   arrivare un `SelectionOwnerChanged` **subito**, «ed e' proprio l'annuncio
 *   che fa ritrovare gli appunti a chi si ricollega».  ⛔ **Non e' vero**, e la
 *   misura e' del 21 agosto: `wl-copy` vivo e proprietario nella sessione,
 *   `wl-paste` che legge il suo testo prima e dopo — e nel registro del figlio
 *   **nessuna** riga di lettura.  Mutter non racconta a una sessione nuova chi
 *   possiede la selezione: racconta solo i CAMBI da li' in poi.
 *
 * ⇒ E la conseguenza era grossa: il client, per farsi trovare quando qualcuno
 *   di la' incolla col mouse, annuncia i suoi appunti appena si collega — e
 *   non sapendo che cosa c'era nella sessione ci prendeva sopra la selezione.
 *   `[M]` `wl-paste` diceva «TESTO-CHE-ERA-GIA-NEL-DESKTOP» prima del
 *   collegamento e «» dopo: **collegandosi si perdeva la clipboard del
 *   desktop**.  ⛔ In una sessione locale la clipboard non sparisce perche' e'
 *   entrato qualcuno, e qui non deve sparire nemmeno.
 *
 * ⭐ Allora la si chiede, una volta, appena la clipboard e' accesa: se c'e' un
 *    proprietario si legge il suo testo e lo si annuncia al client come
 *    qualunque altra copia; se non c'e' nessuno, `leggi_il_testo` lo dice nel
 *    registro e non succede niente.
 */
void appunti_leggi_adesso(Appunti *appunti)
{
	g_autofree char *testo = NULL;
	size_t byte = 0;

	if (!appunti)
		return;

	testo = leggi_il_testo(appunti, &byte);
	if (!testo)
	{
		registro_dettaglio(REG_APPUNTI,
		                   "la sessione non aveva appunti da darci al momento "
		                   "dell'accensione: non e' un guasto");
		return;
	}

	registro_dice(REG_APPUNTI,
	              "⭐ la clipboard che c'era GIA' nella sessione: %zu byte, "
	              "letti all'accensione.  ⚠ Chi si collega non deve perdere "
	              "quel che aveva copiato",
	              byte);

	g_mutex_lock(&appunti->lucchetto);
	g_free(appunti->ultimo);
	appunti->ultimo = g_strdup(testo);
	appunti->ultimo_byte = byte;
	if (appunti->su_testo)
		appunti->su_testo(testo, byte, appunti->dati);
	g_mutex_unlock(&appunti->lucchetto);
}

static void su_trasferimento(GDBusConnection *bus, const char *mittente,
                             const char *percorso, const char *interfaccia,
                             const char *segnale, GVariant *parametri,
                             gpointer dati)
{
	Appunti *appunti = dati;
	const char *mime = NULL;
	guint32 serial = 0;

	(void)bus;
	(void)mittente;
	(void)percorso;
	(void)interfaccia;
	(void)segnale;

	g_variant_get(parametri, "(&su)", &mime, &serial);
	registro_dettaglio(REG_APPUNTI,
	                   "la sessione vuole incollare «%s» (richiesta %u)", mime,
	                   serial);

	g_mutex_lock(&appunti->lucchetto);
	if (appunti->su_richiesta)
	{
		appunti->su_richiesta((uint32_t)serial, appunti->dati);
		g_mutex_unlock(&appunti->lucchetto);
		return;
	}
	g_mutex_unlock(&appunti->lucchetto);

	/* ⛔ Nessuno ascolta: si risponde comunque di NO.  Una richiesta senza
	 *    risposta lascia l'applicazione che incolla in attesa a tempo
	 *    indeterminato, e quel che l'utente vede e' un desktop piantato
	 *    (`appunti.h`, `AppuntiSuRichiesta`). */
	appunti_rispondi(appunti, (uint32_t)serial, NULL, 0);
}

/* ------------------------------------------------------------------ *
 * Il thread che fa girare il contesto
 * ------------------------------------------------------------------ */
static gpointer thread_appunti(gpointer dati)
{
	Appunti *appunti = dati;

	g_main_context_push_thread_default(appunti->contesto);
	g_main_loop_run(appunti->ciclo);
	g_main_context_pop_thread_default(appunti->contesto);
	return NULL;
}

Appunti *appunti_apri(GDBusConnection *bus, const char *percorso_controllo,
                      GError **sbaglio)
{
	Appunti *appunti;

	if (!bus || !percorso_controllo)
	{
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_INVALID_ARGUMENT,
		            "gli appunti vogliono un bus e la sessione di controllo");
		return NULL;
	}

	appunti = g_new0(Appunti, 1);
	appunti->bus = g_object_ref(bus);
	appunti->controllo = g_strdup(percorso_controllo);
	g_mutex_init(&appunti->lucchetto);

	/*
	 * ⛔ Il contesto si crea e si SOTTOSCRIVE qui, sul thread chiamante, con il
	 *    contesto messo come predefinito: GDBus lega la consegna al contesto
	 *    predefinito del thread che **sottoscrive**, non a quello che poi lo fa
	 *    girare.  Sottoscrivere dentro il thread nuovo sarebbe la strada
	 *    apparentemente ovvia, e lascerebbe una finestra in cui i segnali
	 *    arriverebbero prima che il thread sia pronto.
	 */
	appunti->contesto = g_main_context_new();
	g_main_context_push_thread_default(appunti->contesto);

	appunti->sottoscrizione_offerta = g_dbus_connection_signal_subscribe(
	    bus, NULL, IFACE_SESSIONE, "SelectionOwnerChanged", percorso_controllo,
	    NULL, G_DBUS_SIGNAL_FLAGS_NONE, su_padrone_cambiato, appunti, NULL);
	appunti->sottoscrizione_richiesta = g_dbus_connection_signal_subscribe(
	    bus, NULL, IFACE_SESSIONE, "SelectionTransfer", percorso_controllo, NULL,
	    G_DBUS_SIGNAL_FLAGS_NONE, su_trasferimento, appunti, NULL);

	g_main_context_pop_thread_default(appunti->contesto);

	/*
	 * ⛔ Il ciclo e il thread partono PRIMA di `EnableClipboard`, e l'ordine non
	 *    e' indifferente: quella chiamata puo' far arrivare un
	 *    `SelectionOwnerChanged` **subito**.
	 * ⚠ Qui c'era scritto che quel segnale «e' proprio l'annuncio che fa
	 *   ritrovare gli appunti a chi si ricollega»: **e' falso**, misurato il 21
	 *   agosto 2026 — Mutter racconta i CAMBI, non il proprietario che c'era.
	 *   Gli appunti che c'erano gia' si chiedono, e lo fa
	 *   `appunti_leggi_adesso()`.  Accendendo prima la
	 *    clipboard e poi il thread, quel segnale cadrebbe nella finestra in cui
	 *    nessuno fa girare il contesto — ⚠ e il sintomo sarebbe «gli appunti
	 *    funzionano solo dalla seconda copia in poi», che nessuno collega
	 *    all'ordine di due righe.
	 */
	appunti->ciclo = g_main_loop_new(appunti->contesto, FALSE);
	appunti->thread = g_thread_new("remotix-appunti", thread_appunti, appunti);

	{
		GVariantBuilder vuote;
		g_autoptr(GVariant) risposta = NULL;

		/*
		 * ⭐ Senza `mime-types`: cosi' Mutter non ci fa proprietari di niente e
		 *    ci racconta invece chi lo e' adesso.  Vedi `appunti.h`.
		 */
		g_variant_builder_init(&vuote, G_VARIANT_TYPE("a{sv}"));
		risposta = chiama(appunti, "EnableClipboard",
		                  g_variant_new("(a{sv})", &vuote), NULL, sbaglio);
		if (!risposta)
		{
			g_prefix_error(sbaglio, "Mutter non concede la clipboard: ");
			appunti_chiudi(appunti);
			return NULL;
		}
	}

	registro_dice(REG_APPUNTI,
	              "⭐ appunti della sessione accesi (solo testo, nei due versi) "
	              "su %s",
	              percorso_controllo);
	return appunti;
}

char *appunti_ultimo_testo(Appunti *appunti, size_t *byte)
{
	char *copia;

	if (!appunti)
		return NULL;
	g_mutex_lock(&appunti->lucchetto);
	copia = appunti->ultimo ? g_strdup(appunti->ultimo) : NULL;
	if (byte)
		*byte = copia ? appunti->ultimo_byte : 0;
	g_mutex_unlock(&appunti->lucchetto);
	return copia;
}

void appunti_ascolta(Appunti *appunti, AppuntiSuTesto su_testo,
                     AppuntiSuRichiesta su_richiesta, void *dati)
{
	if (!appunti)
		return;
	g_mutex_lock(&appunti->lucchetto);
	appunti->su_testo = su_testo;
	appunti->su_richiesta = su_richiesta;
	appunti->dati = dati;
	g_mutex_unlock(&appunti->lucchetto);
}

void appunti_chiudi(Appunti *appunti)
{
	if (!appunti)
		return;

	/* Prima si smette di ascoltare — e la chiamata aspetta chi e' a meta'
	 * strada — poi si spegne il ciclo, poi si tolgono le sottoscrizioni. */
	appunti_ascolta(appunti, NULL, NULL, NULL);

	/*
	 * ⛔ NIENTE `DisableClipboard`, MAI — nemmeno qui, ed e' la trappola 1 di
	 *    `appunti.h`.  In Mutter 48.7 quella chiamata lascia la clipboard
	 *    accesa a meta', e da li' in poi nessuno la puo' piu' riaccendere: chi
	 *    la spegnesse al distacco si ritroverebbe, alla connessione dopo,
	 *    appunti morti **per il resto della sessione grafica**.
	 *    ⇒ Chiudendo la sessione di controllo se ne va tutto insieme.
	 */

	if (appunti->ciclo)
		g_main_loop_quit(appunti->ciclo);
	if (appunti->thread)
		g_thread_join(appunti->thread);
	g_clear_pointer(&appunti->ciclo, g_main_loop_unref);

	if (appunti->bus)
	{
		if (appunti->sottoscrizione_offerta)
			g_dbus_connection_signal_unsubscribe(
			    appunti->bus, appunti->sottoscrizione_offerta);
		if (appunti->sottoscrizione_richiesta)
			g_dbus_connection_signal_unsubscribe(
			    appunti->bus, appunti->sottoscrizione_richiesta);
	}

	g_clear_pointer(&appunti->contesto, g_main_context_unref);
	g_free(appunti->ultimo);
	g_clear_object(&appunti->bus);
	g_mutex_clear(&appunti->lucchetto);
	g_free(appunti->controllo);
	g_free(appunti);
}

/* ------------------------------------------------------------------ *
 * I due versi
 * ------------------------------------------------------------------ */
gboolean appunti_offri(Appunti *appunti, GError **sbaglio)
{
	GVariantBuilder opzioni;
	g_autoptr(GVariant) risposta = NULL;

	if (!appunti)
		return FALSE;

	/* ⛔ `as` e non `(as)`: nei METODI i tipi non stanno in una tupla — l'altra
	 *    meta' della trappola 2, e questa e' la meta' che sbaglia in silenzio
	 *    dall'altra parte. */
	g_variant_builder_init(&opzioni, G_VARIANT_TYPE("a{sv}"));
	g_variant_builder_add(&opzioni, "{sv}", "mime-types",
	                      g_variant_new_strv(TIPI_TESTO, -1));

	risposta = chiama(appunti, "SetSelection", g_variant_new("(a{sv})", &opzioni),
	                  NULL, sbaglio);
	if (!risposta)
		return FALSE;

	registro_dettaglio(REG_APPUNTI,
	                   "offerto alla sessione il testo del client (%d tipi)",
	                   (int)(sizeof TIPI_TESTO / sizeof *TIPI_TESTO) - 1);
	return TRUE;
}

void appunti_rispondi(Appunti *appunti, uint32_t serial, const char *testo,
                      size_t byte)
{
	g_autoptr(GError) sbaglio = NULL;
	g_autofree char *ripiego = NULL;
	gboolean riuscito = FALSE;
	int fd;

	if (!appunti)
		return;

	/* ⛔⛔⭐ SE IL CLIENT NON HA NIENTE, SI RENDE AL DESKTOP QUEL CHE AVEVA —
	 *      21 agosto 2026, e nasce dalla direttiva dell'utente: «l'esperienza
	 *      dev'essere quanto piu' vicina possibile a una sessione grafica
	 *      locale».
	 *
	 * ⚠ Per farsi trovare quando qualcuno di qua incolla col mouse, il client
	 *   si annuncia appena si collega — e annunciarsi vuol dire prendersi la
	 *   selezione, che e' UNA.  ⛔ Da quel momento chi incolla nel desktop
	 *   chiede a NOI, e se il client non ha niente da dare l'incollata usciva
	 *   vuota: `[M]` `wl-paste` diceva «TESTO-CHE-ERA-GIA-NEL-DESKTOP» prima
	 *   del collegamento e «» dopo.  Cioe' collegarsi CANCELLAVA la clipboard
	 *   del desktop.
	 *
	 * ⭐ La cura sta qui e non tocca il protocollo: la selezione cambia di
	 *    mano, il CONTENUTO no.  Se il client non consegna niente, si consegna
	 *    l'ultimo testo che la sessione ci aveva dato — che e' esattamente quel
	 *    che l'utente aveva copiato di qua.
	 * ⚠ E si dichiara nel registro: un ripiego silenzioso avrebbe la faccia di
	 *   una consegna riuscita. */
	if (!testo || byte == 0)
	{
		size_t quanti = 0;

		ripiego = appunti_ultimo_testo(appunti, &quanti);
		if (ripiego && quanti > 0)
		{
			registro_dice(REG_APPUNTI,
			              "⭐ il client non ha appunti da dare per la richiesta "
			              "%u: rendo alla sessione i %zu byte che aveva LEI.  "
			              "⚠ Collegarsi non deve cancellare la clipboard del "
			              "desktop",
			              serial, quanti);
			testo = ripiego;
			byte = quanti;
		}
	}

	if (!testo || byte == 0)
	{
		/* Niente da consegnare, e lo si dice: e' comunque una risposta, ed e'
		 * quel che sblocca chi sta incollando. */
		g_autoptr(GVariant) risposta =
		    chiama(appunti, "SelectionWriteDone",
		           g_variant_new("(ub)", (guint32)serial, FALSE), NULL, &sbaglio);
		if (!risposta)
			registro_dice(REG_APPUNTI,
			              "⛔ SelectionWriteDone(no) per la richiesta %u non e' "
			              "riuscita (%s): chi incolla puo' restare appeso",
			              serial, sbaglio->message);
		else
			registro_dettaglio(REG_APPUNTI,
			                   "richiesta %u chiusa con «non ce l'ho»", serial);
		return;
	}

	fd = chiama_per_descrittore(appunti, "SelectionWrite",
	                            g_variant_new("(u)", (guint32)serial), &sbaglio);
	if (fd < 0)
	{
		registro_dice(REG_APPUNTI,
		              "⛔ SelectionWrite per la richiesta %u e' stata rifiutata "
		              "(%s)",
		              serial, sbaglio->message);
		return;
	}

	/* ⭐ E la cache diventa quel che la sessione ha DAVVERO in mano: da qui in
	 *    poi il ripiego qui sopra rende questo, non un testo di prima. */
	g_mutex_lock(&appunti->lucchetto);
	if (!ripiego)
	{
		g_free(appunti->ultimo);
		appunti->ultimo = g_strndup(testo, byte);
		appunti->ultimo_byte = byte;
	}
	g_mutex_unlock(&appunti->lucchetto);

	{
		size_t scritti = 0;

		riuscito = TRUE;
		while (scritti < byte)
		{
			gssize adesso = write(fd, testo + scritti, byte - scritti);

			if (adesso < 0)
			{
				if (errno == EINTR)
					continue;
				registro_dice(REG_APPUNTI,
				              "⛔ scrittura verso la sessione fallita a %zu di "
				              "%zu byte: %s",
				              scritti, byte, g_strerror(errno));
				riuscito = FALSE;
				break;
			}
			scritti += (size_t)adesso;
		}
		if (riuscito)
			registro_dettaglio(REG_APPUNTI,
			                   "consegnati %zu byte alla sessione (richiesta %u)",
			                   byte, serial);
	}

	/* ⛔ Si chiude PRIMA di dichiarare fatto: chi legge dall'altro capo aspetta
	 *    la fine del flusso, e un descrittore ancora aperto la fine non la fa
	 *    mai. */
	close(fd);

	{
		g_autoptr(GVariant) risposta =
		    chiama(appunti, "SelectionWriteDone",
		           g_variant_new("(ub)", (guint32)serial, riuscito), NULL,
		           &sbaglio);
		if (!risposta)
			registro_dice(REG_APPUNTI,
			              "⛔ SelectionWriteDone per la richiesta %u non e' "
			              "riuscita: %s",
			              serial, sbaglio->message);
	}
}
