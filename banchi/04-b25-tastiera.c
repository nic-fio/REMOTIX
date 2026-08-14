/*
 * 04-b25-tastiera.c — IL BANCO DELLA TASTIERA (fase 4, anello A5).
 *
 * ⛔ Scritto PRIMA del codice che prova, e CERTIFICATO prima di essere creduto
 *    (`CODER.md` §3.3 e §3.4): `04-b25-lancia.sh` lo punta anche su
 *    QUATTRO implementazioni sbagliate di proposito (`04-b25-guasti.c`) e
 *    PRETENDE che dica ROSSO su ciascuna, e SULLA PROVA GIUSTA.  Un banco che non ha mai visto il difetto non e'
 *    una prova.
 *
 * ---------------------------------------------------------------------------
 * ⭐ CHE COSA PROVA, e perche' non serve ne' QUIC ne' `libei` (`CODER.md` §3.6)
 *
 * Il modulo `src/tastiera.c` risponde a UNA domanda: «per far uscire questo
 * carattere con questa disposizione, quali tasti premo?».  E' una funzione
 * pura: si isola e la si chiama da fuori, su ingressi noti.  Un giro di
 * sessione, compositore e protocollo costerebbe dieci minuti per ogni giro e
 * confonderebbe «la tastiera sbaglia» con «la sessione non e' partita».
 *
 * ---------------------------------------------------------------------------
 * ⛔⛔ COME SI VERIFICA — DAL LATO CHE RICEVE (`CODER.md` §3.8)
 *
 * ⚠ La tentazione era di confrontare i codici usciti con dei numeri scritti a
 *   mano qui dentro («la e' accentata italiana e' il tasto 26 con Maiusc»).
 *   Sarebbe stato un banco che prova la mia aritmetica contro se stessa: se
 *   sbagliassi la tabella, sbaglierebbero tutt'e due allo stesso modo.
 *
 * ⇒ Il banco SIMULA IL COMPOSITORE.  Prende i codici evdev che il modulo gli
 *   consegna, li batte su una macchina a stati `xkb_state` costruita per conto
 *   suo — la stessa macchina che gira dentro Mutter e KWin — e legge CHE
 *   CARATTERE NE ESCE.  Il metro e' il carattere che appare, non il codice che
 *   e' partito.  E' la forma piu' vicina a `I8` che si possa avere senza uno
 *   schermo davanti.
 *
 * ⛔ E LA SIMULAZIONE HA IL SUO CONTROLLO POSITIVO E IL SUO NEGATIVO
 *   (`CODER.md` §3.10), perche' altrimenti «non e' uscito niente» e «non ho
 *   saputo guardare» avrebbero lo stesso aspetto:
 *     · positivo — il simulatore sa vedere una lettera che esce di sicuro?
 *       Si batte il tasto della «a» e ne deve uscire una «a»;
 *     · negativo — il simulatore sa DISTINGUERE?  Si batte il tasto della «e'»
 *       italiana SENZA il Maiusc e ne deve uscire una «e` », cioe' un carattere
 *       DIVERSO.  Un simulatore che dicesse «e' accentata» comunque renderebbe
 *       verde anche l'implementazione che si dimentica i modificatori.
 *
 * ---------------------------------------------------------------------------
 * LE PROVE, e ciascuna e' una tesi di `PIANO.md` righe 630-632 da refutare
 *
 *   1. «e'» con disposizione `it`            ⇒ deve USCIRE la «e'»
 *   2. «e'» con disposizione `us`            ⇒ ⛔ NON producibile, e ⛔ NON deve
 *      uscire una «e» al suo posto
 *   3. «@» su `it` (vuole AltGr) e su `us` (vuole Maiusc): due strade diverse
 *      per lo stesso carattere — e si guarda CHE STRADA e' stata presa
 *   4. un'emoji: non producibile in nessuna delle due — lo strumento sa dire no
 *   5. ⛔⛔ **la disposizione la consegna la SESSIONE**, non la sceglie il nome
 *      negoziato: sessione `it` + client `us` + la `[` ⇒ non deve uscire «è».
 *      E' il caso per cui il contratto e' cambiato il 14 agosto 2026;
 *   6. ⛔ una disposizione che non esiste: `tastiera_apri` DEVE fallire e
 *      dirlo.  Se ripiegasse su `us` in silenzio, il sintomo per l'utente
 *      sarebbe «scrive le lettere sbagliate» e nessuno collegherebbe le due
 *      cose (`CODER.md` §4.2).
 *
 * ---------------------------------------------------------------------------
 * COME SI LEGGE L'ESITO
 *
 *   uscita 0 = VERDE, 1 = ROSSO, 2 = il banco stesso non ha potuto misurare
 *   (che NON e' verde: e' «non ho saputo guardare»).
 *   Le righe vanno anche in JSONL, per ricontrollare senza rieseguire.
 */
#include "../src/tastiera.h"

