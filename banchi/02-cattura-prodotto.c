/*
 * 02-cattura-prodotto — lo STESSO banco di F2.2, puntato sul PRODOTTO.
 *
 * ===========================================================================
 * ⛔ PERCHE' ESISTE, E PERCHE' NON HO TOCCATO `02-cattura-fotogramma.c`
 *
 * Il banco di F2.2 e' nato prima del prodotto, ed e' certificato: `sano 0 →
 * quattro guasti 1 → risanato 0`, `[M]` 12 agosto 2026.  ⛔ Ma quel che
 * certificava era il produttore SCRITTO DENTRO IL BANCO — un consumatore
 * PipeWire suo, con la sua sequenza D-Bus ricopiata da `mutter.h`.  Il prodotto
 * non esisteva ancora.
 *
 * ⇒ Un banco che misura una copia del prodotto **non dice niente sul prodotto**.
 *   E' la forma piu' insidiosa di `LEZIONI.md` §1.3: verde su codice che nessuno
 *   ha ancora eseguito.
 *
 * ⭐ Questo file e' lo stesso produttore — stessa riga di comando, stesso
 *    manifesto, stessi quattro stati d'uscita, stessi due `.raw` — ma la cattura
 *    la fa **`src/cattura.c` e `src/mutter.c`**, cioe' il prodotto.  Il giudice
 *    (`02-cattura-giudica.py`) e la certificazione (`02-cattura-certifica.sh`)
 *    non cambiano di una riga: giudicano i pixel, e non sanno ne' vogliono
 *    sapere chi li ha prodotti.
 *
 * ⭐ E i due produttori restano tutt'e due, perche' insieme sono un controllo
 *    positivo che nessuno dei due sarebbe da solo: **lo stesso giudice, la
 *    stessa scena, due produttori indipendenti**.  Se il verdetto cambia
 *    cambiando produttore, la differenza e' nel produttore — e si sa quale.
 *
 * ===========================================================================
 * ⛔ QUEL CHE QUESTO PROGRAMMA **NON** DIMOSTRA (forma E1, `REVIEWER.md` §2)
 *
 *   `tipo = MemFd`   ⛔ non dice niente su dove Mutter renda: qui la memoria si
 *                    CHIEDE, perche' la fase 2 vuole i pixel leggibili.  E' la
 *                    risposta a una nostra domanda, non una scoperta
 *   `tipo = DMA-BUF` non prova che si renda in GPU: un render node aperto e'
 *                    necessario, non sufficiente
 *
 * ⚠ E non misura il RITMO, e non deve: copia fotogrammi da 8 MB dentro (e
 *   subito fuori) la richiamata di tempo reale di PipeWire.  Il ritmo e' della
 *   fase 0 (36 ± 2 `[M]`) e della fase 3.
 *
 * ===========================================================================
 * uso: identico a 02-cattura-fotogramma, piu' `--10bit`
 *
 *   02-cattura-prodotto --uscita PREFISSO --pronto FILE --segnale-scena FILE
 *        [--larghezza W] [--altezza H] [--fps N] [--bgra] [--dmabuf] [--10bit]
 *        [--dopo-scena S] [--scarta N] [--durata S] [--attesa-scena S]
 *        [--minimo-dopo-scena N] [--etichetta T] [--nodo N]
 */

#include <glib.h>
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#include "cattura.h"
#include "mutter.h"
#include "registro.h"

typedef struct
{
	gboolean preso;
	CatturaFermo fermo;
	const char *danno; /* "pieno" | "parziale" | "assente" — le parole del banco */
} Voce;

static const char *nome_danno(const CatturaFermo *f)
{
	if (!f->danno_dichiarato)
		return "assente";
	return f->danno_copre_tutto ? "pieno" : "parziale";
}

