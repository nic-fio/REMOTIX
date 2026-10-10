#!/usr/bin/env python3
# T7 phase 17 — upgrading without closing the desktops: R7, R8 (the four times), R9.
# Runs ON THE SERVER as nicfio, in the environment of lancia.sh (real browsers in the suite's
# labwc), with the boxes' lock ALREADY taken by t7-campagna.sh.
#
#   python3 t7-aggiorna.py DESKTOP MODE
#     MODE aggiornamento : desktops born with the OLD binary (4fb3287d, previous PAM);
#                          then NEW binary + the product's PAM and restart with
#                          --tetto-sessioni 2; a THIRD user must stay out
#     MODE riavvio       : desktops born with the NEW binary; restart as the box
#                          does it; the second user has the GPU groups removed
#                          before the restart (the terminate-user guard)
#   env: T7_NUOVO=<short md5 of the new binary, in prodotto/remotix.<md5>>
#        T7_WL_FIREFOX, T7_WL_CHROME, T7_WL_TERZO = the labwc sockets for the browsers
import base64
import json
import os
import subprocess
import sys
import threading
import time

sys.path.insert(0, "/media/REMOTIX/src/controllo/banchi/15-suite")
D, MODO = sys.argv[1], sys.argv[2]
sys.argv = [sys.argv[0], "--scatola", D, "--browser", "firefox"]
import suite as S                                                     # noqa: E402

BASE = "/media/REMOTIX/tmp/t7"
R = "/media/REMOTIX/rete11"
P = R + "/prodotto"
BOX = "rete11-" + D
VECCHIO = "4fb3287d"
NUOVO = os.environ["T7_NUOVO"]
PAM_NUOVO = BASE + "/remotix.pam"
PAM_PRIMA = BASE + "/remotix.pam.prima"
EV = os.path.join(BASE, "%s-%s" % (D, MODO))
os.makedirs(EV, exist_ok=True)


def log(m):
    print("%s [%s %s] %s" % (time.strftime("%H:%M:%S"), D, MODO, m), flush=True)


def sudo(cmd, t=300):
    r = subprocess.run(["sudo", "-S", "-p", "", "sh", "-c", cmd], input=S._parola_sudo(),
                       capture_output=True, text=True, errors="replace", timeout=t)
    return r.returncode, (r.stdout + r.stderr)


def dentro(cmd, t=60):
    return sudo("podman exec %s sh -c %s" % (BOX, S._q(cmd)), t)


def scrivi(nome, testo):
    with open(os.path.join(EV, nome), "w") as f:
        f.write(testo if isinstance(testo, str) else json.dumps(testo, indent=1, ensure_ascii=False))


def prodotto(md5, pam):
    c, t = sudo("rm -f %s/remotix; cp %s/remotix.%s %s/remotix; cp %s %s/remotix.pam; "
                "bash %s/11-accendi.sh prodotto %s 2>&1 | tail -2" % (P, P, md5, P, pam, P, R, D))
    c2, t2 = dentro("md5sum /opt/remotix/remotix /etc/pam.d/remotix")
    log("product %s: %s" % (md5, t2.replace("\n", " · ")))
    return t2


def server(tetto=None):
    amb = "env REMOTIX_TETTO_SESSIONI=%d " % tetto if tetto else ""
    c, t = sudo("%sbash %s/11-accendi.sh server %s 2>&1 | tail -3" % (amb, R, D), 180)
    log("server: rc %s %s" % (c, t.strip().replace("\n", " · ")[-200:]))
    return c


def ora_box():
    return float(dentro("date +%s.%N", 20)[1].strip().splitlines()[-1])


def fotografia(u):
    c, t = dentro("python3 /tmp/t7box.py foto %s" % u, 60)
    try:
        return json.loads(t.strip().splitlines()[-1])
    except Exception:                            # noqa: BLE001
        return {"errore": t[-300:]}


ORA = "#!/bin/sh\nf=$HOME/ora-$1.txt\nwhile :; do date +%s.%N >> $f; sleep 1; done\n"
TERMINALE = {
    "gnome": "gnome-terminal -- sh $HOME/t7-ora.sh terminale",
    "kde": "systemd-run --user --scope --unit=app-t7-konsole konsole -e sh $HOME/t7-ora.sh terminale",
    "xfce": "xfce4-terminal -x sh $HOME/t7-ora.sh terminale",
    "lxqt": "qterminal -e 'sh $HOME/t7-ora.sh terminale'",
}


