#include "scambio.h"

#include <freerdp/channels/cliprdr.h>
#include <freerdp/server/cliprdr.h>
#include <gdk-pixbuf/gdk-pixbuf.h>
#include <string.h>
#include <winpr/user.h>

#include "registro.h"

/*
 * Gli identificativi che ci inventiamo per i formati registrati per NOME.
 *
 * I formati sotto 0xC000 sono quelli fissi di Windows (CF_TEXT, CF_DIB…); gli
 * altri si annunciano con un nome, e il numero se lo sceglie chi li annuncia —
 * l'altro capo li riconosce dal nome, non dal numero.
 */
#define FORMATO_HTML 0xC004

/*
 * La tavola delle corrispondenze, ed e' l'unico posto in cui i due mondi si
 * toccano.
 *
 * `mime` e' il nome che usa la sessione (§14.1 di gnome-remote-desktop.md e
 * `grd-mime-type.c`), `formato` quello che viaggia sul filo, `nome` il nome
 * registrato per i formati che non hanno un numero fisso.
 */
typedef struct
{
	const char *mime;
	UINT32 formato;
	const char *nome; /* NULL per i formati fissi */
} Corrispondenza;

static const Corrispondenza tavola[] = {
	/* Il testo per primo, ed e' il caso che conta: `CF_UNICODETEXT` lo rendono
	 * tutti e tre i client, e la conversione la facciamo noi. */
	{ "text/plain;charset=utf-8", CF_UNICODETEXT, NULL },
	{ "UTF8_STRING", CF_UNICODETEXT, NULL },
	{ "text/plain", CF_TEXT, NULL },
	/*
	 * ⛔ LE IMMAGINI PASSANO TUTTE DA `CF_DIB`, e i nomi registrati non
	 *    servono a niente.  Misurato il 5 agosto 2026: annunciando «PNG» al
	 *    client di FreeRDP, la sua selezione X resta senza alcun formato —
	 *    `xf_cliprdr.c` mappa image/png, image/jpeg e tutto il resto su
	 *    `formatToRequest = CF_DIB`, e converte in casa propria.  Windows fa lo
	 *    stesso: cio' che si incolla in Paint e in Word e' il DIB.
	 *
	 *    Ne discende che a convertire tocca a noi: le applicazioni di GNOME
	 *    copiano in PNG, il filo vuole BMP.
	 */
	{ "image/bmp", CF_DIB, NULL },
	{ "image/png", CF_DIB, NULL },
	{ "image/jpeg", CF_DIB, NULL },
	{ "image/gif", CF_DIB, NULL },
	{ "text/html", FORMATO_HTML, "HTML Format" },
};

/* Quel che si offre alla sessione quando il client ha un'immagine: il PNG per
 * primo, che e' quel che le applicazioni di GNOME preferiscono. */
static const char *const mime_immagine[] = { "image/png", "image/bmp", NULL };

struct Scambio
{
	CliprdrServerContext *ctx;
	gboolean aperto;

	/*
	 * ⛔ DUE MODI DI ARRIVARE AGLI APPUNTI, e non e' una ridondanza: e' la
	 *    soluzione di un abbraccio mortale che c'era davvero.
	 *
	 * `palco` e' la via normale, quella della regola di `palco.h`: si prende, si
	 * usa, si lascia — e chi smonta la sessione aspetta.  La usano le richiamate
	 * del CANALE, che girano sul thread di `cliprdr`.
	 *
	 * `appunti` e' il puntatore nudo, e si usa SOLO dentro le richiamate della
	 * SESSIONE.  Il motivo: quelle girano sul thread degli appunti tenendo il
	 * lucchetto degli appunti, e lo smontaggio del palco prende PRIMA il suo
	 * lucchetto in scrittura e POI chiude gli appunti — che aspettano proprio
	 * quel lucchetto.  Una richiamata che si mettesse in coda sul palco
	 * aspetterebbe chi sta aspettando lei.  Li' il puntatore e' vivo per
	 * costruzione: finche' la richiamata gira, `appunti_chiudi` non puo'
	 * finire.
	 */
	Palco *palco;
	Appunti *appunti;

	GMutex lucchetto;

	/*
	 * Quel che il CLIENT ha copiato: i formati del suo ultimo `FORMAT_LIST`,
	 * tradotti in mime.  Serve a rispondere alla sessione che incolla.
	 */
	GArray *formati_client; /* di Corrispondenza, con mime che punta alla tavola */

	/*
	 * E quel che la SESSIONE ha copiato, nei tipi che ha dichiarato.
	 *
	 * Serve perche' il filo chiede `CF_DIB` e basta, e allora bisogna sapere in
	 * che cosa la sessione tenga davvero l'immagine — di solito PNG.
	 */
	GStrv sessione_mime;

	/*
	 * La richiesta della sessione in corso: e' una sola per volta.
	 *
	 * ⛔ Le due meta' arrivano su DUE THREAD diversi e in due momenti diversi —
	 *    la domanda dal thread degli appunti, la risposta da quello del canale —
	 *    quindi il `serial` va tenuto da parte, e va SEMPRE chiuso: una
	 *    richiesta senza risposta lascia in attesa l'applicazione che incolla.
	 */
	gboolean in_corso;
	guint32 serial;
	UINT32 formato_chiesto;
	const char *mime_chiesto;

	guint verso_client;
	guint verso_sessione;
};

/* ------------------------------------------------------------------ *
 * Le conversioni
 * ------------------------------------------------------------------ */
/*
 * Testo: UTF-8 con `\n` di qua, UTF-16LE con `\r\n` e uno zero finale di la'.
 *
 * Il fine riga non e' un dettaglio estetico: un testo incollato in un programma
 * di Windows senza `\r\n` compare tutto su una riga sola, ed e' il difetto che
 * si nota per primo.
 */
