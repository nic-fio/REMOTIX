#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-h1 — REAL BROWSERS for the network hardening of 1.5 (Chrome and Firefox)

    python3 15-h1-browser-net-hardening.py --box xfce --browser chrome --case a,b,c,d,e,f [--fault] [--users 8]

(Normally launched by 15-h1-run.py, which sets the compositor of the desktop and
collects the verdicts of both browsers.)

Until now these parts of 1.5 had been proved only by unit tests and fuzz.  Here a REAL
Chrome / Firefox, in the headless labwc, against the box's SECOND product server
(`15-g7-server.sh`: unit rete15-g7, ports 8611-8614, verbose log) — never the 851x ones.
Every case starts that server again, so its log and its rate buckets begin empty.

  a  H-RETRY   QUIC Retry.  The browser logs in; the server log shows the Initial WITHOUT a
               token answered by a Retry and then «address validated with a Retry».
  b  H-RESET   Stateless Reset.  The server is KILLED (SIGKILL, no farewell) while the page is
               open and logged in, and started again.  The line is held mute (nft, as 15-f019)
               for the downtime so that no ICMP lets the browser notice by itself.  Once the
               server is back the browser's next packet gets a Stateless Reset and the page must
               SAY it within RESET_LIMIT_S (default 10 s), not at the 30 s of the idle clock.
  c  H-GROUPS  Key-exchange groups (branch tls-gruppi).  Login works with this browser, and
               openssl s_client on the TCP page: X25519MLKEM768, X25519, P-256, P-384 pass,
               ffdhe3072 and P-521 are refused.  Chrome: also the group it negotiated (CDP).
               BLOCKED if the product has no restriction (string absent from the binary).
  d  H-RATE    Handshake rate (branch handshake-ritmo).  N tenants (default 8), N browsers of
               this type, all pages open; then the N logins are sent at the same instant from
               the same address.  All must be admitted and the server log must have no
               «HANDSHAKE RATE» line.  BLOCKED if the product has no such limit.
  e  H-PAGE    Page bucket (branch pagina-secchio).  Normal use from the same address: the
               browser reloads the page --pages times (1.5 s apart) and logs in, curl asks
               for the page --curl-n times (0.4 s apart): never a 503, no «answered 503 busy»
               in the server's summary line.  FAULT: 60 curl at once must show the bucket
               biting (some answer other than 200), else the judge is blind.
  f  H-MOVE    Network change, simulated.  A browser does not move by itself in the headless
               labwc, so a small UDP/TCP proxy (this process) stands between browser and
               server and, mid-session, makes the server see another source: first another
               PORT, then another ADDRESS (127.0.0.2).  Per step: the server writes «MOVED to …
               new path validated», the moving scene is still moving in the photos, and the page
               did not say the line dropped.  FAULT (real): the proxy swallows everything after
               a move ⇒ the judge must say FAIL.
               ⚠ It tests the SERVER side of the migration (§2.3), not the browser's own.

Verdicts: PASS / FAIL / BLOCKED (BLOCKED = could not look, with the reason).  A fault pass
that does NOT give red is a FAIL of the test.  Faults of a, b, c, d use the judge on doctored
evidence (declared: they prove the judge can give red); those of e and f are real.

    --certify   only the pure functions (the judges), no box, no browser
