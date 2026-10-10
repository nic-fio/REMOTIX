#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
t8-browser — phase 17, T8 (R39, R11): a REAL browser stays connected to the desktop while REMOTIX is
upgraded (or rolled back) by the package manager, and then re-enters: the desktop is the SAME one.

    (on the server, inside the labwc of 17-t1c-guarda.sh: T1C_PROGRAM=…/t8-browser.py)
    python3 t8-browser.py --port 7511 --username prova --password prova2026 --evidence DIR

1. enters and sees the desktop (the pixel judge of 12-client-veri.py: a black canvas is RED);
   "before" photo; writes DIR/ready;
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


def load(label_name, file):
    s = _iu.spec_from_file_location(label_name, file)
    m = _iu.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--port", type=int, required=True)
    a.add_argument("--host", default="127.0.0.1")
    a.add_argument("--username", default="prova")
    a.add_argument("--password", default=os.environ.get("REMOTIX_PASSWORD", ""))
    a.add_argument("--browser", choices=("chrome", "firefox"), default="chrome")
    a.add_argument("--benches", default=os.environ.get("REMOTIX_BENCHES", "/media/REMOTIX/src/controllo/banchi"))
    a.add_argument("--evidence", required=True)
    a.add_argument("--cap-s", type=int, default=90)
    a.add_argument("--wait-s", type=int, default=1200)
    a.add_argument("--win", default="1920x1080")
    a.add_argument("--base-ports", type=int, default=3170)
    o = a.parse_args()
    REAL = load("genuine", os.path.join(o.benches, "12-client-veri.py"))
    REAL.WINDOW[:] = [int(x) for x in o.win.split("x")]
    o.url = "https://%s:%d/" % (o.host, o.port)
    o.is_visible, o.store, o.leave_on = True, o.evidence, False
    os.makedirs(o.evidence, exist_ok=True)
    for f in ("ready", "via"):
        try:
            os.remove(os.path.join(o.evidence, f))
        except FileNotFoundError:
            pass
    row = {"url": o.url, "browser": o.browser}
    outcome, code_v = "BLOCKED", 3
    g = None
    t0 = time.time()
    try:
        g = REAL.turn_on_driver(o.browser, o)
        pr = REAL.Test(g, o, o.url, o.password)
        ok, m = pr.open_it()
        if not ok:
            row["rationale"] = "the page does not open: " + m
            raise StopIteration
        e, m, _ = pr.enter(o.password)
        if e != REAL.GREEN:
            outcome, code_v, row["rationale"] = "FAIL", 1, "does not get in: " + m
            raise StopIteration
        e, m, _ = pr.first_frame()
        row["before"] = m
        if e != REAL.GREEN:
            outcome, code_v, row["rationale"] = "FAIL", 1, "before the upgrade the desktop is not visible: " + m
            raise StopIteration
        open(os.path.join(o.evidence, "ready"), "w").write(str(time.time()))
        # connected during the upgrade: the painted frames, every second
        fine = time.time() + o.wait_s
        with open(os.path.join(o.evidence, "linea.jsonl"), "w") as lf:
            while time.time() < fine and not os.path.exists(os.path.join(o.evidence, "via")):
                s = pr.state()
                lf.write(json.dumps({"t": round(time.time(), 2), "painted": s.get("painted"),
                                     "lit": s.get("lit")}) + "\n")
                lf.flush()
                time.sleep(1)
        row["collegato_s"] = round(time.time() - t0, 1)
        if not os.path.exists(os.path.join(o.evidence, "via")):
            row["rationale"] = "no \"via\" within %d s" % o.wait_s
            raise StopIteration
        # the reattach: the tab reloaded, we re-enter, and the desktop must be seen again
        t1 = time.time()
        g.reload()
        ok, m = pr.open_it()
        e, m, _ = pr.enter(o.password)
        row["reenter"] = m
        if e != REAL.GREEN:
            outcome, code_v, row["rationale"] = "FAIL", 1, "after the upgrade it does not get back in: " + m
            raise StopIteration
        e, m, _ = pr.first_frame()
        row["after"] = m
        row["riattacco_s"] = round(time.time() - t1, 1)
        if e == REAL.GREEN:
            outcome, code_v, row["rationale"] = "PASS", 0, "desktop seen again after the upgrade"
        else:
            outcome, code_v, row["rationale"] = "FAIL", 1, "gets back in, but the desktop is not visible: " + m
    except StopIteration:
        pass
    except Exception as ex:                      # noqa: BLE001
        row["rationale"] = "the bench crashed: %r" % ex
    finally:
        if g is not None:
            try:
                g.shut()
            except Exception:                    # noqa: BLE001
                pass
    row.update(outcome=outcome, seconds=round(time.time() - t0, 1))
    print("T8 " + json.dumps(row, ensure_ascii=False), flush=True)
    with open(os.path.join(o.evidence, "esito.json"), "w") as fh:
        json.dump(row, fh, ensure_ascii=False, indent=1)
    return code_v


if __name__ == "__main__":
    sys.exit(main())
