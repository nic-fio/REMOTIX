/*
 * 06-b33-risveglio.c — ⛔⛔ LA SECONDA PORTA DEL CLIC CHE MUORE.
 *
 * Sottofase 6.1, §7.1 del documento di fase: *«ogni `cattura_risveglia()`
 * ricrea i dispositivi di `libei`: 3 risvegli, 3 ricambi, con ZERO
 * `ADATTA_TELA`»*.  ⇒ Il clic che muore ha una porta che **non dipende dalla
 * tela**, e si apre proprio mentre l'utente tiene premuto il mouse su un
 * desktop fermo.
 *
 *   ./06-b33-risveglio [--tela 1264x800]     apre, e aspetta comandi su stdin
 *
 * ---------------------------------------------------------------------------
 * ⛔ CHE COS'E' QUESTO PROGRAMMA, E CHE COSA NON E'
 *
 * ⭐ E' `CODER.md` §3.6 alla lettera — *«isola UNA funzione, e chiamala da
 *    fuori»*.  Collega i moduli del PRODOTTO (`src/cattura.c`, `src/input.c`,
 *    `src/mutter.c`, `src/tastiera.c`) e chiama `cattura_risveglia()` — **la
 *    stessa funzione che il figlio chiama quando la scena e' ferma e una chiave
 *    e' dovuta** (`figlio.c:6365`).  ⛔ Non c'e' QUIC, non c'e' `rcp.c`, non
 *    c'e' il formato dei messaggi.
 *
 * ⛔⛔ **E NON E' LA MISURA.**  Quel che questo programma stampa e' il registro
 *      di CHI MANDA, e `CODER.md` §3.8 dice che non vale niente: dice che
 *      abbiamo chiamato una funzione, non che il desktop ha ricevuto qualcosa.
 *      ⇒ Il verdetto lo da' il **testimone dentro la sessione**
 *      (`06-b33-testimone.c`), e lo legge `06-b33-risveglio.py`.
 *
 * ⚠ L'unica cosa che questo programma misura da se' — e la misura, non la
 *   deduce — e' `ricambi_puntatore`, letto da `input_conto()`, che e' una
 *   finestra sullo stato interno di `input.c` e non una riga di registro.
 *
 * ---------------------------------------------------------------------------
 * ⛔ PERCHE' USA `cattura.c` E NON UN CONSUMATORE SCRITTO QUI
 *
 * `04-b24-iniezione.c` si scrive il suo consumatore PipeWire a mano, ed e'
 * giusto per quel che misura (l'input, dove la cattura e' solo il pretesto che
 * fa nascere il viewport).  ⛔ Qui no: **l'imputato E' `cattura_risveglia()`**.
 * Un risveglio scritto a mano nel banco misurerebbe l'idea che ho io di come
 * funziona, non quel che il prodotto fa — e le due cose divergono esattamente
 * il giorno in cui `cattura.c` cambia.
 *
 * ⚠ E `cattura_avvia()` porta con se' i quattro parametri di consumo
 *   (`ParamBuffers` e i tre `ParamMeta`), che un consumatore scritto a mano non
 *   ha: quella differenza cambia la rinegoziazione, cioe' proprio la cosa che
 *   si sta guardando.
 *
 * ---------------------------------------------------------------------------
 * ⛔ IL CONSUMATORE DEVE CONSUMARE, O IL VIEWPORT NON NASCE
 *
 * `[R]` `meta-screen-cast-virtual-stream-src.c:279-283`: il flusso diventa
 * *configured* — e solo allora Mutter aggiunge il viewport da cui nasce il
 * dispositivo assoluto — dentro `..._src_enable`, cioe' **quando qualcuno
 * comincia davvero a leggere i fotogrammi**.  ⇒ Il ciclo dei comandi chiama
 * `cattura_prendi()` a ogni giro, con attesa zero.
 *
 * ---------------------------------------------------------------------------
 * ⭐⭐ E LA CATENA CHE QUESTO BANCO PROVA A SMENTIRE, tutta `[R]` in Mutter 48.7
 *
 *   1. `cattura_risveglia()` chiama `pw_stream_update_params()` sul flusso gia'
 *      aperto (`src/cattura.c:1392`);
 *   2. il produttore rinegozia: `MetaScreenCastStreamSrc` si spegne e si
 *      riaccende, e `meta_screen_cast_virtual_stream_src_enable()`
 *      (`:263-290`) chiama `meta_eis_viewport_notify_changed()`;
 *   3. `on_viewport_changed` (`meta-eis.c:319-323`) emette **`viewports-changed`**;
 *   4. `update_viewports` (`meta-eis-client.c:1049-1062`) chiama
 *      `remove_viewport_devices` — che ⛔ **NON passa da `drop_device()`** — e
 *      poi `add_abs_pointer_devices`.
 *
 * ⇒ Se la catena e' vera, un `risveglia` con `BTN_LEFT` giu' porta
 *   `ricambi_puntatore` a +1 **senza che nessuno abbia toccato la tela**, e da
 *   li' il pulsante e' un ORFANO: il suo rilascio non arriva a nessuno e il
 *   desktop non prende piu' un clic (`meta-seat-impl.c:899-908`).
 *
 * ⛔ L'ipotesi da smentire e' quella scritta in §7.1.  Se `ricambi_puntatore`
 *   NON sale, §7.1 e' falsa e va corretta — e questo banco lo deve poter dire.
 *
 * ---------------------------------------------------------------------------
 * I COMANDI (uno per riga; ogni risposta comincia con «B33R: »)
 *
 *   punta X Y            input_puntatore
 *   pulsante C P         input_pulsante        (C evdev: BTN_LEFT = 272)
 *   posizione C P        input_posizione       (C evdev: KEY_LEFTCTRL = 29)
 *   lettera N            input_lettera
 *   risveglia            ⭐⭐ `cattura_risveglia()`, LA FUNZIONE DEL PRODOTTO
 *   ridimensiona L A     `cattura_ridimensiona()` — il caso GIA' NOTO (§4.6),
 *                        che serve da confronto: la porta che si sapeva
 *   ritela L A           input_ritela
 *   rilascia             input_rilascia_tutto  → stampa QUANTI ne ha rilasciati
 *   dormi MS             ⛔ dorme CONTINUANDO a girare libei e a consumare
 *   stato                il conto, i ricambi, gli orfani, i fotogrammi
 *   fine                 esce pulito
 */
