#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
10-b97-innesta — ⛔ IL GUASTO SI INNESTA IN UN FILE SOLO, E SI DICHIARA.

Sostituisce **l'adattatore** `chiedi_sessione_locale()` di `src/main.c` con una
versione che sa fare il **guardiano finto**: dorme D millisecondi invece di
chiamare logind, e scrive una riga per ogni chiamata.

⭐ LA LEVA E' QUELLA CHE IL PRODOTTO DICHIARA DA SE'.  `src/main.c:1028`:

    «Sono due mestieri, e tenerli separati e' quel che permette al banco di
     innestare un guardiano finto senza toccare il trasporto.»

⇒ `webtransport.c` non cambia di una virgola: `wt_sorveglia_locali()` continua a
  ciclare su tutte le sessioni e a chiamare il gancio come sempre.  ⛔ Quel che
  cambia e' **quanto costa una chiamata**, che e' esattamente la variabile che
  R10-A3 nomina e che sulla macchina vera non si puo' muovere.

---------------------------------------------------------------------------
⛔⛔ IL RITARDO SI LEGGE DA UN FILE, NON DA UNA VARIABILE D'AMBIENTE

Sette sessioni grafiche vere costano **minuti** ad aprirsi.  Con il ritardo in
`environ` ogni valore di D vorrebbe dire riaccendere il server, cioe' rifare
sette palchi — e allora la superficie (D, N) non si misurerebbe mai per intero.
⇒ Il file si rilegge al massimo ogni 500 ms, e **si cambia D senza toccare le
  sessioni**.

Il file: una riga sola, `<giro> <ritardo_ms>`.
  · `ritardo_ms >= 0` — guardiano FINTO: dorme, e non chiama logind;
  · `ritardo_ms < 0`  — guardiano VERO: chiama `sentinella_locale()` e ne
                        **misura il costo**, che e' l'altra meta' del banco.
  · `giro` — l'ancora: un nonce nuovo a ogni braccio.  ⛔ Una riga di registro
    che porta il giro di ieri non puo' essere contata come misura di oggi.

---------------------------------------------------------------------------
⛔ E LE DUE RIGHE CHE IL BANCO PRETENDE, con i nomi stabili

  `b97-guardiano INNESTATO file=…`  — una volta sola, alla prima chiamata.
      ⛔ Se manca, la leva NON ha preso: il banco deve dire «non ho misurato»,
         non «nessuno scatto, tutto bene».
  `b97-guardiano giro=… ritardo_ms=… finto=… chiamate=… costo_us=… utente=…`
      — una per chiamata.  ⭐ `chiamate=` e' quanta sollecitazione e' ARRIVATA
        (`LEZIONI.md` §1.30), `costo_us=` e' il metro.

Uso (sulla macchina di prova, dopo lo scaricamento del tar):
    python3 10-b97-innesta.py <ALBERO>/src/main.c
    python3 10-b97-innesta.py --verifica <ALBERO>/src/main.c
"""
import hashlib
import os
import sys

# ⛔ Il testo ESATTO che si sostituisce.  Se non combacia — perche' `main.c` e'
#    cambiato — l'innesto FALLISCE invece di indovinare dove mettere le righe.
VECCHIO = """static bool chiedi_sessione_locale(void *ctx, const char *utente, char *quale,
                                   size_t quanto)
{
	return sentinella_locale((sentinella *)ctx, utente, quale, quanto);
}
"""

NUOVO = r"""/* ═════════════════════════════════════════════════════════════════════════
 * ⛔⛔ BANCO 10-b97 — IL GUARDIANO FINTO.  QUESTE RIGHE NON STANNO NEL
 *      REPOSITORY: vivono solo nella copia sulla macchina di prova, e l'md5 di
 *      `main.c` prima e dopo l'innesto lo dice.
 *
 * ⭐ Si sostituisce l'ADATTATORE, che e' la leva dichiarata qui sopra: il
 *    trasporto non si tocca, `wt_sorveglia_locali()` e' quello del prodotto.
 * ═════════════════════════════════════════════════════════════════════════ */
#define B97_RILETTURA_MS 500

