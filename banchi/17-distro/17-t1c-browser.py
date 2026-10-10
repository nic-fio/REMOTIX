#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
17-t1c-browser — phase 17, step T1c: a REAL browser enters REMOTIX inside
a distribution VM and must SEE the desktop.

    (on the server, as nicfio, inside a headless labwc)
    python3 17-t1c-browser.py --porta 7511 --utente prova --parola prova2026 \\
        --evidenze /media/REMOTIX/vm17/t1c/esiti/debian13-gnome [--browser chrome]

⭐ This is not the suite (fasi/15): the suite wants a BOX (podman exec, server
   log, c15* tenants).  Here the machine is a VM from `17-vm.sh`, and the
   test user is created by whoever installs by hand.  ⇒ ONLY the drivers and
   the Prova of `12-client-veri.py` are reused (imported, not copied): open → enter →
   primo_fotogramma, with the pixel judge (a black or single-colour canvas
   is RED, not green: "a counter is not looking").

⚠ The certificate is accepted the way the user accepts it («Procedi» panel,
  `GuidaCdp.vai`), no `--ignore-certificate-errors`.
⚠ The window is Full HD (1920x1080): there is no GPU in the VM, encoding is
  in software, and the spec of this step is "low resolution".

Output: one line `T1C {json}` and exit code 0 PASS · 1 FAIL · 3 BLOCKED.
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
    a.add_argument("--porta", type=int, required=True, help="the port forwarded on the server")
    a.add_argument("--host", default="localhost")
    a.add_argument("--utente", default="prova")
    a.add_argument("--parola", default=os.environ.get("REMOTIX_PAROLA", ""))
    a.add_argument("--browser", choices=("chrome", "firefox"), default="chrome")
    a.add_argument("--banchi", default=os.environ.get(
        "REMOTIX_BANCHI", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")),
        help="the folder that contains 12-client-veri.py")
    a.add_argument("--evidenze", default="")
    a.add_argument("--tetto-s", type=int, default=90,
                   help="cap for admission and for the first NON-degenerate frame")
    a.add_argument("--finestra", default="1920x1080")
    a.add_argument("--porte-base", type=int, default=3170)
    o = a.parse_args()
    if not o.parola:
        a.error("--parola is required (or REMOTIX_PAROLA)")

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
            riga["ragione"] = "the browser did not start: %s" % str(e)[:300]
            raise StopIteration
        riga["palco"] = g.palco()
        pr = VERI.Prova(g, o, o.url, o.parola)
        ok, m = pr.apri()
        riga["apri"] = m
        if not ok:
            riga["ragione"] = "the page does not open: " + m
            raise StopIteration
        e, m, s = pr.entra(o.parola)
        riga["entra"] = m
        if e != VERI.VERDE:
            esito, codice = "FAIL", 1
            riga["ragione"] = "does not get in: " + m
            riga["registro_pagina"] = ((s or {}).get("registro") or "")[-1500:]
            raise StopIteration
        e, m, s = pr.primo_fotogramma()
        riga["prima_immagine"] = m
        riga["tela"] = (s or {}).get("tela")
        # ⭐ the photo of the canvas at full resolution, for the reader's eye
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
            riga["foto"] = "not taken: %s" % str(ex)[:200]
        if e == VERI.VERDE:
            esito, codice = "PASS", 0
            riga["ragione"] = "desktop seen: " + m
        else:
            esito, codice = ("FAIL", 1) if e == VERI.ROSSO else ("BLOCKED", 3)
            riga["ragione"] = "gets in, but the desktop is not visible: " + m
            riga["registro_pagina"] = ((s or {}).get("registro") or "")[-1500:]
    except StopIteration:
        pass
    except Exception as ex:                      # noqa: BLE001
        riga["ragione"] = "the bench crashed: %r" % ex
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
