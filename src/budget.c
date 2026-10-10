/* budget.c — ⭐⭐⭐ THE COMPOSITION BUDGET (phase 10, 25 Aug 2026).
 *
 * ⛔ The reason for every number is in `budget.h`, at the top: here there is
 *    only the mechanism.  Whoever changes a number reads that box first, or
 *    will change a calibration believing they are fixing an implementation.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#include "budget.h"
#include "registro.h"

/* ─────────────────────────────────────────────────────────────────────────────
 * ⭐ THE DELIVERED WINDOW — eight buckets of 250 ms, that is two seconds.
 *
 * ⛔ And the buckets serve one thing only that an incremental average cannot do:
 *    **make the delivered DECAY when frames stop arriving**.  A session that
 *    stops must go down towards zero on its own, or it would stay counted at
 *    the rate it had when it was working — and then the count would say
 *    «full» on an empty machine (false NO on everyone who arrives).
 *
 * ⚠ Two seconds and not twenty: `[M]` §6.16 — when eight idle sessions wake up
 *   the **rate** collapses within the first interval of the yardstick (**less
 *   than 2 s**), while the delay rises in 8-10 s.  A longer window would see
 *   the wake-up too late; a shorter one would count the hiccup of one lost
 *   frame as a collapse.
 * ─────────────────────────────────────────────────────────────────────────── */
#define SECCHI 8
#define SECCHIO_US 250000ull
#define FINESTRA_US ((uint64_t)SECCHI * SECCHIO_US)

/* ⛔⭐ HOW MANY DELAYS ARE KEPT, AND WHY THE MEDIAN AND NOT THE MAXIMUM.
 *
 *     The maximum would refuse a user for **a single hiccup** — a false NO on
 *     a datum that does not describe the state of the machine.  The median of
 *     32 samples describes *where the session sits*, and it is the same
 *     quantity that `[M]` §6.5/§6.9 measured («median delay» at every step):
 *     calibrating on one quantity and judging on another is the fastest way
 *     to have an uncalibrated yardstick.
 * ⚠ At ~40 fps, 32 samples are **0.8 s** — the same scale as the window. */
#define RITARDI 32

/* ⛔⭐ THE DELAY SAMPLES **DO NOT EXPIRE**, and it is a choice, not an
 *     oversight.
 *
 *     An **idle** session delivers `[M]` one frame every ~40 s (0.05
 *     Mpixel/s, §6.9): if its samples expired, it would be left **without a
 *     delay**, and the declared fallback (§1.33, uncomfortable direction)
 *     would count it at the worst case.  ⇒ ⛔ **Ten idle tenants would be
 *     rejected while costing nothing** — which is the twin error, and just as
 *     serious, of admitting the eighth that makes everything collapse.
 * ⭐ And in the opposite direction the choice is prudent: a **throttled**
 *    session that goes silent carries its big delay along until it delivers
 *    again.
 */

struct inquilino {
	bool usato;
	char utente[257];
	/* the composed pixels delivered, per bucket */
	uint64_t pixel[SECCHI];
	int secchio;              /* index of the current bucket */
	uint64_t secchio_da_us;   /* the instant the current bucket was born */
	uint64_t primo_us;        /* the first frame ever seen */
	uint64_t ultimo_us;       /* the last one, for slot reuse */
	bool mai_consegnato;
	uint32_t tela_l, tela_a;  /* the last canvas delivered */
	uint32_t ritardo_ms[RITARDI];
	int quanti_ritardi, prossimo_ritardo;
};

static struct inquilino *tabella;
static int quante_caselle;

/* ⛔ `0` = OFF, and it is the default: I6.  See `budget.h` point 5. */
static double capacita_mpixel_s;
static double riserva = BUDGET_RISERVA_PREDEFINITA;
static uint32_t tela_palco_l, tela_palco_a;

/* ------------------------------------------------------------------------- */

