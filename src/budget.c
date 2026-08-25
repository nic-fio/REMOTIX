/* budget.c — ⭐⭐⭐ IL BUDGET DI COMPOSIZIONE (fase 10, 25 agosto 2026).
 *
 * ⛔ La ragione di ogni numero sta in `budget.h`, in testa: qui c'e' solo il
 *    meccanismo.  Chi cambia un numero legge prima quel riquadro, o cambiera'
 *    una taratura credendo di correggere un'implementazione.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#include "budget.h"
#include "registro.h"

/* ─────────────────────────────────────────────────────────────────────────────
 * ⭐ LA FINESTRA DEL CONSEGNATO — otto secchi da 250 ms, cioe' due secondi.
 *
 * ⛔ E i secchi servono a una cosa sola che una media incrementale non sa fare:
 *    **far DECADERE il consegnato quando i fotogrammi smettono di arrivare**.
 *    Una sessione che si ferma deve scendere verso zero da se', o resterebbe
 *    contata al ritmo che aveva quando lavorava — e allora il conto direbbe
 *    «pieno» su una macchina vuota (falso NO su tutti quelli che arrivano).
 *
 * ⚠ Due secondi e non venti: `[M]` §6.16 — al risveglio di otto sessioni ferme
 *   il **ritmo** crolla dentro il primo intervallo del metro (**meno di 2 s**),
 *   mentre il ritardo sale in 8-10 s.  Una finestra piu' lunga vedrebbe il
 *   risveglio troppo tardi; una piu' corta conterebbe il singhiozzo di un
 *   fotogramma perso come un crollo.
 * ─────────────────────────────────────────────────────────────────────────── */
#define SECCHI 8
#define SECCHIO_US 250000ull
#define FINESTRA_US ((uint64_t)SECCHI * SECCHIO_US)

/* ⛔⭐ QUANTI RITARDI SI TENGONO, E PERCHE' LA MEDIANA E NON IL MASSIMO.
 *
 *     Il massimo rifiuterebbe un utente per **un singolo singhiozzo** — un
 *     falso NO su un dato che non descrive lo stato della macchina.  La mediana
 *     di 32 campioni descrive *dove sta* la sessione, ed e' la stessa grandezza
 *     che `[M]` §6.5/§6.9 hanno misurato («ritardo mediano» a ogni gradino):
 *     tarare su una grandezza e giudicare su un'altra e' il modo piu' rapido di
 *     avere un metro non tarato.
 * ⚠ A ~40 fot/s, 32 campioni sono **0,8 s** — la stessa scala della finestra. */
#define RITARDI 32

/* ⛔⭐ I CAMPIONI DEL RITARDO **NON SCADONO**, ed e' una scelta, non una
 *     dimenticanza.
 *
 *     Una sessione **ferma** consegna `[M]` un fotogramma ogni ~40 s (0,05
 *     Mpixel/s, §6.9): se i suoi campioni scadessero, resterebbe **senza
 *     ritardo**, e il ripiego dichiarato (§1.33, verso scomodo) la conterebbe
 *     al caso peggiore.  ⇒ ⛔ **Dieci inquilini fermi verrebbero respinti pur
 *     non costando niente** — che e' l'errore gemello, e altrettanto grave, di
 *     ammettere l'ottavo che fa crollare tutto.
 * ⭐ E nel verso opposto la scelta e' prudente: una sessione **strozzata** che
 *    tace si porta dietro il suo ritardo grosso finche' non consegna di nuovo.
 */

struct inquilino {
	bool usato;
	char utente[257];
	/* i pixel composti consegnati, per secchio */
	uint64_t pixel[SECCHI];
	int secchio;              /* indice del secchio corrente */
	uint64_t secchio_da_us;   /* l'istante in cui il secchio corrente e' nato */
	uint64_t primo_us;        /* il primo fotogramma mai visto */
	uint64_t ultimo_us;       /* l'ultimo, per il riuso della casella */
	bool mai_consegnato;
	uint32_t tela_l, tela_a;  /* l'ultima tela consegnata */
	uint32_t ritardo_ms[RITARDI];
	int quanti_ritardi, prossimo_ritardo;
};

static struct inquilino *tabella;
static int quante_caselle;

/* ⛔ `0` = SPENTO, ed e' il predefinito: I6.  Vedi `budget.h` punto 5. */
static double capacita_mpixel_s;
static double riserva = BUDGET_RISERVA_PREDEFINITA;
static uint32_t tela_palco_l, tela_palco_a;