static bool chiedi_sessione_locale(void *ctx, const char *utente, char *quale,
                                   size_t quanto)
{
	static int avviato = 0;
	static char percorso[512];
	static char giro[64] = "senza-giro";
	static long ritardo_ms = -1;         /* < 0 ⇒ guardiano VERO */
	static uint64_t riletto_ms = 0;
	static unsigned long long chiamate = 0;
	struct timespec t0, t1;
	uint64_t ora;
	long costo_us;
	bool esito;

	if (!avviato) {
		/* ⚠ L'ambiente PRIMA, il percorso compilato POI.  Il predefinito e'
		 *   compilato dentro perche' `07-b64-terreno.sh` accende il server con
		 *   `systemd-run` e non passa variabili d'ambiente arbitrarie — e
		 *   riscrivere il lanciatore CONDIVISO per un banco solo sarebbe un
		 *   guasto per tutti gli altri agenti. */
		const char *v = getenv("REMOTIX_B97_FILE");
		avviato = 1;
		snprintf(percorso, sizeof percorso, "%s",
		         (v && *v) ? v : "@@B97_FILE@@");
		/* ⛔ LA RIGA CHE DICE CHE LA LEVA HA PRESO.  Senza, un banco che
		 *    contasse zero scatti direbbe «tutto bene» su una misura che non
		 *    e' mai stata fatta. */
		registro_dice(REG_SESSIONE,
		              "b97-guardiano INNESTATO file=%s",
		              percorso[0] ? percorso : "NESSUNO");
	}

	/* La rilettura, al massimo ogni mezzo secondo: cambiare D non deve costare
	 * un riavvio, o i palchi si rifanno a ogni braccio. */
	ora = registro_ora_ms();
	if (percorso[0] && ora - riletto_ms >= B97_RILETTURA_MS) {
		FILE *f = fopen(percorso, "r");
		riletto_ms = ora;
		if (f) {
			char g[64];
			long d;
			if (fscanf(f, "%63s %ld", g, &d) == 2
			    && (d != ritardo_ms || strcmp(g, giro) != 0)) {
				snprintf(giro, sizeof giro, "%s", g);
				ritardo_ms = d;
				registro_dice(REG_SESSIONE,
				              "b97-guardiano CAMBIO giro=%s ritardo_ms=%ld",
				              giro, ritardo_ms);
			}
			fclose(f);
		}
	}

	clock_gettime(CLOCK_MONOTONIC, &t0);
	if (ritardo_ms >= 0) {
		/* ⚠ E si risponde `false` come il guardiano VERO su una sessione
		 *   nostra: le nostre non hanno seat (`sentinella.h`), quindi «non c'e'
		 *   nessuna locale» e' la stessa risposta.  ⛔ Il banco misura il COSTO
		 *   della domanda, non un verdetto diverso. */
		struct timespec d;
		d.tv_sec = (time_t)(ritardo_ms / 1000);
		d.tv_nsec = (long)(ritardo_ms % 1000) * 1000000L;
		while (nanosleep(&d, &d) == -1 && errno == EINTR)
			;
		esito = false;
	} else {
		esito = sentinella_locale((sentinella *)ctx, utente, quale, quanto);
	}
	clock_gettime(CLOCK_MONOTONIC, &t1);
	costo_us = (long)((t1.tv_sec - t0.tv_sec) * 1000000L
	                  + (t1.tv_nsec - t0.tv_nsec) / 1000);
	chiamate++;
	registro_dice(REG_SESSIONE,
	              "b97-guardiano giro=%s ritardo_ms=%ld finto=%s chiamate=%llu "
	              "costo_us=%ld utente=%s esito=%d",
	              giro, ritardo_ms, ritardo_ms >= 0 ? "si" : "no", chiamate,
	              costo_us, utente ? utente : "?", (int)esito);
	return esito;
}
"""

MARCA = "b97-guardiano INNESTATO"


def md5(p):
    with open(p, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def principale(argv):
    verifica = "--verifica" in argv
    dove = "/media/REMOTIX/tmp/10b6/b97-ritardo"
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
        if n == 1:
            print("⭐ l'innesto C'E' (una volta sola)")
            return 0
        print("⛔ l'innesto NON c'e' (occorrenze della marca: %d)" % n)
        return 1

    if MARCA in testo:
        print("⚠ gia' innestato: non lo rifaccio")
        print("md5 %s = %s" % (p, md5(p)))
        return 0
    quante = testo.count(VECCHIO)
    if quante != 1:
        print("⛔ NON INNESTO: l'adattatore originale compare %d volte in «%s» "
              "(ne serve esattamente una).  ⚠ `main.c` e' cambiato: l'innesto "
              "va rifatto a mano, non indovinato." % (quante, p))
        return 2
    prima = md5(p)
    nuovo = NUOVO.replace("@@B97_FILE@@", dove)
    if "@@" in nuovo:
        print("⛔ NON INNESTO: il segnaposto del file non e' stato sostituito")
        return 2
    with open(p, "w", encoding="utf-8") as f:
        f.write(testo.replace(VECCHIO, nuovo))
    print("md5 PRIMA  = %s" % prima)
    print("md5 DOPO   = %s" % md5(p))
    print("file del ritardo compilato dentro = %s" % dove)
    print("⭐ innestato in «%s»" % p)
    return 0


if __name__ == "__main__":
    sys.exit(principale(sys.argv[1:]))