#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <xkbcommon/xkbcommon.h>
#include <xkbcommon/xkbcommon-names.h>

/* XKB numera i tasti a partire da 8, evdev da 0. */
#define XKB_DA_EVDEV(e) ((xkb_keycode_t)(e) + 8)

static FILE *jsonl;
static int quante_prove, quante_rosse;

/* ------------------------------------------------------------------ *
 * Il registro del banco
 * ------------------------------------------------------------------ */
static void jstr(const char *s)
{
	fputc('"', jsonl);
	for (; *s; s++)
	{
		if (*s == '"' || *s == '\\')
			fprintf(jsonl, "\\%c", *s);
		else if ((unsigned char)*s < 0x20)
			fprintf(jsonl, "\\u%04x", (unsigned char)*s);
		else
			fputc(*s, jsonl);
	}
	fputc('"', jsonl);
}

/* Un carattere Unicode in una forma che si legge sia a schermo sia in JSON. */
static const char *utf8(uint32_t c, char buf[8])
{
	size_t i = 0;
	if (c < 0x80)
		buf[i++] = (char)c;
	else if (c < 0x800)
	{
		buf[i++] = (char)(0xC0 | (c >> 6));
		buf[i++] = (char)(0x80 | (c & 0x3F));
	}
	else if (c < 0x10000)
	{
		buf[i++] = (char)(0xE0 | (c >> 12));
		buf[i++] = (char)(0x80 | ((c >> 6) & 0x3F));
		buf[i++] = (char)(0x80 | (c & 0x3F));
	}
	else
	{
		buf[i++] = (char)(0xF0 | (c >> 18));
		buf[i++] = (char)(0x80 | ((c >> 12) & 0x3F));
		buf[i++] = (char)(0x80 | ((c >> 6) & 0x3F));
		buf[i++] = (char)(0x80 | (c & 0x3F));
	}
	buf[i] = 0;
	return buf;
}

static void esito(const char *prova, int verde, const char *dettaglio)
{
	quante_prove++;
	if (!verde)
		quante_rosse++;
	printf("  %s  %-46s  %s\n", verde ? "✅" : "⛔ ROSSO", prova, dettaglio);
	fprintf(jsonl, "{\"prova\":");
	jstr(prova);
	fprintf(jsonl, ",\"esito\":\"%s\",\"dettaglio\":", verde ? "verde" : "rosso");
	jstr(dettaglio);
	fprintf(jsonl, "}\n");
	fflush(jsonl);
}

/* ------------------------------------------------------------------ *
 * IL SIMULATORE DEL COMPOSITORE
 *
 * ⛔ Costruisce la disposizione DA SE', dalla stessa stringa di `RCP.md` §4.5,
 *    senza chiedere niente al modulo sotto prova.  E' l'indipendenza che rende
 *    la verifica una verifica.
 * ------------------------------------------------------------------ */
typedef struct
{
	struct xkb_context *ctx;
	struct xkb_keymap *km;
	char nome[128];
} Simulatore;

static void sim_zitto(struct xkb_context *c, enum xkb_log_level l, const char *f, va_list a)
{
	(void)c;
	(void)l;
	(void)f;
	(void)a;
}

static int sim_apri(Simulatore *s, const char *disposizione)
{
	char layout[64] = {0}, variante[64] = {0};
	const char *par;
	struct xkb_rule_names nomi;

	memset(s, 0, sizeof *s);
	par = strchr(disposizione, '(');
	if (par)
	{
		size_t n = (size_t)(par - disposizione);
		if (n >= sizeof layout)
			return 0;
		memcpy(layout, disposizione, n);
		snprintf(variante, sizeof variante, "%s", par + 1);
		char *chiusa = strchr(variante, ')');
		if (chiusa)
			*chiusa = 0;
	}
	else
		snprintf(layout, sizeof layout, "%s", disposizione);

	s->ctx = xkb_context_new(XKB_CONTEXT_NO_FLAGS);
	if (!s->ctx)
		return 0;
	xkb_context_set_log_fn(s->ctx, sim_zitto);

	nomi.rules = "evdev";
	nomi.model = "pc105";
	nomi.layout = layout;
	nomi.variant = variante;
	nomi.options = "";
	s->km = xkb_keymap_new_from_names(s->ctx, &nomi, XKB_KEYMAP_COMPILE_NO_FLAGS);
	if (!s->km)
	{
		xkb_context_unref(s->ctx);
		s->ctx = NULL;
		return 0;
	}
	snprintf(s->nome, sizeof s->nome, "%s", xkb_keymap_layout_get_name(s->km, 0));
	return 1;
}

static void sim_chiudi(Simulatore *s)
{
	if (s->km)
		xkb_keymap_unref(s->km);
	if (s->ctx)
		xkb_context_unref(s->ctx);
	memset(s, 0, sizeof *s);
}