#include <errno.h>
#include <gio/gio.h>
#include <poll.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include "cattura.h"
#include "input.h"
#include "mutter.h"
#include "registro.h"
#include "tastiera.h"

/* ⛔ Le due finestre di banco di `src/input.c`: NON stanno in `input.h`, che e'
 *    il contratto del PRODOTTO e appartiene al coordinatore.  Si dichiarano
 *    qui, con la stessa firma — cambiargliela sotto romperebbe `04-b24`. */
extern void input_conto(const Input *, unsigned *tasti, unsigned *pulsanti,
                        unsigned *ricambi_puntatore, unsigned *ricambi_tastiera, int *pronto);
extern unsigned input_orfani(const Input *);

static MutterSessione *sessione;
static Cattura *cat;
static Input *canale;
static uint32_t tela_l = 1264, tela_a = 800;
static unsigned long fotogrammi;
static unsigned long risvegli;

static void dilo(const char *forma, ...)
{
	va_list argomenti;

	fputs("B33R: ", stdout);
	va_start(argomenti, forma);
	vfprintf(stdout, forma, argomenti);
	va_end(argomenti);
	fputc('\n', stdout);
	fflush(stdout);
}

/*
 * ⛔ UN GIRO DEL CICLO, e le due cose che deve fare stanno insieme apposta:
 *    girare `libei` (o i `DEVICE_ADDED` non si vedono mai) e CONSUMARE (o il
 *    viewport non nasce, `[R]` sopra).  ⚠ Chiamarne una sola e' il difetto che
 *    fa misurare un silenzio e chiamarlo guasto.
 *
 * Ritorna FALSE se il canale di input e' caduto.
 */