static uint64_t ora_us(bool *letta)
{
	struct timespec t;

	if (clock_gettime(CLOCK_MONOTONIC, &t) != 0) {
		/* ⛔ «I could not read the time» is not «it is midnight»: whoever
		 *    receives this declares it and does not judge. */
		if (letta)
			*letta = false;
		return 0;
	}
	if (letta)
		*letta = true;
	return (uint64_t)t.tv_sec * 1000000ull + (uint64_t)(t.tv_nsec / 1000);
}

/* ⛔ The table is sized on the cap in force, and allocated at the first
 *    switch-on.  ⚠ If `calloc` fails, the budget **does not turn on**: a
 *    budget that cannot count must not be able to say no. */
static bool tabella_pronta(int quante)
{
	if (tabella)
		return true;
	if (quante < 1)
		quante = 1;
	tabella = (struct inquilino *)calloc((size_t)quante, sizeof *tabella);
	if (!tabella) {
		registro_dice(REG_BUDGET,
		              "⛔ there is no memory for the budget table (%d "
		              "slots): the budget stays OFF.  ⚠ It is not «it holds»: it is "
		              "«I do not count», and whoever does not count does not say no",
		              quante);
		return false;
	}
	quante_caselle = quante;
	return true;
}

/* ⭐ The user's slot, or the oldest one if it is not there and there is no room.
 *
 * ⛔ Oldest-first reuse looks at `ultimo_us`, and it is needed because NOBODY
 *    tells this module that a stage has died: a tenant that vanished simply
 *    stops delivering, and its slot becomes the oldest.
 * ⚠ And it is not a disguised defect: a stale slot never enters the count,
 *   because the count is filled by the table of **live stages** and not by
 *   this one (see `budget_conto_dentro()`). */
static struct inquilino *casella(const char *utente, bool crea)
{
	struct inquilino *libera = NULL, *vecchia = NULL;

	if (!tabella || !utente || !utente[0])
		return NULL;
	for (int i = 0; i < quante_caselle; i++) {
		struct inquilino *in = &tabella[i];

		if (!in->usato) {
			if (!libera)
				libera = in;
			continue;
		}
		if (strcmp(in->utente, utente) == 0)
			return in;
		if (!vecchia || in->ultimo_us < vecchia->ultimo_us)
			vecchia = in;
	}
	if (!crea)
		return NULL;
	if (!libera)
		libera = vecchia;
	if (!libera)
		return NULL;
	memset(libera, 0, sizeof *libera);
	libera->usato = true;
	libera->mai_consegnato = true;
	snprintf(libera->utente, sizeof libera->utente, "%s", utente);
	return libera;
}

/* ⛔ Brings the window up to `adesso`, emptying the buckets that went out.
 *    ⚠ It is what makes the delivered of whoever stopped DECAY: without
 *      this call at verdict time too (not only at deposit), an idle session
 *      would stay counted at the rate it had. */
static void avanza(struct inquilino *in, uint64_t adesso)
{
	if (in->mai_consegnato)
		return;
	if (adesso < in->secchio_da_us)
		return;  /* ⚠ the clock is monotonic: it should not happen */
	while (adesso - in->secchio_da_us >= SECCHIO_US) {
		in->secchio_da_us += SECCHIO_US;
		in->secchio = (in->secchio + 1) % SECCHI;
		in->pixel[in->secchio] = 0;
		/* ⭐ If the gap is longer than the whole window we do not loop a
		 *    thousand times: everything is zeroed and restarted from now. */
		if (adesso - in->secchio_da_us >= FINESTRA_US) {
			memset(in->pixel, 0, sizeof in->pixel);
			in->secchio_da_us = adesso;
			in->secchio = 0;
			return;
		}
	}
}

/* ⭐ The delivered, in Mpixel/s.  ⛔ Returns `false` when **nothing has been
 *    measured**, and whoever receives it counts the worst case: «I have not
 *    measured» is not «zero» — a session just born has not delivered anything
 *    yet, and counting it zero is exactly the error that starves everyone. */