/*
 * Batte la sequenza come la batterebbe `input.c`: i modificatori prima, il
 * tasto per ultimo — e legge il carattere che il compositore ne trarrebbe.
 * Ritorna 0 se non ne esce niente.
 *
 * ⚠ Poi rilascia tutto all'incontrario e CONTROLLA che lo stato torni pulito:
 *   una sequenza che lascia un modificatore giu' e' la trappola 11 di
 *   `LEZIONI.md` §4, e qui costa due righe vederla.
 */
static uint32_t sim_batti(Simulatore *s, const uint16_t *codici, size_t n, int *stato_sporco)
{
	struct xkb_state *st = xkb_state_new(s->km);
	uint32_t fuori;
	size_t i;

	*stato_sporco = 0;
	if (!st || n == 0)
	{
		if (st)
			xkb_state_unref(st);
		return 0;
	}
	for (i = 0; i + 1 < n; i++)
		xkb_state_update_key(st, XKB_DA_EVDEV(codici[i]), XKB_KEY_DOWN);

	fuori = xkb_state_key_get_utf32(st, XKB_DA_EVDEV(codici[n - 1]));

	/* il tasto vero: giu' e su */
	xkb_state_update_key(st, XKB_DA_EVDEV(codici[n - 1]), XKB_KEY_DOWN);
	xkb_state_update_key(st, XKB_DA_EVDEV(codici[n - 1]), XKB_KEY_UP);
	for (i = n - 1; i-- > 0;)
		xkb_state_update_key(st, XKB_DA_EVDEV(codici[i]), XKB_KEY_UP);

	if (xkb_state_serialize_mods(st, XKB_STATE_MODS_EFFECTIVE) != 0)
		*stato_sporco = 1;

	xkb_state_unref(st);
	return fuori;
}

/* Il nome leggibile di un codice evdev, per il rapporto. */
static const char *nome_modificatore(uint16_t evdev)
{
	switch (evdev)
	{
		case 42: return "Maiusc(sx)";
		case 54: return "Maiusc(dx)";
		case 100: return "AltGr";
		case 29: return "Ctrl(sx)";
		case 56: return "Alt(sx)";
		case 125: return "Super";
		case 58: return "BlocMaiusc";
		case 69: return "BlocNum";
		default: return NULL;
	}
}

static void descrivi(char *fuori, size_t n, const uint16_t *codici, size_t quanti)
{
	size_t i;
	int scritti = 0;
	fuori[0] = 0;
	for (i = 0; i < quanti; i++)
	{
		const char *nome = nome_modificatore(codici[i]);
		scritti += snprintf(fuori + scritti, (int)n - scritti > 0 ? n - (size_t)scritti : 0,
		                    "%s%u%s%s%s", i ? "+" : "", codici[i], nome ? "(" : "",
		                    nome ? nome : "", nome ? ")" : "");
		if (scritti < 0 || (size_t)scritti >= n)
			break;
	}
}

/* ------------------------------------------------------------------ *
 * UNA PROVA
 * ------------------------------------------------------------------ */
typedef enum
{
	ATTESO_PRODUCIBILE,
	ATTESO_NO
} Atteso;

