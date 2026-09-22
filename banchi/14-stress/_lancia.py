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
    a = p.parse_args()

    sys.path.insert(0, QUI)
    os.makedirs(a.dove, exist_ok=True)

    try:
        import stress_nucleo as nucleo
    except Exception as e:
        print("⛔ il nucleo (stress_nucleo.py) non si importa: %s" % e)
        print("   ⇒ non ho potuto guardare: esito 3, e non e' un rosso")
        return 3

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
        r.setdefault("scenario", getattr(scenario, "NOME", os.path.basename(a.scenario)[:-3]))
        r.setdefault("desktop", a.desktop)
        r.setdefault("marca", a.marca)
        r.setdefault("esito", esito)
        r.setdefault("secondi", int(time.time() - t0))
        r.setdefault("quando_finito", time.time())
        try:
            with open(os.path.join(a.dove, "esiti.jsonl"), "a", encoding="utf-8") as f:
                f.write(json.dumps(r, ensure_ascii=False, default=str) + "\n")
        except OSError as e:
            print("⚠ la riga non si e' potuta scrivere: %s" % e)

    return esito


if __name__ == "__main__":
    sys.exit(main())