"""
import copy
import os
import re
import socket
import subprocess
import sys
import threading
import time
import traceback
import importlib.util as _iu

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suite as S                                                     # noqa: E402

_s = _iu.spec_from_file_location("g7comune", os.path.join(S.HERE, "15-g7-common.py"))
G7 = _iu.module_from_spec(_s)
_s.loader.exec_module(G7)
G7.local_box(S)

CASE_FN = {"a": "H-RETRY", "b": "H-RESET", "c": "H-GROUPS", "d": "H-RATE", "e": "H-PAGE", "f": "H-MOVE"}
ALL_CASES = "a,b,c,d,e,f"
RESET_LIMIT_S = 10          # after the server is back; the idle clock is 30 s
RESET_OBSERVE_S = 45


def _chosen():
    """The cases asked for, read BEFORE the common parser (the list of the functions that
    `S.run` turns into BLOCKED when not judged depends on it)."""
    v = ALL_CASES
    for i, a in enumerate(sys.argv):
        if a == "--case" and i + 1 < len(sys.argv):
            v = sys.argv[i + 1]
        elif a.startswith("--case="):
            v = a.split("=", 1)[1]
    return [c for c in v.split(",") if c in CASE_FN]


FUNCTIONS = tuple(CASE_FN[c] for c in _chosen())


def extra(a):
    a.add_argument("--case", default=ALL_CASES, help="a,b,c,d,e,f (default all)")
    a.add_argument("--users", type=int, default=8, help="case d: tenants/browsers (default 8)")
    a.add_argument("--pages", type=int, default=10, help="case e: reloads of the page")
    a.add_argument("--curl-n", type=int, default=20, help="case e: sequential curl")
    a.add_argument("--reset-limit-s", type=int, default=RESET_LIMIT_S)


# ═══════════════════════════════════════════════════════════════════════════
#  THE JUDGES — pure
# ═══════════════════════════════════════════════════════════════════════════
def count(lines, needle):
    return sum(1 for r in lines if needle in r)


def judge_retry(admitted, why, lines):
    n_retry = count(lines, "Initial without a token: Retry sent")
    n_ok = count(lines, "address validated with a Retry")
    if not admitted:
        return S.FAIL, "with the Retry in front the login does not work: %s (Retry sent %d, validated %d)" % (
            why, n_retry, n_ok)
    if n_retry == 0 or n_ok == 0:
        return S.FAIL, ("login works but the log shows no Retry (sent %d, validated %d): "
                        "the browser did not go through the address validation" % (n_retry, n_ok))
    return S.PASS, "admitted after %d Retry sent and %d validated (%s)" % (n_retry, n_ok, why[:60])


def judge_reset(said_after_s, said_before_back, n_reset, limit_s):
    """`said_after_s`: seconds from the server being back to the page saying it (None = never)."""
    if said_before_back:
        return S.BLOCKED, ("the page said the line dropped BEFORE the server was back: the Stateless "
                           "Reset was not exercised (browser's own timer)")
    if said_after_s is None:
        return S.FAIL, ("the page did NOT say it in %d s after the restart (reset lines in the log: %d)"
                        % (RESET_OBSERVE_S, n_reset))
    if n_reset == 0:
        return S.FAIL, ("the page noticed after %.1f s but the server wrote no Stateless Reset: "
                        "it was something else" % said_after_s)
    if said_after_s > limit_s:
        return S.FAIL, "the page noticed after %.1f s (limit %d s; the idle clock is 30 s)" % (
            said_after_s, limit_s)
    return S.PASS, "page told after %.1f s from the restart, %d Stateless Reset sent" % (said_after_s, n_reset)


ALLOWED_GROUPS = ("X25519MLKEM768", "X25519", "P-256", "P-384")
REFUSED_GROUPS = ("ffdhe3072", "P-521")


def judge_groups(admitted, why, probes, lines, group_seen=""):
    """`probes[group]` = negotiated group (str), "" = refused, None = the client does not know it."""
    bad = []
    if not admitted:
        bad.append("login with the browser: %s" % why)
    for g in ALLOWED_GROUPS:
        r = probes.get(g)
        if r is None:
            continue
        if not r:
            bad.append("%s offered alone is refused (it must pass)" % g)
    for g in REFUSED_GROUPS:
        r = probes.get(g)
        if r:
            bad.append("%s offered alone is ACCEPTED (negotiated %s)" % (g, r))
    if not any(probes.get(g) for g in ALLOWED_GROUPS):
        return S.BLOCKED if not bad else S.FAIL, "; ".join(bad) or "no probe could be made"
    if bad:
        return S.FAIL, "; ".join(bad)
    ok = ", ".join("%s→%s" % (g, probes[g]) for g in ALLOWED_GROUPS if probes.get(g))
    no = ", ".join(g for g in REFUSED_GROUPS if probes.get(g) == "")
    mlkem = " · ML-KEM missing in this OpenSSL" if count(lines, "does not know the key-exchange groups") else ""
    return S.PASS, "browser in%s · pass: %s · refused: %s%s" % (
        " (negotiated %s)" % group_seen if group_seen else "", ok, no or "-", mlkem)


def judge_rate(results, lines, wanted):
    """`results`: [(outcome, message), ...] one per login."""
    n_green = sum(1 for e, _m in results if e == S.GREEN)
    n_rate = count(lines, "HANDSHAKE RATE")
    bad = []
    if len(results) != wanted:
        return S.BLOCKED, "only %d logins were sent out of %d" % (len(results), wanted)
    if n_green != wanted:
        bad.append("%d admitted out of %d (%s)" % (n_green, wanted, "; ".join(
            m[:70] for e, m in results if e != S.GREEN)[:240]))
    if n_rate:
        bad.append("%d «HANDSHAKE RATE» lines in the server log" % n_rate)
    if bad:
        return S.FAIL, "; ".join(bad)
    return S.PASS, "%d logins at once from one address: %d admitted, no rate refusal in the log" % (
        wanted, n_green)


def busy_503(lines):
    """Sum of the «N of them then answered 503 busy» of the page's pressure lines."""
    t = 0
    for r in lines:
        for m in re.finditer(r"(\d+) of them then answered 503 busy", r):
            t += int(m.group(1))
    return t


