/*
 * cursore.c — da `struct spa_meta_cursor` (PipeWire) a `CursoreForma` (RCP §7.2).
 *
 * ⛔ Il contratto sta in `cursore.h`, che e' del coordinatore: qui si ATTUA, non si
 *    cambia la cucitura.  Chi trova il contratto sbagliato lo DICE e si ferma —
 *    non lo aggira.
 *
 * ===========================================================================
 * ⛔ IL LAVORO CHE STA QUI E NON STA NE' IN `cattura.c` NE' IN `rcp.c`
 *
 * 1. **distinguere tre stati che il metadato confonde in uno**:
 *
 *      NON PERVENUTO   il metadato non c'e' affatto ⇒ questa funzione non
 *                      viene nemmeno chiamata, e `cattura.c` lo CONTA.  Sul
 *                      filo non parte niente: il client tiene il suo puntatore.
 *      NASCOSTO        il puntatore c'e' e non si deve vedere ⇒ `CURSORE_FORMA`
 *                      con 0x0 e punto attivo 0,0 (RCP §5.5).
 *      INVARIATO       il metadato arriva a OGNI buffer, e quasi sempre e' lo
 *                      stesso di prima ⇒ non si manda niente.
 *
 * 2. far rispettare i limiti di RCP §7.2 **da questa parte**: oltre 256 non si
 *    manda, o il ricevente chiude la sessione per `ERRORE_PROTOCOLLO` — cioe'
 *    un nostro errore qui fa cadere la sessione del client;
 *
 * 3. voltare i byte: Mutter consegna **RGBA premoltiplicato**, il filo vuole
 *    **BGRA premoltiplicato**.
 *
 * ===========================================================================
 * ⛔ COME MUTTER RIEMPIE IL METADATO — `[R]` 14 agosto 2026, letto riga per riga
 *    in `reference-gnome/mutter/src/backends/meta-screen-cast-stream-src.c` e
 *    `meta-screen-cast-virtual-stream-src.c` (e' il nostro caso: `RecordVirtual`).
 *
 *   | quando                                        | che cosa arriva                |
 *   |-----------------------------------------------|--------------------------------|
 *   | puntatore non visibile, o fuori dal flusso     | `id = 0`  (`unset_cursor_…`)   |
 *   | la bitmap NON e' cambiata                      | `id = 1`, `bitmap_offset = 0`  |
 *   | la bitmap e' cambiata, e c'e' una texture      | bitmap `RGBA` con i pixel      |
 *   | la bitmap e' cambiata, e la texture NON c'e'   | bitmap AZZERATA (`set_empty…`) |
 *
 *   ⛔ `set_empty_cursor_sprite_metadata()` scrive `format = RGBA`, poi
 *      `*spa_meta_bitmap = (struct spa_meta_bitmap) { 0 };` — cioe' azzera tutto
 *      quel che aveva appena scritto.  ⇒ arriva una bitmap con `format = 0`,
 *      `0x0`, `stride = 0`, `offset = 0`.  L'INTENZIONE di Mutter e' «cursore
 *      senza immagine», cioe' NASCOSTO; la lettera di `spa/buffer/meta.h` dice
 *      invece che `format = 0` va trattato come «nessuna informazione nuova».
 *      ⇒ Qui si segue **l'intenzione**, perche' e' l'unico modo in cui su Mutter
 *      un cursore invisibile puo' arrivare, e perche' `offset = 0` la conferma:
 *      la stessa intestazione dice *«an offset of 0 means no image data
 *      (invisible)»*.  ⚠ La scelta e' DICHIARATA qui perche' su un altro
 *      compositore potrebbe voler dire l'altra cosa: e' `[R]` su Mutter, `[?]`
 *      altrove.
 *
 *   ⛔ E LA TRAPPOLA DEL RIACCENDERSI: `bitmap_offset = 0` significa «la forma
 *      non e' cambiata», ma dopo un `id = 0` il client non ha piu' niente da
 *      disegnare.  Se al ritorno del puntatore arrivasse solo la posizione, il
 *      cursore resterebbe sparito **senza nessun errore**.  ⇒ l'ultima forma
 *      VISIBILE si conserva, e si RIMANDA quando il puntatore torna.
 *
 * ⚠ E LA MISURA CHE MUTTER PUO' MANDARE E' PIU' GRANDE DEL FILO: il metadato e'
 *   allocato per **384x384** (`CURSOR_META_SIZE(384, 384)`), RCP §7.2 si ferma a
 *   **256**.  Il taglio e' un ripiego, e come tale si DICHIARA nel registro.
 */