static GBytes *testo_verso_client(const char *utf8, gsize quanti, gboolean unicode)
{
	GString *con_cr = g_string_sized_new(quanti + quanti / 8 + 2);

	for (gsize i = 0; i < quanti; i++)
	{
		if (utf8[i] == '\n' && (i == 0 || utf8[i - 1] != '\r'))
			g_string_append_c(con_cr, '\r');
		g_string_append_c(con_cr, utf8[i]);
	}

	if (!unicode)
	{
		/*
		 * CF_TEXT: si consegna cosi' com'e', con lo zero finale.
		 *
		 * ⛔ LA LUNGHEZZA SI LEGGE PRIMA DI LIBERARE.  `g_string_free(s, FALSE)`
		 *    libera la struttura e restituisce il buffer: leggere `s->len`
		 *    nella stessa espressione e' memoria gia' liberata, e l'ordine di
		 *    valutazione degli argomenti in C non e' nemmeno definito.  Il
		 *    genere di difetto che funziona finche' non funziona piu'.
		 */
		gsize quanti_byte = con_cr->len + 1;

		g_string_append_c(con_cr, '\0');
		return g_bytes_new_take(g_string_free(con_cr, FALSE), quanti_byte);
	}

	{
		glong lunghi = 0;
		g_autofree gunichar2 *utf16 = g_utf8_to_utf16(con_cr->str, (glong) con_cr->len, NULL,
		                                              &lunghi, NULL);
		gsize quanti_byte;
		guint8 *fuori;

		g_string_free(con_cr, TRUE);
		if (!utf16)
			return NULL;

		/* Lo zero finale c'e' sempre: la specifica lo vuole, e i client severi
		 * senza di quello mostrano coda di caratteri a caso. */
		quanti_byte = ((gsize) lunghi + 1) * sizeof(gunichar2);
		fuori = g_malloc(quanti_byte);
		memcpy(fuori, utf16, (gsize) lunghi * sizeof(gunichar2));
		fuori[quanti_byte - 2] = 0;
		fuori[quanti_byte - 1] = 0;
		return g_bytes_new_take(fuori, quanti_byte);
	}
}

static GBytes *testo_verso_sessione(const guint8 *dati, gsize quanti, gboolean unicode)
{
	g_autofree char *utf8 = NULL;
	GString *senza_cr;

	if (unicode)
	{
		gsize caratteri = quanti / sizeof(gunichar2);

		/* Lo zero finale, se c'e', non fa parte del testo. */
		while (caratteri > 0 && ((const gunichar2 *) dati)[caratteri - 1] == 0)
			caratteri--;
		utf8 = g_utf16_to_utf8((const gunichar2 *) dati, (glong) caratteri, NULL, NULL, NULL);
	}
	else
	{
		while (quanti > 0 && dati[quanti - 1] == 0)
			quanti--;
		utf8 = g_strndup((const char *) dati, quanti);
	}

	if (!utf8)
		return NULL;

	senza_cr = g_string_sized_new(strlen(utf8));
	for (const char *p = utf8; *p; p++)
	{
		if (p[0] == '\r' && p[1] == '\n')
			continue;
		g_string_append_c(senza_cr, *p);
	}
	{
		gsize quanti_byte = senza_cr->len; /* prima di liberare: vedi sopra */

		return g_bytes_new_take(g_string_free(senza_cr, FALSE), quanti_byte);
	}
}

/*
 * Immagini: `CF_DIB` e' un BMP SENZA i suoi primi quattordici byte.
 *
 * Toglierli e rimetterli e' tutto il lavoro, ma per rimetterli bisogna sapere
 * dove cominciano i pixel — e quello dipende dalla dimensione dell'intestazione
 * DIB, dalla tavolozza e, per le immagini a maschere di bit, da dodici byte in
 * piu'.  Sbagliare quel numero produce un'immagine spostata, non un errore.
 */
static gsize inizio_pixel(const guint8 *dib, gsize quanti)
{
	guint32 intestazione;
	guint16 bit_per_pixel;
	guint32 compressione;
	guint32 colori;
	gsize tavolozza = 0;

	if (quanti < 40)
		return 0;

	intestazione = GUINT32_FROM_LE(*(const guint32 *) (dib + 0));
	bit_per_pixel = GUINT16_FROM_LE(*(const guint16 *) (dib + 14));
	compressione = GUINT32_FROM_LE(*(const guint32 *) (dib + 16));
	colori = GUINT32_FROM_LE(*(const guint32 *) (dib + 32));

	if (intestazione < 12 || intestazione > quanti)
		return 0;

	if (bit_per_pixel <= 8)
		tavolozza = (gsize) (colori ? colori : (1u << bit_per_pixel)) * 4;
	/* BI_BITFIELDS: tre maschere da quattro byte dopo l'intestazione da 40. */
	if (compressione == 3 && intestazione == 40)
		tavolozza += 12;

	return intestazione + tavolozza;
}

static GBytes *bmp_verso_client(const guint8 *bmp, gsize quanti)
{
	if (quanti <= 14 || bmp[0] != 'B' || bmp[1] != 'M')
		return NULL;
	return g_bytes_new(bmp + 14, quanti - 14);
}

static GBytes *dib_verso_sessione(const guint8 *dib, gsize quanti)
{
	gsize salto = inizio_pixel(dib, quanti);
	gsize totale;
	guint8 *bmp;

	if (salto == 0)
		return NULL;

	totale = 14 + quanti;
	bmp = g_malloc(totale);
	bmp[0] = 'B';
	bmp[1] = 'M';
	*(guint32 *) (bmp + 2) = GUINT32_TO_LE((guint32) totale);
	*(guint32 *) (bmp + 6) = 0;
	*(guint32 *) (bmp + 10) = GUINT32_TO_LE((guint32) (14 + salto));
	memcpy(bmp + 14, dib, quanti);
	return g_bytes_new_take(bmp, totale);
}