/* ------------------------------------------------------------------------- */

static uint64_t ora_us(bool *letta)
{
	struct timespec t;

	if (clock_gettime(CLOCK_MONOTONIC, &t) != 0) {
		/* ⛔ «Non ho potuto leggere l'ora» non e' «sono le zero»: chi riceve
		 *    questo lo dichiara e non giudica. */
		if (letta)
			*letta = false;
		return 0;
	}
	if (letta)
		*letta = true;
	return (uint64_t)t.tv_sec * 1000000ull + (uint64_t)(t.tv_nsec / 1000);
}

/* ⛔ La tabella si dimensiona sul tetto in vigore, e si alloca alla prima
 *    accensione.  ⚠ Se `calloc` fallisce, il budget **non si accende**: un
 *    budget che non puo' contare non deve poter dire di no. */
static bool tabella_pronta(int quante)
{
	if (tabella)
		return true;
	if (quante < 1)
		quante = 1;
	tabella = (struct inquilino *)calloc((size_t)quante, sizeof *tabella);
	if (!tabella) {
		registro_dice(REG_BUDGET,
		              "⛔ non c'e' memoria per la tabella del budget (%d "
		              "caselle): il budget resta SPENTO.  ⚠ Non e' «regge»: e' "
		              "«non conto», e chi non conta non dice di no",
		              quante);
		return false;
	}
	quante_caselle = quante;
	return true;
}

/* ⭐ La casella dell'utente, o la piu' vecchia se non c'e' e non c'e' posto.
 *
 * ⛔ Il riuso a piu' vecchia guarda `ultimo_us`, e serve perche' NESSUNO
 *    avvisa questo modulo che un palco e' morto: un inquilino sparito smette
 *    semplicemente di consegnare, e la sua casella diventa la piu' vecchia.
 * ⚠ E non e' un difetto travestito: una casella stantia non entra mai nel
 *   conto, perche' il conto lo riempie la tabella dei **palchi vivi** e non
 *   questa (vedi `budget_conto_dentro()`). */
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

/* ⛔ Porta la finestra fino a `adesso`, svuotando i secchi che sono usciti.
 *    ⚠ E' quel che fa DECADERE il consegnato di chi si e' fermato: senza
 *      questa chiamata anche al momento del verdetto (non solo al deposito),
 *      una sessione ferma resterebbe contata al ritmo che aveva. */
static void avanza(struct inquilino *in, uint64_t adesso)
{
	if (in->mai_consegnato)
		return;
	if (adesso < in->secchio_da_us)
		return;  /* ⚠ l'orologio e' monotono: non dovrebbe succedere */
	while (adesso - in->secchio_da_us >= SECCHIO_US) {
		in->secchio_da_us += SECCHIO_US;
		in->secchio = (in->secchio + 1) % SECCHI;
		in->pixel[in->secchio] = 0;
		/* ⭐ Se il buco e' piu' lungo della finestra intera non si gira mille
		 *    volte: si azzera tutto e si riparte da adesso. */
		if (adesso - in->secchio_da_us >= FINESTRA_US) {
			memset(in->pixel, 0, sizeof in->pixel);
			in->secchio_da_us = adesso;
			in->secchio = 0;
			return;
		}
	}
}

/* ⭐ Il consegnato, in Mpixel/s.  ⛔ Torna `false` quando **non si e'
 *    misurato**, e chi lo riceve conta il caso peggiore: «non ho misurato» non
 *    e' «zero» — una sessione appena nata non ha ancora consegnato niente, e
 *    contarla zero e' esattamente l'errore che affama tutti. */
static bool consegnato(struct inquilino *in, uint64_t adesso, double *mpixel_s)
{
	uint64_t somma = 0;
	double secondi;

	if (!in || in->mai_consegnato)
		return false;
	/* ⛔ Finche' non c'e' una finestra INTERA di storia il numero non descrive
	 *    un ritmo: descrive «da quanto poco e' nata».  ⇒ Non si e' misurato. */
	if (adesso < in->primo_us + FINESTRA_US)
		return false;
	avanza(in, adesso);
	for (int i = 0; i < SECCHI; i++)
		somma += in->pixel[i];
	/* ⚠ Si divide per il tempo COPERTO — i secchi pieni piu' la frazione di
	 *   quello corrente — e non per la finestra nominale: il secchio corrente
	 *   e' mediamente mezzo pieno, e dividerlo per il suo secchio intero
	 *   sottostimerebbe la domanda del ~6 %.  ⛔ Sottostimare la domanda e' il
	 *   verso che affama tutti (§1.33). */
	secondi = (double)(SECCHI - 1) * (double)SECCHIO_US / 1e6;
	secondi += (double)(adesso - in->secchio_da_us) / 1e6;
	if (secondi <= 0.0)
		return false;
	*mpixel_s = (double)somma / 1e6 / secondi;
	return true;
}

