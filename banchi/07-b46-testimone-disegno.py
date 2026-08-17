#!/usr/bin/env python3
"""IL TESTIMONE DEL DISEGNO — quel che `LEZIONI.md` §2.8 dice non essere mai
esistito: un lettore indipendente del percorso di DISEGNO della pagina.

Guida il Firefox VERO (140 ESR) contro il prodotto, si collega come un utente,
e poi:
  · legge i dodici contatori di `Schermo` mentre girano;
  · tira giu' la TELA in PNG, cioe' esattamente i pixel che l'utente guarda;
  · raccoglie le righe del registro della pagina.

  uso: python3 testimone-disegno.py [--porta 7730] [--secondi 40] [--worker]
"""
import argparse, base64, json, os, subprocess, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib.util as _iu
_spec = _iu.spec_from_file_location("marionette", os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "07-b46-marionette.py"))
M = _iu.module_from_spec(_spec); _spec.loader.exec_module(M)

a = argparse.ArgumentParser()
a.add_argument("--ind", default="192.168.0.2")
a.add_argument("--porta", type=int, default=7730)
a.add_argument("--utente", default="prova")
a.add_argument("--parola", default="prova2026")
a.add_argument("--secondi", type=float, default=40)
a.add_argument("--worker", action="store_true")
a.add_argument("--larghezza", type=int, default=1600)
a.add_argument("--altezza", type=int, default=1000)
a.add_argument("--fuori", default="/tmp/testimone-disegno")
a.add_argument("--marionette", type=int, default=2833)
a.add_argument("--visibile", action="store_true")
o = a.parse_args()

os.makedirs(o.fuori, exist_ok=True)
url = "https://%s:%d/%s" % (o.ind, o.porta, "?video=worker" if o.worker else "")

p, m, prof = M.accendi(porta=o.marionette, headless=not o.visibile,
                       largo=o.larghezza, alto=o.altezza)
try:
    m.chiama("WebDriver:NewSession", {"acceptInsecureCerts": True})
    m.misura(o.larghezza, o.altezza)
    m.vai(url)
    print("aperta:", url)
    print("vista :", m.js("return [innerWidth, innerHeight, devicePixelRatio]")["value"])

    m.js("""
      document.getElementById('utente').value = arguments[0];
      document.getElementById('parola').value = arguments[1];
      document.getElementById('vai').click();
      return true;
    """, [o.utente, o.parola])
    print("modulo spedito, aspetto la sessione…")

    t0 = time.time()
    acceso = False
    while time.time() - t0 < 25:
        s = m.js("return document.body.dataset.schermo || ''")["value"]
        if s == "acceso":
            acceso = True
            break
        time.sleep(0.5)
    print("schermo acceso:", acceso, "dopo %.1f s" % (time.time() - t0))

    LETTURA = """
      const s = (window.REMOTIX && REMOTIX.schermo) || null;
      if (!s) return null;
      const t = document.getElementById('schermo');
      return { conti: s.conti, formato: s.formato, dipinta: s.dipinta,
               tela: [s.tela_l, s.tela_a], dec: [s.dec_l, s.dec_a],
               vista: [s.vista_l, s.vista_a],
               buffer: [t.width, t.height],
               stile: [t.style.width, t.style.height],
               coda: (s.dec ? s.dec.decodeQueueSize : null),
               stato: (s.dec ? s.dec.state : null),
               errori: s.errori.slice(-6) };
    """

    campioni = []
    t0 = time.time()
    n = 0
    while time.time() - t0 < o.secondi:
        r = m.js(LETTURA)["value"]
        if r:
            r["t"] = round(time.time() - t0, 2)
            campioni.append(r)
            print("%(t)6.2f s  dipinti %(d)5d  consegnati %(c)5d  saltati_coda %(sc)4d  "
                  "buchi %(b)3d  coda %(q)s  formato %(f)s  buffer %(bu)s" % {
                      "t": r["t"], "d": r["conti"]["dipinti"],
                      "c": r["conti"]["consegnati"], "sc": r["conti"]["saltati_coda"],
                      "b": r["conti"]["buchi"], "q": r["coda"], "f": r["formato"],
                      "bu": r["buffer"]})
        # una tela ogni 5 s
        if int(time.time() - t0) // 5 > n - 1 and r and r["conti"]["dipinti"] > 0:
            n += 1
            dati = m.js("""
              const t = document.getElementById('schermo');
              try { return t.toDataURL('image/png'); } catch (e) { return 'ERRORE ' + e; }
            """)["value"]
            if dati.startswith("data:image/png;base64,"):
                nome = os.path.join(o.fuori, "tela-%02d.png" % n)
                with open(nome, "wb") as f:
                    f.write(base64.b64decode(dati.split(",", 1)[1]))
                print("        ⇒ tela salvata:", nome, os.path.getsize(nome), "byte")
                # ⭐ E LO STESSO ISTANTE VISTO DAL SERVER X: quel che xrdp legge
                #   e ricomprime prima che arrivi agli occhi dell'utente.
                if o.visibile:
                    scherm = os.path.join(o.fuori, "schermo-x-%02d.png" % n)
                    subprocess.run(["import", "-display", os.environ.get("DISPLAY", ":0"),
                                    "-window", "root", scherm],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    print("        ⇒ schermo X   :", scherm)
            else:
                print("        ⛔ tela non leggibile:", dati[:120])
        time.sleep(1.0)

    righe = m.js("return document.getElementById('registro').innerText.slice(-6000)")["value"]
    with open(os.path.join(o.fuori, "registro-pagina.txt"), "w") as f:
        f.write(righe)
    with open(os.path.join(o.fuori, "campioni.json"), "w") as f:
        json.dump(campioni, f, indent=1)
    print("\n--- ultime righe del registro della pagina ---")
    print("\n".join(righe.splitlines()[-25:]))
finally:
    M.spegni(p, prof)
