#!/usr/bin/env python3
"""07-b62 — «IL SUONO PARTE AL PRIMO CLIC»: la pagina lo scrive, e adesso lo fa.

    python3 banchi/07-b62-il-primo-clic.py [--porta 7791] [--schermo :63]

⛔ PERCHE' ESISTE — 21 agosto 2026, trovato da A7 leggendo il file.

   La pagina, quando l'`AudioContext` nasce sospeso, scrive all'utente:
   *«il suono parte al primo clic sulla pagina»*.  ⛔ Sotto quella frase non
   c'era una riga di codice: un solo `resume()`, alla nascita del contesto, e
   **nessun gestore** che ci riprovasse quando il clic arrivava davvero.
   `[M]` A7, in headless: `suspended` per 90 s **anche dopo un clic vero**.

⛔⛔ E DAL 21 AGOSTO IL PREZZO ERA PIU' ALTO: da quando `suona()` butta i
    blocchi che arrivano a contesto fermo — e li butta per una buona ragione,
    con l'orologio fermo ogni conto perde senso — un contesto che non si
    sveglia non e' piu' «audio in ritardo», e' **una sessione muta per
    sempre**.

⭐ QUESTO BANCO NON GUARDA I CONTATORI, GUARDA LO STATO E QUEL CHE ESCE.  Tre
   domande, in quest'ordine, e la terza e' quella che conta:

   1. il contesto nasce sospeso?      (se no, la scena non prova niente e si
                                       dichiara `NIENTE DA GIUDICARE`)
   2. resta sospeso finche' nessuno tocca?
   3. ⭐ dopo un clic VERO, passa a `running` **e i blocchi cominciano a
      uscire**?  ⛔ «running» da solo non basta: e' il difetto di ieri, tutti i
      contatori verdi e zero suono.  Si guarda `usciti`.

⛔ E GIRA SU UN FIREFOX CON SCHERMO, non headless — `--schermo :63`.  In
   headless l'avvio automatico e' bloccato in un modo che un browser di utente
   non ha, e una cura provata li' non direbbe niente di quel che vede l'utente.
   ⚠ Il display virtuale si accende da se' se non c'e'.

⚠ QUEL CHE QUESTO BANCO NON DICE: che il suono sia GIUSTO.  Dice che esce.  La
  purezza del tono la giudica `07-b40`, e l'orecchio l'utente.
"""
import argparse
import importlib.util as iu
import json
import os
import subprocess
import sys
import time

QUI = os.path.dirname(os.path.abspath(__file__))
MACCHINA = "192.168.0.2"


def _mod(nome, file):
    s = iu.spec_from_file_location(nome, os.path.join(QUI, file))
    m = iu.module_from_spec(s)
    s.loader.exec_module(m)
    return m


M = _mod("marionette", "07-b46-marionette.py")

a = argparse.ArgumentParser()
a.add_argument("--porta", type=int, default=7791)
a.add_argument("--schermo", default=":63")
a.add_argument("--utente", default="provaa7")
a.add_argument("--parola", default="provaa7")
a.add_argument("--marionette", type=int, default=2894)
a.add_argument("--attesa", type=int, default=25,
               help="quanti secondi si aspetta SENZA toccare, prima del clic")
o = a.parse_args()

LEGGI = """
const c = (typeof audio_conti === 'function') ? audio_conti() : null;
return JSON.stringify({conti: c, schermo: document.body.dataset.schermo || ''});
"""


def schermo_acceso(display):
    """⭐ Uno schermo virtuale suo.  ⛔ Non si usa quello dell'utente: questo
       banco clicca, e cliccare sullo schermo di chi sta lavorando e' una cosa
       che non si fa."""
    n = display.lstrip(":")
    gia = subprocess.run(["pgrep", "-f", "Xvfb %s" % display],
                         capture_output=True, text=True).stdout.strip()
    if gia:
        return None
    p = subprocess.Popen(["Xvfb", display, "-screen", "0", "1400x1000x24"],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.5)
    return p


def carico():
    return subprocess.run(["uptime"], capture_output=True, text=True).stdout.strip()


