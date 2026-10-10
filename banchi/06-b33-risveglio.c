/*
 * 06-b33-risveglio.c — ⛔⛔ THE SECOND DOOR OF THE DYING CLICK.
 *
 * Sub-phase 6.1, §7.1 of the phase document: *"every `cattura_risveglia()`
 * recreates the `libei` devices: 3 wake-ups, 3 replacements, with ZERO
 * `ADATTA_TELA`"*.  ⇒ The dying click has a door that **does not depend on the
 * canvas**, and it opens precisely while the user holds the mouse pressed on a
 * still desktop.
 *
 *   ./06-b33-risveglio [--tela 1264x800]     opens, and waits for commands on stdin
 *
 * ---------------------------------------------------------------------------
 * ⛔ WHAT THIS PROGRAM IS, AND WHAT IT IS NOT
 *
 * ⭐ It is `CODER.md` §3.6 to the letter — *"isolate ONE function, and call it
 *    from outside"*.  It links the PRODUCT modules (`src/cattura.c`,
 *    `src/input.c`, `src/mutter.c`, `src/tastiera.c`) and calls
 *    `cattura_risveglia()` — **the same function the child calls when the
 *    scene is still and a key is owed** (`figlio.c:6365`).  ⛔ There is no
 *    QUIC, no `rcp.c`, no message format.
 *
 * ⛔⛔ **AND IT IS NOT THE MEASUREMENT.**  What this program prints is the log
 *      of THE SENDER, and `CODER.md` §3.8 says it is worth nothing: it says
 *      we called a function, not that the desktop received anything.
 *      ⇒ The verdict is given by the **witness inside the session**
 *      (`06-b33-testimone.c`), and read by `06-b33-risveglio.py`.
 *
 * ⚠ The only thing this program measures by itself — and it measures it, it
 *   does not deduce it — is `ricambi_puntatore`, read from `input_conto()`,
 *   which is a window on the internal state of `input.c` and not a log line.
 *
 * ---------------------------------------------------------------------------
 * ⛔ WHY IT USES `cattura.c` AND NOT A CONSUMER WRITTEN HERE
 *
 * `04-b24-iniezione.c` writes its own PipeWire consumer by hand, and that is
 * right for what it measures (input, where the capture is only the pretext
 * that makes the viewport be born).  ⛔ Not here: **the defendant IS
 * `cattura_risveglia()`**.  A wake-up written by hand in the bench would
 * measure my idea of how it works, not what the product does — and the two
 * diverge exactly on the day `cattura.c` changes.
 *
 * ⚠ And `cattura_avvia()` brings along the four consumption parameters
 *   (`ParamBuffers` and the three `ParamMeta`), which a hand-written consumer
 *   does not have: that difference changes the renegotiation, that is,
 *   precisely the thing being looked at.
 *
 * ---------------------------------------------------------------------------
 * ⛔ THE CONSUMER MUST CONSUME, OR THE VIEWPORT IS NOT BORN
 *
 * `[R]` `meta-screen-cast-virtual-stream-src.c:279-283`: the stream becomes
 * *configured* — and only then does Mutter add the viewport from which the
 * absolute device is born — inside `..._src_enable`, that is, **when someone
 * really starts reading the frames**.  ⇒ The command loop calls
 * `cattura_prendi()` at every turn, with zero wait.
 *
 * ---------------------------------------------------------------------------
 * ⭐⭐ AND THE CHAIN THIS BENCH TRIES TO REFUTE, all `[R]` in Mutter 48.7
 *
 *   1. `cattura_risveglia()` calls `pw_stream_update_params()` on the already
 *      open stream (`src/cattura.c:1392`);
 *   2. the producer renegotiates: `MetaScreenCastStreamSrc` turns off and on
 *      again, and `meta_screen_cast_virtual_stream_src_enable()`
 *      (`:263-290`) calls `meta_eis_viewport_notify_changed()`;
 *   3. `on_viewport_changed` (`meta-eis.c:319-323`) emits **`viewports-changed`**;
 *   4. `update_viewports` (`meta-eis-client.c:1049-1062`) calls
 *      `remove_viewport_devices` — which ⛔ **does NOT go through
 *      `drop_device()`** — and then `add_abs_pointer_devices`.
 *
 * ⇒ If the chain is true, a `risveglia` with `BTN_LEFT` down brings
 *   `ricambi_puntatore` to +1 **without anybody touching the canvas**, and from
 *   there on the button is an ORPHAN: its release reaches nobody and the
 *   desktop no longer takes a click (`meta-seat-impl.c:899-908`).
 *
 * ⛔ The hypothesis to refute is the one written in §7.1.  If
 *   `ricambi_puntatore` does NOT go up, §7.1 is false and must be corrected —
 *   and this bench must be able to say so.
 *
 * ---------------------------------------------------------------------------
 * THE COMMANDS (one per line; every answer starts with "B33R: ")
 *
 *   punta X Y            input_puntatore
 *   pulsante C P         input_pulsante        (C evdev: BTN_LEFT = 272)
 *   posizione C P        input_posizione       (C evdev: KEY_LEFTCTRL = 29)
 *   lettera N            input_lettera
 *   risveglia            ⭐⭐ `cattura_risveglia()`, THE PRODUCT'S FUNCTION
 *   ridimensiona L A     `cattura_ridimensiona()` — the ALREADY KNOWN case (§4.6),
 *                        which serves as a comparison: the door we knew about
 *   ritela L A           input_ritela
 *   rilascia             input_rilascia_tutto  → prints HOW MANY it released
 *   dormi MS             ⛔ sleeps WHILE KEEPING libei running and consuming
 *   stato                the count, the replacements, the orphans, the frames
 *   fine                 exits cleanly
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

/* ⛔ The two bench windows of `src/input.c`: they are NOT in `input.h`, which
 *    is the PRODUCT contract and belongs to the coordinator.  They are
 *    declared here, with the same signature — changing it under them would
 *    break `04-b24`. */
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
 * ⛔ ONE TURN OF THE LOOP, and the two things it must do sit together on
 *    purpose: run `libei` (or the `DEVICE_ADDED` are never seen) and CONSUME
 *    (or the viewport is not born, `[R]` above).  ⚠ Calling only one of them is
 *    the defect that makes one measure a silence and call it a fault.
 *
 * Returns FALSE if the input channel has dropped.
 */