static void prova_carattere(const char *disposizione, uint32_t carattere, Atteso atteso,
                            const char *perche)
{
	Tastiera *t = NULL;
	Simulatore sim;
	char *errore = NULL;
	uint16_t codici[TASTIERA_MAX_POSIZIONI];
	size_t n = 0;
	int ret;
	char nome[160], dett[320], simbolo[8], uscito8[8];
	uint32_t uscito;
	int sporco = 0;

	utf8(carattere, simbolo);
	snprintf(nome, sizeof nome, "«%s» (U+%04X) su «%s» %s", simbolo, carattere, disposizione,
	         atteso == ATTESO_PRODUCIBILE ? "⇒ deve uscire" : "⇒ NON producibile");

	if (!sim_apri(&sim, disposizione))
	{
		esito(nome, 0, "il SIMULATORE non ha compilato la disposizione — non ho saputo guardare");
		return;
	}

	t = tastiera_apri(disposizione, &errore);
	if (!t)
	{
		snprintf(dett, sizeof dett, "tastiera_apri(\"%s\") ha detto NULL: %s", disposizione,
		         errore ? errore : "(nessun motivo)");
		esito(nome, 0, dett);
		free(errore);
		sim_chiudi(&sim);
		return;
	}

	memset(codici, 0, sizeof codici);
	ret = tastiera_posizioni_per(t, carattere, codici, &n);

	if (ret < 0)
	{
		snprintf(dett, sizeof dett, "ha ritornato -1 (errore) invece di %d",
		         atteso == ATTESO_PRODUCIBILE ? 1 : 0);
		esito(nome, 0, dett);
		goto fine;
	}

	if (atteso == ATTESO_NO)
	{
		if (ret == 0 && n == 0)
		{
			snprintf(dett, sizeof dett,
			         "ha detto NO e non ha mandato niente — e' il caso da scrivere nel registro");
			esito(nome, 1, dett);
			goto fine;
		}
		/* ⛔ Il cuore della prova: che cosa sarebbe USCITO se avessimo battuto? */
		uscito = sim_batti(&sim, codici, n, &sporco);
		utf8(uscito, uscito8);
		{
			char strada[128];
			descrivi(strada, sizeof strada, codici, n);
			snprintf(dett, sizeof dett,
			         "⛔ ha detto SI (%s) e sarebbe uscita «%s» (U+%04X) al posto di «%s»: "
			         "una LETTERA DIVERSA, che RCP.md §7.3 vieta",
			         strada, uscito8, uscito, simbolo);
		}
		esito(nome, 0, dett);
		goto fine;
	}

	/* atteso producibile */
	if (ret == 0)
	{
		esito(nome, 0, "⛔ ha detto «non producibile» un carattere che quella disposizione ha");
		goto fine;
	}
	if (n == 0 || n > TASTIERA_MAX_POSIZIONI)
	{
		snprintf(dett, sizeof dett, "ha detto SI ma con n=%zu posizioni (il massimo e' %d)", n,
		         TASTIERA_MAX_POSIZIONI);
		esito(nome, 0, dett);
		goto fine;
	}

	uscito = sim_batti(&sim, codici, n, &sporco);
	utf8(uscito, uscito8);
	{
		char strada[128];
		descrivi(strada, sizeof strada, codici, n);
		if (uscito == carattere && !sporco)
			snprintf(dett, sizeof dett, "battendo %s esce «%s» — la strada e' %s%s", strada,
			         uscito8, n > 1 ? "con modificatore" : "diretta",
			         perche ? perche : "");
		else if (sporco)
			snprintf(dett, sizeof dett,
			         "⛔ esce «%s» ma la sequenza %s LASCIA UN MODIFICATORE PREMUTO", uscito8,
			         strada);
		else
			snprintf(dett, sizeof dett, "⛔ battendo %s esce «%s» (U+%04X), non «%s» (U+%04X)",
			         strada, uscito8, uscito, simbolo, carattere);
		esito(nome, uscito == carattere && !sporco, dett);
	}

fine:
	free(errore);
	tastiera_chiudi(t);
	sim_chiudi(&sim);
}

/* ------------------------------------------------------------------ *
 * I CONTROLLI DELLO STRUMENTO — si fanno PRIMA, e se falliscono si esce con 2
 * ------------------------------------------------------------------ */
static int controlli_dello_strumento(void)
{
	Simulatore sim;
	uint16_t solo_a[1] = {30};      /* KEY_A */
	uint16_t solo_ac11[1] = {26};   /* KEY_LEFTBRACE: su `it` e' la «e` » */
	uint16_t con_maiusc[2] = {42, 26};
	uint32_t c;
	int sporco;
	char b[8];
	int ok = 1;

	printf("\n  — I CONTROLLI DELLO STRUMENTO (senza questi, «non e' uscito niente» e «non ho\n"
	       "    saputo guardare» hanno lo stesso aspetto — CODER.md §3.10)\n");

	if (!sim_apri(&sim, "it"))
	{
		esito("controllo positivo: il simulatore compila «it»", 0,
		      "no — il banco non puo' misurare niente");
		return 0;
	}

	c = sim_batti(&sim, solo_a, 1, &sporco);
	esito("⭐ positivo: il simulatore vede una lettera che ESCE di sicuro",
	      c == 'a' && !sporco,
	      c == 'a' ? "battuto il tasto 30 su «it», e' uscita «a»" : "battuto il tasto 30, NON e' uscita una «a»");
	ok = ok && (c == 'a');

	c = sim_batti(&sim, solo_ac11, 1, &sporco);
	utf8(c, b);
	{
		char d[128];
		snprintf(d, sizeof d, "tasto 26 senza Maiusc ⇒ «%s» (U+%04X), e NON e' la «e'» accentata", b, c);
		esito("⭐ negativo: il simulatore DISTINGUE i livelli", c == 0x00E8, d);
	}
	ok = ok && (c == 0x00E8);

	c = sim_batti(&sim, con_maiusc, 2, &sporco);
	utf8(c, b);
	{
		char d[160];
		snprintf(d, sizeof d, "Maiusc+26 ⇒ «%s» (U+%04X): il simulatore APPLICA i modificatori", b, c);
		esito("⭐ il simulatore applica i modificatori", c == 0x00E9 && !sporco, d);
	}
	ok = ok && (c == 0x00E9);

	sim_chiudi(&sim);
	return ok;
}

/* ------------------------------------------------------------------ *
 * ⛔ LA TRAPPOLA: il ripiego silenzioso su `us`
 * ------------------------------------------------------------------ */
