#!/usr/bin/env python3
# T7 fase 17 — aggiornare senza chiudere i desktop: R7, R8 (i quattro tempi), R9.
# Gira SUL SERVER come nicfio, nell'ambiente di lancia.sh (browser veri nei labwc
# della suite), con la serratura delle scatole GIA' presa da t7-campagna.sh.
#
#   python3 t7-aggiorna.py DESKTOP MODO
#     MODO aggiornamento : desktop nati col binario VECCHIO (4fb3287d, PAM di prima);
#                          poi binario NUOVO + PAM del prodotto e riavvio con
#                          --tetto-sessioni 2; un TERZO utente deve restare fuori
#     MODO riavvio       : desktop nati col binario NUOVO; riavvio come lo fa la
#                          scatola; al secondo utente si tolgono i gruppi della
#                          scheda prima del riavvio (la guardia di terminate-user)
#   env: T7_NUOVO=<md5 corto del binario nuovo, in prodotto/remotix.<md5>>
#        T7_WL_FIREFOX, T7_WL_CHROME, T7_WL_TERZO = i socket dei labwc per i browser
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
    log("prodotto %s: %s" % (md5, t2.replace("\n", " · ")))
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
    # chi e' rimasto in init.scope (lanciato da podman exec) va nella scope della
    # sessione: e' dove lo metterebbe il pannello del desktop (come T2)
    c, t = dentro(
        "uid=$(id -u %(u)s); sc=$(loginctl show-session $(loginctl list-sessions --no-legend "
        "| awk -v uid=$uid '$2==uid && $6==\"user\"{print $1}' | head -1) -p Scope --value); "
        "cg=/sys/fs/cgroup/user.slice/user-$uid.slice/$sc; "
        "for p in $(ps -u %(u)s -o pid=); do grep -qx 0::/init.scope /proc/$p/cgroup 2>/dev/null && "
        "{ echo $p > $cg/cgroup.procs && echo spostato $p $(cat /proc/$p/comm); }; done" % {"u": u}, 30)
    log("testimoni di %s: %s" % (u, t.strip().replace("\n", " · ")))