/* ⭐ La mediana dei ritardi tenuti.  `false` = mai consegnato niente, quindi
 *    non c'e' niente da mediare — e non e' «ritardo zero». */
static bool ritardo_mediano(const struct inquilino *in, double *ms)
{
	uint32_t v[RITARDI];
	int n;

	if (!in || in->quanti_ritardi <= 0)
		return false;
	n = in->quanti_ritardi;
	memcpy(v, in->ritardo_ms, (size_t)n * sizeof v[0]);
	/* ⚠ Ordinamento a bolle su al massimo 32 elementi, una volta per verdetto:
	 *   `qsort` qui costerebbe piu' righe di quante ne risparmi. */
	for (int i = 1; i < n; i++)
		for (int j = i; j > 0 && v[j] < v[j - 1]; j--) {
			uint32_t t = v[j];
			v[j] = v[j - 1];
			v[j - 1] = t;
		}
	*ms = (double)v[n / 2];
	return true;
}

/* ⭐ Il caso peggiore di una tela: la sua tela per il ritmo massimo che questo
 *    ferro ha mostrato di saper consegnare (§6.9, e vedi `budget.h`). */
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

/* ⛔ La tabella si dimensiona **prima** di accendere: la chiama `main.c` col
 *    tetto in vigore, cosi' le caselle sono tante quanti i palchi possibili e
 *    il riuso a piu' vecchia non morde mai in esercizio normale. */
void budget_caselle(int quante)
{
	if (!tabella)
		quante_caselle = quante;
}

bool budget_acceso(void)
{
	return capacita_mpixel_s > 0.0 && tabella != NULL;
}

/* ⛔ I due conti dei no, e vivono qui perche' e' qui che si scrivono.  ⚠ Non
 *    si azzerano mai: sono «da che questo server e' acceso», che e' l'unica
 *    finestra che chi legge il registro sa ricostruire. */
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
	/* ⛔ UNA riga per verdetto, e non una per fotogramma: qui si passa a ogni
	 *    login, non a ogni pixel.  ⭐ E si scrive anche col budget SPENTO,
	 *    perche' `negati 0` e' il fatto che prova I6 — leggerlo richiede che
	 *    qualcuno lo scriva. */
	registro_dice(REG_BUDGET,
	              "verdetto per «%s»: %s · negati %llu (di cui budget %llu) su "
	              "%llu domande · in vigore --budget-mpixel-s %.1f (%s) "
	              "--tetto-sessioni %d --riserva %.2f%s%s",
	              utente ? utente : "?",
	              ammesso ? "⭐ AMMESSO" : "⛔ NEGATO",
	              (unsigned long long)negati_tutti,
	              (unsigned long long)negati_budget,
	              (unsigned long long)domande_viste,
	              capacita_mpixel_s, budget_acceso() ? "ACCESO" : "SPENTO",
	              tetto_sessioni, riserva,
	              (!ammesso && perche && perche[0]) ? " · motivo: " : "",
	              (!ammesso && perche && perche[0]) ? perche : "");
}