def testimoni(s):
    u = s.chi
    dentro("echo %s | base64 -d > /home/%s/t7-ora.sh; chown %s /home/%s/t7-ora.sh"
           % (base64.b64encode(ORA.encode()).decode(), u, u, u), 30)
    s.nella_sessione(TERMINALE[D])
    s.nella_sessione("sh $HOME/t7-ora.sh sessione")
    s.nella_sessione("systemd-run --user --scope --unit=t7-testimone-utente sh $HOME/t7-ora.sh utente")
    time.sleep(4)
    # whoever stayed in init.scope (launched by podman exec) goes into the session's
    # scope: it is where the desktop panel would put it (as in T2)
    c, t = dentro(
        "uid=$(id -u %(u)s); sc=$(loginctl show-session $(loginctl list-sessions --no-legend "
        "| awk -v uid=$uid '$2==uid && $6==\"user\"{print $1}' | head -1) -p Scope --value); "
        "cg=/sys/fs/cgroup/user.slice/user-$uid.slice/$sc; "
        "for p in $(ps -u %(u)s -o pid=); do grep -qx 0::/init.scope /proc/$p/cgroup 2>/dev/null && "
        "{ echo $p > $cg/cgroup.procs && echo moved $p $(cat /proc/$p/comm); }; done" % {"u": u}, 30)
    log("witnesses of %s: %s" % (u, t.strip().replace("\n", " · ")))


def buchi(u, t0):
    """The longest gap between two beats of each witness, from t0 - 5 s."""
    c, t = dentro("for f in /home/%s/ora-*.txt; do echo \"== $f\"; cat $f; done" % u, 30)
    ris, nome, prec = {}, None, None
    for r in t.splitlines():
        if r.startswith("== "):
            nome, prec = r.split("ora-")[-1].replace(".txt", ""), None
            ris[nome] = {"buco_max_s": 0.0, "battiti": 0, "ultimo": None}
            continue
        try:
            v = float(r.strip())
        except ValueError:
            continue
        if v < t0 - 5:
            prec = v
            continue
        if prec is not None:
            ris[nome]["buco_max_s"] = round(max(ris[nome]["buco_max_s"], v - prec), 2)
        ris[nome]["battiti"] += 1
        ris[nome]["ultimo"] = v
        prec = v
    return ris


def giornale(t0):
    c, t = dentro("journalctl -o short-unix --no-pager --since @%d" % int(t0 - 1), 60)
    scrivi("journal.txt", t)
    return t.splitlines()


def primo(righe, pezzo, dopo=0.0):
    for r in righe:
        if pezzo in r:
            try:
                v = float(r.split()[0])
            except ValueError:
                continue
            if v >= dopo:
                return v, r
    return None, ""


PERSI_IGNORA = {"sleep", "date", "remotix", "runuser", "(sd-pam)"}


def sessione_con(o, nnn, esiti, wl):
    os.environ["WAYLAND_DISPLAY"] = wl
    return S.Sessione(o, nnn, esiti)


