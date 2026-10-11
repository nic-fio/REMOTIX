#!/usr/bin/env python3
# T7 phase 17 — upgrading without closing the desktops: R7, R8 (the four times), R9.
# Runs ON THE SERVER as nicfio, in the environment of launch.sh (real browsers in the suite's
# labwc), with the boxes' lock ALREADY taken by t7-campaign.sh.
#
#   python3 t7-upgrade.py DESKTOP MODE
#     MODE update : desktops born with the OLD binary (4fb3287d, previous PAM);
#                          then NEW binary + the product's PAM and restart with
#                          --session-cap 2; a THIRD user must stay out
#     MODE restart       : desktops born with the NEW binary; restart as the box
#                          does it; the second user has the GPU groups removed
#                          before the restart (the terminate-user guard)
#   env: T7_NEW=<short md5 of the new binary, in prodotto/remotix.<md5>>
#        T7_WL_FIREFOX, T7_WL_CHROME, T7_WL_THIRD = the labwc sockets for the browsers
import base64
import json
import os
import subprocess
import sys
import threading
import time

sys.path.insert(0, "/media/REMOTIX/src/controllo/benches/15-suite")
D, MODE = sys.argv[1], sys.argv[2]
sys.argv = [sys.argv[0], "--box", D, "--browser", "firefox"]
import suite as S                                                     # noqa: E402

BASE = "/media/REMOTIX/tmp/t7"
R = "/media/REMOTIX/rete11"
P = R + "/prodotto"
BOX = "rete11-" + D
OLD = "4fb3287d"
NEW = os.environ["T7_NEW"]
PAM_NEW = BASE + "/remotix.pam"
PAM_BEFORE = BASE + "/remotix.pam.prima"
EV = os.path.join(BASE, "%s-%s" % (D, MODE))
os.makedirs(EV, exist_ok=True)


def log(m):
    print("%s [%s %s] %s" % (time.strftime("%H:%M:%S"), D, MODE, m), flush=True)


def sudo(cmd, t=300):
    r = subprocess.run(["sudo", "-S", "-p", "", "sh", "-c", cmd], input=S._sudo_password(),
                       capture_output=True, text=True, errors="replace", timeout=t)
    return r.returncode, (r.stdout + r.stderr)


def inside(cmd, t=60):
    return sudo("podman exec %s sh -c %s" % (BOX, S._q(cmd)), t)


def write(name, text):
    with open(os.path.join(EV, name), "w") as f:
        f.write(text if isinstance(text, str) else json.dumps(text, indent=1, ensure_ascii=False))


def product(md5, pam):
    c, t = sudo("rm -f %s/remotix; cp %s/remotix.%s %s/remotix; cp %s %s/remotix.pam; "
                "bash %s/11-start.sh product %s 2>&1 | tail -2" % (P, P, md5, P, pam, P, R, D))
    c2, t2 = inside("md5sum /opt/remotix/remotix /etc/pam.d/remotix")
    log("product %s: %s" % (md5, t2.replace("\n", " · ")))
    return t2


def server(cap=None):
    env = "env REMOTIX_SESSION_CAP=%d " % cap if cap else ""
    c, t = sudo("%sbash %s/11-start.sh server %s 2>&1 | tail -3" % (env, R, D), 180)
    log("server: rc %s %s" % (c, t.strip().replace("\n", " · ")[-200:]))
    return c


def now_box():
    return float(inside("date +%s.%N", 20)[1].strip().splitlines()[-1])


def snapshot(u):
    c, t = inside("python3 /tmp/t7box.py foto %s" % u, 60)
    try:
        return json.loads(t.strip().splitlines()[-1])
    except Exception:                            # noqa: BLE001
        return {"error": t[-300:]}


NOW = "#!/bin/sh\nf=$HOME/ora-$1.txt\nwhile :; do date +%s.%N >> $f; sleep 1; done\n"
TERMINAL = {
    "gnome": "gnome-terminal -- sh $HOME/t7-ora.sh terminale",
    "kde": "systemd-run --user --scope --unit=app-t7-konsole konsole -e sh $HOME/t7-ora.sh terminale",
    "xfce": "xfce4-terminal -x sh $HOME/t7-ora.sh terminale",
    "lxqt": "qterminal -e 'sh $HOME/t7-ora.sh terminale'",
}


def witnesses(s):
    u = s.chi
    inside("echo %s | base64 -d > /home/%s/t7-ora.sh; chown %s /home/%s/t7-ora.sh"
           % (base64.b64encode(NOW.encode()).decode(), u, u, u), 30)
    s.in_session(TERMINAL[D])
    s.in_session("sh $HOME/t7-ora.sh sessione")
    s.in_session("systemd-run --user --scope --unit=t7-testimone-utente sh $HOME/t7-ora.sh utente")
    time.sleep(4)
    # whoever stayed in init.scope (launched by podman exec) goes into the session's
    # scope: it is where the desktop panel would put it (as in T2)
    c, t = inside(
        "uid=$(id -u %(u)s); sc=$(loginctl show-session $(loginctl list-sessions --no-legend "
        "| awk -v uid=$uid '$2==uid && $6==\"user\"{print $1}' | head -1) -p Scope --value); "
        "cg=/sys/fs/cgroup/user.slice/user-$uid.slice/$sc; "
        "for p in $(ps -u %(u)s -o pid=); do grep -qx 0::/init.scope /proc/$p/cgroup 2>/dev/null && "
        "{ echo $p > $cg/cgroup.procs && echo moved $p $(cat /proc/$p/comm); }; done" % {"u": u}, 30)
    log("witnesses of %s: %s" % (u, t.strip().replace("\n", " · ")))


