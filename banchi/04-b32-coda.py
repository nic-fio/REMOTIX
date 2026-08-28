#!/usr/bin/env python3
"""04-b32-coda.py — ⭐⭐ LA CODA DEL DECODIFICATORE, misurata mentre cresce.

    python3 banchi/04-b32-coda.py --porta 7721 --utente provao2 \\
            --parola-file /tmp/04-b30/parola --fette 9

⛔ PERCHE' ESISTE, E PERCHE' NON BASTAVA `04-b30`.

`04-b30` misura un RITARDO: una grandezza che si suppone stazionaria, di cui si
prende la mediana.  ⛔ Ma il difetto che questo strumento ha trovato **non e'
stazionario: cresce.**  Una mediana su una grandezza che cresce e' un numero che
dipende da quanto e' durato il giro — cioe' non e' un numero.

⇒ Questo strumento non stampa una mediana: stampa **la pendenza**.  Ogni cinque
  secondi legge tre cose nello stesso istante:

    · quanti fotogrammi il SERVER ha consegnato        (`REMOTIX.schermo.conti`)
    · quanti la PAGINA ne ha dipinti                   (idem)
    · di quanto e' indietro il decodificatore          (`decode()` → richiamo,
                                                        misurato dal prologo di
                                                        `04-b30`)

⛔ E i tre insieme dicono una cosa che nessuno dei tre dice da solo: se
   «consegnati» supera «dipinti» e **nessun contatore di scarto sale**, allora
   l'avanzo non lo butta nessuno e il ritardo sale per sempre.  ⚠ I contatori di
   scarto si stampano accanto apposta (`scartati_ordine`, `trattenuti`,
   `corti`, `saltati_coda`): «zero scarti» e' la meta' della prova, e senza di
   lei «cresce» si potrebbe leggere come «la rete e' lenta».

⚠ Precondizione: la SCENA dev'essere accesa e in movimento, o non c'e' nessun
  fotogramma da consegnare (`LEZIONI.md` §1.1).  ⛔ Lo strumento se ne accorge —
  «consegnati» non cresce — e lo DICE invece di stampare degli zeri.
"""
import argparse
import functools
import importlib.util
import json
import os
import subprocess
import sys
import time

print = functools.partial(print, flush=True)
QUI = os.path.dirname(os.path.abspath(__file__))
ESITI = os.path.join(QUI, "04-b32-esiti.jsonl")


