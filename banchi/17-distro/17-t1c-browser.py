#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
17-t1c-browser — fase 17, tappa T1c: un browser VERO entra in REMOTIX dentro
una VM di distribuzione e deve VEDERE il desktop.

    (sul server, come nicfio, dentro un labwc senza schermo)
    python3 17-t1c-browser.py --porta 7511 --utente prova --parola prova2026 \\
        --evidenze /media/REMOTIX/vm17/t1c/esiti/debian13-gnome [--browser chrome]

⭐ Non e' la suite (fasi/15): la suite vuole una SCATOLA (podman exec, registro
   del server, inquilini c15*).  Qui la macchina e' una VM di `17-vm.sh`, e
   l'utente di prova lo crea chi installa a mano.  ⇒ Si riusano SOLO le guide e
   la Prova di `12-client-veri.py` (importate, non copiate): apri → entra →
   primo_fotogramma, col giudice dei pixel (una tela nera o di un colore solo
   e' ROSSO, non verde: «un contatore non e' guardare»).

⚠ Il certificato si accetta come lo accetta l'utente (pannello «Procedi»,
  `GuidaCdp.vai`), niente `--ignore-certificate-errors`.
⚠ La finestra e' Full HD (1920x1080): nella VM non c'e' la scheda, si codifica
  in software, e la specifica di questa tappa e' «risoluzione bassa».

Uscita: una riga `T1C {json}` e codice 0 PASS · 1 FAIL · 3 BLOCKED.
"""
import argparse
import base64
import importlib.util as _iu
import json
import os
import sys
import time


def carica(nome, file):
    s = _iu.spec_from_file_location(nome, file)
    m = _iu.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def main():
    a = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    a.add_argument("--porta", type=int, required=True, help="la porta inoltrata sul server")
    a.add_argument("--host", default="localhost")
    a.add_argument("--utente", default="prova")
    a.add_argument("--parola", default=os.environ.get("REMOTIX_PAROLA", ""))
    a.add_argument("--browser", choices=("chrome", "firefox"), default="chrome")
    a.add_argument("--banchi", default=os.environ.get(
        "REMOTIX_BANCHI", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")),
        help="la cartella che contiene 12-client-veri.py")
    a.add_argument("--evidenze", default="")
    a.add_argument("--tetto-s", type=int, default=90,
                   help="tetto per l'ammissione e per il primo fotogramma NON degenere")
    a.add_argument("--finestra", default="1920x1080")
    a.add_argument("--porte-base", type=int, default=3170)
    o = a.parse_args()
    if not o.parola:
        a.error("serve --parola (o REMOTIX_PAROLA)")

    VERI = carica("veri", os.path.join(o.banchi, "12-client-veri.py"))
    VERI.FINESTRA[:] = [int(x) for x in o.finestra.split("x")]
    o.url = "https://%s:%d/" % (o.host, o.porta)
    o.visibile, o.salva, o.lascia_acceso = True, o.evidenze, False
    if o.evidenze:
        os.makedirs(o.evidenze, exist_ok=True)

    riga = {"url": o.url, "browser": o.browser, "utente": o.utente}
    esito, codice = "BLOCKED", 3
    g = None
    t0 = time.time()
    try:
        try:
            g = VERI.accendi_guida(o.browser, o)
        except Exception as e:                   # noqa: BLE001
            riga["ragione"] = "il browser non si e' acceso: %s" % str(e)[:300]
            raise StopIteration
        riga["palco"] = g.palco()
        pr = VERI.Prova(g, o, o.url, o.parola)
        ok, m = pr.apri()
        riga["apri"] = m
        if not ok:
            riga["ragione"] = "la pagina non si apre: " + m
            raise StopIteration
        e, m, s = pr.entra(o.parola)
        riga["entra"] = m
        if e != VERI.VERDE:
            esito, codice = "FAIL", 1
            riga["ragione"] = "non entra: " + m
            riga["registro_pagina"] = ((s or {}).get("registro") or "")[-1500:]
            raise StopIteration
        e, m, s = pr.primo_fotogramma()
        riga["prima_immagine"] = m
        riga["tela"] = (s or {}).get("tela")
        # ⭐ la fotografia della tela a piena risoluzione, per l'occhio di chi legge
        try:
            r = g.js("const t=document.getElementById('schermo'); if(!t) return null;"
                     "const b=t.getBoundingClientRect();"
                     "return [b.left,b.top,b.width,b.height,t.width,t.height];")
            riga["tela_px"] = r
            if r and o.evidenze:
                f = g.cdp.chiama("Page.captureScreenshot", format="png",
                                 clip={"x": r[0], "y": r[1], "width": r[2],
                                       "height": r[3], "scale": 1})
                p = os.path.join(o.evidenze, "desktop.png")
                with open(p, "wb") as fh:
                    fh.write(base64.b64decode(f["data"]))
                riga["foto"] = p
        except Exception as ex:                  # noqa: BLE001
            riga["foto"] = "non presa: %s" % str(ex)[:200]
        if e == VERI.VERDE:
            esito, codice = "PASS", 0
            riga["ragione"] = "desktop visto: " + m
        else:
            esito, codice = ("FAIL", 1) if e == VERI.ROSSO else ("BLOCKED", 3)
            riga["ragione"] = "entra, ma il desktop non si vede: " + m
            riga["registro_pagina"] = ((s or {}).get("registro") or "")[-1500:]
    except StopIteration:
        pass
    except Exception as ex:                      # noqa: BLE001
        riga["ragione"] = "il banco e' caduto: %r" % ex
    finally:
        if g is not None:
            try:
                js, rete, _ = g.errori_fuori()
                riga["errori"] = (js + rete)[:10]
            except Exception:                    # noqa: BLE001
                pass
            try:
                g.chiudi()
            except Exception:                    # noqa: BLE001
                pass
    riga.update(esito=esito, secondi=round(time.time() - t0, 1))
    print("T1C " + json.dumps(riga, ensure_ascii=False), flush=True)
    if o.evidenze:
        with open(os.path.join(o.evidenze, "esito.json"), "w") as fh:
            json.dump(riga, fh, ensure_ascii=False, indent=1)
    return codice


if __name__ == "__main__":
    sys.exit(main())