static bool consegnato(struct inquilino *in, uint64_t adesso, double *mpixel_s)
{
	uint64_t somma = 0;
	double secondi;

	if (!in || in->mai_consegnato)
		return false;
	/* ⛔ Until there is a WHOLE window of history the number does not describe
	 *    a rate: it describes «how recently it was born».  ⇒ Not measured. */
	if (adesso < in->primo_us + FINESTRA_US)
		return false;
	avanza(in, adesso);
	for (int i = 0; i < SECCHI; i++)
		somma += in->pixel[i];
	/* ⚠ We divide by the time COVERED — the full buckets plus the fraction of
	 *   the current one — and not by the nominal window: the current bucket is
	 *   on average half full, and dividing it by its whole bucket would
	 *   underestimate the demand by ~6 %.  ⛔ Underestimating the demand is the
	 *   direction that starves everyone (§1.33). */
	secondi = (double)(SECCHI - 1) * (double)SECCHIO_US / 1e6;
	secondi += (double)(adesso - in->secchio_da_us) / 1e6;
	if (secondi <= 0.0)
		return false;
	*mpixel_s = (double)somma / 1e6 / secondi;
	return true;
}

/* ⭐ The median of the kept delays.  `false` = never delivered anything, so
 *    there is nothing to take the median of — and it is not «zero delay». */
static bool ritardo_mediano(const struct inquilino *in, double *ms)
{
	uint32_t v[RITARDI];
	int n;

	if (!in || in->quanti_ritardi <= 0)
		return false;
	n = in->quanti_ritardi;
	memcpy(v, in->ritardo_ms, (size_t)n * sizeof v[0]);
	/* ⚠ Insertion sort on at most 32 elements, once per verdict: `qsort`
	 *   here would cost more lines than it saves. */
	for (int i = 1; i < n; i++)
		for (int j = i; j > 0 && v[j] < v[j - 1]; j--) {
			uint32_t t = v[j];
			v[j] = v[j - 1];
			v[j - 1] = t;
		}
	*ms = (double)v[n / 2];
	return true;
}

/* ⭐ The worst case of a canvas: its canvas times the maximum rate this
 *    hardware has shown it can deliver (§6.9, and see `budget.h`). */
static double peggiore(uint32_t l, uint32_t a)
{
	return (double)l * (double)a / 1e6 * BUDGET_RITMO_MAX_FOT_S;
}

/* ------------------------------------------------------------------------- */

void budget_accendi(double capacita, double f, uint32_t tela_l, uint32_t tela_a)
{
	tela_palco_l = tela_l;
	tela_palco_a = tela_a;
	riserva = f;
	if (riserva < 0.0)
		riserva = 0.0;
	if (riserva > 1.0)
		riserva = 1.0;
	capacita_mpixel_s = capacita > 0.0 ? capacita : 0.0;
	if (capacita_mpixel_s > 0.0 && !tabella_pronta(quante_caselle))
		capacita_mpixel_s = 0.0;
}

/* ⛔ The table is sized **before** switching on: `main.c` calls it with the
 *    cap in force, so the slots are as many as the possible stages and
 *    oldest-first reuse never bites in normal operation. */
void budget_caselle(int quante)
{
	if (!tabella)
		quante_caselle = quante;
}

bool budget_acceso(void)
{
	return capacita_mpixel_s > 0.0 && tabella != NULL;
}

/* ⛔ The two counts of the noes, and they live here because this is where
 *    they are written.  ⚠ They are never reset: they are «since this server
 *    started», which is the only window a log reader can reconstruct. */
static uint64_t domande_viste, negati_tutti, negati_budget;