static gboolean gira_una_volta(void)
{
	CatturaFermo fermo;
	g_autoptr(GError) sbaglio = NULL;

	if (canale && input_gira(canale) < 0)
		return FALSE;
	if (cat)
	{
		/* ⛔ Attesa ZERO: chi consuma qui non deve rallentare il ciclo, deve
		 *    solo esserci.  ⚠ E lo zero NON e' un guasto: su Wayland un
		 *    desktop fermo non consegna niente, ed e' precisamente la scena
		 *    che questo banco vuole. */
		if (cattura_prendi(cat, 0.0, &fermo, &sbaglio) == CATTURA_PRESA_FATTA)
		{
			fotogrammi++;
			cattura_fermo_libera(&fermo);
		}
	}
	return TRUE;
}

static void stampa_stato(const char *quando)
{
	unsigned tasti = 0, pulsanti = 0, rp = 0, rt = 0;
	uint32_t nl = 0, na = 0;
	int pronto = 0;

	input_conto(canale, &tasti, &pulsanti, &rp, &rt, &pronto);
	cattura_misura_negoziata(cat, &nl, &na);
	dilo("STATO %s pronto=%d tasti_premuti=%u pulsanti_premuti=%u orfani=%u "
	     "ricambi_puntatore=%u ricambi_tastiera=%u risvegli=%lu fotogrammi=%lu "
	     "negoziata=%ux%u",
	     quando, pronto, tasti, pulsanti, input_orfani(canale), rp, rt, risvegli, fotogrammi, nl,
	     na);
}

/* ⛔ Dorme CONTINUANDO a girare: un `g_usleep` secco perderebbe i
 *    `DEVICE_REMOVED`/`DEVICE_ADDED` che arrivano 8-24 ms dopo il risveglio, e
 *    il banco direbbe «nessun ricambio» misurando la propria sordita'. */
static gboolean dormi_girando(int ms)
{
	gint64 scadenza = g_get_monotonic_time() + (gint64) ms * 1000;

	while (g_get_monotonic_time() < scadenza)
	{
		if (!gira_una_volta())
			return FALSE;
		g_usleep(5 * 1000);
	}
	return TRUE;
}