static void prova_ripiego_silenzioso(void)
{
	static const char *inesistenti[] = {"zz_non_esiste", "it(variante_che_non_esiste)"};
	size_t i;

	for (i = 0; i < sizeof inesistenti / sizeof *inesistenti; i++)
	{
		char *errore = NULL;
		char nome[160], dett[320];
		Tastiera *t;

		snprintf(nome, sizeof nome, "⛔ «%s» non si carica ⇒ DEVE fallire e DIRLO", inesistenti[i]);
		t = tastiera_apri(inesistenti[i], &errore);
		if (!t)
		{
			if (errore && *errore)
			{
				snprintf(dett, sizeof dett, "NULL, col motivo: «%s»", errore);
				esito(nome, 1, dett);
			}
			else
				esito(nome, 0, "NULL ma SENZA motivo: chi legge il registro non sa perche'");
			free(errore);
			continue;
		}

		/* Ha ritornato una tastiera.  Ha ripiegato?  Lo si chiede alla `e'`. */
		{
			uint16_t codici[TASTIERA_MAX_POSIZIONI];
			size_t n = 0;
			int r = tastiera_posizioni_per(t, 'a', codici, &n);
			snprintf(dett, sizeof dett,
			         "⛔ RIPIEGO SILENZIOSO: ha ritornato una tastiera («%s») per una disposizione "
			         "che non esiste%s. Il sintomo per l'utente e' «scrive le lettere sbagliate», e "
			         "nessuno collega le due cose (CODER.md §4.2)",
			         tastiera_disposizione(t) ? tastiera_disposizione(t) : "(senza nome)",
			         r == 1 ? " — e per giunta scrive" : "");
			esito(nome, 0, dett);
		}
		free(errore);
		tastiera_chiudi(t);
	}
}

/*
 * ⚠ E l'altra faccia: due disposizioni diverse devono PRODURRE DUE NOMI
 *   DIVERSI.  Se `tastiera_disposizione()` dicesse la stessa cosa per `it` e
 *   per `us`, un ripiego non si vedrebbe nemmeno nel registro.
 */
static void prova_nomi_distinti(void)
{
	Tastiera *a = tastiera_apri("it", NULL);
	Tastiera *b = tastiera_apri("us", NULL);
	char dett[320];

	if (!a || !b)
	{
		esito("i nomi delle due disposizioni si distinguono", 0,
		      "una delle due non si e' aperta: la prova non si e' potuta fare");
		tastiera_chiudi(a);
		tastiera_chiudi(b);
		return;
	}
	snprintf(dett, sizeof dett, "«%s» contro «%s»",
	         tastiera_disposizione(a) ? tastiera_disposizione(a) : "(NULL)",
	         tastiera_disposizione(b) ? tastiera_disposizione(b) : "(NULL)");
	esito("⭐ i nomi delle due disposizioni si DISTINGUONO",
	      tastiera_disposizione(a) && tastiera_disposizione(b) &&
	          strcmp(tastiera_disposizione(a), tastiera_disposizione(b)) != 0,
	      dett);
	tastiera_chiudi(a);
	tastiera_chiudi(b);
}

/* Gli ingressi che il protocollo vieta (`RCP.md` §7.3): fuori intervallo e
 * surrogati.  Non sono «non producibili»: sono un errore. */
static void prova_ingressi_illegali(void)
{
	Tastiera *t = tastiera_apri("it", NULL);
	uint16_t codici[TASTIERA_MAX_POSIZIONI];
	size_t n = 1;
	char dett[160];
	int r1, r2;

	if (!t)
	{
		esito("gli ingressi illegali si distinguono dal «non producibile»", 0,
		      "«it» non si e' aperta");
		return;
	}
	r1 = tastiera_posizioni_per(t, 0xD800, codici, &n);
	r2 = tastiera_posizioni_per(t, 0x110000, codici, &n);
	snprintf(dett, sizeof dett, "surrogato ⇒ %d, fuori intervallo ⇒ %d (attesi -1 e -1)", r1, r2);
	esito("gli ingressi illegali NON si confondono col «non producibile»", r1 == -1 && r2 == -1,
	      dett);
	tastiera_chiudi(t);
}

/* ------------------------------------------------------------------ *
 * ⛔⛔ LA PROVA PER CUI IL CONTRATTO E' CAMBIATO
 *
 * `tastiera_apri()` compila la disposizione DAL NOME che il client ha
 * negoziato.  Ma quella con cui il compositore interpretera' i nostri codici e'
 * LA SUA, quella che `libei` consegna col dispositivo.
 *
 * ⇒ Qui si mettono apposta a litigare: **la sessione ha `it`, il client ha
 *   negoziato `us`, e l'utente scrive `[`.**
 *
 *     · su `us` la `[` sta sul tasto 26, da sola;
 *     · su `it` sul tasto 26 c'e' la «e` », e la `[` vuole l'AltGr.
 *
 *   Un modulo che si fida del nome negoziato manda «26», e sullo schermo
 *   dell'utente compare **«è»**.  ⛔ Non un carattere mancante: UN CARATTERE
 *   DIVERSO — cio' che `RCP.md` §7.3 vieta, e che nessuno collegherebbe mai
 *   alla disposizione.
 *
 * ⚠ Il simulatore, qui, e' costruito sulla disposizione DELLA SESSIONE: e'
 *   l'unica che conti, perche' e' l'unica che il compositore applica.
 * ------------------------------------------------------------------ */
