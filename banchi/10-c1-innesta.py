#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
10-c1-innesta — ⛔ IL GUARDIANO FINTO, SU TUTT'E DUE GLI ADATTATORI.

E' `10-b97-innesta.py` esteso di quel tanto che serve a misurare **la cura** del
rilievo P4 (`fasi/10-multi-tenant-e-il-budget.md` §8.2) senza cambiare che cosa
il guardiano finto rappresenta.

---------------------------------------------------------------------------
⛔⛔ CHE COSA IL GUARDIANO FINTO RAPPRESENTA — e non cambia fra i due bracci

    **UN GIRO SINCRONO SU D-BUS VERSO LOGIND COSTA `D` MILLISECONDI.**

⇒ Chi dorme `D` non e' «una sessione»: e' **una domanda a logind**.  E' l'unica
  lettura che rende confrontabili i due bracci, perche' la cura non rende le
  domande piu' veloci: ne fa **una sola invece di N**.

⭐ Percio' il sonno va messo dove il giro su D-Bus avviene DAVVERO, e nei due
   alberi sono due posti diversi:

   · albero **SENZA la cura** — `wt_sorveglia_locali()` chiama il gancio per
     ogni inquilino, e ogni chiamata scende in `sentinella_locale()` ⇒ la leva
     sta su `chiedi_sessione_locale()`, e per un ripasso di N inquilini si
     dorme **N volte**.  E' esattamente `10-b97-innesta.py`.
   · albero **CON la cura** — il ripasso chiama `ripassa_sessioni_locali()`
     **una volta** e riceve la risposta per tutti ⇒ la leva sta anche li', e per
     un ripasso si dorme **una volta sola**.

⛔ E `chiedi_sessione_locale()` resta innestato anche nell'albero curato: li'
   passa ancora la domanda dell'`ATTACCA` (`rcp.c`, una volta per sessione), che
   e' un giro su D-Bus vero e va pagato come tale.  ⚠ Non pagarlo darebbe alla
   cura un vantaggio che non ha.

---------------------------------------------------------------------------
⭐ LE RIGHE, compatibili con `10-b97-lettore.py` byte per byte

Il lettore certificato di `10-b97-guardiano.py` cerca

    b97-guardiano giro=… ritardo_ms=… finto=… chiamate=… costo_us=… utente=… esito=…

⇒ Il nome resta `b97-guardiano` e l'ordine dei campi pure: ⛔ **il campo nuovo
  `dove=` sta IN CODA**, dopo `esito=`, cosi' la sua espressione regolare
  continua a combaciare.  Un banco certificato non si rifa' per aggiungere una
  colonna.  ⭐ `dove=attacca` · `dove=ripasso`: e' la colonna che dice **quale**
  strada ha pagato, cioe' quel che il rosso e il verde devono distinguere.

Uso:
    python3 10-c1-innesta.py [--file=<ritardo>] <ALBERO>/src/main.c
    python3 10-c1-innesta.py --verifica <ALBERO>/src/main.c
"""
import hashlib
import os
import sys

# ⛔ Il testo ESATTO che si sostituisce.  Se non combacia — perche' `main.c` e'
#    cambiato — l'innesto FALLISCE invece di indovinare dove mettere le righe.
VECCHIO_ATTACCA = """static bool chiedi_sessione_locale(void *ctx, const char *utente, char *quale,
                                   size_t quanto)
{
	return sentinella_locale((sentinella *)ctx, utente, quale, quanto);
}
"""

VECCHIO_RIPASSO = """static size_t ripassa_sessioni_locali(void *ctx, const char *const *utenti,
                                      size_t quanti, bool *locale, char *quali,
                                      size_t larghezza)
{
	return sentinella_locali((sentinella *)ctx, utenti, quanti, locale, quali,
	                         larghezza);
}
"""

COMUNE = r"""/* ═════════════════════════════════════════════════════════════════════════
 * ⛔⛔ BANCO 10-c1 — IL GUARDIANO FINTO.  QUESTE RIGHE NON STANNO NEL
 *      REPOSITORY: vivono solo nella copia sulla macchina di prova, e l'md5 di
 *      `main.c` prima e dopo l'innesto lo dice.
 *
 * ⭐ Chi dorme `D` non e' «una sessione»: e' **una domanda a logind**.  Il file
 *    del ritardo si rilegge al massimo ogni mezzo secondo, cosi' D si cambia
 *    senza rifare le sessioni grafiche.
 * ═════════════════════════════════════════════════════════════════════════ */