void budget_riga_verdetto(const char *utente, bool ammesso, uint8_t motivo,
                          int tetto_sessioni, const char *perche)
{
	domande_viste++;
	if (!ammesso) {
		negati_tutti++;
		if (motivo == 0x06)
			negati_budget++;
	}
	/* ⛔ ONE line per verdict, and not one per frame: we pass here at every
	 *    login, not at every pixel.  ⭐ And it is written with the budget OFF
	 *    too, because `negati 0` is the fact that proves I6 — reading it
	 *    requires someone to write it. */
	registro_dice(REG_BUDGET,
	              "verdict for «%s»: %s · denied %llu (of which budget %llu) out of "
	              "%llu requests · in force --budget-mpixel-s %.1f (%s) "
	              "--tetto-sessioni %d --riserva %.2f%s%s",
	              utente ? utente : "?",
	              ammesso ? "⭐ ADMITTED" : "⛔ DENIED",
	              (unsigned long long)negati_tutti,
	              (unsigned long long)negati_budget,
	              (unsigned long long)domande_viste,
	              capacita_mpixel_s, budget_acceso() ? "ON" : "OFF",
	              tetto_sessioni, riserva,
	              (!ammesso && perche && perche[0]) ? " · reason: " : "",
	              (!ammesso && perche && perche[0]) ? perche : "");
}

void budget_riga_avvio(int tetto_sessioni)
{
	/* ⛔⭐ THE LINE A BENCH LOOKS FOR, and it carries the THREE values with the
	 *     **option name next to the number**.  ⚠ It is written first and
	 *     always — on AND off — because it is the one whoever judges calibrates
	 *     on: an oracle calibrated on a number different from the one in force
	 *     would produce false yeses and false noes **of its own**, not of the
	 *     product. */
	registro_dice(REG_BUDGET,
	              "%s phase 10 — THE THREE VALUES IN FORCE: "
	              "budget --budget-mpixel-s %.1f (%s) · "
	              "cap --tetto-sessioni %d · "
	              "reserve --riserva %.2f",
	              budget_acceso() ? "⭐⭐" : "⛔",
	              capacita_mpixel_s, budget_acceso() ? "ON" : "OFF",
	              tetto_sessioni, riserva);
	if (budget_acceso())
		registro_dice(REG_BUDGET,
		              "⭐⭐ phase 10 — THE COMPOSITION BUDGET: ON at %.1f "
		              "Mpixel/s, reserve %.2f, delay threshold %.1f ms, "
		              "worst case %.2f fps (⇒ %.1f Mpixel/s for a "
		              "%ux%u), tolerance %.0f%%, %d slots.  ⛔ The quantity "
		              "is COMPOSITION, not encoding: `[M]` §6.11 the "
		              "ceiling is 0.97 Gpixel/s against 1.86 for the encoder, "
		              "and what saturates `rcs0` is the compositor.  ⛔ Whoever does not fit "
		              "receives CONGEDO 0x06 BUDGET_PIENO **before** their "
		              "stage is born.  ⚠ The number does NOT self-tune (§6.9): before "
		              "the machine has given way once it is a lower "
		              "bound, not a ceiling — this was declared by whoever "
		              "typed `--budget-mpixel-s`",
		              capacita_mpixel_s, riserva, BUDGET_RITARDO_AFFANNO_MS,
		              (double)BUDGET_RITMO_MAX_FOT_S,
		              peggiore(tela_palco_l, tela_palco_a), tela_palco_l,
		              tela_palco_a, BUDGET_TOLLERANZA * 100.0, quante_caselle);
	else
		registro_dice(REG_BUDGET,
		              "⛔ phase 10 — THE COMPOSITION BUDGET: OFF "
		              "(`--budget-mpixel-s 0`, and it is the DEFAULT — "
		              "`CODER.md` I6: what changes what the user sees "
		              "is born off until they have looked at it).  ⛔⛔ With the "
		              "budget off this machine ADMITS EVERYONE: `[M]` §S.2 "
		              "on the saturated scene the eleventh gets in with `negati 0` and "
		              "the first session goes from 39.60 to 0.96 fps (−97.6 %%) "
		              "— it is the violation of I1 the budget exists to "
		              "prevent.  ⭐ It is turned on with `--budget-mpixel-s N`, where "
		              "N is the Mpixel/s of COMPOSITION this machine "
		              "holds, MEASURED at saturation (reserve in force %.2f)",
		              riserva);
}