static char *testo_della_disposizione(const char *disposizione)
{
	Simulatore s;
	char *testo;

	if (!sim_apri(&s, disposizione))
		return NULL;
	testo = xkb_keymap_get_as_string(s.km, XKB_KEYMAP_FORMAT_TEXT_V1);
	sim_chiudi(&s);
	return testo;
}

static void prova_keymap_della_sessione(const char *della_sessione, const char *negoziata,
                                        uint32_t carattere, Atteso atteso)
{
	char *testo = testo_della_disposizione(della_sessione);
	Simulatore sim;
	Tastiera *t = NULL;
	char *errore = NULL;
	uint16_t codici[TASTIERA_MAX_POSIZIONI];
	size_t n = 0;
	int ret, sporco = 0;
	char nome[256], dett[448], simbolo[8], uscito8[8], strada[128];
	uint32_t uscito;

	utf8(carattere, simbolo);
	snprintf(nome, sizeof nome, "sessione «%s» + negoziata «%s», «%s» (U+%04X) %s",
	         della_sessione, negoziata ? negoziata : "(nessuna)", simbolo, carattere,
	         atteso == ATTESO_PRODUCIBILE ? "⇒ deve uscire" : "⇒ NON producibile");

	if (!testo || !sim_apri(&sim, della_sessione))
	{
		esito(nome, 0, "non ho potuto costruire la disposizione della sessione: NON HO MISURATO");
		free(testo);
		return;
	}

	t = tastiera_apri_da_keymap(testo, strlen(testo), negoziata, &errore);
	if (!t)
	{
		snprintf(dett, sizeof dett, "la keymap della sessione non si e' aperta: %s",
		         errore ? errore : "(senza motivo)");
		esito(nome, 0, dett);
		goto fine;
	}

	memset(codici, 0, sizeof codici);
	ret = tastiera_posizioni_per(t, carattere, codici, &n);

	if (atteso == ATTESO_NO)
	{
		if (ret == 0 && n == 0)
			esito(nome, 1, "ha detto NO e non ha mandato niente");
		else
		{
			uscito = sim_batti(&sim, codici, n, &sporco);
			utf8(uscito, uscito8);
			descrivi(strada, sizeof strada, codici, n);
			snprintf(dett, sizeof dett, "⛔ ha detto SI (%s): comparirebbe «%s»", strada, uscito8);
			esito(nome, 0, dett);
		}
		goto fine;
	}

	if (ret != 1 || n == 0)
	{
		snprintf(dett, sizeof dett,
		         "⛔ ha detto «non producibile» (%d) un carattere che LA SESSIONE ha: si e' "
		         "fidato del nome negoziato invece che della disposizione vera",
		         ret);
		esito(nome, 0, dett);
		goto fine;
	}

	uscito = sim_batti(&sim, codici, n, &sporco);
	utf8(uscito, uscito8);
	descrivi(strada, sizeof strada, codici, n);
	if (uscito == carattere && !sporco)
		snprintf(dett, sizeof dett, "battendo %s sulla disposizione DELLA SESSIONE esce «%s»",
		         strada, uscito8);
	else
		snprintf(dett, sizeof dett,
		         "⛔ battendo %s sulla disposizione DELLA SESSIONE esce «%s» (U+%04X), non «%s»: "
		         "UNA LETTERA DIVERSA",
		         strada, uscito8, uscito, simbolo);
	esito(nome, uscito == carattere && !sporco, dett);

fine:
	free(errore);
	tastiera_chiudi(t);
	sim_chiudi(&sim);
	free(testo);
}

/*
 * ⛔ E si puo' chiamare PIU' VOLTE: `gnome.md` §9 dice che un cambio di keymap
 *    distrugge e ricrea il dispositivo tastiera, e `input.c` riapre a ogni
 *    `DEVICE_ADDED`.  ⇒ Due aperture vive insieme non devono ne' perdere ne'
 *    raddoppiare niente: si apre `it`, si apre `us`, e **si torna a chiedere
 *    alla prima**, che deve rispondere come prima.
 */