static void comando(char *riga)
{
	long a1, a2;

	g_strstrip(riga);
	if (!*riga || riga[0] == '#')
		return;

	if (g_str_equal(riga, "fine"))
	{
		dilo("fine");
		input_chiudi(canale);
		cattura_ferma(cat);
		mutter_chiudi(sessione);
		exit(0);
	}
	if (g_str_equal(riga, "stato"))
	{
		stampa_stato("");
		return;
	}
	if (g_str_equal(riga, "rilascia"))
	{
		int quanti = input_rilascia_tutto(canale);

		/* ⛔ IL NUMERO, perche' il banco possa contarlo — `RCP.md` §11.  ⚠ E si
		 *    stampa anche l'orfano: «rilasciati 0» e «ce n'era uno che non si
		 *    poteva rilasciare» sono due fatti diversi. */
		dilo("RILASCIATI %d (orfani rimasti %u)", quanti, input_orfani(canale));
		return;
	}
	if (g_str_equal(riga, "risveglia"))
	{
		unsigned prima = 0, dopo = 0;
		gboolean esito;

		/*
		 * ⛔⛔ IL CUORE DEL BANCO.  Si legge il conto PRIMA, si chiama la
		 *      funzione del prodotto, si gira per 400 ms — che e' il fondo che
		 *      `figlio.c` mette fra un risveglio e l'altro — e si rilegge.
		 *
		 * ⚠ I 400 ms non sono un'attesa prudente: `[M]` §4.6 dice che il
		 *   ricambio arriva **8-24 ms dopo**, e 400 e' venti volte tanto.  Un
		 *   banco che aspettasse 10 ms misurerebbe la propria fretta.
		 */
		input_conto(canale, NULL, NULL, &prima, NULL, NULL);
		esito = cattura_risveglia(cat);
		risvegli++;
		if (!dormi_girando(400))
		{
			dilo("ERRORE: il canale di input e' caduto durante il risveglio");
			exit(4);
		}
		input_conto(canale, NULL, NULL, &dopo, NULL, NULL);
		dilo("RISVEGLIO n.%lu esito=%d ricambi_puntatore %u → %u (delta %d) "
		     "⛔ e NESSUNO ha toccato la tela",
		     risvegli, (int) esito, prima, dopo, (int) dopo - (int) prima);
		return;
	}
	if (sscanf(riga, "dormi %ld", &a1) == 1)
	{
		if (!dormi_girando((int) a1))
		{
			dilo("ERRORE: il canale di input e' caduto durante l'attesa");
			exit(4);
		}
		dilo("dormito %ld ms", a1);
		return;
	}
	if (sscanf(riga, "punta %ld %ld", &a1, &a2) == 2)
	{
		dilo("punta %ld %ld -> %d", a1, a2, input_puntatore(canale, (uint32_t) a1, (uint32_t) a2));
		return;
	}
	if (sscanf(riga, "pulsante %ld %ld", &a1, &a2) == 2)
	{
		dilo("pulsante %ld %ld -> %d", a1, a2, input_pulsante(canale, (uint16_t) a1, (int) a2));
		return;
	}
	if (sscanf(riga, "posizione %ld %ld", &a1, &a2) == 2)
	{
		dilo("posizione %ld %ld -> %d", a1, a2, input_posizione(canale, (uint16_t) a1, (int) a2));
		return;
	}
	if (sscanf(riga, "lettera %ld", &a1) == 1)
	{
		dilo("lettera %ld -> %d", a1, input_lettera(canale, (uint32_t) a1));
		return;
	}
	if (sscanf(riga, "ritela %ld %ld", &a1, &a2) == 2)
	{
		dilo("ritela %ld %ld -> %d", a1, a2,
		     input_ritela(canale, (uint32_t) a1, (uint32_t) a2));
		tela_l = (uint32_t) a1;
		tela_a = (uint32_t) a2;
		return;
	}
	if (sscanf(riga, "ridimensiona %ld %ld", &a1, &a2) == 2)
	{
		unsigned prima = 0, dopo = 0;
		CatturaRitela esito;

		/* ⛔ LA PORTA GIA' NOTA, §4.6: serve da confronto.  Se il ricambio
		 *    arrivasse SOLO di qui, §7.1 sarebbe falsa — ed e' l'unico modo di
		 *    saperlo, perche' un numero senza il suo confronto non distingue
		 *    «il risveglio ricambia» da «ricambia sempre tutto». */
		input_conto(canale, NULL, NULL, &prima, NULL, NULL);
		esito = cattura_ridimensiona(cat, (uint32_t) a1, (uint32_t) a2);
		if (!dormi_girando(400))
		{
			dilo("ERRORE: il canale di input e' caduto durante il ridimensionamento");
			exit(4);
		}
		input_conto(canale, NULL, NULL, &dopo, NULL, NULL);
		dilo("RIDIMENSIONATO a %ldx%ld esito=%d ricambi_puntatore %u → %u (delta %d)", a1, a2,
		     (int) esito, prima, dopo, (int) dopo - (int) prima);
		return;
	}
	dilo("comando ignoto: «%s»", riga);
}