def judge_page(reloads, codes, final_login, lines):
    """`reloads`: [(opened, message, status|None)], `codes`: curl codes, `final_login`: (ok, message)."""
    bad = []
    for i, (ok, m, st) in enumerate(reloads):
        if not ok:
            bad.append("reload %d: %s" % (i + 1, m[:80]))
        if st is not None and st != 200:
            bad.append("reload %d answered %s" % (i + 1, st))
    other = [c for c in codes if c != "200"]
    if other:
        bad.append("%d curl out of %d did not get 200 (%s)" % (len(other), len(codes), ",".join(other[:8])))
    if not final_login[0]:
        bad.append("login after the reloads: %s" % final_login[1][:80])
    n = busy_503(lines)
    if n:
        bad.append("the server counts %d answers «503 busy»" % n)
    if bad:
        return S.FAIL, "; ".join(bad)
    return S.PASS, "%d reloads + login + %d curl, all fine; 503 busy: 0" % (len(reloads), len(codes))


def judge_move(steps):
    """`steps`: [{"name", "moved": bool, "refused": bool, "scene": True/False/None, "closed": bool}]."""
    bad, blind = [], []
    for st in steps:
        if not st["moved"]:
            bad.append("%s: no «MOVED to» in the server log%s" % (
                st["name"], " (path NOT validated)" if st.get("refused") else ""))
        if st["closed"]:
            bad.append("%s: the page told the line dropped" % st["name"])
        if st["scene"] is False:
            bad.append("%s: the scene stopped moving" % st["name"])
        elif st["scene"] is None:
            blind.append("%s: scene not photographable" % st["name"])
    if bad:
        return S.FAIL, "; ".join(bad)
    if blind:
        return S.BLOCKED, "; ".join(blind)
    return S.PASS, " · ".join("%s: moved, scene alive" % st["name"] for st in steps)