static void prova_riaperture(void)
{
	char *ti = testo_della_disposizione("it");
	char *tu = testo_della_disposizione("us");
	Tastiera *a = NULL, *b = NULL;
	uint16_t ca[TASTIERA_MAX_POSIZIONI], cb[TASTIERA_MAX_POSIZIONI];
	size_t na = 0, nb = 0, na2 = 0;
	uint16_t ca2[TASTIERA_MAX_POSIZIONI];
	char dett[320];
	int r1, r2, r3;

	if (!ti || !tu)
	{
		esito("⭐ si puo' riaprire piu' volte senza perdere niente", 0, "NON HO MISURATO");
		goto fine;
	}
	a = tastiera_apri_da_keymap(ti, strlen(ti), NULL, NULL);
	r1 = a ? tastiera_posizioni_per(a, 0x00E9, ca, &na) : -1; /* é su it */

	b = tastiera_apri_da_keymap(tu, strlen(tu), NULL, NULL);
	r2 = b ? tastiera_posizioni_per(b, 0x00E9, cb, &nb) : -1; /* é su us */

	/* ⛔ e adesso di nuovo la PRIMA, che e' ancora viva */
	r3 = a ? tastiera_posizioni_per(a, 0x00E9, ca2, &na2) : -1;

	snprintf(dett, sizeof dett,
	         "it⇒%d (%zu pos.), poi us⇒%d (%zu pos.), poi ANCORA it⇒%d (%zu pos.)", r1, na, r2, nb,
	         r3, na2);
	esito("⭐ due disposizioni vive insieme non si rimescolano",
	      r1 == 1 && r2 == 0 && r3 == 1 && na == na2 && na > 0 &&
	          memcmp(ca, ca2, na * sizeof *ca) == 0,
	      dett);

fine:
	tastiera_chiudi(a);
	tastiera_chiudi(b);
	free(ti);
	free(tu);
}

/* ------------------------------------------------------------------ *
 * ⛔⛔ E SI GUARDA LA RIGA DEL REGISTRO, NON SOLO LA LETTERA
 *
 * ⚠ Questa prova e' nata da un difetto che il banco NON aveva visto.  Il
 *   confronto fra la disposizione della sessione e quella negoziata, nella sua
 *   prima stesura, dichiarava un ripiego **anche quando le due erano la
 *   stessa** — e il banco restava verde, perche' guardava la lettera che
 *   usciva e la lettera usciva giusta.  Il difetto stava tutto nella riga di
 *   registro, che e' l'unica parte di questo lavoro che qualcuno leggera' il
 *   giorno che le lettere non tornano.
 *
 * ⛔ Un «RIPIEGO DICHIARATO» che esce a ogni connessione e' peggio che inutile:
 *    chi legge il registro impara a saltarlo.  ⇒ Si verifica nei DUE versi —
 *    che esca quando deve, e che **non** esca quando non deve.
 *
 * Il registro va su stderr: lo si dirotta su un file per la durata della
 * chiamata, e poi lo si legge.  E' `CODER.md` §3.8 — si verifica dal lato che
 * riceve, e chi riceve questa riga e' un file di registro.
 * ------------------------------------------------------------------ */
static void prova_dichiarazione(const char *della_sessione, const char *negoziata,
                                int deve_dichiarare)
{
	char *testo = testo_della_disposizione(della_sessione);
	char nome[256], dett[384], riga[4096];
	int salvato = -1, tmp = -1;
	FILE *f = NULL;
	Tastiera *t = NULL;
	long letti = 0;
	int dichiarato = 0;
	char modello[] = "/tmp/04-b25-reg-XXXXXX";

	snprintf(nome, sizeof nome, "il registro: sessione «%s» + negoziata «%s» ⇒ %s",
	         della_sessione, negoziata ? negoziata : "(nessuna)",
	         deve_dichiarare ? "DEVE dichiarare il ripiego" : "NON deve gridare al ripiego");

	if (!testo)
	{
		esito(nome, 0, "non ho costruito la disposizione: NON HO MISURATO");
		return;
	}

	tmp = mkstemp(modello);
	if (tmp < 0)
	{
		esito(nome, 0, "non ho potuto dirottare il registro: NON HO MISURATO");
		free(testo);
		return;
	}
	fflush(stderr);
	salvato = dup(STDERR_FILENO);
	dup2(tmp, STDERR_FILENO);

	t = tastiera_apri_da_keymap(testo, strlen(testo), negoziata, NULL);

	fflush(stderr);
	dup2(salvato, STDERR_FILENO);
	close(salvato);

	f = fdopen(tmp, "r");
	if (f)
	{
		rewind(f);
		while (fgets(riga, sizeof riga, f))
		{
			letti++;
			if (strstr(riga, "RIPIEGO DICHIARATO"))
				dichiarato = 1;
		}
		fclose(f);
	}
	unlink(modello);

	/*
	 * ⛔ Il controllo positivo dello STRUMENTO: se non avessi letto nessuna riga
	 *    affatto, «non ha dichiarato» e «non ho saputo leggere il registro»
	 *    avrebbero lo stesso aspetto (`CODER.md` §3.10).
	 */
	if (letti == 0)
	{
		esito(nome, 0, "⛔ non ho letto NESSUNA riga di registro: non so distinguere il "
		               "silenzio dal non aver guardato");
		goto fine;
	}

	snprintf(dett, sizeof dett, "%ld righe di registro, «RIPIEGO DICHIARATO» %s", letti,
	         dichiarato ? "c'e'" : "non c'e'");
	esito(nome, dichiarato == deve_dichiarare, dett);

fine:
	tastiera_chiudi(t);
	free(testo);
}