def carica(nome, percorso):
    spec = importlib.util.spec_from_file_location(nome, percorso)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def principale():
    p = argparse.ArgumentParser()
    p.add_argument("--host", default="192.168.0.2")
    p.add_argument("--porta", type=int, default=7721)
    p.add_argument("--utente", default="provao2")
    p.add_argument("--parola-file", default="/tmp/04-b30/parola")
    p.add_argument("--schermo", default=":90")
    p.add_argument("--diagnosi", type=int, default=9630)
    p.add_argument("--lavoro", default="/tmp/04-b30")
    p.add_argument("--fetta", type=float, default=5.0)
    p.add_argument("--fette", type=int, default=9)
    p.add_argument("--terreno", default="/media/REMOTIX/src/04-b32-terreno.sh")
    p.add_argument("--giro", default=time.strftime("coda-%Y%m%d-%H%M%S"))
    a = p.parse_args()

    b17 = carica("b17", os.path.join(QUI, "03-b17-ritardo.py"))
    b30 = carica("b30", os.path.join(QUI, "04-b30-anello-input.py"))
    palco = b17.Palco(a.schermo, a.diagnosi, (1500, 1000),
                      os.path.join(a.lavoro, "palco"), gpu=True)
    righe = []
    try:
        print("Xvfb:", palco.accendi())
        c = palco
        c.chiama("Page.addScriptToEvaluateOnNewDocument", source=b30.PROLOGO)
        c.chiama("Page.navigate", url="https://%s:%d/" % (a.host, a.porta))
        time.sleep(3)
        s = c.valuta(b17.STATO, attendi=False)
        if not (isinstance(s, dict) and s.get("pronto")):
            b17.batti(c, "thisisunsafe")
            time.sleep(3)
        b17.aspetta(c, b17.STATO, 40, lambda x: x.get("pronto"))
        with open(a.parola_file) as f:
            parola = f.read().strip()
        c.valuta(b17.ENTRA % (json.dumps(a.utente), json.dumps(parola)),
                 attendi=False)
        del parola
        # ⛔ LA SCENA SI ACCENDE **DOPO** CHE QUALCUNO E' ENTRATO, e non prima:
        #    il monitor virtuale nasce col FIGLIO, non col server, e una scena
        #    accesa prima finirebbe «da qualche parte» (`LEZIONI.md` §1.1-bis).
        #    ⚠ E senza scena non c'e' niente da consegnare: questo strumento
        #      stamperebbe degli zeri che sembrano un ritmo.
        acceso = False
        for _ in range(8):
            r = subprocess.run(
                ["python3", os.path.join(os.path.dirname(QUI),
                                         "fondamenta/strumenti/sshpw.py"),
                 "sudo -S -p 'Password sudo: ' bash %s scena-avvia" % a.terreno],
                capture_output=True, text=True, timeout=240)
            if r.returncode == 0:
                acceso = True
                print((r.stdout or "").strip().splitlines()[-1][:160])
                break
            time.sleep(3.0)
        if not acceso:
            print("⛔ la scena non si e' accesa: NON misuro, e non stampo zeri")
            return 3
        b17.aspetta(c, b17.STATO, 60,
                    lambda x: (x.get("conti") or {}).get("dipinti", 0) > 0)
        print("primo fotogramma dipinto")
        prima, t0 = None, None
        for _ in range(a.fette):
            c.valuta(b30.SVUOTA, attendi=False)
            time.sleep(a.fetta)
            r = c.valuta("window.__B30.prendi()", attendi=False)
            camp = (r or {}).get("campioni") or []
            conti = (r or {}).get("pagina") or {}
            rit = sorted(x["t1"] - x["t_dec"] for x in camp if x.get("t_dec"))
            lag = rit[len(rit) // 2] if rit else None
            if prima is None:
                prima, t0, dt = dict(conti), time.time(), 1.0
                d = {k: 0 for k in conti}
            else:
                dt = time.time() - t0
                d = {k: conti.get(k, 0) - prima.get(k, 0) for k in conti}
            riga = {"t_s": round(dt, 1),
                    "ritardo_decode_uscita_ms": None if lag is None else round(lag, 1),
                    "consegnati_al_s": round(d.get("consegnati", 0) / max(dt, 1e-9), 2),
                    "dipinti_al_s": round(d.get("dipinti", 0) / max(dt, 1e-9), 2),
                    "scartati_ordine": conti.get("scartati_ordine"),
                    "trattenuti": conti.get("trattenuti"),
                    "corti": conti.get("corti"),
                    # ⭐ il contatore della cura: se non c'e', questo prodotto
                    #    e' quello di PRIMA — e si vede, invece di indovinarlo
                    "saltati_coda": conti.get("saltati_coda")}
            righe.append(riga)
            print("t=%5.1f s · ritardo %8s ms · consegnati %6.2f/s · dipinti "
                  "%6.2f/s · scartati_ordine %s · trattenuti %s · corti %s · "
                  "saltati_coda %s"
                  % (riga["t_s"], riga["ritardo_decode_uscita_ms"],
                     riga["consegnati_al_s"], riga["dipinti_al_s"],
                     riga["scartati_ordine"], riga["trattenuti"],
                     riga["corti"], riga["saltati_coda"]))
    finally:
        palco.spegni()

    utili = [x for x in righe[1:] if x["ritardo_decode_uscita_ms"] is not None
             and x["consegnati_al_s"] > 1.0]
    if len(utili) < 2:
        # ⛔ «Non ho potuto guardare» non e' «il ritardo non cresce»: senza
        #    fotogrammi non c'e' nessuna pendenza da stampare, e stampare uno
        #    zero sarebbe la sesta veste di `LEZIONI.md` §1.9.
        print("\n    \033[1;31mNO\033[0m  ⛔ NON HO NIENTE DA GIUDICARE: "
              "il ciclo dei fotogrammi non gira (consegnati ~0/s).  ⚠ Non e' "
              "«il ritardo non cresce»: e' «non c'era niente da guardare»")
    esito = {"banco": "B32-coda", "giro": a.giro, "host": a.host,
             "porta": a.porta, "righe": righe,
             "quando": time.strftime("%FT%T")}
    if len(utili) >= 2:
        dt = utili[-1]["t_s"] - utili[0]["t_s"]
        dl = (utili[-1]["ritardo_decode_uscita_ms"]
              - utili[0]["ritardo_decode_uscita_ms"])
        esito["pendenza_ms_al_s"] = round(dl / dt, 2) if dt else None
        esito["ritardo_finale_ms"] = utili[-1]["ritardo_decode_uscita_ms"]
        esito["avanzo_al_s"] = round(utili[-1]["consegnati_al_s"]
                                     - utili[-1]["dipinti_al_s"], 2)
        print("\n\033[1m== CHE COSA DICE\033[0m")
        print("    --  il server consegna %.2f/s, la pagina dipinge %.2f/s ⇒ "
              "avanzo %.2f/s" % (utili[-1]["consegnati_al_s"],
                                 utili[-1]["dipinti_al_s"],
                                 esito["avanzo_al_s"]))
        print("    --  il ritardo `decode()` → richiamo cresce di %s ms al "
              "secondo, e dopo %.0f s vale %s ms"
              % (esito["pendenza_ms_al_s"], utili[-1]["t_s"],
                 esito["ritardo_finale_ms"]))
        if (esito["pendenza_ms_al_s"] or 0) > 20:
            print("    \033[1;31mNO\033[0m  ⛔ IL RITARDO CRESCE SENZA LIMITE: "
                  "niente butta l'avanzo.  ⚠ Non e' «la rete e' lenta» — la "
                  "rete non fa crescere niente, fa un ritardo COSTANTE")
        else:
            print("    \033[1;32mOK\033[0m  ⭐ il ritardo NON cresce: l'avanzo "
                  "viene buttato (guarda `saltati_coda`)")
    with open(ESITI, "a") as f:
        f.write(json.dumps(esito, ensure_ascii=False) + "\n")
    print("depositato in %s" % ESITI)
    return 0


if __name__ == "__main__":
    sys.exit(principale())