static gboolean gira_una_volta(void)
{
	CatturaFermo fermo;
	g_autoptr(GError) sbaglio = NULL;

	if (canale && input_gira(canale) < 0)
		return FALSE;
	if (cat)
	{
		/* ⛔ ZERO wait: whoever consumes here must not slow the loop down, it
		 *    must only be there.  ⚠ And zero is NOT a fault: on Wayland a
		 *    still desktop delivers nothing, and that is precisely the scene
		 *    this bench wants. */
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

/* ⛔ Sleeps WHILE KEEPING the loop running: a plain `g_usleep` would lose the
 *    `DEVICE_REMOVED`/`DEVICE_ADDED` that arrive 8-24 ms after the wake-up, and
 *    the bench would say "no replacement" while measuring its own deafness. */
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

		/* ⛔ THE NUMBER, so that the bench can count it — `RCP.md` §11.  ⚠ And
		 *    the orphan is printed too: "released 0" and "there was one that
		 *    could not be released" are two different facts. */
		dilo("RELEASED %d (orphans left %u)", quanti, input_orfani(canale));
		return;
	}
	if (g_str_equal(riga, "risveglia"))
	{
		unsigned prima = 0, dopo = 0;
		gboolean esito;

		/*
		 * ⛔⛔ THE HEART OF THE BENCH.  The count is read BEFORE, the product
		 *      function is called, the loop runs for 400 ms — which is the
		 *      floor `figlio.c` puts between one wake-up and the next — and it
		 *      is read again.
		 *
		 * ⚠ The 400 ms are not a cautious wait: `[M]` §4.6 says the
		 *   replacement arrives **8-24 ms later**, and 400 is twenty times as
		 *   much.  A bench that waited 10 ms would measure its own haste.
		 */
		input_conto(canale, NULL, NULL, &prima, NULL, NULL);
		esito = cattura_risveglia(cat);
		risvegli++;
		if (!dormi_girando(400))
		{
			dilo("ERRORE: the input channel dropped during the wake-up");
			exit(4);
		}
		input_conto(canale, NULL, NULL, &dopo, NULL, NULL);
		dilo("WAKE-UP n.%lu esito=%d ricambi_puntatore %u → %u (delta %d) "
		     "⛔ and NOBODY touched the canvas",
		     risvegli, (int) esito, prima, dopo, (int) dopo - (int) prima);
		return;
	}
	if (sscanf(riga, "dormi %ld", &a1) == 1)
	{
		if (!dormi_girando((int) a1))
		{
			dilo("ERRORE: the input channel dropped during the wait");
			exit(4);
		}
		dilo("slept %ld ms", a1);
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

		/* ⛔ THE ALREADY KNOWN DOOR, §4.6: it serves as a comparison.  If the
		 *    replacement arrived ONLY from here, §7.1 would be false — and it is
		 *    the only way to know, because a number without its comparison does
		 *    not tell "the wake-up replaces" from "everything always replaces". */
		input_conto(canale, NULL, NULL, &prima, NULL, NULL);
		esito = cattura_ridimensiona(cat, (uint32_t) a1, (uint32_t) a2);
		if (!dormi_girando(400))
		{
			dilo("ERRORE: the input channel dropped during the resize");
			exit(4);
		}
		input_conto(canale, NULL, NULL, &dopo, NULL, NULL);
		dilo("RESIZED to %ldx%ld esito=%d ricambi_puntatore %u → %u (delta %d)", a1, a2,
		     (int) esito, prima, dopo, (int) dopo - (int) prima);
		return;
	}
	dilo("unknown command: «%s»", riga);
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

	/* --- 1. the PRODUCT session, ConnectToEIS included -------------------- */
	sessione = mutter_apri(&sbaglio);
	if (!sessione)
	{
		dilo("ERRORE: mutter_apri: %s", sbaglio->message);
		return 2;
	}
	dilo("session open: node %u, EIS descriptor %d", mutter_nodo(sessione),
	     mutter_eis_fd(sessione));

	/* --- 2. the PRODUCT CAPTURE: it is the defendant ----------------------- */
	cat = cattura_avvia(mutter_nodo(sessione), tela_l, tela_a, 60, CATTURA_STRADA_MEMORIA,
	                    CATTURA_COLORE_BGRX, NULL, NULL, NULL, &sbaglio);
	if (!cat)
	{
		dilo("ERRORE: cattura_avvia: %s", sbaglio ? sbaglio->message : "no reason declared");
		return 2;
	}
	{
		/* ⛔ We wait for the stream to be ACTIVE before going on: before that
		 *    moment there is no viewport, hence no absolute device, and a
		 *    wake-up would have nothing to replace. */
		gint64 scadenza = g_get_monotonic_time() + 20 * G_USEC_PER_SEC;

		while (g_get_monotonic_time() < scadenza && !cattura_attiva(cat))
			g_usleep(50 * 1000);
		if (!cattura_attiva(cat))
		{
			dilo("ERRORE: the stream is not active after 20 s (%s)",
			     cattura_guasto(cat) ?: "no explanation");
			return 2;
		}
	}
	dilo("capture active at %ux%u on node %u", tela_l, tela_a, mutter_nodo(sessione));

	if (mutter_monitor_cerca(sessione))
		dilo("MONITOR %s («%s»)", mutter_monitor_nostro(sessione),
		     mutter_monitor_prodotto(sessione));
	else
		dilo("⚠ our monitor is not known by name: I do NOT say which one it is");

	/* --- 3. the input channel -------------------------------------------- */
	canale = input_apri(sessione, tela_l, tela_a, &errore);
	if (!canale)
	{
		dilo("ERRORE: input_apri: %s", errore ?: "no reason declared");
		return 3;
	}

	/*
	 * ⛔ WE WAIT FOR THE DEVICE TO BE READY, and say when it is.  Injecting
	 *    before "PRONTO" would mean measuring a silence that is not a defect
	 *    (`04-b24-iniezione.c`, same trap).
	 */
	{
		gint64 scadenza = g_get_monotonic_time() + 20 * G_USEC_PER_SEC;
		int pronto = 0;

		while (g_get_monotonic_time() < scadenza && !pronto)
		{
			if (!gira_una_volta())
			{
				dilo("ERRORE: the input channel dropped");
				return 3;
			}
			input_conto(canale, NULL, NULL, NULL, NULL, &pronto);
			if (!pronto)
				g_usleep(50 * 1000);
		}
		if (!pronto)
		{
			dilo("ERRORE: no ABSOLUTE device with a region after 20 s");
			stampa_stato("mai-pronto");
			return 3;
		}
	}
	stampa_stato("all-avvio");
	dilo("PRONTO");

	/* --- 4. the commands ---------------------------------------------------- */
	sonda.fd = STDIN_FILENO;
	sonda.events = POLLIN;
	for (;;)
	{
		sonda.revents = 0;
		if (poll(&sonda, 1, 20) < 0 && errno != EINTR)
			break;
		if (!gira_una_volta())
		{
			dilo("ERRORE: the compositor closed the input channel");
			return 4;
		}
		if (sonda.revents & POLLIN)
		{
			if (!fgets(riga, sizeof riga, stdin))
			{
				/* ⛔ A closed stdin is NOT "fine": it is the driver that went
				 *    away, and the count of what is pressed stays full.  It is
				 *    said, and we exit with a different code. */
				stampa_stato("stdin-chiuso");
				dilo("⛔ stdin closed without «fine»: I exit WITHOUT releasing");
				return 5;
			}
			comando(riga);
		}
	}
	dilo("ERRORE: poll: %s", g_strerror(errno));
	return 4;
}