#define C1_RILETTURA_MS 500

/* ⛔ Lo stato e' UNO SOLO per tutt'e due gli adattatori: due copie del ritardo
 *    vorrebbero dire due bracci con due valori di D senza che si veda. */
static char c1_percorso[512];
static char c1_giro[64] = "senza-giro";
static long c1_ritardo_ms = -1;         /* < 0 ⇒ guardiano VERO */
static uint64_t c1_riletto_ms;
static unsigned long long c1_chiamate;
static int c1_avviato;

static void c1_ripassa_il_file(void)
{
	uint64_t ora;
	FILE *f;

	if (!c1_avviato) {
		const char *v = getenv("REMOTIX_C1_FILE");
		c1_avviato = 1;
		snprintf(c1_percorso, sizeof c1_percorso, "%s",
		         (v && *v) ? v : "@@C1_FILE@@");
		/* ⛔ LA RIGA CHE DICE CHE LA LEVA HA PRESO.  Senza, un banco che
		 *    contasse zero scatti direbbe «tutto bene» su una misura che non
		 *    e' mai stata fatta. */
		registro_dice(REG_SESSIONE, "b97-guardiano INNESTATO file=%s",
		              c1_percorso[0] ? c1_percorso : "NESSUNO");
	}
	ora = registro_ora_ms();
	if (!c1_percorso[0] || ora - c1_riletto_ms < C1_RILETTURA_MS)
		return;
	c1_riletto_ms = ora;
	f = fopen(c1_percorso, "r");
	if (!f)
		return;
	{
		char g[64];
		long d;
		if (fscanf(f, "%63s %ld", g, &d) == 2
		    && (d != c1_ritardo_ms || strcmp(g, c1_giro) != 0)) {
			snprintf(c1_giro, sizeof c1_giro, "%s", g);
			c1_ritardo_ms = d;
			registro_dice(REG_SESSIONE,
			              "b97-guardiano CAMBIO giro=%s ritardo_ms=%ld",
			              c1_giro, c1_ritardo_ms);
		}
	}
	fclose(f);
}

/* Dorme il ritardo, o `false` se il guardiano e' VERO (ritardo negativo). */
static bool c1_dormi(void)
{
	struct timespec d;

	d.tv_sec = (time_t)(c1_ritardo_ms / 1000);
	d.tv_nsec = (long)(c1_ritardo_ms % 1000) * 1000000L;
	while (nanosleep(&d, &d) == -1 && errno == EINTR)
		;
	/* ⚠ Si risponde `false` come il guardiano VERO su una sessione nostra: le
	 *   nostre non hanno seat (`sentinella.h`), quindi «non c'e' nessuna
	 *   locale» e' la stessa risposta.  ⛔ Il banco misura il COSTO della
	 *   domanda, non un verdetto diverso. */
	return false;
}

static void c1_dillo(const char *dove, long costo_us, const char *utente,
                     int esito)
{
	c1_chiamate++;
	registro_dice(REG_SESSIONE,
	              "b97-guardiano giro=%s ritardo_ms=%ld finto=%s chiamate=%llu "
	              "costo_us=%ld utente=%s esito=%d dove=%s",
	              c1_giro, c1_ritardo_ms, c1_ritardo_ms >= 0 ? "si" : "no",
	              c1_chiamate, costo_us, utente ? utente : "?", esito, dove);
}

static bool chiedi_sessione_locale(void *ctx, const char *utente, char *quale,
                                   size_t quanto)
{
	struct timespec t0, t1;
	bool esito;

	c1_ripassa_il_file();
	clock_gettime(CLOCK_MONOTONIC, &t0);
	if (c1_ritardo_ms >= 0)
		esito = c1_dormi();
	else
		esito = sentinella_locale((sentinella *)ctx, utente, quale, quanto);
	clock_gettime(CLOCK_MONOTONIC, &t1);
	c1_dillo("attacca",
	         (long)((t1.tv_sec - t0.tv_sec) * 1000000L
	                + (t1.tv_nsec - t0.tv_nsec) / 1000),
	         utente, (int)esito);
	return esito;
}
"""

NUOVO_RIPASSO = r"""/* ⛔ L'ALTRA META' DELLA LEVA — il RIPASSO, che dopo la cura fa una domanda
 *    sola per tutti gli inquilini.  ⭐ Dorme UNA volta e lo dice: e' proprio la
 *    differenza che il rosso e il verde devono far vedere. */