void budget_deposita(const char *utente, uint32_t larghezza, uint32_t altezza,
                     uint64_t istante_us)
{
	struct inquilino *in;
	bool letta = false;
	uint64_t adesso;

	if (!budget_acceso() || !utente || !utente[0] || !larghezza || !altezza)
		return;
	adesso = ora_us(&letta);
	if (!letta)
		return;
	in = casella(utente, true);
	if (!in)
		return;
	if (in->mai_consegnato) {
		in->mai_consegnato = false;
		in->primo_us = adesso;
		in->secchio_da_us = adesso;
		in->secchio = 0;
	}
	avanza(in, adesso);
	in->pixel[in->secchio] += (uint64_t)larghezza * (uint64_t)altezza;
	in->ultimo_us = adesso;
	in->tela_l = larghezza;
	in->tela_a = altezza;
	/* ⛔ The delay is *capture → parent*, and the instant is stamped by the
	 *    CHILD: it is the uncomfortable direction (an upper bound), which is
	 *    the right one.
	 * ⚠ An instant ahead of our time would mean two different clocks: zero is
	 *   counted instead of subtracting backwards, and no negative number is
	 *   invented. */
	{
		uint64_t d = adesso > istante_us ? adesso - istante_us : 0;
		uint32_t ms = (uint32_t)(d / 1000ull);

		in->ritardo_ms[in->prossimo_ritardo] = ms;
		in->prossimo_ritardo = (in->prossimo_ritardo + 1) % RITARDI;
		if (in->quanti_ritardi < RITARDI)
			in->quanti_ritardi++;
	}
}

void budget_conto_apri(struct budget_conto *c)
{
	memset(c, 0, sizeof *c);
	c->ora_us = ora_us(&c->orologio);
}

void budget_conto_dentro(struct budget_conto *c, const char *utente)
{
	struct inquilino *in;
	double consegna = 0.0, rit = 0.0, pg, d;
	bool ho_consegna, ho_ritardo;
	uint32_t l, a;

	if (!c || !c->orologio || !budget_acceso() || !utente || !utente[0])
		return;
	c->quanti++;
	in = casella(utente, false);

	/* ⚠ The canvas: that of the last frame delivered; if it has never
	 *   delivered, that of the STAGE — which is the upper bound of what it can
	 *   obtain.  ⛔ Uncomfortable direction. */
	l = (in && in->tela_l) ? in->tela_l : tela_palco_l;
	a = (in && in->tela_a) ? in->tela_a : tela_palco_a;
	pg = peggiore(l, a);

	ho_consegna = consegnato(in, c->ora_us, &consegna);
	ho_ritardo = ritardo_mediano(in, &rit);

	/* ── ⛔⛔ THE DELAY GATE — and it stands BEFORE the sum ────────────────
	 *
	 * `[M]` §6.9: at eight sessions the total delivered is 26.6 Mpixel/s against
	 * 480, that is the count on pixels would say *«there is room for five more»*
	 * while everyone sits at 1.5 fps.  ⇒ Whoever delivers little **with a delay
	 * above the threshold** is throttled, not idle, and admitting now violates
	 * I1 on whoever is already working. */
	if (ho_ritardo && rit > BUDGET_RITARDO_AFFANNO_MS &&
	    (!c->strozzato[0] || rit > c->strozzato_ms)) {
		snprintf(c->strozzato, sizeof c->strozzato, "%s", utente);
		c->strozzato_ms = rit;
	}

	/* ── THE DEMAND OF THIS TENANT ────────────────────────────────────── */
	if (!ho_consegna || !ho_ritardo) {
		/* ⛔ DECLARED fallback, and in the uncomfortable direction: without
		 *    the delivered — or without the delay, which is what tells «idle»
		 *    from «throttled» — the worst case is counted. */
		d = pg;
		c->al_peggiore++;
	} else {
		/* ⭐⭐ THE RESERVE: the larger of what it delivers and the fraction
		 *     `F` of its worst case.  It is the defence against the WAKE-UP —
		 *     `[M]` §6.16: eight idle ones at 0.01 % each wake up in 19 ms and
		 *     ask for 130 % of an engine that has 100, and ⛔ the rate
		 *     regulator of phase 9 cannot remedy it (it holds back frames
		 *     already composed and already encoded).  At F = 0.5 the
		 *     overshoot goes from 1 640× to 2×. */
		d = pg * riserva;
		if (consegna > d)
			d = consegna;
	}
	c->domanda += d;
}

