#!/usr/bin/env python3
"""_lancia.py — ⭐ il pezzo di regia che sa parlare python: importa e chiama.

⛔ E' della REGIA (`14-notte.sh`), non uno scenario: comincia con `_` apposta,
   cosi' `elenco_scenari` non lo scambia per uno di loro.

Perche' esiste: il contratto degli scenari e' una funzione python
(`gira(desktop, marca, nucleo, opzioni)`), e un copione bash non sa chiamarla.
⇒ Qui si importa il nucleo, si importa lo scenario, si chiama, e si TRADUCE il
  risultato in un codice d uscita — che e' l unica cosa che bash capisce.

I codici d uscita, gli stessi della rete (§1.52):
   0  regge          1  NON regge          3  non ho potuto guardare
"""
import argparse
import importlib.util
import json
import os
import sys
import time
import traceback

QUI = os.path.dirname(os.path.abspath(__file__))


def carica(percorso, nome):
    spec = importlib.util.spec_from_file_location(nome, percorso)
    m = importlib.util.module_from_spec(spec)
    sys.modules[nome] = m
    spec.loader.exec_module(m)
    return m


def esito_dal_risultato(r):
    """⛔ Non si indovina: se lo scenario non dice un esito, l esito e' 3.

    ⚠ «Non ha detto niente» e «va tutto bene» non devono avere la stessa
      faccia — e' la stessa regola del `None` invece dello zero nei banchi.
    """
    if r is None:
        return 3, "lo scenario non ha detto niente"
    if isinstance(r, bool):
        return (0 if r else 1), ""
    if isinstance(r, int):
        return (r if r in (0, 1, 3) else 3), ("" if r in (0, 1, 3) else
                                              "esito %r, che non conosco" % r)
    if isinstance(r, dict):
        if "esito" in r:
            e = r["esito"]
            try:
                e = int(e)
            except (TypeError, ValueError):
                return 3, "esito %r, che non e' un numero" % (e,)
            return (e if e in (0, 1, 3) else 3), r.get("perche", "")
        return 3, "il dict dello scenario non ha la chiave «esito»"
    return 3, "lo scenario ha risposto %s, che non so leggere" % type(r).__name__


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--scenario", required=True)
    p.add_argument("--desktop", required=True)
    p.add_argument("--marca", required=True)
    p.add_argument("--porta", type=int, required=True)
    p.add_argument("--host", required=True)
    p.add_argument("--dove", required=True)
    p.add_argument("--tetto", type=int, default=600)
    # ⛔ LA DURATA SI PASSA.  Prima non si passava, e gli scenari ricadevano
    #    sempre sul loro `DURATA_S`: finche' la regia legge la durata proprio da
    #    quella costante non si vede niente, ma il giorno che la notte decide di
    #    accorciare un giro, lo scenario girerebbe lungo lo stesso e la riga
    #    direbbe una durata che non e' quella fatta.  `[M]` 23 set 2026.
    p.add_argument("--durata", type=float, default=None)
    # ⭐ PER PROVARE LA CATENA SENZA IL PRODOTTO: `--finto sano` (o `fermo`,
    #   `morto`, …) mette al posto del nucleo vero il nucleo finto degli
    #   scenari.  ⛔ Non e' una misura, e la riga lo DICE (`col_nucleo_finto`):
    #   serve a provare che la riga arriva completa fino al rapporto, senza
    #   accendere un browser sullo schermo di nessuno.
    p.add_argument("--finto", default=None)
    a = p.parse_args()

    sys.path.insert(0, QUI)
    # ⛔ E anche la cartella dello scenario: gli scenari si appoggiano a un
    #    modulo comune accanto a loro (`_comune`), e senza questo l import
    #    fallisce per un dettaglio di come li carico io, non per colpa loro.
    sys.path.insert(0, os.path.dirname(os.path.abspath(a.scenario)))
    os.makedirs(a.dove, exist_ok=True)

    try:
        import stress_nucleo as nucleo
    except Exception as e:
        print("⛔ il nucleo (stress_nucleo.py) non si importa: %s" % e)
        print("   ⇒ non ho potuto guardare: esito 3, e non e' un rosso")
        return 3

    if a.finto:
        try:
            # ⚠ Per percorso: il finto sta in `scenari/`, che non e' detto sia
            #   la cartella dello scenario che si sta lanciando.
            finto = carica(os.path.join(QUI, "scenari", "_nucleo_finto.py"),
                           "_nucleo_finto")
            nucleo = finto.Finto(a.finto)
        except Exception as e:                   # noqa: BLE001
            print("⛔ il nucleo finto non si carica: %s" % e)
            return 3
        print("⚠⚠ NUCLEO FINTO («%s»): questo giro NON misura il prodotto." % a.finto)

    try:
        scenario = carica(a.scenario, "scenario_" + os.path.basename(a.scenario)[:-3])
    except Exception as e:
        print("⛔ lo scenario %s non si importa: %s" % (a.scenario, e))
        return 3

    if not hasattr(scenario, "gira"):
        print("⛔ %s non ha la funzione «gira»: non e' uno scenario" % a.scenario)
        return 3

    opzioni = {
        "porta": a.porta,
        "host": a.host,
        "dove": a.dove,
        "secco": False,
        "tetto_s": a.tetto,
        "quando": time.time(),
    }
    if a.durata:
        opzioni["durata_s"] = a.durata

    # ⭐ La riga la scrive chi la scrive, ma la COMPLETA sempre il nucleo: marca
    #   del browser, numeri in vista, verdetto in parole.  ⛔ In un posto solo.
    def scrivi(r, esito, perche, quanto):
        r.setdefault("scenario", getattr(scenario, "NOME",
                                         os.path.basename(a.scenario)[:-3]))
        r.setdefault("desktop", a.desktop)
        r.setdefault("marca", a.marca)
        r.setdefault("browser", a.marca)
        r.setdefault("esito", esito)
        if perche:
            r.setdefault("perche", perche)
        r.setdefault("secondi", round(quanto, 1))
        r.setdefault("quando_finito", time.time())
        r.setdefault("regole", {})
        if a.durata and r["regole"].get("durata_s") is None:
            r["regole"]["durata_s"] = a.durata
        r.setdefault("tetto_s", a.tetto)
        r.setdefault("porta", a.porta)
        if a.finto:
            r["col_nucleo_finto"] = a.finto
        try:
            nucleo.completa_la_riga(r)
        except Exception as e:                   # noqa: BLE001
            print("⚠ la riga non si e' potuta completare: %s" % e)
        try:
            with open(os.path.join(a.dove, "esiti.jsonl"), "a", encoding="utf-8") as f:
                f.write(json.dumps(r, ensure_ascii=False, default=str) + "\n")
        except OSError as e:
            print("⚠ la riga non si e' potuta scrivere: %s" % e)

    t0 = time.time()
    try:
        r = scenario.gira(a.desktop, a.marca, nucleo, opzioni)
    except KeyboardInterrupt:
        print("⛔ interrotto a mano")
        return 3
    except Exception:
        # ⛔ Un guasto DEL BANCO non e' un rosso del prodotto: §1.52.  E il
        #    perche' si stampa per intero, o domattina non si diagnostica.
        traceback.print_exc()
        print("⛔ lo scenario e' morto per conto suo: esito 3, non un rosso")
        # ⭐⭐ E LA RIGA SI SCRIVE LO STESSO.  Un giro morto a meta' che non
        #    lascia niente domattina somiglia a un giro mai partito: la riga
        #    dice almeno scenario, scatola, MARCA del browser e su che cosa e'
        #    morto — e il resto della catena la riconosce come «morta per
        #    strada», non come un verde.
        ultimo = traceback.format_exc().strip().splitlines()[-1]
        scrivi({"morto_per_strada": True,
                "perche": "lo scenario e' morto per strada: %s" % ultimo[:300],
                "traccia": traceback.format_exc()[-2000:]},
               3, None, time.time() - t0)
        return 3

    esito, perche = esito_dal_risultato(r)
    if perche:
        print("   %s" % perche)
    print("   %s · %s · %s ⇒ esito %d in %.0f s"
          % (getattr(scenario, "NOME", "?"), a.desktop, a.marca, esito,
             time.time() - t0))

    # ⚠ Se lo scenario ha risposto con un dict ma NON ha scritto la sua riga,
    #   la scrive qui: il dict lo sa gia' tutto, buttarlo sarebbe perdere la
    #   misura per una formalita'.  La regia si accorge da sola dei doppioni.
    if isinstance(r, dict) and not r.get("riga_scritta"):
        scrivi(r, esito, perche, time.time() - t0)
    elif not isinstance(r, dict):
        # ⛔ Uno scenario che risponde un numero o un booleano non lascerebbe
        #    NIENTE: nemmeno con che browser e' stato fatto il giro.
        scrivi({"perche": perche or "lo scenario non ha dato misure",
                "senza_misure": True},
               esito, None, time.time() - t0)

    return esito


if __name__ == "__main__":
    sys.exit(main())