#include "cursore.h"

#include "registro.h"

#include <spa/buffer/meta.h>
#include <spa/param/video/raw.h>

#include <inttypes.h>
#include <stdlib.h>
#include <string.h>

#define AREA "cursore"

/* Quanti byte al massimo puo' occupare un'immagine consegnata sul filo. */
#define BYTE_MAX ((size_t) CURSORE_MAX_LATO * (size_t) CURSORE_MAX_LATO * 4u)

/* ⚠ Un tetto di ragionevolezza PRIMA di moltiplicare: una misura assurda letta
 *   da memoria altrui non deve diventare una moltiplicazione che trabocca.  Non
 *   e' il limite del filo (che e' 256): e' il limite oltre il quale si dichiara
 *   «malformato» invece di «tagliato». */
#define LATO_ASSURDO 8192u

struct cursore
{
	CursoreArrivata quando_cambia;
	void *chi;

	uint32_t serie;

	int consegnata; /* si e' gia' consegnato qualcosa?              */
	int nascosto;   /* l'ultima consegnata era 0x0                  */

	/*
	 * L'ultima forma VISIBILE conosciuta.  ⛔ Sopravvive al nascondimento
	 * apposta: Mutter riaccende il puntatore senza rimandare la bitmap.
	 */
	int ha_forma;
	uint16_t larghezza, altezza;
	int16_t attivo_x, attivo_y;
	uint8_t *immagine; /* quella CONSEGNATA: vive fino al richiamo dopo */
	uint8_t *scratch;  /* dove si volta la nuova, per poterla CONFRONTARE */
	size_t byte;

	/* I conti: servono a distinguere «non e' cambiato» da «non e' arrivato»
	 * sei ore dopo, e sono il numero che il banco confronta col proprio. */
	struct
	{
		uint64_t visti;        /* chiamate a cursore_metadato            */
		uint64_t id_zero;      /* il produttore dice «nessun cursore»    */
		uint64_t senza_bitmap; /* id != 0 ma bitmap_offset == 0          */
		uint64_t con_bitmap;   /* una bitmap c'era                       */
		uint64_t vuote;        /* bitmap che vuol dire «nascosto»        */
		uint64_t uguali;       /* bitmap identica alla precedente        */
		uint64_t cambi;        /* CursoreForma consegnate                */
		uint64_t tagliate;     /* piu' grandi di 256: ⛔ ripiego         */
		uint64_t punto_fuori;  /* punto attivo fuori dall'immagine       */
		uint64_t malformate;
		uint64_t forma_ignota; /* visibile, ma la forma non l'abbiamo mai vista */
		uint64_t rifiutate;    /* chi riceve ha detto no                 */
	} conto;

	/* I guai che si dicono UNA volta e non a ogni fotogramma. */
	int detto_formato;
	uint32_t formato_visto;
	int detto_taglio;
	int detto_punto;
	int detto_ignota;
};

/* ------------------------------------------------------------------ *
 *  La consegna
 * ------------------------------------------------------------------ */

static int consegna(Cursore *c, const CursoreForma *forma)
{
	int esito;

	c->conto.cambi++;
	c->consegnata = 1;
	if (!c->quando_cambia)
		return 1;
	esito = c->quando_cambia(c->chi, forma);
	if (esito < 0)
	{
		c->conto.rifiutate++;
		registro_dice(AREA, "⛔ chi riceve ha RIFIUTATO la forma %ux%u (serie %u): non e' partita",
		              (unsigned) forma->larghezza, (unsigned) forma->altezza,
		              (unsigned) forma->serie);
		return -1;
	}
	return 1;
}