/*
 * HTML: sul filo viaggia il formato `CF_HTML`, che e' l'HTML avvolto in una
 * intestazione di offset in byte.  Gli offset vanno scritti in decimale a
 * dieci cifre, e devono essere quelli veri: un client che trova
 * `StartFragment` fuori posto incolla mezza pagina o niente.
 */
#define CF_HTML_TESTA                                                                              \
	"Version:0.9\r\nStartHTML:%010zu\r\nEndHTML:%010zu\r\nStartFragment:%010zu\r\n"                 \
	"EndFragment:%010zu\r\n"
#define CF_HTML_PRIMA "<html><body>\r\n<!--StartFragment-->"
#define CF_HTML_DOPO "<!--EndFragment-->\r\n</body></html>"

static GBytes *html_verso_client(const char *html, gsize quanti)
{
	g_autofree char *finta = g_strdup_printf(CF_HTML_TESTA, (gsize) 0, (gsize) 0, (gsize) 0,
	                                         (gsize) 0);
	gsize testa = strlen(finta);
	gsize inizio_html = testa;
	gsize inizio_pezzo = testa + strlen(CF_HTML_PRIMA);
	gsize fine_pezzo = inizio_pezzo + quanti;
	gsize fine_html = fine_pezzo + strlen(CF_HTML_DOPO);
	GString *fuori = g_string_sized_new(fine_html + 1);

	g_string_append_printf(fuori, CF_HTML_TESTA, inizio_html, fine_html, inizio_pezzo, fine_pezzo);
	g_string_append(fuori, CF_HTML_PRIMA);
	g_string_append_len(fuori, html, (gssize) quanti);
	g_string_append(fuori, CF_HTML_DOPO);
	g_string_append_c(fuori, '\0');
	{
		gsize quanti_byte = fuori->len; /* prima di liberare: vedi sopra */

		return g_bytes_new_take(g_string_free(fuori, FALSE), quanti_byte);
	}
}

static GBytes *html_verso_sessione(const guint8 *dati, gsize quanti)
{
	g_autofree char *testo = g_strndup((const char *) dati, quanti);
	const char *inizio = strstr(testo, "<!--StartFragment-->");
	const char *fine = strstr(testo, "<!--EndFragment-->");

	if (inizio && fine && fine > inizio)
	{
		inizio += strlen("<!--StartFragment-->");
		return g_bytes_new(inizio, (gsize) (fine - inizio));
	}

	/* Senza i marcatori si consegna quel che c'e' dopo l'intestazione: meglio
	 * dell'HTML con dentro «Version:0.9». */
	inizio = strstr(testo, "<html");
	if (!inizio)
		inizio = strstr(testo, "<HTML");
	if (inizio)
		return g_bytes_new(inizio, strlen(inizio));
	return g_bytes_new(testo, strlen(testo));
}

/*
 * Da un formato d'immagine all'altro, con gdk-pixbuf.
 *
 * Serve perche' i due mondi non si incontrano: le applicazioni di GNOME
 * copiano in PNG, i client RDP chiedono `CF_DIB` (cioe' BMP) e nient'altro.
 * Senza questa conversione «copia immagine» funzionerebbe solo fra programmi
 * che gia' parlano BMP, cioe' quasi nessuno.
 */
static GBytes *converti_immagine(GBytes *dentro, const char *tipo_uscita)
{
	g_autoptr(GdkPixbufLoader) lettore = gdk_pixbuf_loader_new();
	g_autoptr(GError) sbaglio = NULL;
	GdkPixbuf *pixbuf;
	gchar *fuori = NULL;
	gsize quanti_fuori = 0;
	gsize quanti = 0;
	const guint8 *dati = g_bytes_get_data(dentro, &quanti);

	if (!gdk_pixbuf_loader_write(lettore, dati, quanti, &sbaglio) ||
	    !gdk_pixbuf_loader_close(lettore, &sbaglio))
	{
		avviso("appunti: immagine non interpretabile (%s)", sbaglio->message);
		return NULL;
	}

	pixbuf = gdk_pixbuf_loader_get_pixbuf(lettore);
	if (!pixbuf)
		return NULL;

	if (!gdk_pixbuf_save_to_buffer(pixbuf, &fuori, &quanti_fuori, tipo_uscita, &sbaglio, NULL))
	{
		avviso("appunti: immagine non convertibile in %s (%s)", tipo_uscita, sbaglio->message);
		return NULL;
	}
	return g_bytes_new_take(fuori, quanti_fuori);
}

/* Da quel che ha dato la sessione a quel che si spedisce al client. */
static GBytes *converti_verso_client(UINT32 formato, const char *mime, GBytes *dalla_sessione)
{
	gsize quanti = 0;
	const guint8 *dati = g_bytes_get_data(dalla_sessione, &quanti);

	switch (formato)
	{
		case CF_UNICODETEXT:
			return testo_verso_client((const char *) dati, quanti, TRUE);
		case CF_TEXT:
			return testo_verso_client((const char *) dati, quanti, FALSE);
		case CF_DIB:
		{
			g_autoptr(GBytes) in_bmp = NULL;

			/* Se la sessione non tiene gia' un BMP, lo si fa: sul filo va il
			 * DIB e nient'altro. */
			if (g_ascii_strcasecmp(mime, "image/bmp") == 0)
				in_bmp = g_bytes_ref(dalla_sessione);
			else
				in_bmp = converti_immagine(dalla_sessione, "bmp");
			if (!in_bmp)
				return NULL;

			dati = g_bytes_get_data(in_bmp, &quanti);
			return bmp_verso_client(dati, quanti);
		}
		case FORMATO_HTML:
			return html_verso_client((const char *) dati, quanti);
		default:
			return g_bytes_ref(dalla_sessione);
	}
}