enum budget_esito budget_conto_verdetto(struct budget_conto *c,
                                        const char *nuovo, uint32_t tela_l,
                                        uint32_t tela_a, char *perche,
                                        size_t perche_cap)
{
	double d_nuovo, tetto, domanda;

	if (perche && perche_cap)
		perche[0] = '\0';
	if (!budget_acceso())
		return BUDGET_REGGE;
	if (!c || !c->orologio) {
		if (perche && perche_cap)
			snprintf(perche, perche_cap,
			         "the monotonic clock could not be read: the budget "
			         "HAS NOT MEASURED, and does not judge");
		return BUDGET_NON_SO;
	}
	if (c->strozzato[0]) {
		if (perche && perche_cap)
			snprintf(perche, perche_cap,
			         "this machine is already struggling: the session of «%s» "
			         "delivers with %.0f ms of delay (measured threshold %.1f "
			         "ms), and letting someone in now would take frame rate away "
			         "from whoever is working.  ⭐ Try again shortly",
			         c->strozzato, c->strozzato_ms, BUDGET_RITARDO_AFFANNO_MS);
		return BUDGET_NON_REGGE;
	}

	if (!tela_l || !tela_a) {
		tela_l = tela_palco_l;
		tela_a = tela_palco_a;
	}
	d_nuovo = peggiore(tela_l, tela_a);
	domanda = c->domanda + d_nuovo;
	tetto = capacita_mpixel_s * (1.0 + BUDGET_TOLLERANZA);

	if (domanda <= tetto) {
		if (perche && perche_cap)
			snprintf(perche, perche_cap,
			         "demand %.1f ≤ %.1f Mpixel/s (%d inside%s, the newcomer "
			         "asks for %.1f at worst with %ux%u)",
			         domanda, tetto, c->quanti,
			         c->al_peggiore ? ", some of them counted at the worst "
			                          "case" : "",
			         d_nuovo, tela_l, tela_a);
		return BUDGET_REGGE;
	}
	/* ⛔⭐ THE BODY CARRIES THE FIGURES, and it is not decoration: **demand**
	 *     and **capacity** are the two numbers on which the no was decided, and
	 *     without them tomorrow's line cannot be reread — «the server is full»
	 *     says neither how much, nor of what.
	 *
	 * ⛔⛔ AND THE GESTURE PROMISED IS ONLY THE ONE THAT IS TRUE HERE.
	 *
	 *      At this point the session's canvas **is not decided yet** (it is
	 *      decided at `SESSIONE`), and the only canvas number at hand is
	 *      `video.misura_massima` — which is the **DECODER**'s ceiling, not the
	 *      size of the window: `src/pagina.html` spells it out, *«it does not
	 *      change the canvas: it is a ceiling … because a phone's decoder has
	 *      limits its screen does not declare»*, and the page measures it with
	 *      a ladder of `VideoDecoder.isConfigSupported`.
	 *      ⇒ ⛔ **Shrinking the window does NOT lower the cost counted here**:
	 *        whoever did so and tried again would receive the very same no,
	 *        and a sentence promising it would be **false**.
	 *      ⭐ What is true instead: capacity comes back as soon as someone
	 *        leaves, and a device that declares a smaller ceiling really costs
	 *        less.  ⚠ That is what is promised, and only that. */
	if (perche && perche_cap)
		snprintf(perche, perche_cap,
		         "this machine has no composition capacity left: the %d "
		         "sessions already open ask for %.0f of the %.0f Mpixel/s "
		         "declared, and yours would ask for %.0f more (%ux%u at %.1f "
		         "fps).  ⭐ Try again shortly: capacity comes back as soon as "
		         "someone leaves",
		         c->quanti, c->domanda, capacita_mpixel_s, d_nuovo, tela_l,
		         tela_a, (double)BUDGET_RITMO_MAX_FOT_S);
	return BUDGET_NON_REGGE;
}