def certify():
    ok = True

    def prova(what, real):
        nonlocal ok
        ok &= bool(real)
        print("%s %s" % ("⭐" if real else "⛔", what))
    R = ["Initial without a token: Retry sent (95 bytes)", "address validated with a Retry"]
    prova("retry: log with both lines ⇒ PASS", judge_retry(True, "x", R)[0] == S.PASS)
    prova("retry: no Retry line ⇒ FAIL", judge_retry(True, "x", ["other"])[0] == S.FAIL)
    prova("retry: login fails ⇒ FAIL", judge_retry(False, "x", R)[0] == S.FAIL)
    prova("reset: told after 2 s with a reset ⇒ PASS", judge_reset(2.0, False, 1, 10)[0] == S.PASS)
    prova("reset: told after 30 s ⇒ FAIL", judge_reset(30.0, False, 1, 10)[0] == S.FAIL)
    prova("reset: never told ⇒ FAIL", judge_reset(None, False, 0, 10)[0] == S.FAIL)
    prova("reset: told but no reset in the log ⇒ FAIL", judge_reset(2.0, False, 0, 10)[0] == S.FAIL)
    prova("reset: told before the server was back ⇒ BLOCKED", judge_reset(1.0, True, 1, 10)[0] == S.BLOCKED)
    pr = {"X25519MLKEM768": "X25519MLKEM768", "X25519": "X25519", "P-256": "P-256", "P-384": "P-384",
          "ffdhe3072": "", "P-521": ""}
    prova("groups: allowed pass and others refused ⇒ PASS", judge_groups(True, "x", pr, [])[0] == S.PASS)
    prova("groups: ffdhe3072 accepted ⇒ FAIL", judge_groups(True, "x", dict(pr, ffdhe3072="ffdhe3072"), [])[0] == S.FAIL)
    prova("groups: X25519 refused ⇒ FAIL", judge_groups(True, "x", dict(pr, X25519=""), [])[0] == S.FAIL)
    prova("groups: browser login fails ⇒ FAIL", judge_groups(False, "x", pr, [])[0] == S.FAIL)
    prova("groups: client without ML-KEM, rest right ⇒ PASS",
          judge_groups(True, "x", dict(pr, X25519MLKEM768=None), [])[0] == S.PASS)
    g = [(S.GREEN, "ok")] * 8
    prova("rate: 8 of 8 and no line ⇒ PASS", judge_rate(g, [], 8)[0] == S.PASS)
    prova("rate: 7 of 8 ⇒ FAIL", judge_rate(g[:7] + [(S.RED, "no")], [], 8)[0] == S.FAIL)
    prova("rate: 8 of 8 but a rate line ⇒ FAIL", judge_rate(g, ["⚠ HANDSHAKE RATE: 3 new"], 8)[0] == S.FAIL)
    prova("rate: 5 logins sent of 8 ⇒ BLOCKED", judge_rate(g[:5], [], 8)[0] == S.BLOCKED)
    rl = [(True, "ok", 200)] * 3
    prova("page: all fine ⇒ PASS", judge_page(rl, ["200"] * 5, (True, "ok"), [])[0] == S.PASS)
    prova("page: a 503 from curl ⇒ FAIL", judge_page(rl, ["200", "503"], (True, "ok"), [])[0] == S.FAIL)
    prova("page: reload answered 503 ⇒ FAIL", judge_page([(True, "ok", 503)], [], (True, "ok"), [])[0] == S.FAIL)
    prova("page: form missing ⇒ FAIL", judge_page([(False, "no form", None)], [], (True, "ok"), [])[0] == S.FAIL)
    prova("page: «5 of them then answered 503 busy» ⇒ FAIL",
          judge_page(rl, [], (True, "ok"), ["... DELAYED: 7 over 4 ...; 5 of them then answered 503 busy after 3 s"])[0] == S.FAIL)
    prova("page: «0 of them then answered 503 busy» ⇒ PASS",
          judge_page(rl, [], (True, "ok"), ["... 0 of them then answered 503 busy after 3 s"])[0] == S.PASS)
    st = [{"name": "port", "moved": True, "scene": True, "closed": False},
          {"name": "address", "moved": True, "scene": True, "closed": False}]
    prova("move: both moves and scene alive ⇒ PASS", judge_move(st)[0] == S.PASS)
    prova("move: no MOVED ⇒ FAIL", judge_move([dict(st[0], moved=False)])[0] == S.FAIL)
    prova("move: scene stopped ⇒ FAIL", judge_move([dict(st[0], scene=False)])[0] == S.FAIL)
    prova("move: page told the drop ⇒ FAIL", judge_move([dict(st[0], closed=True)])[0] == S.FAIL)
    prova("move: scene not photographable ⇒ BLOCKED", judge_move([dict(st[0], scene=None)])[0] == S.BLOCKED)
    # the proxy: a UDP datagram goes through and back, and a rebind changes the source seen
    try:
        srv = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        srv.bind(("127.0.0.1", 0))
        srv.settimeout(3)
        px = MoveProxy(0, srv.getsockname()[1], bind_host="127.0.0.1")
        px.start()
        cli = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        cli.settimeout(3)
        cli.sendto(b"uno", ("127.0.0.1", px.lp))
        d1, a1 = srv.recvfrom(100)
        srv.sendto(b"eco", a1)
        back = cli.recvfrom(100)[0]
        px.rebind("127.0.0.2")
        cli.sendto(b"due", ("127.0.0.1", px.lp))
        d2, a2 = srv.recvfrom(100)
        px.blackhole = True
        cli.sendto(b"tre", ("127.0.0.1", px.lp))
        srv.settimeout(0.7)
        try:
            srv.recvfrom(100)
            swallowed = False
        except socket.timeout:
            swallowed = True
        px.close()
        prova("proxy: forward, return, new source after rebind, blackhole (%s → %s)" % (a1[0], a2[0]),
              d1 == b"uno" and back == b"eco" and d2 == b"due" and a2[0] == "127.0.0.2"
              and a1[1] != a2[1] and swallowed)
    except Exception as e:                       # noqa: BLE001
        prova("proxy: %r" % e, False)
    return 0 if ok else 1


# ═══════════════════════════════════════════════════════════════════════════
#  THE TOOLS
# ═══════════════════════════════════════════════════════════════════════════
def fresh_server(o):
    """Our server (rete15-g7) started again: log set aside, empty rate buckets."""
    ok, t = G7.server("start", o.box)
    if not ok:
        raise S.Blocked("our server (rete15-g7) does not start: %s" % (t or "")[-300:])
    return (t or "on").splitlines()[0]


def in_product(box, text):
    """Does the product installed in the box contain this text? (feature present in the binary)"""
    c, t = G7.inside(box, "grep -c -a -F -- '%s' /opt/remotix/remotix" % text, 30)
    try:
        return int((t or "0").split()[-1]) > 0
    except (ValueError, IndexError):
        return False


def nudge(s, k):
    """The mouse moves (a packet goes out), as whoever is in front of the screen would do."""
    try:
        x, y = s.pr.center(s.state(), 0.3 + 0.1 * (k % 4), 0.5)
        s.g.move_to(x, y)
    except Exception:                            # noqa: BLE001
        pass


def curl_code(url, timeout=10):
    try:
        r = subprocess.run(["curl", "-sk", "-o", "/dev/null", "-w", "%{http_code}", "--max-time", str(timeout), url],
                           capture_output=True, text=True, timeout=timeout + 5)
        return r.stdout.strip() or "000"
    except Exception:                            # noqa: BLE001
        return "000"