/* E all'incontrario. */
static GBytes *converti_verso_sessione(UINT32 formato, const char *mime, const guint8 *dati,
                                       gsize quanti)
{
	switch (formato)
	{
		case CF_UNICODETEXT:
			return testo_verso_sessione(dati, quanti, TRUE);
		case CF_TEXT:
			return testo_verso_sessione(dati, quanti, FALSE);
		case CF_DIB:
		case CF_DIBV5:
		{
			g_autoptr(GBytes) bmp = dib_verso_sessione(dati, quanti);

			if (!bmp)
				return NULL;
			if (g_ascii_strcasecmp(mime, "image/bmp") == 0)
				return g_steal_pointer(&bmp);
			/* La sessione ha chiesto PNG (o altro): si converte, ed e' il caso
			 * normale — le applicazioni di GNOME il BMP non lo vogliono. */
			return converti_immagine(bmp, g_ascii_strcasecmp(mime, "image/jpeg") == 0 ? "jpeg"
			                              : g_ascii_strcasecmp(mime, "image/gif") == 0 ? "png"
			                                                                           : "png");
		}
		case FORMATO_HTML:
			return html_verso_sessione(dati, quanti);
		default:
			return g_bytes_new(dati, quanti);
	}
}

/* ------------------------------------------------------------------ *
 * La tavola, usata nei due versi
 * ------------------------------------------------------------------ */
static const Corrispondenza *per_mime(const char *mime)
{
	for (gsize i = 0; i < G_N_ELEMENTS(tavola); i++)
	{
		if (g_ascii_strcasecmp(tavola[i].mime, mime) == 0)
			return &tavola[i];
	}
	return NULL;
}

/*
 * Che formato del filo e' questo, e con che mime lo chiediamo alla sessione.
 *
 * I formati fissi si riconoscono dal numero; quelli registrati DAL NOME, e non
 * dal numero — che ciascun capo si sceglie da sé.  Confondere le due cose
 * significa chiedere PNG e ricevere un elenco di file.
 */
static const Corrispondenza *per_formato(UINT32 formato, const char *nome)
{
	if (nome && *nome)
	{
		for (gsize i = 0; i < G_N_ELEMENTS(tavola); i++)
		{
			if (tavola[i].nome && g_ascii_strcasecmp(tavola[i].nome, nome) == 0)
				return &tavola[i];
		}
		return NULL;
	}

	for (gsize i = 0; i < G_N_ELEMENTS(tavola); i++)
	{
		if (!tavola[i].nome && tavola[i].formato == formato)
			return &tavola[i];
	}
	/* Il DIBV5 si accetta in ingresso, e si tratta come un DIB. */
	if (formato == CF_DIBV5)
		return per_mime("image/bmp");
	return NULL;
}

/* ------------------------------------------------------------------ *
 * Verso il client: la sessione ha copiato qualcosa
 * ------------------------------------------------------------------ */
/*
 * Annuncia al client i tipi che la sessione tiene adesso.
 *
 * Sta in una funzione sua perche' si chiama da DUE momenti diversi, e servono
 * entrambi:
 *
 *   - quando la sessione copia qualcosa (`SelectionOwnerChanged`);
 *   - quando il CLIENT dichiara le proprie capacita', cioe' quando e' pronto ad
 *     ascoltare.
 *
 * ⛔ IL SECONDO E' QUELLO CHE FA FUNZIONARE LA RICONNESSIONE, ed e' costato una
 *    prova.  Accendendo gli appunti, Mutter ci racconta subito che cosa c'e'
 *    nella clipboard; ma se lo si gira al client mentre il canale sta ancora
 *    facendo lo scambio delle capacita', quell'elenco arriva troppo presto e il
 *    client lo lascia cadere — e chi si ricollega trova gli appunti vuoti senza
 *    che nulla si lamenti.  Quindi si ridice, quando lui dice di essere pronto.
 */
static void annuncia_al_client(Scambio *scambio)
{
	CLIPRDR_FORMAT_LIST elenco = { 0 };
	CLIPRDR_FORMAT formati[G_N_ELEMENTS(tavola)] = { 0 };
	UINT32 quanti = 0;
	g_autoptr(GString) detto = g_string_new(NULL);
	g_auto(GStrv) mime = NULL;

	if (!scambio->aperto)
		return;

	g_mutex_lock(&scambio->lucchetto);
	mime = g_strdupv(scambio->sessione_mime);
	g_mutex_unlock(&scambio->lucchetto);

	if (!mime || !mime[0])
		return;

	for (gsize i = 0; mime[i]; i++)
	{
		const Corrispondenza *c = per_mime(mime[i]);
		gboolean gia_messo = FALSE;

		if (!c)
			continue;
		for (UINT32 j = 0; j < quanti; j++)
		{
			if (formati[j].formatId == c->formato)
				gia_messo = TRUE;
		}
		if (gia_messo)
			continue;

		formati[quanti].formatId = c->formato;
		formati[quanti].formatName = (char *) c->nome; /* NULL per i formati fissi */
		quanti++;
		g_string_append_printf(detto, "%s%s", detto->len ? ", " : "", c->mime);
	}

	if (quanti == 0)
	{
		diagnostica("la sessione ha copiato qualcosa che non sappiamo tradurre: non si annuncia");
		return;
	}

	elenco.common.msgType = CB_FORMAT_LIST;
	elenco.numFormats = quanti;
	elenco.formats = formati;

	if (scambio->ctx->ServerFormatList(scambio->ctx, &elenco) != CHANNEL_RC_OK)
		avviso("l'elenco dei formati non e' partito: il client non sapra' che c'e' da incollare");
	else
		informazione("appunti: la sessione ha (%s), annunciato al client", detto->str);
}

/*
 * La sessione ha copiato qualcosa.
 *
 * Gira sul thread degli appunti: si tiene l'elenco dei tipi — serve anche
 * dopo, per sapere in che formato la sessione tenga davvero un'immagine — e lo
 * si annuncia.
 */
