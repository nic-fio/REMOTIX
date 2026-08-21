#!/usr/bin/env python3
"""06-b35-regola.py — i sei numeri di un giro, e il giudizio, tenuti separati.

    python3 06-b35-regola.py ambiente <misura.json> <tela_nuova> <non_spediti>
        stampa i sei numeri del giro, in JSON, e basta.

    python3 06-b35-regola.py giudica <ambiente.json> <Q> <06-b35-guasti.py> \\
                                     [ambiente-del-giro-SANO.json]
        applica la regola di <Q> e stampa la riga d'esito.

    python3 06-b35-regola.py --controllo
        ⭐ il controllo positivo dello STRUMENTO.

⛔⛔ PERCHE' ESISTE, E NON E' UN RIORDINO — rilievo della revisione
    avversariale, 21 agosto 2026, terzo rilievo su `06-b35-certifica.sh`:

    *«Non c'e' NESSUN giro sano, in tutto il certificatore. Ogni regola e'
    valutata solo sotto il guasto.»*

    E il caso concreto: `fasi/06 §5.1` dichiara che **il codice sano** produce
    gia' 4 giri su 18 col desktop non adattato e `NON_ORA` al fondo dei 3 s.
    ⇒ La regola di **G1** — `non_ora >= 6 and ms_mediano > 2500 and
    fotogrammi < 100` — e' **soddisfacibile da codice sano sotto contesa
    GPU**, cioe' proprio la scena di `06-b39-contesa.sh`.  Un certificatore
    che guarda solo il guasto scriverebbe `ATTESO-CONFERMATO` e starebbe
    certificando **il carico**, non il guasto.

⇒ Qui la regola si applica a DUE ambienti — quello del guasto e quello del
  giro **sano** preso nella **stessa ora e sotto lo stesso carico** — e se
  torna vera in tutti e due, il caso si dichiara **NON DISCRIMINANTE**.  Non
  «rosso», non «verde»: *non distingue*, che e' un'altra cosa e va scritta.

⚠ E l'ambiente dei numeri e' TUTTO quel che la regola puo' vedere: `eval` gira
  con `__builtins__` vuoto, e i nomi sono solo i sei.
"""
import importlib.util
import json
import statistics
import sys

NOMI = ("adattate", "non_ora", "ms_mediano", "fotogrammi",
        "tela_nuova_dal_palco", "non_spediti")


def ambiente(percorso_json, tela_nuova, non_spediti):
    d = json.load(open(percorso_json, encoding="utf-8"))
    tele = [v for v in d["controllo_dopo_sessione"] if v["tipo"] == "TELA"]
    msl = [t["ms"] for t in d["tentativi"] if t.get("ms") is not None]
    return {
        "adattate": sum(1 for v in tele if v["esito"] == "ADATTATA"),
        "non_ora": sum(1 for v in tele if v["motivo"] == "NON_ORA"),
        "ms_mediano": statistics.median(msl) if msl else -1,
        # ⛔ «fotogrammi» sono quelli COMPLETI arrivati al client: uno spedito
        #    e non completato non e' un pixel.
        "fotogrammi": d["fotogrammi_totali"],
        "tela_nuova_dal_palco": int(tela_nuova),
        "non_spediti": int(non_spediti),
    }


def applica(regola, amb):
    """Vero/falso, oppure un'eccezione: `eval` senza builtins e coi soli sei."""
    return bool(eval(regola, {"__builtins__": {}}, dict(amb)))


def giudica(amb, q, guasti_py, amb_sano=None):
    s = importlib.util.spec_from_file_location("g", guasti_py)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    regola = m.GUASTI[q]["regola"]
    try:
        visto = applica(regola, amb)
    except Exception as e:  # noqa: BLE001
        return f"{q} REGOLA-ROTTA {e}", 1
    numeri = " ".join(f"{k}={amb[k]}" for k in NOMI)

    anche_sano = None
    if amb_sano is not None:
        try:
            anche_sano = applica(regola, amb_sano)
        except Exception:  # noqa: BLE001
            anche_sano = None

    # ⛔ «CONFERMATO» vuol dire che l'ATTESO DICHIARATO PRIMA si e' avverato —
    #    non «e' diventato rosso»: l'atteso di G4 e' VERDE, e chiamarlo
    #    «visto» direbbe il falso su meta' dei casi.
    esito = "ATTESO-CONFERMATO" if visto else "ATTESO-SMENTITO"

    if anche_sano is True and visto:
        # ⛔⛔ Il caso non distingue: la stessa regola torna vera sul codice
        #     SANO, misurato nella stessa ora e sotto lo stesso carico.
        esito = "NON-DISCRIMINANTE (vera anche sul SANO)"
    coda = ""
    if amb_sano is not None:
        coda = ("  | sano: " + " ".join(f"{k}={amb_sano[k]}" for k in NOMI)
                + f" · regola sul sano = {anche_sano}")
    else:
        coda = "  | ⚠ NESSUN GIRO SANO: la regola non e' stata messa a confronto"
    return f"{q} {esito} {numeri}  [regola: {regola}]{coda}", 0


