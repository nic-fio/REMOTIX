"""hold - log in from the browser (as lib.Rig does), then stay logged in for N seconds so that the box can be looked at from outside.

    RX_BANCO=vm python3 hold.py [seconds]          env: RX_USER (default bc1), RX_PASS (default bc1pass2026), RX_BOX (default gnome),
                                                   RX_KEEP=1 (do NOT end the user's existing sessions first: to try a remote login
                                                   while the same user has a LOCAL session, and to see what the product answers)
Writes /tmp/hold-ready when the desktop has arrived.  Not one of the checks: a bench helper for the step 2 and step 4 inspections."""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib  # noqa: E402

user, password = os.environ.get("RX_USER", "bc1"), os.environ.get("RX_PASS", "bc1pass2026")
if os.environ.get("RX_KEEP"):
    lib._made.add((os.environ.get("RX_BOX", "gnome"), user))   # what Rig does once per user (end_users + cleanup at exit) is skipped
rig = lib.Rig(os.environ.get("RX_BOX", "gnome"), "chrome", user, password, "hold", cap=60)
try:
    rig.start()
    rig.open_page()
    try:
        s = rig.login()
    except Exception as e:  # noqa: BLE001  - a refusal is an answer, not a crash
        print("login NOT admitted:", type(e).__name__, str(e)[:400], flush=True)
        raise SystemExit(3)
    print("login:", s["outcome"].strip(), flush=True)
    d = rig.settle(60)
    lib.save_png("hold-desktop.png", d["png"])
    print("desktop ok, holding", flush=True)
    open("/tmp/hold-ready", "w").write("1")
    time.sleep(int(sys.argv[1]) if len(sys.argv) > 1 else 120)
finally:
    rig.stop()
    print("stopped", flush=True)