/*
 * ⛔ NASCOSTO E' UNO STATO, NON UN'ASSENZA: si manda 0x0 con punto attivo 0,0
 *    (RCP §5.5), e si manda UNA volta sola — non a ogni buffer in cui il
 *    puntatore continua a non esserci.
 */
static int consegna_nascosto(Cursore *c, const char *motivo)
{
	CursoreForma forma;

	if (c->consegnata && c->nascosto)
		return 0;

	c->serie++;
	c->nascosto = 1;

	memset(&forma, 0, sizeof forma);
	forma.serie = c->serie;
	forma.immagine = NULL;

	registro_dice(AREA, "il puntatore si NASCONDE (%s) — CURSORE_FORMA 0x0, serie %u", motivo,
	              (unsigned) c->serie);
	return consegna(c, &forma);
}

/* Il puntatore torna e Mutter non rimanda la bitmap: si rimanda l'ultima nota. */
static int consegna_forma_conservata(Cursore *c)
{
	CursoreForma forma;

	c->serie++;
	c->nascosto = 0;

	memset(&forma, 0, sizeof forma);
	forma.larghezza = c->larghezza;
	forma.altezza = c->altezza;
	forma.attivo_x = c->attivo_x;
	forma.attivo_y = c->attivo_y;
	forma.serie = c->serie;
	forma.immagine = c->immagine;

	registro_dice(AREA,
	              "il puntatore RITORNA e Mutter non rimanda la forma: si rimanda l'ultima nota "
	              "(%ux%u, serie %u)",
	              (unsigned) c->larghezza, (unsigned) c->altezza, (unsigned) c->serie);
	return consegna(c, &forma);
}

/* ------------------------------------------------------------------ *
 *  I byte: da RGBA/BGRA premoltiplicato a BGRA premoltiplicato
 * ------------------------------------------------------------------ */

/*
 * ⛔ Il formato si guarda, non si da' per scontato.  Mutter manda
 *    `SPA_VIDEO_FORMAT_RGBA` — cioe' `COGL_PIXEL_FORMAT_RGBA_8888_PRE`, che e'
 *    **premoltiplicato** `[R]` — e il filo vuole BGRA premoltiplicato: cambia
 *    solo l'ordine, non l'alfa.
 *
 * ⚠ Le varianti senza alfa (`RGBx`, `BGRx`) si accettano con alfa piena: sono
 *   opache per definizione, e una forma opaca e' meglio di nessuna forma.
 *
 * Ritorna 1 se va invertito rosso con blu, 0 se si copia dritto, -1 se il
 * formato non si sa leggere.
 */
static int verso_dei_byte(uint32_t formato, int *alfa_piena)
{
	*alfa_piena = 0;
	switch (formato)
	{
	case SPA_VIDEO_FORMAT_RGBA:
		return 1;
	case SPA_VIDEO_FORMAT_BGRA:
		return 0;
	case SPA_VIDEO_FORMAT_RGBx:
		*alfa_piena = 1;
		return 1;
	case SPA_VIDEO_FORMAT_BGRx:
		*alfa_piena = 1;
		return 0;
	default:
		return -1;
	}
}

/* ------------------------------------------------------------------ *
 *  Le chiamate
 * ------------------------------------------------------------------ */

Cursore *cursore_apri(CursoreArrivata quando_cambia, void *chi)
{
	Cursore *c = calloc(1, sizeof *c);

	if (!c)
		return NULL;
	c->immagine = malloc(BYTE_MAX);
	c->scratch = malloc(BYTE_MAX);
	if (!c->immagine || !c->scratch)
	{
		free(c->immagine);
		free(c->scratch);
		free(c);
		return NULL;
	}
	c->quando_cambia = quando_cambia;
	c->chi = chi;
	return c;
}