def main():
    E = S.Esiti(S.argomenti("t7"))
    o1 = S.argomenti("t7")
    o1.evidenze = EV
    o2 = S.argomenti("t7")
    o2.browser, o2.evidenze = "chrome", EV
    wl_ff, wl_cr = os.environ["T7_WL_FIREFOX"], os.environ["T7_WL_CHROME"]
    esito = {"desktop": D, "modo": MODO}
    sudo("podman cp %s/t7box.py %s:/tmp/t7box.py" % (BASE, BOX))

    # 1. the binary the desktops are born with
    if MODO == "aggiornamento":
        esito["prima"] = prodotto(VECCHIO, PAM_PRIMA)
    else:
        esito["prima"] = prodotto(NUOVO, PAM_NUOVO)
    if server() != 0:
        esito["esito"] = "server did not start"
        return esito

    s1 = sessione_con(o1, "971", E, wl_ff).__enter__()
    try:
        s2 = sessione_con(o2, "972", E, wl_cr).__enter__()
    except Exception:
        s1.__exit__(None, None, None)
        raise
    try:
        for s in (s1, s2):
            ok, m = s.entra()
            log("%s (%s) enters: %s %s" % (s.chi, s.o.browser, ok, m[:100]))
            if not ok:
                esito["esito"] = "enter failed: %s %s" % (s.chi, m)
                return esito
        time.sleep(8)
        for s in (s1, s2):
            testimoni(s)
        time.sleep(3)
        prima = {s.chi: fotografia(s.chi) for s in (s1, s2)}
        scrivi("prima.json", prima)
        for s in (s1, s2):
            s.foto("prima-" + s.chi)
            log("%s: stage before %s" % (s.chi, prima[s.chi].get("palco")))
        if MODO == "riavvio":
            # the `terminate-user` guard: at re-entry the product will have to
            # put s2 back in the GPU groups, and NOT bring down their desktop
            c, t = dentro("for g in $(stat -c %%G /dev/dri/* | sort -u); do gpasswd -d %s $g "
                          ">/dev/null 2>&1 && echo removed $g; done; id %s" % (s2.chi, s2.chi))
            log("GPU groups removed from %s: %s" % (s2.chi, t.strip().replace("\n", " · ")))
            esito["gruppi_tolti"] = t.strip()

        # 2. the restart (and in the upgrade, first, the new binary)
        if MODO == "aggiornamento":
            esito["dopo"] = prodotto(NUOVO, PAM_NUOVO)
        t0 = ora_box()
        rc = server(2 if MODO == "aggiornamento" else None)
        t1 = ora_box()
        righe = giornale(t0)
        t_pronto, _ = primo(righe, "ready: https", t0)
        t_avvio, r_avvio = primo(righe, "Started rete11-server", t0)
        t_ritr, r_ritr = primo(righe, "live REMOTIX desktops found again at startup", t0)
        ritrovati = [r for r in righe if "FOUND AGAIN the desktop of" in r]
        esito["a_servizio_fermo_s"] = round(t_pronto - t0, 2) if t_pronto else None
        esito["c_ritrovata_dall_avvio_s"] = round(t_ritr - t_avvio, 3) if t_ritr and t_avvio else None
        esito["c_ritrovata_dallo_stop_s"] = round(t_ritr - t0, 2) if t_ritr else None
        esito["riga_ritrovati"] = r_ritr[r_ritr.find("live REMOTIX desktops"):][:220]
        esito["ritrovati"] = [r[r.find("FOUND AGAIN"):][:200] for r in ritrovati]
        log("found again: %s" % esito["riga_ritrovati"])

        # 3. the cap counts them: a third user, with --tetto-sessioni 2, stays out
        if MODO == "aggiornamento":
            o3 = S.argomenti("t7")
            o3.evidenze, o3.porte_base = EV, o3.porte_base + 4
            with sessione_con(o3, "973", E, os.environ["T7_WL_TERZO"]) as s3:
                ok3, m3 = s3.entra()
                time.sleep(2)
                c, t = dentro("journalctl -o cat --no-pager --since @%d | grep -a '%s' | "
                              "grep -a 'will NOT have' | head -2" % (int(t0), s3.chi), 30)
                esito["tetto_terzo_entra"] = ok3
                esito["tetto_terzo_riga"] = t.strip()[:300]
                log("third user %s: enters=%s — %s" % (s3.chi, ok3, t.strip()[:200]))

        # 4. the reattach: the two together, each with their browser (the tab reloaded)
        tempi = {}

        def rientra(s):
            a = time.time()
            ok, m = s.entra()
            tempi[s.chi] = (ok, m[:120], time.time() - a, time.time())
        tt = [threading.Thread(target=rientra, args=(s,)) for s in (s1, s2)]
        tr0 = time.time()
        for t_ in tt:
            t_.start()
        for t_ in tt:
            t_.join(240)
        for s in (s1, s2):
            ok, m, dur, fine = tempi.get(s.chi, (False, "no answer", None, None))
            esito["d_%s_%s" % (s.o.browser, s.chi)] = {
                "entra": ok, "motivo": m, "riattacco_s": round(dur, 2) if dur else None,
                "dallo_stop_s": round(fine - tr0 + (t1 - t0), 2) if fine else None}
            log("%s re-enters: %s in %s s — %s" % (s.chi, ok, dur and round(dur, 2), m[:80]))
        time.sleep(10)
        dopo = {s.chi: fotografia(s.chi) for s in (s1, s2)}
        scrivi("dopo.json", dopo)
        righe = giornale(t0)
        for s in (s1, s2):
            s.foto("dopo-" + s.chi)
            p0 = [x["pid"] for x in prima[s.chi].get("palco", [])]
            p1 = [x["pid"] for x in dopo[s.chi].get("palco", [])]
            vivi = {x["pid"] for x in dopo[s.chi].get("processi", [])}
            persi = [x for x in prima[s.chi].get("processi", [])
                     if x["pid"] not in vivi and x["comm"] not in PERSI_IGNORA
                     and not x["cg"].endswith("/init.scope")]
            rientro = [r for r in righe if "COMES BACK to their desktop" in r and s.chi in r]
            esito["b_%s" % s.chi] = {
                "palco_prima": p0, "palco_dopo": p1, "palco_uguale": bool(p0) and p0 == p1,
                "processi_persi": [(x["pid"], x["comm"]) for x in persi],
                "rientra_suo": any(("stage pid %d " % p) in r for p in p0 for r in rientro),
                "riga_rientro": rientro[0][rientro[0].find("COMES BACK"):][:200] if rientro else "",
                "testimoni": buchi(s.chi, t0)}
            log("%s: stage %s → %s, lost %s" % (s.chi, p0, p1, esito["b_%s" % s.chi]["processi_persi"]))
        if MODO == "riavvio":
            g = [r for r in righe if "user manager is NOT" in r or "user manager restarted" in r]
            esito["guardia_terminate_user"] = [r[r.find("«"):][:220] for r in g]
            c, t = dentro("id %s" % s2.chi)
            esito["gruppi_dopo"] = t.strip()
        c, t = dentro("journalctl -o cat --no-pager --since @%d | grep -a 'stage\\|ZERO MONITOR\\|virtual "
                      "monitor\\|RIPRESA\\|RESUMED\\|FOUND AGAIN\\|COMES BACK' | tail -60" % int(t0), 30)
        scrivi("righe-palco.txt", t)
        esito["esito"] = "fatto"
        return esito
    finally:
        s2.__exit__(None, None, None)
        s1.__exit__(None, None, None)


if __name__ == "__main__":
    try:
        e = main()
    except Exception as x:                       # noqa: BLE001
        import traceback
        traceback.print_exc()
        e = {"desktop": D, "modo": MODO, "esito": "CADUTO %r" % x}
    scrivi("esito.json", e)
    print("T7 " + json.dumps(e, ensure_ascii=False), flush=True)