def holes(u, t0):
    """The longest gap between two beats of each witness, from t0 - 5 s."""
    c, t = inside("for f in /home/%s/ora-*.txt; do echo \"== $f\"; cat $f; done" % u, 30)
    result, name, prev = {}, None, None
    for r in t.splitlines():
        if r.startswith("== "):
            name, prev = r.split("ora-")[-1].replace(".txt", ""), None
            result[name] = {"buco_max_s": 0.0, "battiti": 0, "ultimo": None}
            continue
        try:
            v = float(r.strip())
        except ValueError:
            continue
        if v < t0 - 5:
            prev = v
            continue
        if prev is not None:
            result[name]["buco_max_s"] = round(max(result[name]["buco_max_s"], v - prev), 2)
        result[name]["battiti"] += 1
        result[name]["ultimo"] = v
        prev = v
    return result


def journal(t0):
    c, t = inside("journalctl -o short-unix --no-pager --since @%d" % int(t0 - 1), 60)
    write("journal.txt", t)
    return t.splitlines()


def first(lines, piece, dopo=0.0):
    for r in lines:
        if piece in r:
            try:
                v = float(r.split()[0])
            except ValueError:
                continue
            if v >= dopo:
                return v, r
    return None, ""


LOST_IGNORE = {"sleep", "date", "remotix", "runuser", "(sd-pam)"}


def session_with(o, nnn, outcomes, wl):
    os.environ["WAYLAND_DISPLAY"] = wl
    return S.Session(o, nnn, outcomes)