def doc_status(g, first=0):
    """Chrome only: the HTTP status of the page documents received after event `first`
    (list, new index); Firefox: ([], first)."""
    cdp = getattr(g, "cdp", None)
    if cdp is None:
        return [], first
    ev = cdp.events
    out = []
    for e in ev[first:]:
        if e.get("method") == "Network.responseReceived":
            p = e.get("params", {})
            if p.get("type") == "Document":
                out.append(p.get("response", {}).get("status"))
    return out, len(ev)


def chrome_group(g):
    """Chrome only: the key-exchange group of the page's TLS, from the CDP events."""
    cdp = getattr(g, "cdp", None)
    if cdp is None:
        return ""
    for e in cdp.events:
        if e.get("method") == "Network.responseReceived":
            d = e.get("params", {}).get("response", {}).get("securityDetails") or {}
            if d.get("keyExchangeGroup"):
                return d["keyExchangeGroup"]
    return ""


def openssl_group(host, port, group):
    """Negotiated TLS 1.3 group offering ONLY `group`: str; "" refused; None = unknown to the client."""
    try:
        r = subprocess.run(["openssl", "s_client", "-connect", "%s:%d" % (host, port), "-tls1_3", "-groups", group],
                           input=b"", capture_output=True, timeout=20)
    except Exception:                            # noqa: BLE001
        return None
    t = (r.stdout + r.stderr).decode("utf-8", "replace")
    m = re.search(r"Negotiated TLS1\.3 group:\s*(\S+)", t) or re.search(r"Server Temp Key:\s*(\S+)", t)
    if m:
        return m.group(1)
    if re.search(r"unsupported|unknown group|Error with command|bad group", t, re.I) and "alert" not in t:
        return None
    return ""


class MoveProxy:
    """A UDP + TCP relay between the browser and OUR server, in this process.  What the server
    sees is the relay's upstream socket: `rebind(ip)` gives every client a NEW upstream socket
    (new port, and from `ip`), exactly what a NAT re-binding or an interface change looks like
    to the server.  The browser does not notice: it keeps talking to the relay's address.
    `blackhole`: everything from the browser is swallowed (the fault)."""

    def __init__(self, listen_port, target_port, bind_host="0.0.0.0", target_host="127.0.0.1"):
        self.tp, self.th = target_port, target_host
        self.src = "127.0.0.1"
        self.blackhole = False
        self.done = threading.Event()
        self.lock = threading.Lock()
        self.up = {}
        self.udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp.bind((bind_host, listen_port))
        self.lp = self.udp.getsockname()[1]
        self.udp.settimeout(0.5)
        self.tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.tcp.bind((bind_host, self.lp))
        self.tcp.listen(64)
        self.tcp.settimeout(0.5)
        self.sent_up = self.sent_down = 0

    def start(self):
        threading.Thread(target=self._udp_in, daemon=True).start()
        threading.Thread(target=self._tcp_accept, daemon=True).start()

    def close(self):
        self.done.set()
        time.sleep(0.7)
        for x in [self.udp, self.tcp] + list(self.up.values()):
            try:
                x.close()
            except OSError:
                pass

    def _new_up(self, client):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind((self.src, 0))
        s.connect((self.th, self.tp))
        s.settimeout(0.5)
        threading.Thread(target=self._udp_back, args=(client, s), daemon=True).start()
        return s

    def _udp_in(self):
        while not self.done.is_set():
            try:
                data, client = self.udp.recvfrom(65535)
            except socket.timeout:
                continue
            except OSError:
                return
            if self.blackhole:
                continue
            with self.lock:
                up = self.up.get(client)
                if up is None:
                    up = self.up[client] = self._new_up(client)
            try:
                up.send(data)
                self.sent_up += 1
            except OSError:
                pass

    def _udp_back(self, client, s):
        while not self.done.is_set():
            try:
                data = s.recv(65535)
            except socket.timeout:
                if self.up.get(client) is not s:
                    return               # superseded by a rebind
                continue
            except OSError:
                return
            if self.up.get(client) is not s:
                return
            try:
                self.udp.sendto(data, client)
                self.sent_down += 1
            except OSError:
                pass

    def rebind(self, src):
        """From now on the server sees `src` and a new port."""
        with self.lock:
            self.src = src
            for client in list(self.up):
                old = self.up[client]
                self.up[client] = self._new_up(client)
                try:
                    old.close()
                except OSError:
                    pass

    def _tcp_accept(self):
        while not self.done.is_set():
            try:
                c, _a = self.tcp.accept()
            except socket.timeout:
                continue
            except OSError:
                return
            try:
                u = socket.create_connection((self.th, self.tp), timeout=10)
            except OSError:
                c.close()
                continue
            for a, b in ((c, u), (u, c)):
                threading.Thread(target=self._pump, args=(a, b), daemon=True).start()

    @staticmethod
    def _pump(a, b):
        try:
            while True:
                d = a.recv(65536)
                if not d:
                    break
                b.sendall(d)
        except OSError:
            pass
        finally:
            for x in (a, b):
                try:
                    x.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass


def save(s, name, lines):
    return s.save_text(name, lines) if s is not None else ""


# ═══════════════════════════════════════════════════════════════════════════
#  THE CASES
# ═══════════════════════════════════════════════════════════════════════════
def case_a(o, E):
    fresh_server(o)
    reg = G7.Log(o.box)
    sign = reg.lines()
    with S.Session(o, "110", E) as s:
        ok, m = s.enter()
        lines = reg.da(sign)
        ev = [save(s, "h-a-server.txt", lines), s.save_console()]
    e, r = judge_retry(ok, m, lines)
    E.put("H-RETRY", e, r, expected="login through the Retry; the log shows Retry sent and validated",
          observed="%d lines of the server since the start" % len(lines), evidence=ev)
    if o.fault:
        doctored = [x for x in lines if "Retry" not in x]
        e2, r2 = judge_retry(ok, m, doctored)
        E.fault("H-RETRY", e2 == S.FAIL, "log without the Retry lines ⇒ the judge says %s (%s)" % (e2, r2[:90]))


def case_b(o, E):
    fresh_server(o)
    reg = G7.Log(o.box)
    lm = G7.DeadLine(o.port)
    lm.remove()
    ev = []
    try:
        with S.Session(o, "111", E) as s:
            ok, m = s.enter()
            if not ok:
                raise S.Blocked("you cannot get in even with a healthy server: " + m)
            st0 = G7.page(s.g)
            if G7.page_says(st0):
                raise S.Blocked("the page already says the line dropped before the restart")
            print("   in: %s" % m, flush=True)
            # the line goes mute, the server is killed (no farewell) and started again
            lm.put()
            G7.inside(o.box, "systemctl kill --kill-who=main -s KILL rete15-g7", 30)
            for _ in range(20):
                c, t = G7.inside(o.box, "systemctl is-active rete15-g7", 15)
                if (t or "").strip() != "active":
                    break
                time.sleep(0.5)
            k = 0
            t_down = time.time()
            said_early = False
            while time.time() - t_down < 3:
                nudge(s, k)
                k += 1
                if G7.page_says(G7.page(s.g)):
                    said_early = True
                time.sleep(0.5)
            ok2, t2 = G7.server("start", o.box)
            t_back = time.time()
            removed = lm.remove()
            if not ok2:
                raise S.Blocked("our server does not start again: %s" % (t2 or "")[-200:])
            if not removed:
                raise S.Blocked("THE nft RULE CANNOT BE REMOVED")
            said_after = None
            while time.time() - t_back < RESET_OBSERVE_S:
                nudge(s, k)
                k += 1
                if G7.page_says(G7.page(s.g)):
                    said_after = time.time() - t_back
                    break
                time.sleep(0.5)
            lines = reg.da(0)
            n_reset = count(lines, "Stateless Reset of")
            final = G7.page(s.g)
            ev = [save(s, "h-b-server.txt", lines), save(s, "h-b-page.txt", [repr(final)]), s.save_console()]
            e, r = judge_reset(said_after, said_early, n_reset, o.reset_limit_s)
            E.put("H-RESET", e, r, expected="the page says it within %d s of the server being back (idle clock: 30 s)"
                  % o.reset_limit_s, observed=r, evidence=ev)
            if o.fault:
                e2, r2 = judge_reset(33.0, False, n_reset, o.reset_limit_s)
                e3, r3 = judge_reset(said_after, False, 0, o.reset_limit_s)
                E.fault("H-RESET", e2 == S.FAIL and e3 == S.FAIL,
                        "notice at 33 s ⇒ %s · notice with no reset in the log ⇒ %s" % (e2, e3))
    finally:
        lm.remove()