def buchi(u, t0):
    """Il buco piu' lungo fra due battiti di ciascun testimone, da t0 - 5 s."""
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

    # 1. il binario con cui nascono i desktop
    if MODO == "aggiornamento":
        esito["prima"] = prodotto(VECCHIO, PAM_PRIMA)
    else:
        esito["prima"] = prodotto(NUOVO, PAM_NUOVO)
    if server() != 0:
        esito["esito"] = "server non partito"
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
            log("%s (%s) entra: %s %s" % (s.chi, s.o.browser, ok, m[:100]))
            if not ok:
                esito["esito"] = "entra fallito: %s %s" % (s.chi, m)
                return esito
        time.sleep(8)
        for s in (s1, s2):
            testimoni(s)
        time.sleep(3)
        prima = {s.chi: fotografia(s.chi) for s in (s1, s2)}
        scrivi("prima.json", prima)
        for s in (s1, s2):
            s.foto("prima-" + s.chi)
            log("%s: palco prima %s" % (s.chi, prima[s.chi].get("palco")))
        if MODO == "riavvio":
            # la guardia di `terminate-user`: al rientro il prodotto dovra'
            # rimettere s2 nei gruppi della scheda, e NON buttargli giu' il desktop
            c, t = dentro("for g in $(stat -c %%G /dev/dri/* | sort -u); do gpasswd -d %s $g "
                          ">/dev/null 2>&1 && echo tolto $g; done; id %s" % (s2.chi, s2.chi))
            log("gruppi della scheda tolti a %s: %s" % (s2.chi, t.strip().replace("\n", " · ")))
            esito["gruppi_tolti"] = t.strip()

        # 2. il riavvio (e nell'aggiornamento, prima, il binario nuovo)
        if MODO == "aggiornamento":
            esito["dopo"] = prodotto(NUOVO, PAM_NUOVO)
        t0 = ora_box()
        rc = server(2 if MODO == "aggiornamento" else None)
        t1 = ora_box()
        righe = giornale(t0)
        t_pronto, _ = primo(righe, "pronto: https", t0)
        t_avvio, r_avvio = primo(righe, "Started rete11-server", t0)
        t_ritr, r_ritr = primo(righe, "desktop REMOTIX vivi ritrovati all'avvio", t0)
        ritrovati = [r for r in righe if "RITROVATO il desktop di" in r]
        esito["a_servizio_fermo_s"] = round(t_pronto - t0, 2) if t_pronto else None
        esito["c_ritrovata_dall_avvio_s"] = round(t_ritr - t_avvio, 3) if t_ritr and t_avvio else None
        esito["c_ritrovata_dallo_stop_s"] = round(t_ritr - t0, 2) if t_ritr else None
        esito["riga_ritrovati"] = r_ritr[r_ritr.find("desktop REMOTIX"):][:220]
        esito["ritrovati"] = [r[r.find("RITROVATO"):][:200] for r in ritrovati]
        log("ritrovati: %s" % esito["riga_ritrovati"])

        # 3. il tetto li conta: un terzo utente, con --tetto-sessioni 2, resta fuori
        if MODO == "aggiornamento":
            o3 = S.argomenti("t7")
            o3.evidenze, o3.porte_base = EV, o3.porte_base + 4
            with sessione_con(o3, "973", E, os.environ["T7_WL_TERZO"]) as s3:
                ok3, m3 = s3.entra()
                time.sleep(2)
                c, t = dentro("journalctl -o cat --no-pager --since @%d | grep -a '%s' | "
                              "grep -a 'NON avra' | head -2" % (int(t0), s3.chi), 30)
                esito["tetto_terzo_entra"] = ok3
                esito["tetto_terzo_riga"] = t.strip()[:300]
                log("terzo utente %s: entra=%s — %s" % (s3.chi, ok3, t.strip()[:200]))

        # 4. il riattacco: i due insieme, ciascuno col suo browser (la scheda ricaricata)
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
            ok, m, dur, fine = tempi.get(s.chi, (False, "nessuna risposta", None, None))
            esito["d_%s_%s" % (s.o.browser, s.chi)] = {
                "entra": ok, "motivo": m, "riattacco_s": round(dur, 2) if dur else None,
                "dallo_stop_s": round(fine - tr0 + (t1 - t0), 2) if fine else None}
            log("%s rientra: %s in %s s — %s" % (s.chi, ok, dur and round(dur, 2), m[:80]))
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
            rientro = [r for r in righe if "RIENTRA nel suo desktop" in r and s.chi in r]
            esito["b_%s" % s.chi] = {
                "palco_prima": p0, "palco_dopo": p1, "palco_uguale": bool(p0) and p0 == p1,
                "processi_persi": [(x["pid"], x["comm"]) for x in persi],
                "rientra_suo": any(("palco pid %d " % p) in r for p in p0 for r in rientro),
                "riga_rientro": rientro[0][rientro[0].find("RIENTRA"):][:200] if rientro else "",
                "testimoni": buchi(s.chi, t0)}
            log("%s: palco %s → %s, persi %s" % (s.chi, p0, p1, esito["b_%s" % s.chi]["processi_persi"]))
        if MODO == "riavvio":
            g = [r for r in righe if "NON si fa rinascere" in r or "gestore d'utente fatto rinascere" in r]
            esito["guardia_terminate_user"] = [r[r.find("«"):][:220] for r in g]
            c, t = dentro("id %s" % s2.chi)
            esito["gruppi_dopo"] = t.strip()
        c, t = dentro("journalctl -o cat --no-pager --since @%d | grep -a 'palco\\|ZERO MONITOR\\|monitor "
                      "virtuale\\|RIPRESA\\|RITROVAT\\|RIENTRA' | tail -60" % int(t0), 30)
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