static void su_offerta_della_sessione(const char *const *mime, gpointer dati)
{
	Scambio *scambio = dati;

	g_mutex_lock(&scambio->lucchetto);
	g_clear_pointer(&scambio->sessione_mime, g_strfreev);
	scambio->sessione_mime = g_strdupv((GStrv) mime);
	g_mutex_unlock(&scambio->lucchetto);

	annuncia_al_client(scambio);
}

/*
 * Il client vuole incollare: ci chiede i dati di un formato.
 *
 * Gira sul thread del canale, e qui si ASPETTA — `appunti_leggi` apre un
 * descrittore verso l'applicazione che possiede la selezione e lo legge fino in
 * fondo.  Va bene che aspetti: ferma il canale degli appunti, non il ciclo
 * della connessione, e nessun fotogramma dipende da questo thread.
 */
static UINT su_richiesta_del_client(CliprdrServerContext *ctx,
                                    const CLIPRDR_FORMAT_DATA_REQUEST *richiesta)
{
	Scambio *scambio = ctx->custom;
	const Corrispondenza *c = per_formato(richiesta->requestedFormatId, NULL);
	CLIPRDR_FORMAT_DATA_RESPONSE risposta = { 0 };
	g_autoptr(GError) sbaglio = NULL;
	g_autoptr(GBytes) dalla_sessione = NULL;
	g_autoptr(GBytes) convertiti = NULL;

	/* Un formato registrato: il numero e' quello che abbiamo annunciato noi. */
	if (!c)
	{
		for (gsize i = 0; i < G_N_ELEMENTS(tavola); i++)
		{
			if (tavola[i].formato == richiesta->requestedFormatId)
				c = &tavola[i];
		}
	}

	risposta.common.msgType = CB_FORMAT_DATA_RESPONSE;

	/*
	 * Per le immagini il mime della tavola non basta: `CF_DIB` corrisponde a
	 * quattro tipi diversi, e quello giusto e' quello che la SESSIONE ha
	 * davvero.  Si guarda il suo elenco, preferendo il BMP — che non va
	 * convertito — e poi il PNG.
	 */
	if (c && c->formato == CF_DIB)
	{
		static const char *const ordine[] = { "image/bmp", "image/png", "image/jpeg", "image/gif",
			                                  NULL };
		const Corrispondenza *scelto = NULL;

		g_mutex_lock(&scambio->lucchetto);
		for (gsize i = 0; ordine[i] && !scelto; i++)
		{
			for (gsize j = 0; scambio->sessione_mime && scambio->sessione_mime[j]; j++)
			{
				if (g_ascii_strcasecmp(scambio->sessione_mime[j], ordine[i]) == 0)
				{
					scelto = per_mime(ordine[i]);
					break;
				}
			}
		}
		g_mutex_unlock(&scambio->lucchetto);
		if (scelto)
			c = scelto;
	}

	if (c)
	{
		/* Thread del canale: si prende e si lascia (vedi il commento su
		 * `Scambio`).  Se la sessione se n'e' andata, non c'e' piu' niente da
		 * leggere e si risponde di no. */
		Appunti *appunti = palco_appunti_prendi(scambio->palco);

		if (appunti)
			dalla_sessione = appunti_leggi(appunti, c->mime, &sbaglio);
		palco_appunti_lascia(scambio->palco);
	}

	if (dalla_sessione)
		convertiti = converti_verso_client(c->formato, c->mime, dalla_sessione);

	if (!convertiti)
	{
		/*
		 * Si risponde CON UN FALLIMENTO, non con il silenzio: un client che non
		 * riceve risposta a un `FORMAT_DATA_REQUEST` resta con il menu «Incolla»
		 * bloccato, e non c'e' niente che lo sblocchi.
		 */
		avviso("appunti: non ho «%s» da dare al client (%s)",
		       c ? c->mime : "quel formato",
		       sbaglio ? sbaglio->message : "formato non tradotto");
		risposta.common.msgFlags = CB_RESPONSE_FAIL;
		risposta.common.dataLen = 0;
		risposta.requestedFormatData = NULL;
		return ctx->ServerFormatDataResponse(ctx, &risposta);
	}

	{
		gsize quanti = 0;
		const guint8 *dati = g_bytes_get_data(convertiti, &quanti);

		risposta.common.msgFlags = CB_RESPONSE_OK;
		risposta.common.dataLen = (UINT32) quanti;
		risposta.requestedFormatData = dati;

		scambio->verso_client++;
		informazione("appunti: dati «%s» al client, %" G_GSIZE_FORMAT " byte", c->mime, quanti);
		return ctx->ServerFormatDataResponse(ctx, &risposta);
	}
}

/* ------------------------------------------------------------------ *
 * Verso la sessione: il client ha copiato qualcosa
 * ------------------------------------------------------------------ */
