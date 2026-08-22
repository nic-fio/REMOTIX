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
    GPU**, cioe' proprio la scena di `06-b41-contesa.sh`.  Un certificatore
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
        "tela_nuova_dal_palco", "non_spediti",
        "tentativi_con_risposta", "tentativi_senza_risposta")


def ambiente(percorso_json, tela_nuova, non_spediti):
    d = json.load(open(percorso_json, encoding="utf-8"))
    tele = [v for v in d["controllo_dopo_sessione"] if v["tipo"] == "TELA"]
    msl = [t["ms"] for t in d["tentativi"] if t.get("ms") is not None]
    # ⛔⛔ E I TENTATIVI SCADUTI SI CONTANO — rilievo R5 della revisione
    #     avversariale, 22 agosto 2026.  Prima sparivano nella comprensione qui
    #     sopra: un tentativo senza risposta non entrava in NESSUN numero.
    #     ⚠ E lo scarto era sempre **dalla parte dei lenti**, cioe' proprio la
    #     coda che le regole di questo banco cercano.
    senza = sum(1 for t in d["tentativi"] if t.get("ms") is None)
    return {
        "adattate": sum(1 for v in tele if v["esito"] == "ADATTATA"),
        "non_ora": sum(1 for v in tele if v["motivo"] == "NON_ORA"),
        # ⛔⛔ IL SENTINELLA CADEVA DALLA PARTE DEL VERDE — rilievo R5, e vale
        #     da solo tutta questa riga.
        #
        #     Qui c'era `-1`.  Se NESSUN tentativo riceve risposta — la scena
        #     sotto contesa, dove tutte e nove le richieste superano l'attesa —
        #     `msl` e' vuota, `ms_mediano` valeva **-1**, e la regola di **G2**
        #     (`non_ora >= 6 and ms_mediano < 200`) diventava **vera**: il
        #     certificatore scriveva «G2 ATTESO-CONFERMATO — le risposte
        #     arrivano SUBITO» **mentre non ne era arrivata nemmeno una**.
        #
        # ⇒ Adesso e' `None`, che NON si confronta: `None < 200` solleva
        #   `TypeError`, e `giudica()` (piu' sotto) se ne accorge PRIMA e
        #   dichiara «NON-MISURATO» invece di far cadere la moneta.
        # ⭐ E' la stessa forma della cura di G3: **il sentinella deve cadere
        #   dalla parte del rosso**.  Un numero che passa un confronto per caso
        #   e' un falso verde travestito da misura.
        "ms_mediano": statistics.median(msl) if msl else None,
        # ⛔ «fotogrammi» sono quelli COMPLETI arrivati al client: uno spedito
        #    e non completato non e' un pixel.
        "fotogrammi": d["fotogrammi_totali"],
        "tela_nuova_dal_palco": int(tela_nuova),
        "non_spediti": int(non_spediti),
        "tentativi_con_risposta": len(msl),
        "tentativi_senza_risposta": senza,
    }


def applica(regola, amb):
    """Vero/falso, oppure un'eccezione: `eval` senza builtins e coi soli sei."""
    return bool(eval(regola, {"__builtins__": {}}, dict(amb)))