# ===========================================================================
def _finto(adattate, non_ora, ms, fotogrammi):
    tele = ([{"tipo": "TELA", "esito": "ADATTATA", "motivo": 0}] * adattate
            + [{"tipo": "TELA", "esito": "RIFIUTATA", "motivo": "NON_ORA"}] * non_ora)
    return {"controllo_dopo_sessione": tele,
            "tentativi": [{"ms": ms}],
            "fotogrammi_totali": fotogrammi}


def controllo():
    import os
    import tempfile
    print("⭐ CONTROLLO POSITIVO DELLO STRUMENTO — ambienti finti, risposta nota\n")
    guai = []

    def prova(nome, atteso, avuto):
        segno = "OK " if avuto == atteso else "⛔ "
        print(f"    {segno} {nome}: atteso {atteso!r} · avuto {avuto!r}")
        if avuto != atteso:
            guai.append(nome)

    with tempfile.TemporaryDirectory() as d:
        pg = os.path.join(d, "g.json")
        json.dump(_finto(0, 9, 3000.0, 12), open(pg, "w"))
        amb_g = ambiente(pg, 0, 0)
        prova("i sei numeri del guasto",
              {"adattate": 0, "non_ora": 9, "ms_mediano": 3000.0,
               "fotogrammi": 12, "tela_nuova_dal_palco": 0, "non_spediti": 0},
              amb_g)

        ps = os.path.join(d, "s.json")
        json.dump(_finto(9, 0, 40.0, 300), open(ps, "w"))
        amb_s = ambiente(ps, 9, 0)

        # un finto 06-b35-guasti.py con la regola vera di G1
        pgu = os.path.join(d, "guasti.py")
        open(pgu, "w").write(
            'GUASTI = {"G1": {"regola": '
            '"non_ora >= 6 and ms_mediano > 2500 and fotogrammi < 100"}}\n')

        riga, _ = giudica(amb_g, "G1", pgu, amb_s)
        prova("guasto rosso + sano verde ⇒ CONFERMATO",
              True, "ATTESO-CONFERMATO" in riga)

        # ⛔⛔ IL VELENO: il SANO, sotto contesa, produce gli STESSI numeri del
        #     guasto.  Lo strumento deve rifiutarsi di chiamarlo «confermato».
        riga, _ = giudica(amb_g, "G1", pgu, amb_g)
        prova("guasto rosso + sano ANCHE rosso ⇒ NON-DISCRIMINANTE",
              True, "NON-DISCRIMINANTE" in riga)
        prova("  ...e NON dice «confermato»", False, "ATTESO-CONFERMATO" in riga)

        # ⛔ E senza giro sano lo strumento lo DICHIARA, invece di tacere.
        riga, _ = giudica(amb_g, "G1", pgu, None)
        prova("senza giro sano, lo dichiara", True, "NESSUN GIRO SANO" in riga)

        # ⛔ E una regola che nomina qualcosa che non c'e' non passa in silenzio.
        open(pgu, "w").write('GUASTI = {"G1": {"regola": "pippo > 0"}}\n')
        riga, _ = giudica(amb_g, "G1", pgu, amb_s)
        prova("regola rotta dichiarata", True, "REGOLA-ROTTA" in riga)

    print()
    if guai:
        print(f"⛔ CONTROLLO POSITIVO FALLITO su {len(guai)}: {guai}")
        return 1
    print("⭐ CONTROLLO POSITIVO SUPERATO")
    return 0


if __name__ == "__main__":
    if "--controllo" in sys.argv:
        sys.exit(controllo())
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    if sys.argv[1] == "ambiente":
        json.dump(ambiente(sys.argv[2], sys.argv[3], sys.argv[4]),
                  sys.stdout, ensure_ascii=False)
        print()
        sys.exit(0)
    if sys.argv[1] == "giudica":
        amb = json.load(open(sys.argv[2], encoding="utf-8"))
        sano = (json.load(open(sys.argv[5], encoding="utf-8"))
                if len(sys.argv) > 5 else None)
        riga, u = giudica(amb, sys.argv[3], sys.argv[4], sano)
        print(riga)
        sys.exit(u)
    sys.exit(__doc__)