static UINT su_elenco_del_client(CliprdrServerContext *ctx, const CLIPRDR_FORMAT_LIST *elenco)
{
	Scambio *scambio = ctx->custom;
	CLIPRDR_FORMAT_LIST_RESPONSE risposta = { 0 };
	g_autoptr(GPtrArray) mime = g_ptr_array_new();
	g_autoptr(GString) detto = g_string_new(NULL);
	g_autoptr(GError) sbaglio = NULL;

	g_mutex_lock(&scambio->lucchetto);
	g_array_set_size(scambio->formati_client, 0);

	for (UINT32 i = 0; i < elenco->numFormats; i++)
	{
		const CLIPRDR_FORMAT *f = &elenco->formats[i];
		const Corrispondenza *c = per_formato(f->formatId, f->formatName);
		Corrispondenza mio;
		gboolean gia_messo = FALSE;

		if (!c)
			continue;

		for (guint j = 0; j < scambio->formati_client->len; j++)
		{
			if (g_array_index(scambio->formati_client, Corrispondenza, j).mime == c->mime)
				gia_messo = TRUE;
		}
		if (gia_messo)
			continue;

		/* Si conserva il NUMERO DEL CLIENT, non il nostro: e' quello che va
		 * rimandato indietro quando la sessione chiedera' di incollare. */
		mio.mime = c->mime;
		mio.formato = f->formatId;
		mio.nome = c->nome;
		g_array_append_val(scambio->formati_client, mio);
		g_string_append_printf(detto, "%s%s", detto->len ? ", " : "", c->mime);

		if (c->formato == CF_DIB)
		{
			/*
			 * Il client ha un'immagine, e la tiene in DIB.  Alla sessione si
			 * offrono i tipi che le applicazioni si aspettano — PNG per primo —
			 * e a convertire penseremo noi quando chiederanno.
			 */
			for (gsize k = 0; mime_immagine[k]; k++)
				g_ptr_array_add(mime, (gpointer) mime_immagine[k]);
		}
		else
		{
			g_ptr_array_add(mime, (gpointer) c->mime);
		}
	}
	g_mutex_unlock(&scambio->lucchetto);

	/* Il riscontro va mandato SEMPRE, anche se non abbiamo capito niente: senza,
	 * i client severi non mandano un secondo elenco per il resto della
	 * sessione. */
	risposta.common.msgType = CB_FORMAT_LIST_RESPONSE;
	risposta.common.msgFlags = CB_RESPONSE_OK;
	ctx->ServerFormatListResponse(ctx, &risposta);

	if (mime->len == 0)
	{
		diagnostica("appunti: il client ha copiato solo formati che non sappiamo tradurre");
		return CHANNEL_RC_OK;
	}

	g_ptr_array_add(mime, NULL);
	{
		Appunti *appunti = palco_appunti_prendi(scambio->palco);

		if (!appunti)
			diagnostica("appunti: la sessione non c'e' piu': l'offerta del client resta qui");
		else if (appunti_offri(appunti, (const char *const *) mime->pdata, &sbaglio))
			informazione("appunti: il client ha copiato (%s), offerto alla sessione", detto->str);
		else
			avviso("appunti: la sessione non ha accettato l'offerta (%s)", sbaglio->message);
		palco_appunti_lascia(scambio->palco);
	}

	return CHANNEL_RC_OK;
}

/*
 * La sessione vuole incollare quel che ha il client.
 *
 * Gira sul thread degli appunti: si chiede al client e si torna subito.  La
 * risposta arrivera' sul thread del canale, che chiudera' la richiesta.
 */
static void su_richiesta_della_sessione(const char *mime, guint32 serial, gpointer dati)
{
	Scambio *scambio = dati;
	CLIPRDR_FORMAT_DATA_REQUEST richiesta = { 0 };
	UINT32 formato = 0;
	const char *mime_scelto = NULL;
	guint32 vecchio_serial = 0;
	gboolean c_era = FALSE;

	g_mutex_lock(&scambio->lucchetto);

	{
		const Corrispondenza *voluto = per_mime(mime);

		for (guint i = 0; i < scambio->formati_client->len; i++)
		{
			const Corrispondenza *c = &g_array_index(scambio->formati_client, Corrispondenza, i);

			/*
			 * Si confronta il FORMATO DEL FILO, non il mime: la sessione puo'
			 * chiedere `image/png` mentre il client ha un `CF_DIB`, ed e' il
			 * caso normale — la conversione la facciamo noi.
			 */
			if (voluto && c->formato == voluto->formato)
			{
				formato = c->formato;
				mime_scelto = voluto->mime;
				break;
			}
		}
	}

	if (!mime_scelto)
	{
		g_mutex_unlock(&scambio->lucchetto);
		diagnostica("appunti: la sessione chiede «%s», che il client non offre", mime);
		appunti_rispondi(scambio->appunti, serial, NULL);
		return;
	}

	/*
	 * ⛔ UNA RICHIESTA PER VOLTA, e la vecchia si chiude prima di aprire la
	 *    nuova.  Se non lo si facesse, la prima resterebbe appesa per sempre e
	 *    l'applicazione che l'aveva fatta con lei — e sarebbe un desktop che si
	 *    pianta incollando due volte di fila.
	 */
	if (scambio->in_corso)
	{
		c_era = TRUE;
		vecchio_serial = scambio->serial;
	}

	scambio->in_corso = TRUE;
	scambio->serial = serial;
	scambio->formato_chiesto = formato;
	scambio->mime_chiesto = mime_scelto;
	g_mutex_unlock(&scambio->lucchetto);

	if (c_era)
	{
		avviso("appunti: una richiesta era ancora in attesa, la chiudo per fare posto");
		appunti_rispondi(scambio->appunti, vecchio_serial, NULL);
	}

	richiesta.common.msgType = CB_FORMAT_DATA_REQUEST;
	richiesta.requestedFormatId = formato;
	if (scambio->ctx->ServerFormatDataRequest(scambio->ctx, &richiesta) != CHANNEL_RC_OK)
	{
		avviso("appunti: la richiesta al client non e' partita");
		g_mutex_lock(&scambio->lucchetto);
		scambio->in_corso = FALSE;
		g_mutex_unlock(&scambio->lucchetto);
		appunti_rispondi(scambio->appunti, serial, NULL);
	}
}

/* Consegna alla sessione, dal thread del canale: si prende e si lascia. */
static void consegna(Scambio *scambio, guint32 serial, GBytes *dati)
{
	Appunti *appunti = palco_appunti_prendi(scambio->palco);

	if (appunti)
		appunti_rispondi(appunti, serial, dati);
	palco_appunti_lascia(scambio->palco);
}