def giudica(amb, q, guasti_py, amb_sano=None):
    s = importlib.util.spec_from_file_location("g", guasti_py)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    regola = m.GUASTI[q]["regola"]
    numeri = " ".join(f"{k}={amb.get(k)}" for k in NOMI)

    # ⛔⛔ IL RIFIUTO DICHIARATO, PRIMA DEL CONFRONTO — rilievo R5, 22 agosto
    #     2026.  Se la regola NOMINA `ms_mediano` e quel numero non esiste (zero
    #     tentativi con risposta), non si giudica: si dichiara di NON aver
    #     misurato.
    # ⚠ E la guardia e' sul NOME dentro la regola, non sul caso: G5 gira
    #   legittimamente senza `ms_mediano` (la sua regola non lo nomina), e
    #   rifiutarlo sarebbe un rosso all'imputato sbagliato.
    if "ms_mediano" in regola and amb.get("ms_mediano") is None:
        return (f"{q} NON-MISURATO (ZERO tentativi con risposta: «ms_mediano» "
                f"non esiste, e la regola lo nomina) {numeri}  "
                f"[regola: {regola}]  ⛔ un sentinella qui avrebbe passato il "
                f"confronto per caso", 1)

    try:
        visto = applica(regola, amb)
    except Exception as e:  # noqa: BLE001
        return f"{q} REGOLA-ROTTA {e}  {numeri}  [regola: {regola}]", 1

    anche_sano = None
    sano_dice = "non calcolata"
    if amb_sano is not None:
        # ⚠ E anche qui: se il giro SANO non ha `ms_mediano`, non e' un metro
        #   per una regola che lo nomina — e si scrive, invece di stampare un
        #   `None` che si legge come «falso».
        if "ms_mediano" in regola and amb_sano.get("ms_mediano") is None:
            sano_dice = ("⛔ NON CONFRONTABILE (il giro sano non ha "
                         "«ms_mediano»: zero tentativi con risposta)")
        else:
            try:
                anche_sano = applica(regola, amb_sano)
                sano_dice = str(anche_sano)
            except Exception as e:  # noqa: BLE001
                anche_sano = None
                sano_dice = f"⛔ NON CONFRONTABILE ({e})"

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
        coda = ("  | sano: " + " ".join(f"{k}={amb_sano.get(k)}" for k in NOMI)
                + f" · regola sul sano = {sano_dice}")
    else:
        coda = "  | ⚠ NESSUN GIRO SANO: la regola non e' stata messa a confronto"
    return f"{q} {esito} {numeri}  [regola: {regola}]{coda}", 0