def main():
    E = S.Outcomes(S.call_args("t7"))
    o1 = S.call_args("t7")
    o1.evidence = EV
    o2 = S.call_args("t7")
    o2.browser, o2.evidence = "chrome", EV
    wl_ff, wl_cr = os.environ["T7_WL_FIREFOX"], os.environ["T7_WL_CHROME"]
    outcome = {"desktop": D, "modo": MODE}
    sudo("podman cp %s/t7box.py %s:/tmp/t7box.py" % (BASE, BOX))

    # 1. the binary the desktops are born with
    if MODE == "aggiornamento":
        outcome["before"] = product(OLD, PAM_BEFORE)
    else:
        outcome["before"] = product(NEW, PAM_NEW)
    if server() != 0:
        outcome["outcome"] = "server did not start"
        return outcome

    s1 = session_with(o1, "971", E, wl_ff).__enter__()
    try:
        s2 = session_with(o2, "972", E, wl_cr).__enter__()
    except Exception:
        s1.__exit__(None, None, None)
        raise
    try:
        for s in (s1, s2):
            ok, m = s.enter()
            log("%s (%s) enters: %s %s" % (s.chi, s.o.browser, ok, m[:100]))
            if not ok:
                outcome["outcome"] = "enter failed: %s %s" % (s.chi, m)
                return outcome
        time.sleep(8)
        for s in (s1, s2):
            witnesses(s)
        time.sleep(3)
        prima = {s.chi: snapshot(s.chi) for s in (s1, s2)}
        write("prima.json", prima)
        for s in (s1, s2):
            s.photo("prima-" + s.chi)
            log("%s: stage before %s" % (s.chi, prima[s.chi].get("stage")))
        if MODE == "riavvio":
            # the `terminate-user` guard: at re-entry the product will have to
            # put s2 back in the GPU groups, and NOT bring down their desktop
            c, t = inside("for g in $(stat -c %%G /dev/dri/* | sort -u); do gpasswd -d %s $g "
                          ">/dev/null 2>&1 && echo removed $g; done; id %s" % (s2.chi, s2.chi))
            log("GPU groups removed from %s: %s" % (s2.chi, t.strip().replace("\n", " · ")))
            outcome["gruppi_tolti"] = t.strip()

        # 2. the restart (and in the upgrade, first, the new binary)
        if MODE == "aggiornamento":
            outcome["after"] = product(NEW, PAM_NEW)
        t0 = now_box()
        rc = server(2 if MODE == "aggiornamento" else None)
        t1 = now_box()
        lines = journal(t0)
        t_ready, _ = first(lines, "ready: https", t0)
        t_startup, r_startup = first(lines, "Started rete11-server", t0)
        t_found_again, r_found_again = first(lines, "live REMOTIX desktops found again at startup", t0)
        found_again = [r for r in lines if "FOUND AGAIN the desktop of" in r]
        outcome["a_servizio_fermo_s"] = round(t_ready - t0, 2) if t_ready else None
        outcome["c_ritrovata_dall_avvio_s"] = round(t_found_again - t_startup, 3) if t_found_again and t_startup else None
        outcome["c_ritrovata_dallo_stop_s"] = round(t_found_again - t0, 2) if t_found_again else None
        outcome["riga_ritrovati"] = r_found_again[r_found_again.find("live REMOTIX desktops"):][:220]
        outcome["found_again"] = [r[r.find("FOUND AGAIN"):][:200] for r in found_again]
        log("found again: %s" % outcome["riga_ritrovati"])

        # 3. the cap counts them: a third user, with --session-cap 2, stays out
        if MODE == "aggiornamento":
            o3 = S.call_args("t7")
            o3.evidence, o3.ports_base = EV, o3.ports_base + 4
            with session_with(o3, "973", E, os.environ["T7_WL_THIRD"]) as s3:
                ok3, m3 = s3.enter()
                time.sleep(2)
                c, t = inside("journalctl -o cat --no-pager --since @%d | grep -a '%s' | "
                              "grep -a 'will NOT have' | head -2" % (int(t0), s3.chi), 30)
                outcome["tetto_terzo_entra"] = ok3
                outcome["tetto_terzo_riga"] = t.strip()[:300]
                log("third user %s: enters=%s — %s" % (s3.chi, ok3, t.strip()[:200]))

        # 4. the reattach: the two together, each with their browser (the tab reloaded)
        times = {}

        def reenter(s):
            a = time.time()
            ok, m = s.enter()
            times[s.chi] = (ok, m[:120], time.time() - a, time.time())
        tt = [threading.Thread(target=reenter, args=(s,)) for s in (s1, s2)]
        tr0 = time.time()
        for t_ in tt:
            t_.start()
        for t_ in tt:
            t_.join(240)
        for s in (s1, s2):
            ok, m, dur, fine = times.get(s.chi, (False, "no answer", None, None))
            outcome["d_%s_%s" % (s.o.browser, s.chi)] = {
                "entra": ok, "reason": m, "riattacco_s": round(dur, 2) if dur else None,
                "dallo_stop_s": round(fine - tr0 + (t1 - t0), 2) if fine else None}
            log("%s re-enters: %s in %s s — %s" % (s.chi, ok, dur and round(dur, 2), m[:80]))
        time.sleep(10)
        dopo = {s.chi: snapshot(s.chi) for s in (s1, s2)}
        write("dopo.json", dopo)
        lines = journal(t0)
        for s in (s1, s2):
            s.photo("dopo-" + s.chi)
            p0 = [x["pid"] for x in prima[s.chi].get("stage", [])]
            p1 = [x["pid"] for x in dopo[s.chi].get("stage", [])]
            living = {x["pid"] for x in dopo[s.chi].get("processes", [])}
            lost = [x for x in prima[s.chi].get("processes", [])
                     if x["pid"] not in living and x["comm"] not in LOST_IGNORE
                     and not x["cg"].endswith("/init.scope")]
            reentry = [r for r in lines if "COMES BACK to their desktop" in r and s.chi in r]
            outcome["b_%s" % s.chi] = {
                "palco_prima": p0, "palco_dopo": p1, "palco_uguale": bool(p0) and p0 == p1,
                "processi_persi": [(x["pid"], x["comm"]) for x in lost],
                "rientra_suo": any(("stage pid %d " % p) in r for p in p0 for r in reentry),
                "riga_rientro": reentry[0][reentry[0].find("COMES BACK"):][:200] if reentry else "",
                "testimoni": holes(s.chi, t0)}
            log("%s: stage %s → %s, lost %s" % (s.chi, p0, p1, outcome["b_%s" % s.chi]["processi_persi"]))
        if MODE == "riavvio":
            g = [r for r in lines if "user manager is NOT" in r or "user manager restarted" in r]
            outcome["guardia_terminate_user"] = [r[r.find("«"):][:220] for r in g]
            c, t = inside("id %s" % s2.chi)
            outcome["gruppi_dopo"] = t.strip()
        c, t = inside("journalctl -o cat --no-pager --since @%d | grep -a 'stage\\|ZERO MONITOR\\|virtual "
                      "monitor\\|RIPRESA\\|RESUMED\\|FOUND AGAIN\\|COMES BACK' | tail -60" % int(t0), 30)
        write("righe-palco.txt", t)
        outcome["outcome"] = "done"
        return outcome
    finally:
        s2.__exit__(None, None, None)
        s1.__exit__(None, None, None)


if __name__ == "__main__":
    try:
        e = main()
    except Exception as x:                       # noqa: BLE001
        import traceback
        traceback.print_exc()
        e = {"desktop": D, "modo": MODE, "outcome": "CADUTO %r" % x}
    write("esito.json", e)
    print("T7 " + json.dumps(e, ensure_ascii=False), flush=True)