/* ------------------------------------------------------------------ *
 * main
 * ------------------------------------------------------------------ */
int main(int argc, char **argv)
{
	const char *dove = argc > 1 ? argv[1] : "banchi/04-b25-esiti.jsonl";

	jsonl = fopen(dove, "w");
	if (!jsonl)
	{
		fprintf(stderr, "⛔ non riesco a scrivere %s\n", dove);
		return 2;
	}

	printf("\n== BANCO 04-b25 — LA TASTIERA: dalla lettera al martelletto\n");
	printf("   il metro e' IL CARATTERE CHE ESCE da un `xkb_state` indipendente,\n"
	       "   non il codice che il modulo dice di aver scelto.\n");

	if (!controlli_dello_strumento())
	{
		printf("\n⛔ LO STRUMENTO NON E' CERTIFICATO: non misuro niente.\n");
		fclose(jsonl);
		return 2;
	}

	printf("\n  — LE LETTERE (PIANO.md righe 630-632)\n");
	prova_carattere("it", 0x00E9, ATTESO_PRODUCIBILE, "");  /* é */
	prova_carattere("us", 0x00E9, ATTESO_NO, "");           /* ⛔ la prova che pesa di piu' */
	prova_carattere("it", 0x00E8, ATTESO_PRODUCIBILE, "");  /* è, senza modificatore */
	prova_carattere("it", 'a', ATTESO_PRODUCIBILE, "");     /* controllo positivo sul modulo */
	prova_carattere("us", 'A', ATTESO_PRODUCIBILE, "");     /* Maiusc FA la lettera */

	printf("\n  — LO STESSO CARATTERE, DUE STRADE (SPECIFICHE.md §7.3: Maiusc e AltGr\n"
	       "    non sono comandi, servono a FARE la lettera)\n");
	prova_carattere("it", '@', ATTESO_PRODUCIBILE, "");     /* AltGr */
	prova_carattere("us", '@', ATTESO_PRODUCIBILE, "");     /* Maiusc */

	printf("\n  — QUEL CHE NON E' SCRIVIBILE SI DICHIARA, NON SI FALSIFICA\n");
	prova_carattere("it", 0x1F600, ATTESO_NO, "");          /* 😀 */
	prova_carattere("us", 0x1F600, ATTESO_NO, "");
	prova_carattere("it", 0x4E2D, ATTESO_NO, "");           /* 中 */

	printf("\n  — ⛔ LA TRAPPOLA: IL RIPIEGO SILENZIOSO\n");
	prova_ripiego_silenzioso();
	prova_nomi_distinti();

	printf("\n  — GLI INGRESSI CHE IL PROTOCOLLO VIETA\n");
	prova_ingressi_illegali();

	printf("\n  — ⛔⛔ LA DISPOSIZIONE LA CONSEGNA LA SESSIONE, NON LA SCEGLIE IL NOME\n"
	       "    (il caso per cui il contratto e' cambiato: sessione «it», client «us»)\n");
	/* ⛔ IL CASO: la `[` — su `us` e' il tasto 26 nudo, su `it` c'e' la «è». */
	prova_keymap_della_sessione("it", "us", '[', ATTESO_PRODUCIBILE);
	/* e il gemello: un carattere che la sessione NON ha, per quanto il client lo chieda */
	prova_keymap_della_sessione("us", "it", 0x00E9, ATTESO_NO);
	/* i controlli positivi: quando combaciano, tutto come prima */
	prova_keymap_della_sessione("it", "it", 0x00E9, ATTESO_PRODUCIBILE);
	prova_keymap_della_sessione("it", NULL, '[', ATTESO_PRODUCIBILE);
	prova_riaperture();

	printf("\n  — ⛔ E LA RIGA DEL REGISTRO, NEI DUE VERSI\n");
	prova_dichiarazione("it", "us", 1);  /* non combaciano ⇒ si dichiara */
	prova_dichiarazione("it", "it", 0);  /* ⛔ combaciano ⇒ NON si grida */
	prova_dichiarazione("us", "us", 0);
	prova_dichiarazione("it", NULL, 0);  /* nessuna negoziata: niente da confrontare */

	printf("\n== %d prove, %d ROSSE  ⇒  %s\n\n", quante_prove, quante_rosse,
	       quante_rosse ? "⛔ ROSSO" : "✅ VERDE");
	fprintf(jsonl, "{\"totale\":%d,\"rosse\":%d,\"esito\":\"%s\"}\n", quante_prove, quante_rosse,
	        quante_rosse ? "rosso" : "verde");
	fclose(jsonl);
	return quante_rosse ? 1 : 0;
}