# ===========================================================================
def _finto(adattate, non_ora, ms, fotogrammi, scaduti=0):
    """⚠ `ms=None` + `scaduti=N`: il giro in cui NESSUNA risposta e' arrivata."""
    tele = ([{"tipo": "TELA", "esito": "ADATTATA", "motivo": 0}] * adattate
            + [{"tipo": "TELA", "esito": "RIFIUTATA", "motivo": "NON_ORA"}] * non_ora)
    tent = ([] if ms is None else [{"ms": ms}]) + [{"ms": None}] * scaduti
    return {"controllo_dopo_sessione": tele,
            "tentativi": tent,
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
        prova("gli otto numeri del guasto",
              {"adattate": 0, "non_ora": 9, "ms_mediano": 3000.0,
               "fotogrammi": 12, "tela_nuova_dal_palco": 0, "non_spediti": 0,
               "tentativi_con_risposta": 1, "tentativi_senza_risposta": 0},
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

        # ===================================================================
        # ⛔⭐ LA REGOLA VERA DI G3 CADE DALLA PARTE GIUSTA — 22 agosto 2026.
        #
        #     La terza clausola era `tela_nuova_dal_palco == 0`, ed era **vera
        #     esattamente quando lo strumento non aveva guardato**: uno zero e'
        #     quel che lascia un registro illeggibile.  Adesso e' `== 1` — il
        #     conto della sola riconciliazione di nascita — e questo controllo
        #     pretende che i due casi si separino, invece di crederlo.
        #     ⚠ Il file dei guasti e' QUELLO VERO, non un finto: se qualcuno
        #     rimettesse lo `0`, questo controllo diventa rosso.
        # ===================================================================
        import pathlib
        vero = str(pathlib.Path(__file__).with_name("06-b35-guasti.py"))
        if os.path.exists(vero):
            # il giro G3 come e' stato misurato il 21 agosto
            g3 = {"adattate": 3, "non_ora": 7, "ms_mediano": 3003.35,
                  "fotogrammi": 586, "tela_nuova_dal_palco": 1,
                  "non_spediti": 0}
            # lo STESSO giro, ma con lo strumento che non ha visto niente
            cieco = dict(g3, tela_nuova_dal_palco=0)
            # e il metro sano della stessa ora
            sano21 = {"adattate": 10, "non_ora": 0, "ms_mediano": 47.45,
                      "fotogrammi": 169, "tela_nuova_dal_palco": 10,
                      "non_spediti": 0}
            riga, _ = giudica(g3, "G3", vero, sano21)
            prova("G3 sul giro VERO del 21 ago ⇒ CONFERMATO",
                  True, "ATTESO-CONFERMATO" in riga)
            riga, _ = giudica(cieco, "G3", vero, sano21)
            prova("G3 con lo strumento CIECO (0) ⇒ NON confermato",
                  False, "ATTESO-CONFERMATO" in riga)
            # ⭐ e la terza clausola deve DISTINGUERE G3 da G1, se no i due
            #    guasti hanno la stessa regola e il banco vede «un» problema.
            g1 = {"adattate": 3, "non_ora": 7, "ms_mediano": 3014.15,
                  "fotogrammi": 11, "tela_nuova_dal_palco": 8,
                  "non_spediti": 7}
            riga, _ = giudica(g1, "G3", vero, sano21)
            prova("la regola di G3 sul giro di G1 ⇒ NON confermato",
                  False, "ATTESO-CONFERMATO" in riga)
            riga, _ = giudica(g3, "G1", vero, sano21)
            prova("la regola di G1 sul giro di G3 ⇒ NON confermato",
                  False, "ATTESO-CONFERMATO" in riga)

            # ===============================================================
            # ⛔⛔ R5 — IL SENTINELLA CHE PASSAVA IL CONFRONTO, 22 agosto 2026.
            #
            #     La scena: sotto contesa NESSUNA delle nove richieste riceve
            #     risposta entro l'attesa del client.  ⇒ `ms_mediano` non
            #     esiste.  Col vecchio `-1`, la regola di G2 (`non_ora >= 6 and
            #     ms_mediano < 200`) diventava VERA e il banco scriveva
            #     «le risposte arrivano SUBITO» su un giro **senza risposte**.
            # ⚠ E la prova e' fatta sul giro VERO passato per `ambiente()`, non
            #   su un dizionario scritto a mano: cosi' controlla anche la riga
            #   che costruisce i numeri, non solo quella che li giudica.
            # ===============================================================
            pmuto = os.path.join(d, "muto.json")
            json.dump(_finto(0, 9, None, 0, scaduti=9), open(pmuto, "w"))
            amb_muto = ambiente(pmuto, 1, 0)
            prova("giro MUTO: ms_mediano e' None, non un numero",
                  True, amb_muto["ms_mediano"] is None)
            prova("  ...e i 9 scaduti sono CONTATI, non scartati",
                  (0, 9), (amb_muto["tentativi_con_risposta"],
                           amb_muto["tentativi_senza_risposta"]))
            riga, u = giudica(amb_muto, "G2", vero, sano21)
            prova("G2 sul giro MUTO ⇒ NON confermato",
                  False, "ATTESO-CONFERMATO" in riga)
            prova("  ...e lo DICHIARA: «NON-MISURATO»",
                  True, "NON-MISURATO" in riga)
            prova("  ...e l'uscita e' rossa", 1, u)
            # ⛔ Il veleno vero: col sentinella VECCHIO la stessa scena passava.
            #    Se qualcuno rimettesse un numero al posto del `None`, questa
            #    riga diventa rossa.
            vecchio = dict(amb_muto, ms_mediano=-1)
            riga, _ = giudica(vecchio, "G2", vero, sano21)
            prova("⛔ col sentinella VECCHIO (-1) sarebbe passato",
                  True, "ATTESO-CONFERMATO" in riga)
            # ⭐ E G5 — che NON nomina `ms_mediano` — non dev'essere rifiutato:
            #    il rifiuto e' sulla regola, non sul caso.
            g5 = {"adattate": 0, "non_ora": 0, "ms_mediano": None,
                  "fotogrammi": 0, "tela_nuova_dal_palco": 157,
                  "non_spediti": 1, "tentativi_con_risposta": 0,
                  "tentativi_senza_risposta": 0}
            riga, _ = giudica(g5, "G5", vero, sano21)
            prova("⭐ G5 (che non nomina ms_mediano) NON viene rifiutato",
                  True, "ATTESO-CONFERMATO" in riga)
        else:
            print(f"    ⛔  06-b35-guasti.py non e' accanto a me ({vero}): "
                  f"i quattro controlli su G3 NON sono stati fatti")
            guai.append("guasti.py assente")

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