static void manifesto_voce(GString *s, const char *chiave, const Voce *v, const char *file)
{
	if (!v->preso)
	{
		g_string_append_printf(s, "  \"%s\": null,\n", chiave);
		return;
	}
	g_string_append_printf(s,
	                       "  \"%s\": {\n"
	                       "    \"file\": \"%s\",\n"
	                       "    \"byte\": %" G_GUINT64_FORMAT ",\n"
	                       "    \"stride\": %u,\n"
	                       "    \"offset\": 0,\n"
	                       "    \"dimensione_chunk\": %" G_GUINT64_FORMAT ",\n"
	                       "    \"tipo_dichiarato\": \"%s\",\n"
	                       "    \"danno\": \"%s\",\n"
	                       "    \"indice_fra_gli_arrivati\": %" G_GUINT64_FORMAT ",\n"
	                       "    \"seq\": %" G_GUINT64_FORMAT ",\n"
	                       "    \"pts\": %" G_GINT64_FORMAT ",\n"
	                       "    \"seq_nota\": %s,\n"
	                       /* ⭐ La misura che il produttore NON dichiara, fatta da noi
	                        *    sui pixel consegnati — e scritta come misura. */
	                       "    \"range_misurato\": {\"min\": [%u, %u, %u], "
	                       "\"max\": [%u, %u, %u], \"esito\": \"%s\"},\n"
	                       "    \"nero\": %s,\n"
	                       "    \"uniforme\": %s\n"
	                       "  },\n",
	                       chiave, file, v->fermo.byte, v->fermo.stride, v->fermo.byte,
	                       cattura_buffer_nome(v->fermo.consegna.buffer_dichiarato), v->danno,
	                       v->fermo.indice, v->fermo.seq, v->fermo.pts,
	                       v->fermo.seq_nota ? "true" : "false", v->fermo.consegna.minimo[0],
	                       v->fermo.consegna.minimo[1], v->fermo.consegna.minimo[2],
	                       v->fermo.consegna.massimo[0], v->fermo.consegna.massimo[1],
	                       v->fermo.consegna.massimo[2],
	                       cattura_range_misurato_nome(v->fermo.consegna.range_misurato),
	                       v->fermo.consegna.nero ? "true" : "false",
	                       v->fermo.consegna.uniforme ? "true" : "false");
}

