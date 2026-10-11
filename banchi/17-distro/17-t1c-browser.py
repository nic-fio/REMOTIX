#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
17-t1c-browser — phase 17, step T1c: a REAL browser enters REMOTIX inside
a distribution VM and must SEE the desktop.

    (on the server, as nicfio, inside a headless labwc)
    python3 17-t1c-browser.py --port 7511 --user prova --password prova2026 \\
        --evidence /media/REMOTIX/vm17/t1c/esiti/debian13-gnome [--browser chrome]

⭐ This is not the suite (fasi/15): the suite wants a BOX (podman exec, server
   log, c15* tenants).  Here the machine is a VM from `17-vm.sh`, and the
   test user is created by whoever installs by hand.  ⇒ ONLY the drivers and
   the Prova of `12-client-veri.py` are reused (imported, not copied): open → enter →
   first_frame, with the pixel judge (a black or single-colour canvas
   is RED, not green: "a counter is not looking").

⚠ The certificate is accepted the way the user accepts it («Procedi» panel,
  `CdpDriver.vai`), no `--ignore-certificate-errors`.
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


def load(name, file):
    s = _iu.spec_from_file_location(name, file)
    m = _iu.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def main():
    a = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    a.add_argument("--port", type=int, required=True, help="the port forwarded on the server")
    a.add_argument("--host", default="localhost")
    a.add_argument("--user", default="prova")
    a.add_argument("--password", default=os.environ.get("REMOTIX_PASSWORD", ""))
    a.add_argument("--browser", choices=("chrome", "firefox"), default="chrome")
    a.add_argument("--benches", default=os.environ.get(
        "REMOTIX_BENCHES", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")),
        help="the folder that contains 12-client-veri.py")
    a.add_argument("--evidence", default="")
    a.add_argument("--cap-s", type=int, default=90,
                   help="cap for admission and for the first NON-degenerate frame")
    a.add_argument("--window", default="1920x1080")
    a.add_argument("--base-port", type=int, default=3170)
    o = a.parse_args()
    if not o.password:
        a.error("--password is required (or REMOTIX_PASSWORD)")

    VERI = load("veri", os.path.join(o.benches, "12-client-veri.py"))
    VERI.WINDOW[:] = [int(x) for x in o.window.split("x")]
    o.url = "https://%s:%d/" % (o.host, o.port)
    o.visible, o.save, o.leave_running = True, o.evidence, False
    if o.evidence:
        os.makedirs(o.evidence, exist_ok=True)

    line = {"url": o.url, "browser": o.browser, "user": o.user}
    outcome, code = "BLOCKED", 3
    g = None
    t0 = time.time()
    try:
        try:
            g = VERI.turn_on_driver(o.browser, o)
        except Exception as e:                   # noqa: BLE001
            line["rationale"] = "the browser did not start: %s" % str(e)[:300]
            raise StopIteration
        line["stage"] = g.stage()
        pr = VERI.Test(g, o, o.url, o.password)
        ok, m = pr.do_open()
        line["apri"] = m
        if not ok:
            line["rationale"] = "the page does not open: " + m
            raise StopIteration
        e, m, s = pr.enter(o.password)
        line["entra"] = m
        if e != VERI.GREEN:
            outcome, code = "FAIL", 1
            line["rationale"] = "does not get in: " + m
            line["registro_pagina"] = ((s or {}).get("log") or "")[-1500:]
            raise StopIteration
        e, m, s = pr.first_frame()
        line["prima_immagine"] = m
        line["canvas"] = (s or {}).get("canvas")
        # ⭐ the photo of the canvas at full resolution, for the reader's eye
        try:
            r = g.js("const t=document.getElementById('viewer'); if(!t) return null;"
                     "const b=t.getBoundingClientRect();"
                     "return [b.left,b.top,b.width,b.height,t.width,t.height];")
            line["tela_px"] = r
            if r and o.evidence:
                f = g.cdp.call("Page.captureScreenshot", format="png",
                                 clip={"x": r[0], "y": r[1], "width": r[2],
                                       "height": r[3], "scale": 1})
                p = os.path.join(o.evidence, "desktop.png")
                with open(p, "wb") as fh:
                    fh.write(base64.b64decode(f["data"]))
                line["photo"] = p
        except Exception as ex:                  # noqa: BLE001
            line["photo"] = "not taken: %s" % str(ex)[:200]
        if e == VERI.GREEN:
            outcome, code = "PASS", 0
            line["rationale"] = "desktop seen: " + m
        else:
            outcome, code = ("FAIL", 1) if e == VERI.RED else ("BLOCKED", 3)
            line["rationale"] = "gets in, but the desktop is not visible: " + m
            line["registro_pagina"] = ((s or {}).get("log") or "")[-1500:]
    except StopIteration:
        pass
    except Exception as ex:                      # noqa: BLE001
        line["rationale"] = "the bench crashed: %r" % ex
    finally:
        if g is not None:
            try:
                js, network, _ = g.errors_out()
                line["errors"] = (js + network)[:10]
            except Exception:                    # noqa: BLE001
                pass
            try:
                g.close()
            except Exception:                    # noqa: BLE001
                pass
    line.update(outcome=outcome, seconds=round(time.time() - t0, 1))
    print("T1C " + json.dumps(line, ensure_ascii=False), flush=True)
    if o.evidence:
        with open(os.path.join(o.evidence, "esito.json"), "w") as fh:
            json.dump(line, fh, ensure_ascii=False, indent=1)
    return code


if __name__ == "__main__":
    sys.exit(main())