void budget_riga_avvio(int tetto_sessioni)
{
	/* ⛔⭐ LA RIGA CHE UN BANCO CERCA, e porta i TRE valori col **nome
	 *     dell'opzione accanto al numero**.  ⚠ Si scrive per prima e sempre —
	 *     acceso E spento — perche' e' quella su cui si tara chi giudica: un
	 *     oracolo tarato su un numero diverso da quello in vigore produrrebbe
	 *     falsi si' e falsi no **suoi**, non del prodotto. */
	registro_dice(REG_BUDGET,
	              "%s fase 10 — I TRE VALORI IN VIGORE: "
	              "budget --budget-mpixel-s %.1f (%s) · "
	              "tetto --tetto-sessioni %d · "
	              "riserva --riserva %.2f",
	              budget_acceso() ? "⭐⭐" : "⛔",
	              capacita_mpixel_s, budget_acceso() ? "ACCESO" : "SPENTO",
	              tetto_sessioni, riserva);
	if (budget_acceso())
		registro_dice(REG_BUDGET,
		              "⭐⭐ fase 10 — IL BUDGET DI COMPOSIZIONE: ACCESO a %.1f "
		              "Mpixel/s, riserva %.2f, soglia del ritardo %.1f ms, "
		              "caso peggiore %.2f fot/s (⇒ %.1f Mpixel/s per una "
		              "%ux%u), tolleranza %.0f%%, %d caselle.  ⛔ La grandezza "
		              "e' la COMPOSIZIONE, non la codifica: `[M]` §6.11 il "
		              "soffitto e' 0,97 Gpixel/s contro 1,86 del codificatore, "
		              "e a saturare `rcs0` e' il compositore.  ⛔ Chi non ci sta "
		              "riceve CONGEDO 0x06 BUDGET_PIENO **prima** che nasca il "
		              "suo palco.  ⚠ Il numero NON si auto-tara (§6.9): prima "
		              "che la macchina abbia ceduto una volta e' un limite "
		              "inferiore, non un soffitto — questo l'ha dichiarato chi "
		              "ha battuto `--budget-mpixel-s`",
		              capacita_mpixel_s, riserva, BUDGET_RITARDO_AFFANNO_MS,
		              (double)BUDGET_RITMO_MAX_FOT_S,
		              peggiore(tela_palco_l, tela_palco_a), tela_palco_l,
		              tela_palco_a, BUDGET_TOLLERANZA * 100.0, quante_caselle);
	else
		registro_dice(REG_BUDGET,
		              "⛔ fase 10 — IL BUDGET DI COMPOSIZIONE: SPENTO "
		              "(`--budget-mpixel-s 0`, ed e' il PREDEFINITO — "
		              "`CODER.md` I6: quel che cambia cio' che l'utente vede "
		              "nasce spento finche' non l'ha guardato).  ⛔⛔ Con il "
		              "budget spento questa macchina AMMETTE TUTTI: `[M]` §S.2 "
		              "sulla scena satura l'undicesimo entra con `negati 0` e "
		              "la prima sessione passa da 39,60 a 0,96 fot/s (−97,6 %%) "
		              "— e' la violazione di I1 che il budget esiste per "
		              "impedire.  ⭐ Si accende con `--budget-mpixel-s N`, dove "
		              "N sono i Mpixel/s di COMPOSIZIONE che questa macchina "
		              "regge, MISURATI a saturazione (riserva in vigore %.2f)",
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
	/* ⛔ Il ritardo e' *cattura → padre*, e l'istante lo timbra il FIGLIO: e'
	 *    il verso scomodo (un maggiorante), che e' quello giusto.
	 * ⚠ Un istante piu' avanti dell'ora nostra vorrebbe dire due orologi
	 *   diversi: si conta zero invece di sottrarre alla rovescia, e non si
	 *   inventa un numero negativo. */
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

	/* ⚠ La tela: quella dell'ultimo fotogramma consegnato; se non ha mai
	 *   consegnato, quella del PALCO — che e' il maggiorante di quel che potra'
	 *   ottenere.  ⛔ Verso scomodo. */
	l = (in && in->tela_l) ? in->tela_l : tela_palco_l;
	a = (in && in->tela_a) ? in->tela_a : tela_palco_a;
	pg = peggiore(l, a);

	ho_consegna = consegnato(in, c->ora_us, &consegna);
	ho_ritardo = ritardo_mediano(in, &rit);

	/* ── ⛔⛔ LA PORTA DEL RITARDO — e sta PRIMA della somma ──────────────
	 *
	 * `[M]` §6.9: a otto sessioni il consegnato totale e' 26,6 Mpixel/s contro
	 * 480, cioe' il conto sui pixel direbbe *«c'e' posto per altre cinque»*
	 * mentre tutti stanno a 1,5 fot/s.  ⇒ Chi consegna poco **con un ritardo
	 * sopra la soglia** e' strozzato, non fermo, e ammettere adesso viola I1 su
	 * chi sta gia' lavorando. */
	if (ho_ritardo && rit > BUDGET_RITARDO_AFFANNO_MS &&
	    (!c->strozzato[0] || rit > c->strozzato_ms)) {
		snprintf(c->strozzato, sizeof c->strozzato, "%s", utente);
		c->strozzato_ms = rit;
	}

	/* ── LA DOMANDA DI QUESTO INQUILINO ────────────────────────────────── */
	if (!ho_consegna || !ho_ritardo) {
		/* ⛔ Ripiego DICHIARATO, e nel verso scomodo: senza il consegnato — o
		 *    senza il ritardo, che e' quel che distingue «ferma» da
		 *    «strozzata» — si conta il caso peggiore. */
		d = pg;
		c->al_peggiore++;
	} else {
		/* ⭐⭐ LA RISERVA: il piu' grande fra quel che consegna e la frazione
		 *     `F` del suo caso peggiore.  E' la difesa contro il RISVEGLIO —
		 *     `[M]` §6.16: otto ferme da 0,01 % l'una si accendono in 19 ms e
		 *     chiedono il 130 % di un motore che ne ha 100, e ⛔ il regolatore
		 *     della fase 9 non lo puo' rimediare (ferma fotogrammi gia'
		 *     composti e gia' codificati).  A F = 0,5 lo sforamento passa da
		 *     1 640× a 2×. */
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
			         "l'orologio monotono non si e' fatto leggere: il budget "
			         "NON HA MISURATO, e non giudica");
		return BUDGET_NON_SO;
	}
	if (c->strozzato[0]) {
		if (perche && perche_cap)
			snprintf(perche, perche_cap,
			         "questa macchina e' gia' in affanno: la sessione di «%s» "
			         "consegna con %.0f ms di ritardo (soglia misurata %.1f "
			         "ms), e far entrare qualcuno adesso toglierebbe ritmo a "
			         "chi sta lavorando.  ⭐ Riprova fra poco",
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
			         "domanda %.1f ≤ %.1f Mpixel/s (%d dentro%s, il nuovo ne "
			         "chiede %.1f al peggio con %ux%u)",
			         domanda, tetto, c->quanti,
			         c->al_peggiore ? ", di cui alcuni contati al caso "
			                          "peggiore" : "",
			         d_nuovo, tela_l, tela_a);
		return BUDGET_REGGE;
	}
	/* ⛔⭐ IL CORPO PORTA LE CIFRE, e non e' decorazione: **domanda** e
	 *     **capacita'** sono i due numeri su cui il no e' stato deciso, e senza
	 *     di loro la riga di domani non si sa rileggere — «il server e' pieno»
	 *     non dice ne' quanto, ne' di che cosa.
	 *
	 * ⛔⛔ E IL GESTO CHE SI PROMETTE E' SOLO QUELLO CHE E' VERO QUI.
	 *
	 *      A questo punto la tela della sessione **non e' ancora decisa** (si
	 *      decide a `SESSIONE`), e il solo numero di tela che si ha in mano e'
	 *      `video.misura_massima` — che e' il tetto del **DECODIFICATORE**, non
	 *      la misura della finestra: `src/pagina.html` lo scrive a lettere,
	 *      *«non cambia la tela: e' un tetto … perche' il decodificatore di un
	 *      telefono ha limiti che il suo schermo non dichiara»*, e la pagina lo
	 *      misura con una scala di `VideoDecoder.isConfigSupported`.
	 *      ⇒ ⛔ **Rimpicciolire la finestra NON abbassa il costo contato qui**:
	 *        chi lo facesse e riprovasse riceverebbe lo stesso identico no, e
	 *        una frase che glielo promettesse sarebbe **falsa**.
	 *      ⭐ Quel che invece e' vero: la capacita' torna appena qualcuno esce,
	 *        e un dispositivo che dichiara un tetto piu' piccolo costa meno
	 *        davvero.  ⚠ Si promette quello, e basta quello. */
	if (perche && perche_cap)
		snprintf(perche, perche_cap,
		         "questa macchina non ha piu' capacita' di composizione: le %d "
		         "sessioni gia' aperte ne chiedono %.0f dei %.0f Mpixel/s "
		         "dichiarati, e la tua ne chiederebbe altri %.0f (%ux%u a %.1f "
		         "fot/s).  ⭐ Riprova fra poco: la capacita' torna appena "
		         "qualcuno esce",
		         c->quanti, c->domanda, capacita_mpixel_s, d_nuovo, tela_l,
		         tela_a, (double)BUDGET_RITMO_MAX_FOT_S);
	return BUDGET_NON_REGGE;
}