/* La risposta del client alla richiesta di prima. */
static UINT su_risposta_del_client(CliprdrServerContext *ctx,
                                   const CLIPRDR_FORMAT_DATA_RESPONSE *risposta)
{
	Scambio *scambio = ctx->custom;
	g_autoptr(GBytes) convertiti = NULL;
	guint32 serial;
	UINT32 formato;
	const char *mime;

	g_mutex_lock(&scambio->lucchetto);
	if (!scambio->in_corso)
	{
		g_mutex_unlock(&scambio->lucchetto);
		diagnostica("appunti: risposta del client senza richiesta in corso, la lascio cadere");
		return CHANNEL_RC_OK;
	}
	serial = scambio->serial;
	formato = scambio->formato_chiesto;
	mime = scambio->mime_chiesto;
	scambio->in_corso = FALSE;
	g_mutex_unlock(&scambio->lucchetto);

	if ((risposta->common.msgFlags & CB_RESPONSE_FAIL) || !risposta->requestedFormatData ||
	    risposta->common.dataLen == 0)
	{
		avviso("appunti: il client non ha consegnato «%s»", mime);
		consegna(scambio, serial, NULL);
		return CHANNEL_RC_OK;
	}

	convertiti = converti_verso_sessione(formato, mime, risposta->requestedFormatData,
	                                     risposta->common.dataLen);
	if (!convertiti)
	{
		avviso("appunti: «%s» dal client non e' traducibile (%u byte)", mime,
		       risposta->common.dataLen);
		consegna(scambio, serial, NULL);
		return CHANNEL_RC_OK;
	}

	scambio->verso_sessione++;
	informazione("appunti: «%s» dal client alla sessione, %" G_GSIZE_FORMAT " byte", mime,
	             g_bytes_get_size(convertiti));
	consegna(scambio, serial, convertiti);
	return CHANNEL_RC_OK;
}

/* ------------------------------------------------------------------ *
 * Le richiamate di servizio
 * ------------------------------------------------------------------ */
static UINT su_capacita_del_client(CliprdrServerContext *ctx,
                                   const CLIPRDR_CAPABILITIES *capacita)
{
	Scambio *scambio = ctx->custom;

	/* Quel che il client dichiara e' gia' in §1.2 e §1.3 di REFERENCE.md; qui
	 * serve averlo nel registro della sessione, non dedotto da un'altra prova. */
	for (UINT32 i = 0; i < capacita->cCapabilitiesSets; i++)
	{
		const CLIPRDR_GENERAL_CAPABILITY_SET *generale =
		    (const CLIPRDR_GENERAL_CAPABILITY_SET *) &capacita->capabilitySets[i];

		if (generale->capabilitySetType != CB_CAPSTYPE_GENERAL)
			continue;
		informazione("appunti del client: versione %u, nomi lunghi %s, file %s, blocco dati %s",
		             generale->version,
		             (generale->generalFlags & CB_USE_LONG_FORMAT_NAMES) ? "si" : "no",
		             (generale->generalFlags & CB_STREAM_FILECLIP_ENABLED) ? "si" : "no",
		             (generale->generalFlags & CB_CAN_LOCK_CLIPDATA) ? "si" : "no");
	}

	/* Adesso che il client dice di essere pronto, gli si racconta che cosa c'e'
	 * gia' nella clipboard della sessione.  E' la riga che fa ritrovare gli
	 * appunti a chi si ricollega. */
	annuncia_al_client(scambio);
	return CHANNEL_RC_OK;
}

static UINT su_cartella_temporanea(CliprdrServerContext *ctx,
                                   const CLIPRDR_TEMP_DIRECTORY *cartella)
{
	/* Serve solo ai file, che sono fuori da questa fase. */
	return CHANNEL_RC_OK;
}

static UINT su_blocco(CliprdrServerContext *ctx, const CLIPRDR_LOCK_CLIPBOARD_DATA *blocco)
{
	return CHANNEL_RC_OK; /* si accetta e si ignora: non teniamo copie datate */
}

static UINT su_sblocco(CliprdrServerContext *ctx, const CLIPRDR_UNLOCK_CLIPBOARD_DATA *sblocco)
{
	return CHANNEL_RC_OK;
}

static UINT su_riscontro_elenco(CliprdrServerContext *ctx,
                                const CLIPRDR_FORMAT_LIST_RESPONSE *risposta)
{
	if (risposta->common.msgFlags & CB_RESPONSE_FAIL)
		avviso("appunti: il client ha rifiutato il nostro elenco di formati");
	return CHANNEL_RC_OK;
}

/*
 * I file: si rifiuta, e si rifiuta DICENDOLO.
 *
 * Esporre i file del client dentro la sessione vuol dire un filesystem
 * virtuale FUSE — 1591 righe nel riferimento — ed e' l'ultima voce della fase
 * 8, non questa.  Chi non risponde affatto lascia il client in attesa.
 */
static UINT su_richiesta_file(CliprdrServerContext *ctx,
                              const CLIPRDR_FILE_CONTENTS_REQUEST *richiesta)
{
	CLIPRDR_FILE_CONTENTS_RESPONSE risposta = { 0 };

	risposta.common.msgType = CB_FILECONTENTS_RESPONSE;
	risposta.common.msgFlags = CB_RESPONSE_FAIL;
	risposta.streamId = richiesta->streamId;
	diagnostica("appunti: il client chiede il contenuto di un file, e i file non li facciamo");
	return ctx->ServerFileContentsResponse(ctx, &risposta);
}

/* ------------------------------------------------------------------ *
 * Ciclo di vita
 * ------------------------------------------------------------------ */
