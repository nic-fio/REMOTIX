#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
t8-browser — phase 17, T8 (R39, R11): a REAL browser stays connected to the desktop while REMOTIX is
upgraded (or rolled back) by the package manager, and then re-enters: the desktop is the SAME one.

    (on the server, inside the labwc of 17-t1c-guarda.sh: T1C_PROGRAMMA=…/t8-browser.py)
    python3 t8-browser.py --porta 7511 --utente prova --parola prova2026 --evidenze DIR

1. enters and sees the desktop (the pixel judge of 12-client-veri.py: a black canvas is RED);
   "before" photo; writes DIR/pronto;
2. stays connected (the tab open) until DIR/via appears (cap 20 minutes), counting the
   frames painted each second (DIR/linea.jsonl);
3. reloads the tab, re-enters, and must see the desktop again within the cap; "after" photo.
Output: one line `T8 {json}`; exit code 0 PASS · 1 FAIL · 3 BLOCKED.
"""
import argparse
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
    a = argparse.ArgumentParser()
    a.add_argument("--porta", type=int, required=True)
    a.add_argument("--host", default="127.0.0.1")
    a.add_argument("--utente", default="prova")
    a.add_argument("--parola", default=os.environ.get("REMOTIX_PAROLA", ""))
    a.add_argument("--browser", choices=("chrome", "firefox"), default="chrome")
    a.add_argument("--banchi", default=os.environ.get("REMOTIX_BANCHI", "/media/REMOTIX/src/controllo/banchi"))
    a.add_argument("--evidenze", required=True)
    a.add_argument("--tetto-s", type=int, default=90)
    a.add_argument("--attesa-s", type=int, default=1200)
    a.add_argument("--finestra", default="1920x1080")
    a.add_argument("--porte-base", type=int, default=3170)
    o = a.parse_args()
    VERI = carica("veri", os.path.join(o.banchi, "12-client-veri.py"))
    VERI.FINESTRA[:] = [int(x) for x in o.finestra.split("x")]
    o.url = "https://%s:%d/" % (o.host, o.porta)
    o.visibile, o.salva, o.lascia_acceso = True, o.evidenze, False
    os.makedirs(o.evidenze, exist_ok=True)
    for f in ("pronto", "via"):
        try:
            os.remove(os.path.join(o.evidenze, f))
        except FileNotFoundError:
            pass
    riga = {"url": o.url, "browser": o.browser}
    esito, codice = "BLOCKED", 3
    g = None
    t0 = time.time()
    try:
        g = VERI.accendi_guida(o.browser, o)
        pr = VERI.Prova(g, o, o.url, o.parola)
        ok, m = pr.apri()
        if not ok:
            riga["ragione"] = "the page does not open: " + m
            raise StopIteration
        e, m, _ = pr.entra(o.parola)
        if e != VERI.VERDE:
            esito, codice, riga["ragione"] = "FAIL", 1, "does not get in: " + m
            raise StopIteration
        e, m, _ = pr.primo_fotogramma()
        riga["prima"] = m
        if e != VERI.VERDE:
            esito, codice, riga["ragione"] = "FAIL", 1, "before the upgrade the desktop is not visible: " + m
            raise StopIteration
        open(os.path.join(o.evidenze, "pronto"), "w").write(str(time.time()))
        # connected during the upgrade: the painted frames, every second
        fine = time.time() + o.attesa_s
        with open(os.path.join(o.evidenze, "linea.jsonl"), "w") as lf:
            while time.time() < fine and not os.path.exists(os.path.join(o.evidenze, "via")):
                s = pr.stato()
                lf.write(json.dumps({"t": round(time.time(), 2), "dipinti": s.get("dipinti"),
                                     "acceso": s.get("acceso")}) + "\n")
                lf.flush()
                time.sleep(1)
        riga["collegato_s"] = round(time.time() - t0, 1)
        if not os.path.exists(os.path.join(o.evidenze, "via")):
            riga["ragione"] = "no \"via\" within %d s" % o.attesa_s
            raise StopIteration
        # the reattach: the tab reloaded, we re-enter, and the desktop must be seen again
        t1 = time.time()
        g.ricarica()
        ok, m = pr.apri()
        e, m, _ = pr.entra(o.parola)
        riga["rientra"] = m
        if e != VERI.VERDE:
            esito, codice, riga["ragione"] = "FAIL", 1, "after the upgrade it does not get back in: " + m
            raise StopIteration
        e, m, _ = pr.primo_fotogramma()
        riga["dopo"] = m
        riga["riattacco_s"] = round(time.time() - t1, 1)
        if e == VERI.VERDE:
            esito, codice, riga["ragione"] = "PASS", 0, "desktop seen again after the upgrade"
        else:
            esito, codice, riga["ragione"] = "FAIL", 1, "gets back in, but the desktop is not visible: " + m
    except StopIteration:
        pass
    except Exception as ex:                      # noqa: BLE001
        riga["ragione"] = "the bench crashed: %r" % ex
    finally:
        if g is not None:
            try:
                g.chiudi()
            except Exception:                    # noqa: BLE001
                pass
    riga.update(esito=esito, secondi=round(time.time() - t0, 1))
    print("T8 " + json.dumps(riga, ensure_ascii=False), flush=True)
    with open(os.path.join(o.evidenze, "esito.json"), "w") as fh:
        json.dump(riga, fh, ensure_ascii=False, indent=1)
    return codice


if __name__ == "__main__":
    sys.exit(main())