def main():
    print("⛔ 07-b62 — «il suono parte al primo clic».  carico: %s" % carico())
    xvfb = schermo_acceso(o.schermo)
    url = "https://%s:%d/" % (MACCHINA, o.porta)
    # ⛔ NIENTE preferenze di avvio automatico: la scena e' proprio quella in
    #    cui il motore blocca l'audio finche' non c'e' un gesto.  Metterle
    #    renderebbe la prova verde senza provare niente.
    p, m, prof = M.accendi(porta=o.marionette, headless=False,
                           largo=1200, alto=800, schermo=o.schermo)
    esito = {}
    try:
        m.chiama("WebDriver:NewSession", {"acceptInsecureCerts": True})
        m.misura(1200, 800)
        m.vai(url)
        m.js("""document.getElementById('utente').value = arguments[0];
                document.getElementById('parola').value = arguments[1];
                document.getElementById('vai').click(); return true;""",
             [o.utente, o.parola])
        t0 = time.time()
        while time.time() - t0 < 60:
            if m.js("return document.body.dataset.schermo || ''")["value"] == "acceso":
                break
            time.sleep(0.5)
        else:
            raise RuntimeError("⛔ lo schermo non si e' acceso in 60 s")

        # ── 1 · come nasce ────────────────────────────────────────────────
        time.sleep(3)
        d = json.loads(m.js(LEGGI)["value"])
        c0 = d["conti"] or {}
        esito["nasce"] = c0.get("contesto")
        print("   1 · il contesto nasce  «%s»  (ricevuti %s, usciti %s, "
              "sospesi %s, risvegli %s)"
              % (esito["nasce"], c0.get("ricevuti"), c0.get("usciti"),
                 c0.get("sospesi"), c0.get("risvegli")))
        if esito["nasce"] == "running":
            # ⛔ §3.10: la scena non ha prodotto la condizione che voleva
            #    provare.  Non e' un verde.
            print("   ⭐ NIENTE DA GIUDICARE: qui il contesto nasce gia' "
                  "avviato, quindi la promessa «parte al primo clic» non viene "
                  "messa alla prova.  ⚠ Non e' «la cura funziona».")
            return 3

        # ── 2 · quanto resta fermo se nessuno tocca ───────────────────────
        print("   2 · aspetto %d s SENZA toccare niente…" % o.attesa)
        time.sleep(o.attesa)
        d = json.loads(m.js(LEGGI)["value"])
        c1 = d["conti"] or {}
        esito["prima_del_clic"] = c1
        print("       dopo %d s: «%s», ricevuti %s, usciti %s, sospesi %s"
              % (o.attesa, c1.get("contesto"), c1.get("ricevuti"),
                 c1.get("usciti"), c1.get("sospesi")))

        # ── 3 · IL CLIC, e quel che succede dopo ──────────────────────────
        print("   3 · clic vero sulla pagina")
        m.chiama("WebDriver:PerformActions", {"actions": [{
            "type": "pointer", "id": "mouse",
            "parameters": {"pointerType": "mouse"},
            "actions": [{"type": "pointerMove", "duration": 40, "x": 600, "y": 400},
                        {"type": "pointerDown", "button": 0},
                        {"type": "pause", "duration": 90},
                        {"type": "pointerUp", "button": 0}]}]})
        time.sleep(8)
        d = json.loads(m.js(LEGGI)["value"])
        c2 = d["conti"] or {}
        esito["dopo_il_clic"] = c2
        print("       dopo il clic: «%s», ricevuti %s, usciti %s, sospesi %s, "
              "risvegli %s, coda %s ms"
              % (c2.get("contesto"), c2.get("ricevuti"), c2.get("usciti"),
                 c2.get("sospesi"), c2.get("risvegli"), c2.get("in_coda_ms")))

        # ── il verdetto ───────────────────────────────────────────────────
        usciti_prima = c1.get("usciti") or 0
        usciti_dopo = c2.get("usciti") or 0
        acceso = c2.get("contesto") == "running"
        esce = usciti_dopo > usciti_prima + 50
        print("\n   %s il contesto si e' svegliato al clic" % ("⭐" if acceso else "⛔"))
        print("   %s ⭐ E IL SUONO ESCE: usciti %d → %d dopo il clic"
              % ("⭐" if esce else "⛔", usciti_prima, usciti_dopo))
        if c2.get("risvegli"):
            print("   ⭐ risvegli %s: il gestore c'e' e ha fatto il suo lavoro"
                  % c2.get("risvegli"))
        else:
            print("   ⚠ risvegli 0: si e' svegliato da solo, non per il gesto — "
                  "la cura non e' stata messa alla prova da questa scena")
        print("\n   carico alla fine: %s" % carico())
        return 0 if (acceso and esce) else 1
    finally:
        M.spegni(p, prof)
        if xvfb:
            xvfb.terminate()


if __name__ == "__main__":
    sys.exit(main())
