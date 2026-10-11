#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
t8-browser — phase 17, T8 (R39, R11): a REAL browser stays connected to the desktop while REMOTIX is
upgraded (or rolled back) by the package manager, and then re-enters: the desktop is the SAME one.

    (on the server, inside the labwc of 17-t1c-guarda.sh: T1C_PROGRAM=…/t8-browser.py)
    python3 t8-browser.py --port 7511 --user prova --password prova2026 --evidence DIR

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


def load(name, file):
    s = _iu.spec_from_file_location(name, file)
    m = _iu.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--port", type=int, required=True)
    a.add_argument("--host", default="127.0.0.1")
    a.add_argument("--user", default="prova")
    a.add_argument("--password", default=os.environ.get("REMOTIX_PASSWORD", ""))
    a.add_argument("--browser", choices=("chrome", "firefox"), default="chrome")
    a.add_argument("--benches", default=os.environ.get("REMOTIX_BENCHES", "/media/REMOTIX/src/controllo/banchi"))
    a.add_argument("--evidence", required=True)
    a.add_argument("--cap-s", type=int, default=90)
    a.add_argument("--wait-s", type=int, default=1200)
    a.add_argument("--window", default="1920x1080")
    a.add_argument("--base-port", type=int, default=3170)
    o = a.parse_args()
    VERI = load("veri", os.path.join(o.benches, "12-client-veri.py"))
    VERI.WINDOW[:] = [int(x) for x in o.window.split("x")]
    o.url = "https://%s:%d/" % (o.host, o.port)
    o.visible, o.save, o.leave_running = True, o.evidence, False
    os.makedirs(o.evidence, exist_ok=True)
    for f in ("pronto", "via"):
        try:
            os.remove(os.path.join(o.evidence, f))
        except FileNotFoundError:
            pass
    line = {"url": o.url, "browser": o.browser}
    outcome, code = "BLOCKED", 3
    g = None
    t0 = time.time()
    try:
        g = VERI.turn_on_driver(o.browser, o)
        pr = VERI.Test(g, o, o.url, o.password)
        ok, m = pr.do_open()
        if not ok:
            line["rationale"] = "the page does not open: " + m
            raise StopIteration
        e, m, _ = pr.enter(o.password)
        if e != VERI.GREEN:
            outcome, code, line["rationale"] = "FAIL", 1, "does not get in: " + m
            raise StopIteration
        e, m, _ = pr.first_frame()
        line["before"] = m
        if e != VERI.GREEN:
            outcome, code, line["rationale"] = "FAIL", 1, "before the upgrade the desktop is not visible: " + m
            raise StopIteration
        open(os.path.join(o.evidence, "pronto"), "w").write(str(time.time()))
        # connected during the upgrade: the painted frames, every second
        fine = time.time() + o.wait_s
        with open(os.path.join(o.evidence, "linea.jsonl"), "w") as lf:
            while time.time() < fine and not os.path.exists(os.path.join(o.evidence, "via")):
                s = pr.state()
                lf.write(json.dumps({"t": round(time.time(), 2), "painted": s.get("painted"),
                                     "on": s.get("on")}) + "\n")
                lf.flush()
                time.sleep(1)
        line["collegato_s"] = round(time.time() - t0, 1)
        if not os.path.exists(os.path.join(o.evidence, "via")):
            line["rationale"] = "no \"via\" within %d s" % o.wait_s
            raise StopIteration
        # the reattach: the tab reloaded, we re-enter, and the desktop must be seen again
        t1 = time.time()
        g.reload()
        ok, m = pr.do_open()
        e, m, _ = pr.enter(o.password)
        line["rientra"] = m
        if e != VERI.GREEN:
            outcome, code, line["rationale"] = "FAIL", 1, "after the upgrade it does not get back in: " + m
            raise StopIteration
        e, m, _ = pr.first_frame()
        line["after"] = m
        line["riattacco_s"] = round(time.time() - t1, 1)
        if e == VERI.GREEN:
            outcome, code, line["rationale"] = "PASS", 0, "desktop seen again after the upgrade"
        else:
            outcome, code, line["rationale"] = "FAIL", 1, "gets back in, but the desktop is not visible: " + m
    except StopIteration:
        pass
    except Exception as ex:                      # noqa: BLE001
        line["rationale"] = "the bench crashed: %r" % ex
    finally:
        if g is not None:
            try:
                g.close()
            except Exception:                    # noqa: BLE001
                pass
    line.update(outcome=outcome, seconds=round(time.time() - t0, 1))
    print("T8 " + json.dumps(line, ensure_ascii=False), flush=True)
    with open(os.path.join(o.evidence, "esito.json"), "w") as fh:
        json.dump(line, fh, ensure_ascii=False, indent=1)
    return code


if __name__ == "__main__":
    sys.exit(main())
