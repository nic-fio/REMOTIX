#!/usr/bin/env python3
"""07-b61 — LA CURA SU UNA SESSIONE VERA, e la pagina di prima accanto.

    python3 banchi/07-b61-sessione.py [--nuova 7791] [--vecchia 7792] [--durata 150]

⛔ PERCHE' DUE PORTE E NON UNA: `07-b61-ancora.js` prova l'algoritmo dentro un
   `AudioContext` finto di cui governa l'orologio.  E' una prova vera ma di
   un'altra cosa — dice che la scaletta e' giusta, ⚠ non che su una scheda
   audio vera, con un `AudioContext` vero e una rete vera, il cuscino stia
   fermo.  ⇒ Qui girano **due sessioni sullo stesso binario, con lo stesso tono
   di prova**, e l'unica differenza e' il file `pagina.html`: la nuova sulla
   prima porta, quella di prima sulla seconda.

⭐ E LA PAGINA VECCHIA NON E' UN LUSSO: senza, un cuscino fermo a 250 ms si
   potrebbe sempre attribuire a «stasera la rete andava bene».  ⛔ Il difetto
   che si sta curando compare solo quando qualcosa si perde, e non si comanda
   alla rete di perdere.  ⇒ Le due colonne, nella stessa mezz'ora e sulla
   stessa macchina, sono l'unica forma di prova disponibile.

⚠ QUEL CHE QUESTO BANCO NON DICE, e va detto prima dei numeri:
  · gira su **Firefox headless**, cioe' senza GPU e con il dispositivo audio
    che il portatile gli concede.  ⛔ Non e' l'orecchio dell'utente e non lo
    sostituisce (I8);
  · il tono di prova e' un **flusso costante**: non c'e' un desktop che carica
    il thread principale.  ⇒ ⛔ Questa scena NON prova ne' smentisce la
    causa «il video occupa il thread che programma l'audio» — la prova quella
    solo una sessione con un video in riproduzione.
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
a.add_argument("--nuova", type=int, default=7791)
a.add_argument("--vecchia", type=int, default=7792)
a.add_argument("--durata", type=int, default=150)
# ⛔ Una colonna sola, e il reperto lo DICE.  ⚠ Rilievo R9 del 22 agosto 2026:
#    il file degli esiti diceva «nuova» e «vecchia» anche quando le due porte
#    erano la stessa, e un reperto committato e' una prova — se mente, mente
#    a chi lo legge fra un mese.
a.add_argument("--sola", action="store_true",
               help="una porta sola: niente colonna di confronto")
a.add_argument("--utente", default="provaa7")
a.add_argument("--parola", default="provaa7")
# ⛔ Una porta di Marionette SUA: 2828 e 2861 sono di altri banchi, e due
#    Firefox sulla stessa porta si rubano la sessione a vicenda.
a.add_argument("--marionette", type=int, default=2891)
o = a.parse_args()

LETTURA = """
const a = (typeof audio_conti === 'function') ? audio_conti() : null;
return JSON.stringify({
  conti: a,
  /* ⛔ NON da `AUDIO`: e' un `let`, non e' sull'oggetto globale e da qui non
     si vede.  I contatori escono da `audio_conti()`, che e' una funzione. */
  schermo: document.body.dataset.schermo || ''
});
"""


def orologio_cammina(m):
    """⭐ Prova che in questo browser l'audio ha davvero un orologio.

    ⛔ Si fa su un `AudioContext` A PARTE, non su quello della pagina: quello
       della pagina e' proprio l'oggetto sotto esame, e chiedergli di
       certificarsi da solo non proverebbe niente."""
    prova = """
      const c = new AudioContext({sampleRate: 48000});
      const fatto = arguments[arguments.length - 1];
      const t1 = c.currentTime;
      setTimeout(() => {
        const t2 = c.currentTime, st = c.state;
        const b = c.baseLatency || 0, u = c.outputLatency || 0;
        c.close();
        fatto(JSON.stringify({stato: st, avanzato: t2 - t1,
                              base_ms: b * 1000, uscita_ms: u * 1000}));
      }, 1200);
    """
    r = m.chiama("WebDriver:ExecuteAsyncScript", {"script": prova, "args": []})
    return json.loads(r["value"])


def una(porta, nome):
    print("\n══ %s — porta %d ═══════════════════════════════════" % (nome, porta))
    url = "https://%s:%d/" % (MACCHINA, porta)
    # ⛔⛔ LE PREFERENZE NON SONO UN DETTAGLIO — 21 agosto 2026, e senza di
    #     loro questo banco ha misurato per mezz'ora un ambiente morto.
    #     Firefox headless BLOCCA l'avvio automatico dell'audio: l'
    #     `AudioContext` nasce `suspended`, `resume()` non si risolve mai e
    #     `currentTime` resta a **zero per sempre**.  ⇒ Tutti i conti della
    #     pagina — che sono differenze di tempi — perdono senso insieme.
    #     ⚠ Un browser di utente non ha questo problema: li' c'e' un clic.
    p, m, prof = M.accendi(porta=o.marionette, headless=True, largo=1200, alto=800,
        profilo_prefs={"media.autoplay.default": 0,
                       "media.autoplay.blocking_policy": 0,
                       "media.autoplay.block-webaudio": False})
    campioni = []
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
            raise RuntimeError("⛔ lo schermo non si e' acceso in 60 s: "
                + (m.js("return document.getElementById('registro')"
                        ".innerText.slice(-600)")["value"] or "(registro vuoto)"))
        # ⛔⭐ IL CONTROLLO POSITIVO DELL'AMBIENTE, e viene PRIMA di ogni
        #     numero: si guarda che l'orologio dell'`AudioContext` cammini.
        #     ⚠ Un orologio fermo e un audio perfetto danno la stessa `coda`,
        #     gli stessi `BUCHI` e gli stessi `suonati`.  ⇒ Senza questa
        #     verifica il banco non distingue «suona» da «non c'e' nessun
        #     dispositivo» — `CODER.md` §3.10 applicato all'AMBIENTE invece
        #     che alla misura.
        d = orologio_cammina(m)
        if d["avanzato"] < 0.9:
            raise RuntimeError(
                "⛔ NIENTE DA GIUDICARE: in 1,2 s l'orologio dell'AudioContext "
                "e' avanzato di %.3f s (stato «%s»).  ⚠ Qui non suona niente e "
                "nessun numero di questa sessione vuol dire quel che sembra"
                % (d["avanzato"], d["stato"]))
        print("   ⭐ l'orologio audio cammina: +%.3f s in 1,2 s (stato «%s»)"
              % (d["avanzato"], d["stato"]))

        t0 = time.time()
        while time.time() - t0 < o.durata:
            time.sleep(5)
            try:
                d = json.loads(m.js(LETTURA)["value"])
            except Exception as e:
                print("   ⚠ lettura fallita: %s" % e)
                continue
            c = d.get("conti")
            if not c:
                continue
            c.setdefault("riarmi", None)
            c.setdefault("tirate", None)
            c["t"] = round(time.time() - t0, 1)
            campioni.append(c)
            print("   %6.1fs  ric %6d  suon %6d  USCITI %-6s tagl %-5s "
                  "coda %4s ms  BUCHI %-3s mancati %-4s pieni %-4s tirate %-3s"
                  % (c["t"], c["ricevuti"], c["suonati"],
                     c.get("usciti", "—"), c.get("tagliati", "—"),
                     c["in_coda_ms"], c.get("riarmi", "—"),
                     c.get("mancati", "—"), c["scartati_pieno"],
                     c.get("tirate", "—")))
    finally:
        M.spegni(p, prof)
    return campioni


def riassunto(nome, camp):
    if len(camp) < 3:
        # ⛔ §3.10: pochi campioni non sono «tutto a posto».
        print("   ⭐ %s: NIENTE DA GIUDICARE — solo %d campioni" % (nome, len(camp)))
        return None
    code = [c["in_coda_ms"] for c in camp]
    e = {
        "nome": nome, "campioni": len(camp),
        "coda_min": min(code), "coda_max": max(code),
        "coda_vaga": max(code) - min(code),
        "coda_prima": code[0], "coda_ultima": code[-1],
        "buchi": camp[-1].get("riarmi"),
        "buchi_dopo": (None if camp[-1].get("riarmi") is None
                       else camp[-1]["riarmi"] - (camp[0].get("riarmi") or 0)),
        "pieni": camp[-1]["scartati_pieno"],
        "mancati": camp[-1].get("mancati"),
        "ricevuti": camp[-1]["ricevuti"] - camp[0]["ricevuti"],
        "usciti": camp[-1].get("usciti"),
        "tagliati": camp[-1].get("tagliati"),
        "tirate": camp[-1].get("tirate"),
        "uscita_ms": camp[-1].get("uscita_ms"),
        "aoff_ms": camp[-1].get("aoff_ms"),
    }
    print("   %-22s coda %d→%d ms (vaga %d) · BUCHI %s (+%s) · pieni %s · "
          "mancati %s · USCITI %s · tagliati %s · tirate %s"
          % (nome, e["coda_prima"], e["coda_ultima"], e["coda_vaga"],
             e["buchi"], e["buchi_dopo"], e["pieni"], e["mancati"],
             e["usciti"], e["tagliati"], e["tirate"]))
    # ⛔⭐ IL VERDETTO CHE CONTA, e viene prima di tutti gli altri: una
    #     sessione in cui NIENTE e' uscito e' muta, e tutti gli altri numeri
    #     possono essere verdi lo stesso.
    if e["usciti"] is None:
        print("      ⭐ NIENTE DA GIUDICARE sul suono: questa pagina non "
              "conta `usciti` (e' quella di prima)")
    elif e["usciti"] < 0.5 * (camp[-1]["suonati"] - camp[0]["suonati"]):
        print("      ⛔⛔ MUTA: solo %s blocchi hanno raggiunto la loro fine "
              "naturale" % e["usciti"])
    else:
        print("      ⭐ ha suonato: %s blocchi usciti fino in fondo"
              % e["usciti"])
    return e


def carico():
    return subprocess.run(["uptime"], capture_output=True, text=True).stdout.strip()


def main():
    print("⛔ 07-b61 — la cura su una sessione vera.  carico: %s" % carico())
    nuova = una(o.nuova, "pagina in albero")
    if o.sola:
        print("\n══ IL REPERTO ═════════════════════════════════════════")
        print("   carico alla fine: %s" % carico())
        a1 = riassunto("in albero", nuova)
        fuori = os.path.join(QUI, "07-b61-esiti.json")
        json.dump({"quando": time.strftime("%Y-%m-%d %H:%M"),
                   "colonne": "una sola: --sola",
                   "porta": o.nuova, "durata_s": o.durata,
                   "carico": carico(), "campioni": nuova,
                   "riassunto": {"in albero": a1}},
                  open(fuori, "w"), indent=1)
        print("\n   esiti in %s" % fuori)
        return 0 if a1 else 3
    vecchia = una(o.vecchia, "pagina di PRIMA (scaletta per successione)")
    print("\n══ IL CONFRONTO ═══════════════════════════════════════")
    print("   carico alla fine: %s" % carico())
    a1 = riassunto("nuova", nuova)
    a2 = riassunto("di prima", vecchia)
    if not a1 or not a2:
        return 3
    print("\n   ⚠ E la lettura onesta: se in questa mezz'ora la rete non ha "
          "perso niente,\n     le due colonne DEVONO somigliarsi — il difetto "
          "si vede solo quando\n     qualcosa si perde.  Guardare `mancati`: e' "
          "lui che dice se la scena\n     ha avuto occasione di mostrare il "
          "difetto.")
    fuori = os.path.join(QUI, "07-b61-esiti.json")
    json.dump({"nuova": nuova, "vecchia": vecchia,
               "riassunto": {"nuova": a1, "vecchia": a2}},
              open(fuori, "w"), indent=1)
    print("\n   esiti in %s" % fuori)
    return 0


if __name__ == "__main__":
    sys.exit(main())