int main(int argc, char **argv)
{
	uint32_t larghezza = 1920, altezza = 1080, fps = 60, nodo = 0;
	double dopo_scena = 3.0, durata = 12.0, attesa_scena = 25.0;
	guint64 scarta = 10, minimo_dopo_scena = 1;
	CatturaStrada strada = CATTURA_STRADA_MEMORIA;
	CatturaColore colore = CATTURA_COLORE_BGRX;
	const char *etichetta = "senza-nome";
	const char *uscita = NULL, *pronto = NULL, *segnale_scena = NULL;
	const char *nome_colore_chiesto = "BGRx";
	MutterSessione *sessione = NULL;
	Cattura *cattura = NULL;
	Voce primo = { 0 }, regime = { 0 };
	CatturaConsegna consegna;
	CatturaConteggi conto;
	guint64 prima_della_scena = 0, dopo_la_scena = 0;
	g_autoptr(GError) sbaglio = NULL;
	g_autofree char *file_primo = NULL, *file_regime = NULL, *file_json = NULL;
	GString *manifesto;
	gint64 scadenza, fine;
	int codice = 0, i;
	const char *esito;
	char quando[64];
	time_t adesso_epoch;
	struct tm adesso_tm;

	for (i = 1; i < argc; i++)
	{
		if (!strcmp(argv[i], "--uscita") && i + 1 < argc)
			uscita = argv[++i];
		else if (!strcmp(argv[i], "--pronto") && i + 1 < argc)
			pronto = argv[++i];
		else if (!strcmp(argv[i], "--segnale-scena") && i + 1 < argc)
			segnale_scena = argv[++i];
		else if (!strcmp(argv[i], "--nodo") && i + 1 < argc)
			nodo = (uint32_t) atoi(argv[++i]);
		else if (!strcmp(argv[i], "--larghezza") && i + 1 < argc)
			larghezza = (uint32_t) atoi(argv[++i]);
		else if (!strcmp(argv[i], "--altezza") && i + 1 < argc)
			altezza = (uint32_t) atoi(argv[++i]);
		else if (!strcmp(argv[i], "--fps") && i + 1 < argc)
			fps = (uint32_t) atoi(argv[++i]);
		else if (!strcmp(argv[i], "--dopo-scena") && i + 1 < argc)
			dopo_scena = atof(argv[++i]);
		else if (!strcmp(argv[i], "--attesa-scena") && i + 1 < argc)
			attesa_scena = atof(argv[++i]);
		else if (!strcmp(argv[i], "--durata") && i + 1 < argc)
			durata = atof(argv[++i]);
		else if (!strcmp(argv[i], "--scarta") && i + 1 < argc)
			scarta = (guint64) atoll(argv[++i]);
		else if (!strcmp(argv[i], "--minimo-dopo-scena") && i + 1 < argc)
			minimo_dopo_scena = (guint64) atoll(argv[++i]);
		else if (!strcmp(argv[i], "--dmabuf"))
			strada = CATTURA_STRADA_SCHEDA;
		else if (!strcmp(argv[i], "--bgra"))
		{
			colore = CATTURA_COLORE_BGRA;
			nome_colore_chiesto = "BGRA";
		}
		else if (!strcmp(argv[i], "--10bit"))
		{
			/* ⭐ LA DOMANDA DEI DIECI BIT, FATTA AL PRODUTTORE.
			 *
			 * `STUDI.md` §gnome §8.3 `[R]` dice che Mutter consegna solo BGRx e BGRA.
			 * Chiedere un formato a dieci bit e ricevere un rifiuto trasforma
			 * quella lettura in una MISURA — e il rifiuto va scritto, non
			 * dedotto (`LEZIONI.md` §1.11). */
			colore = CATTURA_COLORE_10BIT;
			nome_colore_chiesto = "10 bit (xBGR_210LE e compagni)";
		}
		else if (!strcmp(argv[i], "--etichetta") && i + 1 < argc)
			etichetta = argv[++i];
		else if (!strcmp(argv[i], "--parlantina"))
			registro_parlantina(TRUE);
		else
		{
			/* ⛔ E si dice QUALE argomento non si e' capito.  La prima stesura
			 *    stampava solo la riga d'uso, e il 12 agosto 2026 e' costata un
			 *    giro intero: mancava `--etichetta`, il banco ha letto «uscita 2»
			 *    e la riga d'aiuto, e da fuori aveva l'aspetto di un produttore
			 *    che non parte.  E' `FASI.md` §00-ambiente B3 punto 2 — *un'opzione
			 *    rifiutata non e' un difetto del bersaglio*. */
			fprintf(stderr,
			        "⛔ non capisco l'argomento «%s».\n"
			        "uso: %s --uscita PREFISSO --pronto FILE --segnale-scena FILE\n"
			        "        [--larghezza W] [--altezza H] [--fps N] [--bgra] [--dmabuf]\n"
			        "        [--10bit] [--dopo-scena S] [--scarta N] [--durata S]\n"
			        "        [--attesa-scena S] [--minimo-dopo-scena N] [--etichetta T]\n"
			        "        [--nodo N] [--parlantina]\n",
			        argv[i], argv[0]);
			return 2;
		}
	}
	if (!uscita || !pronto || !segnale_scena)
	{
		fprintf(stderr, "⛔ servono --uscita, --pronto e --segnale-scena: l'ordine fra il "
		                "monitor e la scena e' un EVENTO, non un'attesa a tempo.\n");
		return 2;
	}

	file_primo = g_strdup_printf("%s-primo.raw", uscita);
	file_regime = g_strdup_printf("%s-regime.raw", uscita);
	file_json = g_strdup_printf("%s.json", uscita);

	adesso_epoch = time(NULL);
	gmtime_r(&adesso_epoch, &adesso_tm);
	strftime(quando, sizeof quando, "%Y-%m-%dT%H:%M:%SZ", &adesso_tm);

	fprintf(stderr, "== %s: chiesti %ux%u, %s, tetto %u fps, strada %s ==\n", etichetta, larghezza,
	        altezza, nome_colore_chiesto, fps,
	        strada == CATTURA_STRADA_SCHEDA ? "scheda (DMA-BUF)" : "memoria");
	fprintf(stderr, "   il produttore e' IL PRODOTTO: src/cattura.c + src/mutter.c\n");

	/* --- il palco -------------------------------------------------------- */
	if (nodo == 0)
	{
		sessione = mutter_apri(&sbaglio);
		if (!sessione)
		{
			fprintf(stderr, "⛔ monitor virtuale non montato: %s\n", sbaglio->message);
			return 1;
		}
		nodo = mutter_nodo(sessione);
	}

	/* --- la cattura ------------------------------------------------------ */
	cattura = cattura_avvia(nodo, larghezza, altezza, fps, strada, colore, NULL, NULL, NULL,
	                        &sbaglio);
	if (!cattura)
	{
		printf("GUASTO\t%s\t%s\n", etichetta, sbaglio->message);
		fprintf(stderr, "⛔ FALLITO: %s\n", sbaglio->message);
		mutter_chiudi(sessione);
		return 2;
	}

	/* Si aspetta che il flusso sia ATTIVO davvero prima di dire «pronto»:
	 * scriverlo prima vorrebbe dire accendere la scena su un monitor che non
	 * esiste ancora. */
	scadenza = g_get_monotonic_time() + 10 * G_USEC_PER_SEC;
	while (!cattura_attiva(cattura) && g_get_monotonic_time() < scadenza)
		g_usleep(20000);
	if (!cattura_attiva(cattura))
	{
		printf("GUASTO\t%s\tflusso mai attivo\n", etichetta);
		fprintf(stderr, "⛔ FALLITO (non «zero»): il flusso non e' mai diventato attivo%s%s.\n",
		        cattura_guasto(cattura) ? " — " : "",
		        cattura_guasto(cattura) ? cattura_guasto(cattura) : "");
		cattura_ferma(cattura);
		mutter_chiudi(sessione);
		return 2;
	}

	/* ⛔ E ADESSO — non prima — si chiede COME SI CHIAMA il nostro schermo.
	 *    Il monitor virtuale compare quando il consumatore si aggancia, `[M]`, e
	 *    questo e' anche il momento in cui il nome serve: la scena si apre dopo,
	 *    e va mandata su QUESTO schermo per nome (`CODER.md` §3.9). */
	if (sessione)
	{
		mutter_monitor_cerca(sessione);
		fprintf(stderr, "   monitor nostro: %s («%s»)\n",
		        mutter_monitor_nostro(sessione) ? mutter_monitor_nostro(sessione) : "NON LO SO",
		        mutter_monitor_prodotto(sessione) ? mutter_monitor_prodotto(sessione) : "—");
	}

	/* --- il fotogramma «primo»: prima che la scena esista ---------------- *
	 * ⛔ E9 (`CODER.md` §3.5) per un'immagine ferma: il campione dell'avvio non
	 *    e' un difetto — e' il PRODOTTO, quel che vede chi si collega adesso. Il
	 *    difetto sarebbe misurarlo e scrivere il numero in una colonna che la
	 *    fase 3 leggera' come regime.  ⇒ Due fotogrammi, due file, e il manifesto
	 *    dice per ciascuno quale fosse fra gli arrivati. */
	{
		CatturaPresa p = cattura_prendi(cattura, 3.0, &primo.fermo, &sbaglio);

		if (p == CATTURA_PRESA_FATTA)
		{
			primo.preso = TRUE;
			primo.danno = nome_danno(&primo.fermo);
		}
		else if (p == CATTURA_PRESA_GUASTO)
		{
			printf("GUASTO\t%s\t%s\n", etichetta, sbaglio->message);
			fprintf(stderr, "⛔ FALLITO sul «primo»: %s\n", sbaglio->message);
			cattura_ferma(cattura);
			mutter_chiudi(sessione);
			return 2;
		}
		else if (p == CATTURA_PRESA_PIXEL_ALTROVE)
		{
			primo.preso = FALSE; /* i pixel vivono sulla scheda: si dice, non si finge */
		}
		g_clear_error(&sbaglio);
	}

	if (!g_file_set_contents(pronto, "pronto\n", -1, &sbaglio))
	{
		fprintf(stderr, "⛔ non riesco a scrivere %s: %s\n", pronto, sbaglio->message);
		cattura_ferma(cattura);
		mutter_chiudi(sessione);
		return 1;
	}
	fprintf(stderr, "  pronto: la scena si puo' accendere adesso\n");

	/* --- si aspetta che chi lancia dichiari la scena accesa -------------- */
	scadenza = g_get_monotonic_time() + (gint64) (attesa_scena * G_USEC_PER_SEC);
	while (!g_file_test(segnale_scena, G_FILE_TEST_EXISTS) && g_get_monotonic_time() < scadenza)
		g_usleep(50000);
	if (!g_file_test(segnale_scena, G_FILE_TEST_EXISTS))
	{
		printf("GUASTO\t%s\tla scena non e' mai stata dichiarata accesa\n", etichetta);
		fprintf(stderr, "⛔ FALLITO: dopo %.1f s nessuno ha dichiarato la scena accesa.\n",
		        attesa_scena);
		cattura_ferma(cattura);
		mutter_chiudi(sessione);
		return 2;
	}
	cattura_conteggi(cattura, &conto);
	prima_della_scena = conto.arrivati;
	fine = g_get_monotonic_time() + (gint64) (durata * G_USEC_PER_SEC);
	fprintf(stderr, "  scena accesa: %" G_GUINT64_FORMAT " fotogrammi erano gia' arrivati\n",
	        prima_della_scena);

	/* --- il fotogramma «regime» ------------------------------------------ *
	 * Si lascia passare `--dopo-scena`, si buttano `--scarta` fotogrammi (sono
	 * l'accensione della scena, non il regime), e poi si prende **l'ultimo della
	 * finestra**: cosi' il danno che porta e' quello del regime. */
	g_usleep((gulong) (dopo_scena * G_USEC_PER_SEC));
	for (i = 0; (guint64) i < scarta && g_get_monotonic_time() < fine; i++)
	{
		CatturaFermo buttato = { 0 };

		if (cattura_prendi(cattura, 0.5, &buttato, &sbaglio) == CATTURA_PRESA_GUASTO)
			break;
		cattura_fermo_libera(&buttato);
		g_clear_error(&sbaglio);
	}
	g_clear_error(&sbaglio);

	while (g_get_monotonic_time() < fine - (gint64) (0.7 * G_USEC_PER_SEC))
		g_usleep(50000);

	{
		CatturaPresa p = cattura_prendi(cattura, 1.5, &regime.fermo, &sbaglio);

		if (p == CATTURA_PRESA_FATTA)
		{
			regime.preso = TRUE;
			regime.danno = nome_danno(&regime.fermo);
		}
		else if (p == CATTURA_PRESA_GUASTO)
		{
			printf("GUASTO\t%s\t%s\n", etichetta, sbaglio->message);
			fprintf(stderr, "⛔ FALLITO sul «regime»: %s\n", sbaglio->message);
			cattura_fermo_libera(&primo.fermo);
			cattura_ferma(cattura);
			mutter_chiudi(sessione);
			return 2;
		}
		g_clear_error(&sbaglio);
	}

	/* --- le guardie, PRIMA di scrivere qualunque numero ------------------ */
	if (!cattura_attiva(cattura))
	{
		printf("GUASTO\t%s\tflusso caduto durante la presa\n", etichetta);
		fprintf(stderr, "⛔ FALLITO (non «zero»): il flusso era attivo ed e' caduto.\n");
		cattura_ferma(cattura);
		mutter_chiudi(sessione);
		return 2;
	}
	cattura_conteggi(cattura, &conto);
	dopo_la_scena = conto.arrivati - prima_della_scena;

	/*
	 * ⛔ SCENA VIVA E ZERO FOTOGRAMMI NON E' UNO ZERO: E' UN GUASTO.
	 *
	 * Il 12 agosto 2026 questo banco e' uscito VERDE mentre il difetto era vivo:
	 * la sessione aveva gia' un monitor, `mpv --fs` andava a schermo intero su
	 * QUELLO, e la nostra cattura riceveva zero.  Con una scena dichiarata viva e
	 * in movimento, zero fotogrammi e' la prova che stiamo guardando uno schermo
	 * diverso da quello su cui dipinge la scena.
	 */
	if (dopo_la_scena < minimo_dopo_scena)
	{
		printf("GUASTO\t%s\tscena viva e %" G_GUINT64_FORMAT " fotogrammi dopo\n", etichetta,
		       dopo_la_scena);
		fprintf(stderr,
		        "⛔ FALLITO (non «zero»): la scena era dichiarata viva e sono arrivati\n"
		        "   %" G_GUINT64_FORMAT " fotogrammi dopo di lei (minimo preteso %" G_GUINT64_FORMAT
		        ").\n   Prima della scena ne erano arrivati %" G_GUINT64_FORMAT
		        ": il flusso funziona.\n"
		        "   ⇒ Non e' il desktop fermo: e' che la scena dipinge su uno SCHERMO DIVERSO\n"
		        "     da quello che stiamo catturando (il nostro e' %s).\n",
		        dopo_la_scena, minimo_dopo_scena, prima_della_scena,
		        sessione && mutter_monitor_nostro(sessione) ? mutter_monitor_nostro(sessione)
		                                                    : "ignoto");
		cattura_fermo_libera(&primo.fermo);
		cattura_fermo_libera(&regime.fermo);
		cattura_ferma(cattura);
		mutter_chiudi(sessione);
		return 2;
	}

	/* --- la scrittura ---------------------------------------------------- */
	if (!cattura_consegna(cattura, &consegna))
	{
		printf("GUASTO\t%s\tnessun formato negoziato\n", etichetta);
		fprintf(stderr, "⛔ FALLITO: nessun formato e' stato negoziato: non c'e' niente da "
		                "dichiarare, e non scrivo zeri al posto suo.\n");
		cattura_ferma(cattura);
		mutter_chiudi(sessione);
		return 2;
	}

	if (conto.arrivati == 0)
	{
		esito = "ZERO FOTOGRAMMI";
		codice = 3;
	}
	else if (strada == CATTURA_STRADA_SCHEDA)
	{
		esito = "TIPO DICHIARATO, PIXEL NON LETTI (dmabuf)";
		codice = 0;
	}
	else if (!primo.preso && !regime.preso)
	{
		printf("GUASTO\t%s\tfotogrammi arrivati ma nessuno copiabile\n", etichetta);
		fprintf(stderr, "⛔ FALLITO: sono arrivati %" G_GUINT64_FORMAT " fotogrammi e nessuno "
		                "aveva pixel leggibili.\n",
		        conto.arrivati);
		cattura_ferma(cattura);
		mutter_chiudi(sessione);
		return 2;
	}
	else
	{
		esito = "UN FOTOGRAMMA";
		codice = 0;
		if (primo.preso &&
		    !g_file_set_contents(file_primo, (const char *) primo.fermo.pixel,
		                         (gssize) primo.fermo.byte, &sbaglio))
		{
			fprintf(stderr, "⛔ non riesco a scrivere %s: %s\n", file_primo, sbaglio->message);
			cattura_ferma(cattura);
			mutter_chiudi(sessione);
			return 1;
		}
		if (regime.preso &&
		    !g_file_set_contents(file_regime, (const char *) regime.fermo.pixel,
		                         (gssize) regime.fermo.byte, &sbaglio))
		{
			fprintf(stderr, "⛔ non riesco a scrivere %s: %s\n", file_regime, sbaglio->message);
			cattura_ferma(cattura);
			mutter_chiudi(sessione);
			return 1;
		}
	}

	/* --- il manifesto ---------------------------------------------------- */
	manifesto = g_string_new("{\n");
	g_string_append_printf(manifesto,
	                       "  \"strumento\": \"02-cattura-prodotto (src/cattura.c + "
	                       "src/mutter.c)\",\n"
	                       "  \"etichetta\": \"%s\",\n"
	                       "  \"quando_utc\": \"%s\",\n"
	                       "  \"nodo_pipewire\": %u,\n"
	                       "  \"esito\": \"%s\",\n"
	                       "  \"uscita\": %d,\n",
	                       etichetta, quando, nodo, esito, codice);
	g_string_append_printf(manifesto,
	                       "  \"chiesto\": {\n"
	                       "    \"larghezza\": %u, \"altezza\": %u, \"fps_massimi\": %u,\n"
	                       "    \"colore\": \"%s\", \"strada\": \"%s\",\n"
	                       "    \"cadenza\": \"0/1 con maxFramerate a %u — «mandami un "
	                       "fotogramma quando cambia qualcosa»\"\n"
	                       "  },\n",
	                       larghezza, altezza, fps,
	                       colore == CATTURA_COLORE_BGRA ? "BGRA"
	                       : colore == CATTURA_COLORE_10BIT ? "10bit"
	                                                        : "BGRx",
	                       strada == CATTURA_STRADA_SCHEDA ? "dmabuf" : "memoria", fps);
	g_string_append_printf(manifesto,
	                       "  \"negoziato\": {\n"
	                       "    \"noto\": %s,\n"
	                       "    \"larghezza\": %u, \"altezza\": %u,\n"
	                       "    \"colore\": \"%s\",\n"
	                       "    \"modificatore\": \"0x%" G_GINT64_MODIFIER "x\",\n"
	                       "    \"chi_lo_dice\": \"PipeWire, SPA_PARAM_Format nella richiamata "
	                       "param_changed — non e' l'etichetta che gli abbiamo dato noi\"\n"
	                       "  },\n",
	                       consegna.noto ? "true" : "false", consegna.larghezza, consegna.altezza,
	                       consegna.formato, (guint64) consegna.modificatore);

	g_string_append_printf(
	    manifesto,
	    "  \"consegna_a_F2_3\": {\n"
	    "    \"bit_per_canale\": %d,\n"
	    "    \"bit_per_canale_chi_lo_dice\": \"il FORMATO negoziato (%s), %s. STUDI.md §gnome §8.3 "
	    "[R]: supported_formats[] di Mutter 48.7 ha DUE voci, BGRx e BGRA — da questa "
	    "cattura NON escono dieci bit veri\",\n"
	    "    \"⛔ F2.3-A\": \"un HEVC Main10 alimentato da qui porta 8 bit promossi a 10: "
	    "l'etichetta dice Main10, l'immagine viene bene lo stesso, e l'imputato e' LA "
	    "CATTURA, non il codificatore\",\n"
	    "    \"stride\": %u,\n"
	    "    \"stride_chi_lo_dice\": \"⛔ LETTO dal chunk del buffer, mai calcolato come "
	    "larghezza×4 — oggi coincide, e proprio per questo la regola va scritta\",\n"
	    "    \"byte_per_fotogramma\": %" G_GUINT64_FORMAT ",\n"
	    "    \"range\": \"%s\",\n"
	    "    \"matrice\": \"%s\",\n"
	    "    \"trasferimento\": \"%s\",\n"
	    "    \"primari\": \"%s\",\n"
	    "    \"chi_lo_dice\": \"spa_video_info_raw.color_range / .color_matrix / "
	    ".transfer_function / .color_primaries, riempiti da spa_format_video_raw_parse sul "
	    "SPA_PARAM_Format del produttore\",\n"
	    "    \"⚠ sulla matrice\": \"alla cattura i pixel sono RGB: nessuna matrice 601/709 "
	    "e' stata applicata da noi. La matrice la SCEGLIE F2.3 nel convertire in YCbCr, e "
	    "F2.6 deve confrontare con la stessa — un confronto fatto con la matrice sbagliata "
	    "misura la matrice\",\n"
	    "    \"range_misurato_dal_prodotto\": \"%s\",\n"
	    "    \"valori_grezzi\": {\"color_range\": %u, \"color_matrix\": %u, "
	    "\"transfer_function\": %u, \"color_primaries\": %u}\n"
	    "  },\n",
	    consegna.bit_per_canale, consegna.formato, cattura_fonte_nome(consegna.fonte_bit),
	    /* ⛔ Lo stride si legge da QUALUNQUE fotogramma sia arrivato, anche da uno
	     *    senza pixel: sulla strada della scheda i pixel non sono qui, ma lo
	     *    stride e' un fatto del chunk, ed e' uno dei quattro che si
	     *    dichiarano a valle.  Scrivere 0 li' sarebbe un silenzio spacciato
	     *    per un numero. */
	    regime.fermo.stride ? regime.fermo.stride : primo.fermo.stride,
	    regime.fermo.byte ? regime.fermo.byte
	                      : (guint64) (regime.fermo.stride ? regime.fermo.stride
	                                                       : primo.fermo.stride) *
	                            consegna.altezza,
	    cattura_range_nome(consegna.range_grezzo), cattura_matrice_nome(consegna.matrice_grezza),
	    cattura_trasferimento_nome(consegna.trasferimento_grezzo),
	    cattura_primari_nome(consegna.primari_grezzi),
	    cattura_range_misurato_nome(regime.preso ? regime.fermo.consegna.range_misurato
	                                             : CATTURA_RANGE_NON_MISURATO),
	    consegna.range_grezzo, consegna.matrice_grezza, consegna.trasferimento_grezzo,
	    consegna.primari_grezzi);

	g_string_append(manifesto, "  \"buffer\": {\n    \"tipi_visti\": [");
	for (i = 0; (guint) i < conto.quanti_tipi; i++)
		g_string_append_printf(manifesto, "%s\"%s\"", i ? ", " : "",
		                       cattura_buffer_nome(conto.tipi_visti[i]));
	g_string_append_printf(manifesto,
	                       "],\n"
	                       "    \"chiesto\": \"%s\",\n"
	                       "    \"distinti_riciclati\": %u,\n"
	                       "    \"chi_lo_dice\": \"PipeWire, spa_data.type del piano 0 di ogni "
	                       "buffer — chiesto in DUE posti (il modificatore nel formato e "
	                       "SPA_PARAM_BUFFERS_dataType)\"\n"
	                       "  },\n",
	                       cattura_buffer_nome(consegna.buffer_chiesto), conto.buffer_distinti);

	g_string_append_printf(manifesto,
	                       "  \"fotogrammi\": {\n"
	                       "    \"minimo_dopo_la_scena_preteso\": %" G_GUINT64_FORMAT ",\n"
	                       "    \"arrivati_in_tutto\": %" G_GUINT64_FORMAT ",\n"
	                       "    \"prima_della_scena\": %" G_GUINT64_FORMAT ",\n"
	                       "    \"dopo_la_scena\": %" G_GUINT64_FORMAT ",\n"
	                       "    \"danno_pieno\": %" G_GUINT64_FORMAT ",\n"
	                       "    \"danno_parziale\": %" G_GUINT64_FORMAT ",\n"
	                       "    \"danno_assente\": %" G_GUINT64_FORMAT ",\n"
	                       "    \"senza_header\": %" G_GUINT64_FORMAT ",\n"
	                       "    \"solo_cursore_scartati\": %" G_GUINT64_FORMAT ",\n"
	                       "    \"stride_zero_scartati\": %" G_GUINT64_FORMAT ",\n"
	                       "    \"senza_pixel_scartati\": %" G_GUINT64_FORMAT "\n"
	                       "  },\n",
	                       minimo_dopo_scena, conto.arrivati, prima_della_scena, dopo_la_scena,
	                       conto.danno_pieno, conto.danno_parziale, conto.danno_assente,
	                       conto.senza_intestazione, conto.solo_cursore, conto.stride_zero,
	                       conto.senza_pixel);

	g_string_append_printf(manifesto,
	                       "  \"schermo\": {\n"
	                       "    \"connettore\": \"%s\",\n"
	                       "    \"prodotto\": \"%s\",\n"
	                       "    \"chi_lo_dice\": \"DisplayConfig.GetCurrentState prima e dopo "
	                       "RecordVirtual, piu' il nome del PRODOTTO: due strade indipendenti "
	                       "che devono concordare, perche' i due monitor virtuali del server "
	                       "sono ENTRAMBI 1920×1080@60\"\n"
	                       "  },\n",
	                       sessione && mutter_monitor_nostro(sessione)
	                           ? mutter_monitor_nostro(sessione)
	                           : "NON LO SO",
	                       sessione && mutter_monitor_prodotto(sessione)
	                           ? mutter_monitor_prodotto(sessione)
	                           : "—");

	manifesto_voce(manifesto, "primo", &primo, file_primo);
	manifesto_voce(manifesto, "regime", &regime, file_regime);

	g_string_append(manifesto,
	                "  \"avvertenze\": [\n"
	                "    \"⛔ E1 — il tipo di buffer NON dice dove Mutter renda. Un MemFd qui e' "
	                "la risposta a quel che ABBIAMO CHIESTO noi (servono i pixel leggibili), non "
	                "una scoperta sul compositore. LEZIONI.md §1.11.\",\n"
	                "    \"⛔ E1 — e nemmeno il contrario: un DMA-BUF non prova che si renda in "
	                "GPU. Un render node aperto e' necessario, non sufficiente.\",\n"
	                "    \"⚠ questo strumento NON misura il ritmo: copia fotogrammi da 8 MB "
	                "dentro la richiamata di tempo reale. Il ritmo e' della fase 0 (36 ± 2) e "
	                "della fase 3.\",\n"
	                "    \"⚠ il range 0-255 e' MISURATO da noi sui pixel, non dichiarato dal "
	                "produttore, e dipende dalla scena: una scena senza nero e bianco pieni non "
	                "arriva agli estremi, e cio' NON proverebbe un range limitato.\",\n"
	                "    \"⚠ la macchina ha DUE GPU: un buffer della scheda sbagliata non e' "
	                "importabile, e il sintomo e' composizione in software senza un errore da "
	                "nessuna parte. Sulla strada della memoria i pixel arrivano comunque: questo "
	                "giro NON lo vedrebbe.\"\n"
	                "  ]\n}\n");

	if (!g_file_set_contents(file_json, manifesto->str, -1, &sbaglio))
	{
		fprintf(stderr, "⛔ non riesco a scrivere %s: %s\n", file_json, sbaglio->message);
		g_string_free(manifesto, TRUE);
		cattura_ferma(cattura);
		mutter_chiudi(sessione);
		return 1;
	}
	g_string_free(manifesto, TRUE);

	printf("PRESA\t%s\t%s\t%s\t%" G_GUINT64_FORMAT "\t%" G_GUINT64_FORMAT "\t%s\n", etichetta,
	       esito, file_json, conto.arrivati, dopo_la_scena,
	       cattura_buffer_nome(consegna.buffer_dichiarato));
	fprintf(stderr,
	        "  esito: %s\n"
	        "  arrivati %" G_GUINT64_FORMAT " (prima della scena %" G_GUINT64_FORMAT ", dopo %"
	        G_GUINT64_FORMAT ")\n"
	        "  danno: pieno %" G_GUINT64_FORMAT ", parziale %" G_GUINT64_FORMAT ", assente %"
	        G_GUINT64_FORMAT "\n"
	        "  buffer distinti riciclati: %u · tipo dichiarato: %s\n"
	        "  stride LETTO: %u · byte: %" G_GUINT64_FORMAT "\n"
	        "  manifesto: %s\n",
	        esito, conto.arrivati, prima_della_scena, dopo_la_scena, conto.danno_pieno,
	        conto.danno_parziale, conto.danno_assente, conto.buffer_distinti,
	        cattura_buffer_nome(consegna.buffer_dichiarato),
	        regime.fermo.stride ? regime.fermo.stride : primo.fermo.stride, regime.fermo.byte,
	        file_json);

	cattura_fermo_libera(&primo.fermo);
	cattura_fermo_libera(&regime.fermo);
	cattura_ferma(cattura);
	mutter_chiudi(sessione);
	return codice;
}