int cursore_metadato(Cursore *c, const void *spa_meta_cursor, size_t dimensione)
{
	const struct spa_meta_cursor *m = spa_meta_cursor;
	const struct spa_meta_bitmap *b;
	const uint8_t *base = spa_meta_cursor;
	size_t inizio_pixel, servono, byte;
	uint32_t sorgente_l, sorgente_a;
	uint16_t larghezza, altezza;
	int16_t attivo_x, attivo_y;
	int inverti, alfa_piena;
	uint32_t y;
	uint8_t *scambio;
	CursoreForma forma;

	if (!c)
		return -1;
	c->conto.visti++;

	/*
	 * ⛔ «Troppo corto» NON e' «nascosto»: e' un metadato che non si sa
	 *    leggere, e si dichiara invece di produrre un cursore fatto di memoria
	 *    altrui — che e' esattamente il difetto che RCP §7.2 nomina.
	 */
	if (!m || dimensione < sizeof *m)
	{
		c->conto.malformate++;
		registro_dice(AREA, "⛔ metadato del cursore troppo corto: %zu byte, ne servono %zu",
		              dimensione, sizeof *m);
		return -1;
	}

	/* --- 1. il produttore dice «nessun cursore» ------------------------- */
	if (!spa_meta_cursor_is_valid(m))
	{
		c->conto.id_zero++;
		return consegna_nascosto(c, "id = 0");
	}

	/* --- 2. la forma non e' cambiata ------------------------------------ */
	if (m->bitmap_offset == 0)
	{
		c->conto.senza_bitmap++;
		if (!c->nascosto && c->consegnata)
			return 0;
		if (c->ha_forma)
			return consegna_forma_conservata(c);
		/*
		 * ⛔ Il puntatore c'e' e la sua forma non l'abbiamo MAI vista: non e'
		 *    «nascosto» e non e' «invariato».  Non si inventa niente — si
		 *    dichiara e si aspetta la prima bitmap.
		 */
		c->conto.forma_ignota++;
		if (!c->detto_ignota)
		{
			c->detto_ignota = 1;
			registro_dice(AREA,
			              "⚠ il puntatore e' visibile ma la sua forma non e' ancora arrivata "
			              "(solo posizione): niente da mandare, si aspetta");
		}
		return 0;
	}

	/* --- 3. c'e' una bitmap: prima si controlla che ci stia ------------- */
	if (m->bitmap_offset < sizeof *m || m->bitmap_offset > dimensione ||
	    dimensione - m->bitmap_offset < sizeof *b)
	{
		c->conto.malformate++;
		registro_dice(AREA, "⛔ bitmap_offset %u fuori dal metadato (%zu byte): scartata",
		              (unsigned) m->bitmap_offset, dimensione);
		return -1;
	}
	b = (const struct spa_meta_bitmap *) (base + m->bitmap_offset);
	c->conto.con_bitmap++;

	/*
	 * --- 4. la bitmap che vuol dire «nascosto» ---------------------------
	 * Vedi il riquadro in cima: su Mutter e' `set_empty_cursor_sprite_metadata`,
	 * che azzera tutto.  `offset == 0` e' la stessa cosa detta da
	 * `spa/buffer/meta.h`: «no image data (invisible)».
	 */
	if (b->format == 0 || b->offset == 0 || b->size.width == 0 || b->size.height == 0)
	{
		c->conto.vuote++;
		return consegna_nascosto(c, "bitmap vuota (il puntatore non ha immagine)");
	}

	sorgente_l = b->size.width;
	sorgente_a = b->size.height;
	if (sorgente_l > LATO_ASSURDO || sorgente_a > LATO_ASSURDO || b->stride <= 0 ||
	    (uint32_t) b->stride < sorgente_l * 4u || b->offset < sizeof *b)
	{
		c->conto.malformate++;
		registro_dice(AREA, "⛔ bitmap non interpretabile: %ux%u, stride %d, offset %u",
		              (unsigned) sorgente_l, (unsigned) sorgente_a, (int) b->stride,
		              (unsigned) b->offset);
		return -1;
	}

	inizio_pixel = (size_t) m->bitmap_offset + (size_t) b->offset;
	servono = (size_t) b->stride * (size_t) (sorgente_a - 1) + (size_t) sorgente_l * 4u;
	if (inizio_pixel > dimensione || dimensione - inizio_pixel < servono)
	{
		c->conto.malformate++;
		registro_dice(AREA,
		              "⛔ i pixel del cursore non ci stanno: servono %zu byte da %zu, il metadato "
		              "ne ha %zu",
		              servono, inizio_pixel, dimensione);
		return -1;
	}

	inverti = verso_dei_byte(b->format, &alfa_piena);
	if (inverti < 0)
	{
		c->conto.malformate++;
		if (!c->detto_formato || c->formato_visto != b->format)
		{
			c->detto_formato = 1;
			c->formato_visto = b->format;
			registro_dice(AREA,
			              "⛔ formato del cursore non gestito (SPA %u): non si manda niente "
			              "invece di mandare i colori scambiati",
			              (unsigned) b->format);
		}
		return -1;
	}

	/*
	 * --- 5. ⛔ IL LIMITE DI RCP §7.2 SI FA RISPETTARE QUI -----------------
	 *
	 * Oltre 256 il ricevente chiude la sessione per `ERRORE_PROTOCOLLO`: e' il
	 * nostro difetto che fa cadere il client.  ⇒ Si TAGLIA (il verbo e' di
	 * `cursore.h`), e ⛔ il ripiego si DICHIARA — `CODER.md` §4.2.
	 *
	 * ⚠ Il taglio e' l'angolo in alto a sinistra, che e' dove sta il disegno di
	 *   ogni cursore e dove sta il punto attivo.  Che sia la scelta giusta e'
	 *   `[?]`: non e' mai stato visto scattare (Mutter alloca il metadato per
	 *   384x384, ma i temi di GNOME arrivano a 64-96).  Se un giorno scattasse
	 *   davvero, la cosa da misurare e' se convenga invece **sottocampionare**.
	 */
	larghezza = sorgente_l > CURSORE_MAX_LATO ? (uint16_t) CURSORE_MAX_LATO : (uint16_t) sorgente_l;
	altezza = sorgente_a > CURSORE_MAX_LATO ? (uint16_t) CURSORE_MAX_LATO : (uint16_t) sorgente_a;
	if (larghezza != sorgente_l || altezza != sorgente_a)
	{
		c->conto.tagliate++;
		if (!c->detto_taglio)
		{
			c->detto_taglio = 1;
			registro_dice(AREA,
			              "⛔ RIPIEGO: il cursore e' %ux%u, il filo si ferma a %u (RCP §7.2) — si "
			              "manda l'angolo %ux%u",
			              (unsigned) sorgente_l, (unsigned) sorgente_a,
			              (unsigned) CURSORE_MAX_LATO, (unsigned) larghezza, (unsigned) altezza);
		}
	}

	/*
	 * ⛔ E IL PUNTO ATTIVO DEVE STARE DENTRO L'IMMAGINE (RCP §5.5), o il
	 *    ricevente chiude.  Fuori si riporta dentro, e si dichiara.
	 */
	if (m->hotspot.x < 0 || m->hotspot.x >= (int32_t) larghezza || m->hotspot.y < 0 ||
	    m->hotspot.y >= (int32_t) altezza)
	{
		c->conto.punto_fuori++;
		if (!c->detto_punto)
		{
			c->detto_punto = 1;
			registro_dice(AREA,
			              "⛔ RIPIEGO: punto attivo %d,%d fuori da %ux%u — riportato dentro "
			              "(RCP §5.5)",
			              (int) m->hotspot.x, (int) m->hotspot.y, (unsigned) larghezza,
			              (unsigned) altezza);
		}
		attivo_x = m->hotspot.x < 0
		               ? 0
		               : (m->hotspot.x >= (int32_t) larghezza ? (int16_t) (larghezza - 1)
		                                                      : (int16_t) m->hotspot.x);
		attivo_y = m->hotspot.y < 0
		               ? 0
		               : (m->hotspot.y >= (int32_t) altezza ? (int16_t) (altezza - 1)
		                                                    : (int16_t) m->hotspot.y);
	}
	else
	{
		attivo_x = (int16_t) m->hotspot.x;
		attivo_y = (int16_t) m->hotspot.y;
	}

	/* --- 6. i byte, voltati riga per riga nel banco di lavoro ------------ */
	byte = (size_t) larghezza * (size_t) altezza * 4u;
	for (y = 0; y < altezza; y++)
	{
		const uint8_t *riga = base + inizio_pixel + (size_t) y * (size_t) b->stride;
		uint8_t *fuori = c->scratch + (size_t) y * (size_t) larghezza * 4u;
		uint32_t x;

		if (!inverti && !alfa_piena)
		{
			memcpy(fuori, riga, (size_t) larghezza * 4u);
			continue;
		}
		for (x = 0; x < larghezza; x++)
		{
			uint8_t r0 = riga[x * 4 + 0], r1 = riga[x * 4 + 1];
			uint8_t r2 = riga[x * 4 + 2], r3 = riga[x * 4 + 3];

			fuori[x * 4 + 0] = inverti ? r2 : r0;
			fuori[x * 4 + 1] = r1;
			fuori[x * 4 + 2] = inverti ? r0 : r2;
			fuori[x * 4 + 3] = alfa_piena ? 0xFF : r3;
		}
	}

	/*
	 * --- 7. ⛔ E' CAMBIATA DAVVERO? --------------------------------------
	 *
	 * Il metadato arriva a OGNI buffer.  Senza questo confronto si rimanderebbe
	 * la stessa immagine mille volte — che e' la ragione per cui questo modulo
	 * esiste (`cursore.h`).  ⇒ i byte nuovi si voltano nel banco di lavoro, si
	 * CONFRONTANO con quelli consegnati, e solo se differiscono si scambiano i
	 * due secchi (cosi' l'immagine consegnata resta valida fino al richiamo
	 * successivo, come promette `cursore.h`).
	 *
	 * ⚠ E si confronta con l'ultima **consegnata**: dopo un nascondimento il
	 *   client non ha piu' niente da disegnare, quindi la stessa forma va
	 *   rimandata anche se e' identica.
	 */
	if (!c->nascosto && c->consegnata && c->ha_forma && c->larghezza == larghezza &&
	    c->altezza == altezza && c->attivo_x == attivo_x && c->attivo_y == attivo_y &&
	    c->byte == byte && memcmp(c->immagine, c->scratch, byte) == 0)
	{
		c->conto.uguali++;
		return 0;
	}

	scambio = c->immagine;
	c->immagine = c->scratch;
	c->scratch = scambio;

	c->larghezza = larghezza;
	c->altezza = altezza;
	c->attivo_x = attivo_x;
	c->attivo_y = attivo_y;
	c->byte = byte;
	c->ha_forma = 1;
	c->nascosto = 0;
	c->serie++;

	memset(&forma, 0, sizeof forma);
	forma.larghezza = larghezza;
	forma.altezza = altezza;
	forma.attivo_x = attivo_x;
	forma.attivo_y = attivo_y;
	forma.serie = c->serie;
	forma.immagine = c->immagine;

	return consegna(c, &forma);
}

void cursore_chiudi(Cursore *c)
{
	if (!c)
		return;
	registro_dice(AREA,
	              "metadati %" PRIu64 ": id=0 %" PRIu64 ", solo posizione %" PRIu64
	              ", con bitmap %" PRIu64 " (uguali %" PRIu64 ", vuote %" PRIu64
	              ") ⇒ CURSORE_FORMA consegnate %" PRIu64 "; tagliate %" PRIu64
	              ", punto fuori %" PRIu64 ", malformate %" PRIu64 ", rifiutate %" PRIu64
	              ", forma ignota %" PRIu64,
	              c->conto.visti, c->conto.id_zero, c->conto.senza_bitmap, c->conto.con_bitmap,
	              c->conto.uguali, c->conto.vuote, c->conto.cambi, c->conto.tagliate,
	              c->conto.punto_fuori, c->conto.malformate, c->conto.rifiutate,
	              c->conto.forma_ignota);
	free(c->immagine);
	free(c->scratch);
	free(c);
}