int main(int argc, char **argv)
{
	g_autoptr(GError) sbaglio = NULL;
	g_autofree char *errore = NULL;
	struct pollfd sonda;
	char riga[256];

	setvbuf(stdout, NULL, _IOLBF, 0);
	registro_parlantina(TRUE);

	for (int i = 1; i < argc; i++)
		if (!strcmp(argv[i], "--tela") && i + 1 < argc)
			sscanf(argv[++i], "%ux%u", &tela_l, &tela_a);

	/* --- 1. la sessione del PRODOTTO, ConnectToEIS compreso ---------------- */
	sessione = mutter_apri(&sbaglio);
	if (!sessione)
	{
		dilo("ERRORE: mutter_apri: %s", sbaglio->message);
		return 2;
	}
	dilo("sessione aperta: nodo %u, descrittore EIS %d", mutter_nodo(sessione),
	     mutter_eis_fd(sessione));

	/* --- 2. la CATTURA DEL PRODOTTO: e' lei l'imputato --------------------- */
	cat = cattura_avvia(mutter_nodo(sessione), tela_l, tela_a, 60, CATTURA_STRADA_MEMORIA,
	                    CATTURA_COLORE_BGRX, NULL, NULL, NULL, &sbaglio);
	if (!cat)
	{
		dilo("ERRORE: cattura_avvia: %s", sbaglio ? sbaglio->message : "senza motivo dichiarato");
		return 2;
	}
	{
		/* ⛔ Si aspetta che il flusso sia ATTIVO prima di andare avanti: prima
		 *    di quel momento non c'e' nessun viewport, quindi nessun
		 *    dispositivo assoluto, e un risveglio non avrebbe niente da
		 *    ricambiare. */
		gint64 scadenza = g_get_monotonic_time() + 20 * G_USEC_PER_SEC;

		while (g_get_monotonic_time() < scadenza && !cattura_attiva(cat))
			g_usleep(50 * 1000);
		if (!cattura_attiva(cat))
		{
			dilo("ERRORE: il flusso non e' attivo dopo 20 s (%s)",
			     cattura_guasto(cat) ?: "senza spiegazione");
			return 2;
		}
	}
	dilo("cattura attiva a %ux%u sul nodo %u", tela_l, tela_a, mutter_nodo(sessione));

	if (mutter_monitor_cerca(sessione))
		dilo("MONITOR %s («%s»)", mutter_monitor_nostro(sessione),
		     mutter_monitor_prodotto(sessione));
	else
		dilo("⚠ il nostro monitor non si sa per nome: NON dico quale sia");

	/* --- 3. il canale di input -------------------------------------------- */
	canale = input_apri(sessione, tela_l, tela_a, &errore);
	if (!canale)
	{
		dilo("ERRORE: input_apri: %s", errore ?: "senza motivo dichiarato");
		return 3;
	}

	/*
	 * ⛔ SI ASPETTA CHE IL DISPOSITIVO SIA PRONTO, e si dice quando lo e'.
	 *    Iniettare prima di «PRONTO» vorrebbe dire misurare un silenzio che non
	 *    e' un difetto (`04-b24-iniezione.c`, stessa trappola).
	 */
	{
		gint64 scadenza = g_get_monotonic_time() + 20 * G_USEC_PER_SEC;
		int pronto = 0;

		while (g_get_monotonic_time() < scadenza && !pronto)
		{
			if (!gira_una_volta())
			{
				dilo("ERRORE: il canale di input e' caduto");
				return 3;
			}
			input_conto(canale, NULL, NULL, NULL, NULL, &pronto);
			if (!pronto)
				g_usleep(50 * 1000);
		}
		if (!pronto)
		{
			dilo("ERRORE: nessun dispositivo ASSOLUTO con una regione dopo 20 s");
			stampa_stato("mai-pronto");
			return 3;
		}
	}
	stampa_stato("all-avvio");
	dilo("PRONTO");

	/* --- 4. i comandi ------------------------------------------------------ */
	sonda.fd = STDIN_FILENO;
	sonda.events = POLLIN;
	for (;;)
	{
		sonda.revents = 0;
		if (poll(&sonda, 1, 20) < 0 && errno != EINTR)
			break;
		if (!gira_una_volta())
		{
			dilo("ERRORE: il compositore ha chiuso il canale di input");
			return 4;
		}
		if (sonda.revents & POLLIN)
		{
			if (!fgets(riga, sizeof riga, stdin))
			{
				/* ⛔ Lo stdin chiuso NON e' «fine»: e' chi guida che se n'e'
				 *    andato, e il conto di quel che e' premuto resta pieno.
				 *    Si dice, e si esce con un codice diverso. */
				stampa_stato("stdin-chiuso");
				dilo("⛔ stdin chiuso senza «fine»: esco SENZA rilasciare");
				return 5;
			}
			comando(riga);
		}
	}
	dilo("ERRORE: poll: %s", g_strerror(errno));
	return 4;
}
