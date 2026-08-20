#!/usr/bin/env python3
"""07-b48-testimone.py — guida il banco «la tela contro la verità» da solo.

    python3 banchi/07-b48-testimone.py [--visibile] [--porta 8099]

⛔ PERCHE' ESISTE, e la data: 17 agosto 2026.  Il banco `07-b48` va aperto sei
   volte con sei interruttori diversi, e finora le apriva l'utente a mano —
   mentre io cambiavo la pagina sotto.  «Se non mi dai il tempo di fare le
   prove non si va da nessuna parte; altrimenti falle tu.»  ⇒ Le fa questo.

Guida un Firefox VERO col protocollo Marionette (nessun geckodriver, nessuna
coordinata), aspetta che la pagina abbia finito, e legge `window.RISULTATO` —
⭐ non il DOM: un numero letto dall'impaginazione è un numero che cambia se
cambia il foglio di stile.

⚠ E il modo `--visibile` non è un vezzo: in `--headless` Firefox non prende la
  strada della GPU, quindi un giro headless misura la decodifica e il disegno
  in SOFTWARE.  Per dire qualcosa sull'hardware ci vuole una finestra vera, e
  il testimone lo DICHIARA nella riga d'esito invece di lasciarlo intendere.
"""
import argparse, json, os, sys, time
import importlib.util as _iu

_qui = os.path.dirname(os.path.abspath(__file__))
_spec = _iu.spec_from_file_location("marionette", os.path.join(_qui, "07-b46-marionette.py"))
M = _iu.module_from_spec(_spec)
_spec.loader.exec_module(M)

GIRI = [
    ("certifica AV1",  "?guasto=1"),
    ("certifica H264", "?flusso=h264&guasto=1"),
    ("AV1  60/s",      ""),
    ("AV1  a tutta",   "?ritmo=0"),
    ("H264 60/s",      "?flusso=h264"),
    ("H264 a tutta",   "?flusso=h264&ritmo=0"),
]

def main():
    a = argparse.ArgumentParser()
    a.add_argument("--visibile", action="store_true",
                   help="finestra vera invece di headless: serve per la GPU")
    a.add_argument("--porta", type=int, default=8099)
    a.add_argument("--marionette", type=int, default=2841)
    a.add_argument("--attesa", type=int, default=240, help="secondi per giro")
    o = a.parse_args()

    base = "http://localhost:%d/" % o.porta
    p, m, prof = M.accendi(porta=o.marionette, headless=not o.visibile,
                           largo=1600, alto=1000)
    esiti = []
    try:
        m.sessione()
        for nome, coda in GIRI:
            m.vai(base + coda)
            scaduto = time.time() + o.attesa
            r = None
            while time.time() < scaduto:
                r = m.js("return window.RISULTATO || null;")["value"]
                if r:
                    break
                time.sleep(1)
            if not r:
                # ⛔ Un'attesa scaduta non e' una diagnosi: si chiede alla
                #   pagina che cosa stava dicendo quando il tempo e' finito.
                try:
                    st = m.js("return document.getElementById('stato').textContent")["value"]
                except Exception as e:
                    st = "(non leggibile: %s)" % e
                print("⛔ %-14s NON ha finito in %d s — la pagina diceva: «%s»"
                      % (nome, o.attesa, st))
                esiti.append((nome, None))
                continue
            esiti.append((nome, r))
            d, t = r["decodificatore"], r["tela"]
            print("%-14s dec %4d fuori posto (peggio %6.1f, %2d fotogrammi) · "
                  "tela %4d (peggio %6.1f, %2d fotogrammi) · usciti %d/%d · errori %d"
                  % (nome, d["fuori_posto"], d["peggio"], d["fotogrammi"],
                     t["fuori_posto"], t["peggio"], t["fotogrammi"],
                     r["fotogrammi_usciti"], r["fotogrammi_dati"],
                     r["errori_decodificatore"]))
            sc = r.get("scostamento_comune") or {}
            if sc and (abs(sc.get("decodificatore", 0)) > 1 or abs(sc.get("tela", 0)) > 1):
                print("               ⚠ scostamento COMUNE di colore: dec %+.1f · tela %+.1f "
                      "(tolto dal giudizio: è una convenzione, non un blocco)"
                      % (sc.get("decodificatore", 0), sc.get("tela", 0)))
            sys.stdout.flush()
    finally:
        M.spegni(p, prof)

    print("\n⚠ strada grafica: %s" % ("finestra vera (GPU possibile)" if o.visibile
                                      else "HEADLESS — tutto in software"))
    # ⛔ I due giri di certificazione devono essere ROSSI: se il banco non vede
    #    il guasto che gli si è messo dentro, gli altri quattro non valgono.
    for nome, r in esiti:
        if r and r["guasto"]:
            visti = r["decodificatore"]["fuori_posto"] + r["tela"]["fuori_posto"]
            print("%s: il guasto innestato è stato %s"
                  % (nome, "VISTO" if visti else "⛔ NON VISTO — banco cieco"))
    with open(os.path.join(_qui, "07-b48-esiti.json"), "w") as f:
        json.dump(esiti, f, indent=1)
    print("esiti in banchi/07-b48-esiti.json")

if __name__ == "__main__":
    main()