Scambio *scambio_apri(HANDLE vcm, rdpContext *contesto, Palco *palco)
{
	Scambio *scambio = g_new0(Scambio, 1);
	Appunti *appunti = palco_appunti_prendi(palco);

	if (!appunti)
	{
		/* La sessione non ha appunti — Mutter li ha negati, o e' gia' finita.
		 * Non e' un guasto: e' una sessione senza copia-incolla, e lo ha gia'
		 * detto il palco. */
		palco_appunti_lascia(palco);
		g_free(scambio);
		return NULL;
	}

	g_mutex_init(&scambio->lucchetto);
	scambio->palco = palco;
	scambio->appunti = appunti;
	scambio->formati_client = g_array_new(FALSE, FALSE, sizeof(Corrispondenza));

	scambio->ctx = cliprdr_server_context_new(vcm);
	if (!scambio->ctx)
	{
		errore("cliprdr_server_context_new fallita");
		goto guasto;
	}

	scambio->ctx->custom = scambio;
	scambio->ctx->rdpcontext = contesto;

	/*
	 * Quel che il server dichiara di saper fare.
	 *
	 * I nomi lunghi servono ai formati registrati (PNG, HTML Format…), e li
	 * dichiarano tutti e tre i client (§1.2 e §1.3).  Tutto il resto riguarda i
	 * file, che non facciamo: dichiararlo sarebbe una promessa da non
	 * mantenere.
	 */
	scambio->ctx->useLongFormatNames = TRUE;
	scambio->ctx->streamFileClipEnabled = FALSE;
	scambio->ctx->fileClipNoFilePaths = FALSE;
	scambio->ctx->canLockClipData = FALSE;
	scambio->ctx->hasHugeFileSupport = FALSE;

	scambio->ctx->ClientCapabilities = su_capacita_del_client;
	scambio->ctx->TempDirectory = su_cartella_temporanea;
	scambio->ctx->ClientFormatList = su_elenco_del_client;
	scambio->ctx->ClientFormatListResponse = su_riscontro_elenco;
	scambio->ctx->ClientFormatDataRequest = su_richiesta_del_client;
	scambio->ctx->ClientFormatDataResponse = su_risposta_del_client;
	scambio->ctx->ClientLockClipboardData = su_blocco;
	scambio->ctx->ClientUnlockClipboardData = su_sblocco;
	scambio->ctx->ClientFileContentsRequest = su_richiesta_file;

	if (scambio->ctx->Open(scambio->ctx) != CHANNEL_RC_OK)
	{
		avviso("apertura del canale degli appunti fallita");
		goto guasto;
	}

	/*
	 * ⛔ R22 — SERVE IL SUO THREAD, e non e' una comodita'.
	 *
	 *    La sequenza iniziale — capacita' piu' `MONITOR_READY` — la esegue una
	 *    funzione statica di FreeRDP che chiama SOLO il thread di `Start`.
	 *    Aprendo il canale e pompandolo dal nostro ciclo, il canale resterebbe
	 *    aperto e muto, e il client aspetterebbe per sempre un `MONITOR_READY`
	 *    che nessuno manda — senza un errore da nessuna parte.
	 */
	if (scambio->ctx->Start(scambio->ctx) != CHANNEL_RC_OK)
	{
		avviso("il canale degli appunti non e' partito");
		goto guasto;
	}
	scambio->aperto = TRUE;

	/* Da adesso i due segnali della sessione arrivano qui. */
	appunti_ascolta(appunti, su_offerta_della_sessione, su_richiesta_della_sessione, scambio);

	/*
	 * ⛔ E SI PRENDE QUEL CHE LA SESSIONE HA GIA' IN MANO.
	 *
	 *    Gli appunti sono accesi da quando esiste il palco, e il segnale che
	 *    dice «c'e' qualcosa di nuovo» e' passato prima che questa connessione
	 *    esistesse.  Chi si ricollega deve poterlo sapere lo stesso, e lo sa da
	 *    qui — l'annuncio al client parte poi, quando dichiara le proprie
	 *    capacita' (vedi `annuncia_al_client`).
	 */
	scambio->sessione_mime = appunti_ultimi_tipi(appunti);
	palco_appunti_lascia(palco);

	diagnostica("canale degli appunti aperto");
	return scambio;

guasto:
	palco_appunti_lascia(palco);
	scambio_chiudi(scambio);
	return NULL;
}

void scambio_chiudi(Scambio *scambio)
{
	if (!scambio)
		return;

	/*
	 * Prima si smette di ascoltare la sessione — e la chiamata aspetta chi e' a
	 * meta' strada — poi si ferma il canale.  All'incontrario, un segnale
	 * arrivato durante lo smontaggio troverebbe un contesto gia' liberato.
	 *
	 * Si passa dal palco, come si deve fare da questo thread: se la sessione se
	 * n'e' andata prima della connessione, gli appunti non ci sono piu' e non
	 * c'e' niente da spegnere.
	 */
	{
		Appunti *appunti = palco_appunti_prendi(scambio->palco);

		if (appunti)
		{
			appunti_ascolta(appunti, NULL, NULL, NULL);

			/* Una richiesta rimasta in sospeso si chiude: chi incolla sta
			 * aspettando, e la sessione sopravvive alla connessione. */
			if (scambio->in_corso)
			{
				diagnostica("appunti: chiudo la richiesta rimasta in sospeso");
				appunti_rispondi(appunti, scambio->serial, NULL);
			}
		}
		scambio->in_corso = FALSE;
		palco_appunti_lascia(scambio->palco);
	}

	if (scambio->ctx)
	{
		if (scambio->aperto)
			scambio->ctx->Stop(scambio->ctx);
		cliprdr_server_context_free(scambio->ctx);
	}

	if (scambio->formati_client)
		g_array_free(scambio->formati_client, TRUE);
	g_strfreev(scambio->sessione_mime);
	g_mutex_clear(&scambio->lucchetto);
	g_free(scambio);
}

void scambio_conti(const Scambio *scambio, guint *verso_client, guint *verso_sessione)
{
	if (!scambio)
		return;
	if (verso_client)
		*verso_client = scambio->verso_client;
	if (verso_sessione)
		*verso_sessione = scambio->verso_sessione;
}