def case_c(o, E):
    if not in_product(o.box, "X25519MLKEM768"):
        raise S.Blocked("the product in the box has no key-exchange groups restriction (branch without tls-gruppi)")
    fresh_server(o)
    reg = G7.Log(o.box)
    sign = reg.lines()
    with S.Session(o, "112", E) as s:
        ok, m = s.enter()
        group_seen = chrome_group(s.g) if o.browser == "chrome" else ""
        probes = {g: openssl_group(o.host, o.port, g) for g in ALLOWED_GROUPS + REFUSED_GROUPS}
        lines = reg.da(sign)
        ev = [save(s, "h-c-server.txt", lines), save(s, "h-c-openssl.txt", ["%s: %r" % kv for kv in probes.items()]),
              s.save_console()]
    e, r = judge_groups(ok, m, probes, lines, group_seen)
    E.put("H-GROUPS", e, r, expected="the browser gets in; only X25519MLKEM768/X25519/P-256/P-384 are accepted",
          observed=r, evidence=ev)
    if o.fault:
        bad = dict(probes, ffdhe3072="ffdhe3072")
        e2, r2 = judge_groups(ok, m, bad, lines, group_seen)
        e3, r3 = judge_groups(False, "no login", probes, lines, group_seen)
        E.fault("H-GROUPS", e2 == S.FAIL and e3 == S.FAIL,
                "ffdhe3072 accepted ⇒ %s · login failed ⇒ %s" % (e2, e3))


def case_d(o, E):
    if not in_product(o.box, "HANDSHAKE RATE"):
        raise S.Blocked("the product in the box has no handshake rate limit (branch without handshake-ritmo)")
    n = o.users
    fresh_server(o)
    reg = G7.Log(o.box)
    sign = reg.lines()
    sessions = []
    results = [None] * n
    t0s = [0.0] * n
    try:
        for i in range(n):
            o2 = copy.copy(o)
            o2.base_port = o.base_port + 100 + 6 * i       # one pair of debug ports per browser
            o2.cap_s = 90
            o2.width, o2.height = 1280, 720
            if o.evidence:
                o2.evidence = os.path.join(o.evidence, "d%d" % i)
                os.makedirs(o2.evidence, exist_ok=True)
            s = S.Session(o2, "113", E)
            s.__enter__()
            sessions.append(s)
            ok, m = s.pr.do_open()
            if not ok:
                raise S.Blocked("browser %d: the page does not open: %s" % (i + 1, m))
            print("   %d/%d page open (%s)" % (i + 1, n, s.chi), flush=True)
        gate = threading.Barrier(n)

        def go(i):
            try:
                gate.wait(60)
                t0s[i] = time.time()
                e, m, _st = sessions[i].pr.enter(sessions[i].password)
                results[i] = (e, m)
            except Exception as ex:               # noqa: BLE001
                results[i] = (S.RED, "the bench: %r" % ex)
        th = [threading.Thread(target=go, args=(i,)) for i in range(n)]
        for t in th:
            t.start()
        for t in th:
            t.join(300)
        time.sleep(3)
        lines = reg.da(sign)
        spread = (max(t0s) - min(t0s)) if all(t0s) else -1
        res = [r or (S.RED, "no answer") for r in results]
        ev = [save(sessions[0], "h-d-server.txt", lines)]
        e, r = judge_rate(res, lines, n)
        r += " (the %d logins started within %.2f s; %d Retry validated)" % (
            n, spread, count(lines, "address validated with a Retry"))
        E.put("H-RATE", e, r, expected="%d logins from one address at the same time all admitted, no rate refusal" % n,
              observed=r, evidence=ev)
        if o.fault:
            e2, r2 = judge_rate(res[:-1] + [(S.RED, "refused")], lines, n)
            e3, r3 = judge_rate(res, lines + ["⚠ HANDSHAKE RATE: 3 new handshakes refused"], n)
            E.fault("H-RATE", e2 == S.FAIL and e3 == S.FAIL,
                    "one login refused ⇒ %s · a rate line in the log ⇒ %s" % (e2, e3))
    finally:
        for s in reversed(sessions):
            try:
                s.__exit__(None, None, None)
            except Exception as ex:               # noqa: BLE001
                print("   ⚠ exit of %s: %s" % (s.chi, ex))


def case_e(o, E):
    fresh_server(o)
    reg = G7.Log(o.box)
    sign = reg.lines()
    reloads, codes = [], []
    with S.Session(o, "114", E) as s:
        idx = 0
        for i in range(o.pages):
            ok, m = s.pr.do_open()
            st, idx = doc_status(s.g, idx)
            reloads.append((ok, m, st[-1] if st else None))
            time.sleep(1.5)
        fin = s.enter(do_open=False)
        for i in range(o.curl_n):
            codes.append(curl_code(o.url))
            time.sleep(0.4)
        time.sleep(11)                  # the pressure line is written at most every 10 s
        lines = reg.da(sign)
        e, r = judge_page(reloads, codes, fin, lines)
        ev = [save(s, "h-e-server.txt", lines), save(s, "h-e-curl.txt", [",".join(codes)]), s.save_console()]
        E.put("H-PAGE", e, r, expected="normal use from one address: no 503, the page always opens",
              observed=r, evidence=ev)
        if o.fault:
            time.sleep(6)               # the bucket refills
            from concurrent.futures import ThreadPoolExecutor
            with ThreadPoolExecutor(60) as ex:
                burst = list(ex.map(lambda _i: curl_code(o.url, 12), range(60)))
            non200 = [c for c in burst if c != "200"]
            E.fault("H-PAGE", len(non200) > 0,
                    "60 requests at once from one address ⇒ %d not 200 (%s): the bucket %s"
                    % (len(non200), ",".join(sorted(set(non200))) or "-",
                       "bites" if non200 else "did NOT bite: the judge could not see a 503"))