static size_t ripassa_sessioni_locali(void *ctx, const char *const *utenti,
                                      size_t quanti, bool *locale, char *quali,
                                      size_t larghezza)
{
	struct timespec t0, t1;
	size_t trovate = 0;

	c1_ripassa_il_file();
	clock_gettime(CLOCK_MONOTONIC, &t0);
	if (c1_ritardo_ms >= 0) {
		for (size_t k = 0; k < quanti; k++) {
			locale[k] = false;
			if (quali && larghezza)
				quali[k * larghezza] = '\0';
		}
		c1_dormi();
	} else {
		trovate = sentinella_locali((sentinella *)ctx, utenti, quanti, locale,
		                            quali, larghezza);
	}
	clock_gettime(CLOCK_MONOTONIC, &t1);
	c1_dillo("ripasso",
	         (long)((t1.tv_sec - t0.tv_sec) * 1000000L
	                + (t1.tv_nsec - t0.tv_nsec) / 1000),
	         quanti ? utenti[0] : "?", (int)trovate);
	return trovate;
}
"""

MARCA = "b97-guardiano INNESTATO"


def md5(p):
    with open(p, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def principale(argv):
    verifica = "--verifica" in argv
    dove = "/media/REMOTIX/tmp/10c1/c1-ritardo"
    for a in argv:
        if a.startswith("--file="):
            dove = a.split("=", 1)[1]
    resto = [a for a in argv if not a.startswith("--")]
    if not resto:
        print("⛔ manca il percorso di main.c")
        return 2
    p = resto[0]
    if not os.path.exists(p):
        print("⛔ «%s» non c'e'" % p)
        return 2
    with open(p, encoding="utf-8") as f:
        testo = f.read()

    if verifica:
        n = testo.count(MARCA)
        print("md5 %s = %s" % (p, md5(p)))
        print("adattatore del RIPASSO innestato: %s"
              % ("si" if "dove=ripasso" in testo or 'c1_dillo("ripasso"' in testo
                 else "NO (albero senza la cura)"))
        if n == 1:
            print("⭐ l'innesto C'E' (una volta sola)")
            return 0
        print("⛔ l'innesto NON c'e' (occorrenze della marca: %d)" % n)
        return 1

    if MARCA in testo:
        print("⚠ gia' innestato: non lo rifaccio")
        print("md5 %s = %s" % (p, md5(p)))
        return 0
    if testo.count(VECCHIO_ATTACCA) != 1:
        print("⛔ NON INNESTO: l'adattatore dell'ATTACCA compare %d volte in "
              "«%s» (ne serve esattamente una).  ⚠ `main.c` e' cambiato: "
              "l'innesto va rifatto a mano, non indovinato."
              % (testo.count(VECCHIO_ATTACCA), p))
        return 2
    prima = md5(p)
    comune = COMUNE.replace("@@C1_FILE@@", dove)
    if "@@" in comune:
        print("⛔ NON INNESTO: il segnaposto del file non e' stato sostituito")
        return 2
    testo = testo.replace(VECCHIO_ATTACCA, comune)

    # ⛔ Il ripasso c'e' solo nell'albero CON la cura, e la sua assenza NON e' un
    #    guasto: e' il braccio del rosso.  ⇒ Si dichiara, non si indovina.
    quanti_ripasso = testo.count(VECCHIO_RIPASSO)
    if quanti_ripasso == 1:
        testo = testo.replace(VECCHIO_RIPASSO, NUOVO_RIPASSO)
        print("⭐ innestato ANCHE il ripasso: questo albero HA la cura di P4")
    elif quanti_ripasso == 0:
        print("⚠ l'adattatore del ripasso non c'e': questo albero e' SENZA la "
              "cura di P4 (braccio del rosso), e si dorme una volta per "
              "inquilino")
    else:
        print("⛔ NON INNESTO: l'adattatore del ripasso compare %d volte"
              % quanti_ripasso)
        return 2

    with open(p, "w", encoding="utf-8") as f:
        f.write(testo)
    print("md5 PRIMA  = %s" % prima)
    print("md5 DOPO   = %s" % md5(p))
    print("file del ritardo compilato dentro = %s" % dove)
    print("⭐ innestato in «%s»" % p)
    return 0


if __name__ == "__main__":
    sys.exit(principale(sys.argv[1:]))