def case_f(o, E):
    fresh_server(o)
    reg = G7.Log(o.box)
    proxy = MoveProxy(o.port + 80, o.port)
    proxy.start()
    o2 = copy.copy(o)
    o2.url = "https://%s:%d/" % (o.host, proxy.lp)
    try:
        with S.Session(o2, "115", E) as s:
            ok, m = s.enter()
            if not ok:
                raise S.Blocked("CONTROL: the login through the neutral relay does not work (not a product "
                                "verdict): %s" % m)
            pid, t = G7.launch_scene(s)
            if not pid:
                raise S.Blocked("the moving scene does not start: " + t)
            alive, t = G7.wait_scene(s, S)
            if not alive:
                raise S.Blocked("before the move: " + t)
            print("   in through the relay, scene alive; moving the source of the server's view", flush=True)

            def step(name, ip, black=False):
                sign = reg.lines()
                proxy.blackhole = black
                proxy.rebind(ip)
                t0 = time.time()
                moved = refused = False
                k = 0
                while time.time() - t0 < 20 and not moved:
                    nudge(s, k)
                    k += 1
                    new = reg.da(sign)
                    moved = any("MOVED to" in x for x in new)
                    refused = refused or any("was NOT validated" in x for x in new)
                    if black and time.time() - t0 > 8:
                        break
                    time.sleep(1)
                time.sleep(2)
                new = reg.da(sign)
                moves, d, evs = G7.scene_moves(s, "h-f-%s" % name)
                closed = G7.page_says(G7.page(s.g)) is True
                print("   %s (%s): moved=%s refused=%s scene=%s closed=%s · %s" % (
                    name, ip, moved, refused, moves, closed, d), flush=True)
                return {"name": name, "moved": moved, "refused": refused, "scene": moves, "closed": closed,
                        "lines": new, "evidence": evs}
            st = [step("another port", "127.0.0.1"), step("another address", "127.0.0.2")]
            lines = reg.da(0)
            ev = [save(s, "h-f-server.txt", lines), s.save_console()] + [x for q in st for x in q["evidence"]]
            e, r = judge_move(st)
            E.put("H-MOVE", e, r, expected="after a new source port and a new address the server writes «MOVED to» "
                  "and the session goes on", observed=r, evidence=ev)
            if o.fault:
                bad = step("swallowed", "127.0.0.3", black=True)
                e2, r2 = judge_move([bad])
                E.fault("H-MOVE", e2 == S.FAIL,
                        "the relay swallows everything after a move ⇒ the judge says %s (%s)" % (e2, r2[:100]))
    finally:
        proxy.close()


CASES = {"a": case_a, "b": case_b, "c": case_c, "d": case_d, "e": case_e, "f": case_f}


def body(o, E):
    if not o.port:
        o.port = G7.PORTS_G7[o.box]
    if o.port != G7.PORTS_G7[o.box]:
        raise S.Blocked("port %d is not our server's (%d)" % (o.port, G7.PORTS_G7[o.box]))
    o.url = "https://%s:%d/" % (o.host, o.port)
    before = G7.inside(o.box, "systemctl is-active rete11-server; systemctl show -p MainPID --value rete11-server", 30)[1]
    try:
        for c in _chosen():
            fn = CASE_FN[c]
            print("── case %s · %s ──" % (c, fn), flush=True)
            try:
                CASES[c](copy.copy(o), E)
            except S.Blocked as b:
                E.put(fn, S.BLOCKED, str(b))
                if o.fault:
                    E.put(fn, S.BLOCKED, str(b), passed="fault")
            except Exception as ex:               # noqa: BLE001
                print(traceback.format_exc())
                E.put(fn, S.BLOCKED, "the bench fell over: %r" % ex)
                if o.fault:
                    E.put(fn, S.BLOCKED, "the bench fell over: %r" % ex, passed="fault")
    finally:
        G7.server("stop", o.box)
        after = G7.inside(o.box, "systemctl is-active rete11-server; systemctl show -p MainPID --value rete11-server", 30)[1]
        print("   everybody's server (851x) before/after: %s | %s" % (" ".join(before.split()), " ".join(after.split())),
              flush=True)


if __name__ == "__main__":
    sys.exit(S.run(__doc__, FUNCTIONS, body, certify, extra))
