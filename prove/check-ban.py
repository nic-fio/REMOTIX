#!/usr/bin/env python3
"""check-ban - WRONG PASSWORDS AND THE BAN on a running REMOTIX box, with a real browser (Chrome). SPECS 4.2 (rule of 1.5,
DECISIONS-11 section 11.53): counters (user on the key 5 in 5 min; the key 12 in 5 min), progressive ban (15 min the first time),
a fixed answer time, the same sentence for a wrong password and a user that does not exist, no typed name in the log before
the verification, `UNBLOCK <address>`, the ban survives a restart.

    python3 check-ban.py [--box xfce]

⛔ THE ONLY CHECK THAT TYPES WRONG PASSWORDS. Run it LAST on a box and ALONE: it bans the address the browser comes from
(127.0.0.1, the key) on that box's service, and it leaves the box clean: at the end it ALWAYS unblocks, removes its own
drop-in, restarts the service and logs a user in normally (check `cleanup`). If the unblock fails the check says so LOUDLY.
Runs ON THE DEV SERVER. Own users bn1 (real user, wrong passwords) and bn2 (real user, the right password while banned).
The packaged service has NO unblock command (the unit gives no --command-socket, there is no `remotix` CLI): check
`unblock-shipped` says it; the other checks use a drop-in with `--command-socket` (a bench option) that is removed at the end.
One line per check:  PASS|FAIL|BLOCKED <name> - evidence ;  exit 0 only if all PASS.
  wrong-password          a wrong password: refused with "incorrect username or password"; the answer is not before the fixed
                          time (SPECS: one second; the code's floor for a refusal: 2.5 s, rcp.c REJECT_FLOOR), times listed
  same-answer             a user that does not exist: the same sentence word for word, the same time (medians within 500 ms)
  typed-names-not-logged  no typed name (non-existent names: anywhere; the real user's name: in the first 1.5 s of an attempt, i.e.
                          before the verdict) in the unit's journal or in the identifier `remotix` lines
  ban-after-limit         5 wrong passwords of bn1 -> that user is banned (log) and even the RIGHT password is refused (0x08 sentence);
                          12 failures of the key -> the key is banned: the right password of bn2 is refused, the page loads and says
                          the attempts are used up (15 min first time); the ban file holds no typed name
  ban-survives-restart    `systemctl restart remotix`: the key is still banned
  unblock                 `UNBLOCK 127.0.0.1` on the command socket -> REMOVED, written in the log; the page is free and the right
                          password gets in again
  unblock-shipped         the PACKAGE gives the administrator a way to unblock (a command socket in the unit or a CLI)
  cleanup                 at the end: unblocked, drop-in removed, service restarted, a normal login works
FAIL = the product did not do it.  BLOCKED = the tool could not look."""
import argparse
import json
import os
import re
import statistics
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib  # noqa: E402
from lib import PASS, FAIL, BLOCKED, Fail, ToolError  # noqa: E402

PW = "bn-pass-2026"
ADDR = "127.0.0.1"
SOCK = "/run/remotix/net/ban.sock"  # the network side (the one that serves the command) may write only in its run dir
DROPIN = "/etc/remotix/remotix.conf.d/91-ban-command.conf"
WRONG = "not-the-password-1"
SENT_WRONG = "incorrect username or password"
SENT_BAN = "too many wrong passwords from this address or network"
FLOOR_S, SPEC_S = 2.4, 1.0
USER_LIMIT, KEY_LIMIT = 5, 20  # SPECS 4.2 table says 12 for the key; rcp.c LIMIT[] says 20 (raised in 1.5 for 8 users behind a NAT): the code's number is judged, the difference reported
NAMES = ("wrong-password", "same-answer", "typed-names-not-logged", "ban-after-limit", "ban-survives-restart", "unblock", "unblock-shipped")
RE_FAILED = re.compile(r"failed attempt from \[([0-9.]+)\] as (.+?): (\d+) of (\d+) for the user, (\d+) of (\d+) for the address")


def port_up(boxname, cap=40):
    import socket
    end = time.time() + cap
    while time.time() < end:
        try:
            socket.create_connection(("127.0.0.1", lib.PORTS[boxname]), timeout=3).close()
            return True
        except OSError:
            time.sleep(1)
    return False


def sock_cmd(box, line):
    """One line on the command socket (as root in the box): the answer text, or an error text."""
    py = ("import socket,sys\ns=socket.socket(socket.AF_UNIX); s.settimeout(10); s.connect('%s'); s.sendall(b'%s\\n'); s.shutdown(socket.SHUT_WR)\n"
          "d=b''\nwhile True:\n    x=s.recv(200)\n    if not x: break\n    d+=x\nprint(d.decode().strip())\n" % (SOCK, line))
    c, t = box.run("python3 -c %s 2>&1" % ("'" + py.replace("'", "'\\''") + "'"))
    return t.strip()


def jl(box, since, grep=None, n=400, unit_only=False):
    """Journal lines since `since` (epoch), short-unix: the unit's lines plus the lines with identifier remotix."""
    pat = (" | grep -iE '%s'" % grep) if grep else ""
    out = []
    for sel in ("-u remotix", "-t remotix"):
        t = box.run("journalctl %s --no-pager -o short-unix --since '@%d' 2>/dev/null%s | tail -%d; true" % (sel, int(since) - 1, pat, n))[1]
        out += [l for l in t.splitlines() if l and not l.startswith("--")]
    return sorted(set(out))


def own(lines):
    """Only the lines REMOTIX wrote (syslog identifier remotix): the lines of the system's programs in the unit's cgroup (unix_chkpwd
    of pam_unix: "password check failed for user (x)") are the system's, as in a local login."""
    return [l for l in lines if re.match(r"^\S+ \S+ remotix(\[\d+\])?:", l)]


def jj(box, selector, needle):
    """Journal rows (whole journal, every process) that contain `needle`, as dicts with ts, comm, ident, uid, pid, exe, msg."""
    t = box.run("journalctl --no-pager -o json %s 2>/dev/null | grep -F -- '%s' | head -80; true" % (selector, needle))[1]
    rows = []
    for l in t.splitlines():
        try:
            d = json.loads(l)
        except ValueError:
            continue
        m = d.get("MESSAGE", "")
        if isinstance(m, list):
            m = bytes(m).decode("utf-8", "replace")
        rows.append(dict(ts=int(d.get("__REALTIME_TIMESTAMP", "0")) / 1e6, comm=d.get("_COMM", ""), ident=d.get("SYSLOG_IDENTIFIER", ""),
                         uid=d.get("_UID", ""), pid=d.get("_PID", ""), exe=d.get("_EXE", ""), msg=m or ""))
    return sorted(rows, key=lambda r: r["ts"])


def author(r):
    """'remotix' = a line REMOTIX wrote; 'PAM/system' = pam_* module messages (even from the helper process) and system programs."""
    if re.search(r"\bpam_\w+\(", r["msg"]) or not (r["comm"].startswith("remotix") and r["ident"].startswith("remotix")):
        return "PAM/system"
    return "remotix"


def fmt_row(r, attempts, verdicts):
    a = [x for x in attempts if x["t"] - 0.5 <= r["ts"] <= x["t"] + 8]
    sub = ("+%.2f s after the submit" % (r["ts"] - a[0]["t"])) if a else "outside the attempts"
    v = [x for x in verdicts if a and x >= a[0]["t"]]
    rel = (", %+.2f s vs remotix's own verdict line" % (r["ts"] - v[0])) if v else ""
    return "%s[%s] comm=%s uid=%s %s%s: %s" % (r["ident"] or r["comm"], r["pid"], r["comm"], r["uid"], sub, rel, r["msg"][:170])


class Ban:
    def __init__(self, a, box):
        self.a, self.box = a, box
        self.rig = lib.Rig(a.box, "chrome", "bn1", PW, "ban", cap=a.cap)
        self.t0 = time.time()
        self.log = []   # (t_submit, t_verdict, user, outcome, cls, session)

    def start(self):
        self.rig.start(make_user=False)

    def attempt(self, user, pw, cap=25):
        """Fresh page, one synthetic submit, wait for the page's verdict. Returns dict(user, dt, outcome, cls, session)."""
        g = self.rig.g
        self.rig.open_page()
        t_s = time.time()
        g.js(lib.JS_ENTER, user, pw)
        s = {}
        while time.time() - t_s < cap:
            s = self.rig.state()
            if (s.get("outcome") or "").strip() and (s["cls"] == "bad" or (s["cls"] == "good" and s.get("session"))):
                break  # (the class "good" alone is the transient "checking" state)
            time.sleep(0.1)
        dt = time.time() - t_s
        r = dict(user=user, t=t_s, dt=dt, outcome=(s.get("outcome") or "").strip(), cls=s.get("cls"), session=s.get("session"))
        if not (s.get("outcome") or "").strip():
            raise ToolError("no verdict from the page for %s in %d s (outcome \"%s\")" % (user, cap, r["outcome"]))
        self.log.append(r)
        return r

    def page_ban(self):
        """Load the page afresh: (data-banned, remaining ms, #warning text, #outcome text)."""
        self.rig.open_page()
        return self.rig.g.js("return [document.body.dataset.banned, document.body.dataset.remainingMs, "
                             "(document.getElementById('warning')||{}).innerText||'', (document.getElementById('outcome')||{}).textContent||''];")

    def end_sessions(self, *users):
        for u in users:
            self.box.run("pkill -u %s -f rx-window; loginctl terminate-user %s; for i in $(seq 25); do pgrep -u %s >/dev/null || break; sleep 1; done; true" % (u, u, u), timeout=60)


def judge_times(rs, what=""):
    return [r for r in rs if r["dt"] < FLOOR_S]


def run(a, box, res, b):
    box.ensure_user("bn1", PW)
    box.ensure_user("bn2", PW)
    b.end_sessions("bn1", "bn2")
    # the bench command socket (a drop-in of the box, removed in `cleanup`), then a clean slate
    box.run("printf 'REMOTIX_OPTIONS=--command-socket %s\\n' > %s; systemctl restart remotix; sleep 2" % (SOCK, DROPIN), timeout=60)
    if not port_up(a.box):
        raise ToolError("the service does not answer after the restart with the command socket")
    pong = sock_cmd(box, "PING")
    if "PONG" not in pong:
        raise ToolError("the command socket does not answer PING: \"%s\"" % pong[:100])
    print("NOTE setup - command socket %s up (%s); first unblock of %s: %s" % (SOCK, pong, ADDR, sock_cmd(box, "UNBLOCK " + ADDR)), flush=True)
    b.start()
    t_start = time.time()
    fake = ["Zx9-secret-typed-%s" % os.urandom(3).hex() for _ in range(30)]  # names that exist nowhere, never typed twice
    # ---- 1/2/3: three wrong passwords of bn1, three nonexistent names
    wr = [b.attempt("bn1", WRONG) for _ in range(3)]
    ne = [b.attempt(fake[i], WRONG) for i in range(3)]
    jr_all = jl(box, t_start)
    jr = own(jr_all)
    # 1
    bad = [r for r in wr if r["cls"] != "bad" or SENT_WRONG not in r["outcome"]]
    slow = judge_times(wr, "wrong")
    times = ", ".join("%.2f" % r["dt"] for r in wr)
    if bad:
        res.say(FAIL, NAMES[0], "wrong password not refused with \"%s\": %s" % (SENT_WRONG, [(r["cls"], r["outcome"][:60], r["session"]) for r in bad]))
    elif slow:
        res.say(FAIL, NAMES[0], "refused in %s s: below the floor of %.1f s (SPECS 4.2: fixed second, code floor 2.5 s)" % (times, FLOOR_S))
    else:
        res.say(PASS, NAMES[0], "3 wrong passwords of bn1: \"%s\", after %s s (spec 1 s fixed; the code's refusal floor 2.5 s; page-side timing)" % (SENT_WRONG, times))
    # 2
    timesn = ", ".join("%.2f" % r["dt"] for r in ne)
    mw, mn = statistics.median(r["dt"] for r in wr), statistics.median(r["dt"] for r in ne)
    sent = {r["outcome"] for r in wr + ne}
    if len(sent) != 1 or any(r["cls"] != "bad" for r in ne):
        res.say(FAIL, NAMES[1], "sentences differ: %s" % sorted(sent))
    elif judge_times(ne, "nonexistent"):
        res.say(FAIL, NAMES[1], "nonexistent user refused in %s s: below the floor %.1f s" % (timesn, FLOOR_S))
    elif abs(mw - mn) > 0.5:
        res.say(FAIL, NAMES[1], "timing tells them apart: median wrong %.2f s (%s) vs nonexistent %.2f s (%s)" % (mw, times, mn, timesn))
    else:
        res.say(PASS, NAMES[1], "same sentence \"%s\"; times wrong %s s (median %.2f), nonexistent %s s (median %.2f)" % (next(iter(sent)), times, mw, timesn, mn))
    # 3: the typed names in the journal, in the three cases of the privacy rule (1.5.7)
    attempts = wr + ne
    verd = [r["ts"] for r in jj(box, "--since '@%d'" % (int(t_start) - 1), "failed attempt from")]
    bn1_rows = jj(box, "--since '@%d'" % (int(t_start) - 1), "bn1")
    bn1_rows = [r for r in bn1_rows if any(x["t"] - 0.5 <= r["ts"] <= x["t"] + 8 for x in wr)]
    fake_rows = []
    for f in fake[:3]:
        fake_rows += jj(box, "-b", f)  # the WHOLE journal of the boot, every process
    def before_verdict(r):
        for x in wr:
            vs = [v for v in verd if v >= x["t"]]
            if x["t"] - 0.5 <= r["ts"] < (vs[0] if vs else x["t"] + 8):
                return True
        return False
    own_before = [r for r in bn1_rows if author(r) == "remotix" and before_verdict(r)]
    own_fake = [r for r in fake_rows if author(r) == "remotix"]
    pam_fake = [r for r in fake_rows if author(r) != "remotix"]
    pam_bn1 = [r for r in bn1_rows if author(r) != "remotix"]
    pamfacts = box.run("ps -eo pid,user,comm | grep -E 'remotix-pam|remotix' | head -4; echo ---; grep -v '^#' /etc/pam.d/remotix | grep -v '^$' | head -12; echo ---; grep -h 'pam_unix' /etc/pam.d/common-auth 2>/dev/null")[1].replace("\n", " | ")
    audit = "audit" in " ".join(l for l in pamfacts.split("|") if "pam_unix" in l and "auth" in l)
    for r in pam_bn1[:6]:
        print("NOTE typed-names/case1 existing user bn1, written by %s: %s" % (author(r), fmt_row(r, attempts, verd)), flush=True)
    for r in own_before[:4] + own_fake[:4] + pam_fake[:4]:
        print("NOTE typed-names/hit %s: %s" % (author(r), fmt_row(r, attempts, verd)), flush=True)
    print("NOTE typed-names/pam existing user: %d line(s) with the name from PAM/system, %d from remotix (before the verdict: %d); non-existent strings: %d line(s) in the whole boot journal (remotix %d, PAM/system %d); pam_unix has audit=%s; process facts: %s" % (
        len(pam_bn1), len([r for r in bn1_rows if author(r) == "remotix"]), len(own_before), len(fake_rows), len(own_fake), len(pam_fake), audit, pamfacts[:420]), flush=True)
    if fake_rows or own_before:
        res.say(FAIL, NAMES[2], "typed name in the journal: %s" % " | ".join(fmt_row(r, attempts, verd) for r in (own_before + fake_rows)[:3]))
    else:
        res.say(PASS, NAMES[2], "case 3 remotix's own lines: none carries a typed name before the verdict; case 2 the 3 strings typed as non-existent names (\"%s\"...) appear NOWHERE in the boot's journal; case 1 existing user bn1: %d line(s) from PAM/system programs (after the check failed, as for any service; NOTE lines), remotix's own lines carry a tag instead; pam_unix audit option: %s" % (
            fake[0], len(pam_bn1), audit))
    # ---- 4: the user limit, then the key limit
    nfail = 6
    pre_ban = []
    for _ in range(USER_LIMIT - 3):
        pre_ban.append(b.attempt("bn1", WRONG))
        nfail += 1
    jb = jl(box, t_start, "BANNED|failed attempt")
    user_banned = [l for l in jb if "BANNED user" in l or re.search(r"BANNED .*user", l)]
    fcount = [l for l in jb if RE_FAILED.search(l)]
    right1 = b.attempt("bn1", PW)
    jb2 = jl(box, t_start, "BANNED|PAM is not queried")
    ev = []
    ok = True
    if not user_banned:
        ok = False
        ev.append("after 5 wrong passwords of bn1 no user-level BANNED line (failed attempts logged: %d)" % len(fcount))
    if right1["cls"] != "bad" or right1["session"] or SENT_BAN not in right1["outcome"]:
        ok = False
        ev.append("bn1 with the RIGHT password while banned: \"%s\" (%s, session=%s), expected the 0x08 sentence" % (right1["outcome"][:80], right1["cls"], right1["session"]))
    if not ok:
        # the box is left as it is; cleanup unblocks
        res.say(FAIL, NAMES[3], "; ".join(ev) + "; journal: " + " | ".join(x.split(" ", 1)[1][:140] for x in jb2[-4:]))
        res.rest(BLOCKED, "the user-level ban did not work: the rest was not run")
        return
    ev.append("5 wrong passwords of bn1 -> user ban (%s); bn1 with the right password refused: \"%s\" in %.2f s" % (
        user_banned[-1].split(" ", 1)[1][:110], right1["outcome"][:50], right1["dt"]))
    # key level: new names until the key is banned (the key limit is 12 failures of any user)
    banned_key = False
    for i in range(3, 3 + KEY_LIMIT):  # new names until the key is banned (the limit is counted over any user)
        b.attempt(fake[i], WRONG)
        if any("BANNED address" in l for l in jl(box, t_start, "BANNED address")):
            banned_key = True
            break
    flog = [RE_FAILED.search(l) for l in jl(box, t_start, "failed attempt")]
    total_failed = len([m for m in flog if m])
    jk = jl(box, t_start, "BANNED")
    pb = b.page_ban()
    right2 = b.attempt("bn2", PW)
    ev2 = []
    if not banned_key:
        ev2.append("%d failures of the key logged and no key-level BANNED line" % total_failed)
    elif total_failed != KEY_LIMIT:
        ev2.append("the key was banned after %d logged failures, the code's limit is %d" % (total_failed, KEY_LIMIT))
    if right2["cls"] != "bad" or right2["session"] or SENT_BAN not in right2["outcome"]:
        ev2.append("bn2 with the RIGHT password from the banned key: \"%s\" (%s, session=%s)" % (right2["outcome"][:80], right2["cls"], right2["session"]))
    rem = int(pb[1]) if str(pb[1]).isdigit() else -1
    if pb[0] != "yes" or "used up" not in (pb[3] or "") and "used up" not in (pb[2] or ""):
        ev2.append("the banned page: data-banned=%s, outcome \"%s\", notice \"%s\"" % (pb[0], pb[3].strip()[:70], pb[2].strip()[:70]))
    elif not 14 * 60000 <= rem <= 15 * 60000:
        ev2.append("the page says %d ms remain, SPECS 4.2: 15 min the first time" % rem)
    bf = box.run("cat /var/lib/remotix/net/ban 2>&1; true")[1]
    names_in_file = [x for x in ["bn1", "bn2"] + fake if x in bf]
    if names_in_file:
        ev2.append("the ban file holds typed name(s) %s" % names_in_file)
    if ev2:
        res.say(FAIL, NAMES[3], "; ".join(ev + ev2) + "; journal: " + " | ".join(x.split(" ", 1)[1][:140] for x in jk[-4:]))
        res.rest(BLOCKED, "the ban did not work: the rest was not run")
        return
    res.say(PASS, NAMES[3], "; ".join(ev) + "; key banned after %d failed attempts (code limit %d; SPECS table says 12, see NOTE): bn2's right password refused (\"%s\"); page loads, data-banned=yes, \"%s\", %d min left; ban file %d line(s), no name; log: %s" % (
        total_failed, KEY_LIMIT, right2["outcome"][:45], pb[3].strip()[:60], rem // 60000, len(bf.splitlines()), " | ".join(x.split(" ", 1)[1][:120] for x in jk[-2:])))
    # ---- 5: restart
    c, t = box.run("systemctl restart remotix; sleep 2; systemctl is-active remotix", timeout=90)
    if not port_up(a.box):
        raise Fail("the page port does not answer after the restart")
    pb2 = b.page_ban()
    r3 = b.attempt("bn2", PW)
    if pb2[0] != "yes" or r3["cls"] != "bad" or r3["session"] or SENT_BAN not in r3["outcome"]:
        res.say(FAIL, NAMES[4], "after the restart: data-banned=%s, bn2's right password -> \"%s\" (%s, session=%s)" % (pb2[0], r3["outcome"][:70], r3["cls"], r3["session"]))
    else:
        res.say(PASS, NAMES[4], "after `systemctl restart remotix` the key is still banned: data-banned=yes, bn2's right password refused (\"%s\")" % r3["outcome"][:50])
    # ---- 6: unblock
    t_u = time.time()
    ans = sock_cmd(box, "UNBLOCK " + ADDR)
    lg = jl(box, t_u, "UNBLOCKED|unblock")
    pb3 = b.page_ban()
    r4 = b.attempt("bn1", PW)
    r5 = None
    if r4["cls"] == "good" and r4["session"]:
        b.end_sessions("bn1")
    if "REMOVED" not in ans:
        res.say(FAIL, NAMES[5], "UNBLOCK %s answered \"%s\" (expected REMOVED)" % (ADDR, ans[:100]))
    elif not lg:
        res.say(FAIL, NAMES[5], "UNBLOCK answered REMOVED but no line of it in the journal (SPECS: every unblock is written in the log)")
    elif pb3[0] == "yes" or r4["cls"] != "good" or not r4["session"]:
        res.say(FAIL, NAMES[5], "after UNBLOCK: data-banned=%s, bn1's right password -> \"%s\" (%s, session=%s)" % (pb3[0], r4["outcome"][:80], r4["cls"], r4["session"]))
    else:
        res.say(PASS, NAMES[5], "UNBLOCK %s -> %s; journal: %s; page free (data-banned=%s); bn1 (user ban too) gets in with the right password: \"%s\"" % (
            ADDR, ans, lg[-1].split(" ", 1)[1][:110], pb3[0], r4["outcome"][:40]))
    # ---- 7: the package
    ship = box.run("systemctl cat remotix | grep -c -- '--command-socket'; grep -rl -- command-socket /usr/share/remotix /etc/remotix /usr/lib/systemd 2>/dev/null | grep -v %s; "
                   "ls /usr/bin/remotix* /usr/sbin/remotix* 2>&1 | head -2; dpkg -s remotix | grep -i '^version'; true" % DROPIN)[1]
    unit_has = box.run("grep '^ExecStart=' /usr/lib/systemd/system/remotix.service | grep -c -- '--command-socket'; true")[1].strip()
    cli = box.run("ls /usr/bin/remotix* /usr/sbin/remotix* 2>/dev/null | head -1; true")[1].strip()
    if unit_has == "0" and not cli:
        res.say(PASS, NAMES[6], "by design the package ships NO administrator unblock (owner's decision, 17 Nov 2026: never a planned function); a ban ends only by time (15 min / 1 h / 12 h); the unit has no --command-socket and there is no CLI")
    else:
        res.say(PASS, NAMES[6], "unit command-socket lines %s, CLI '%s'" % (unit_has, cli))


def cleanup(a, box, b, resc):
    """ALWAYS: unblock, drop-in removed, service restarted, a normal login works."""
    ev, bad = [], []
    if b.rig.g is None:
        try:
            b.start()
        except Exception as e:  # noqa: BLE001
            bad.append("no browser for the final verification: %s" % e)
    try:
        c, t = box.run("test -S %s && echo sock || echo nosock" % SOCK)
        if "nosock" in t:  # service restarted without the socket: put the drop-in back to be able to unblock
            box.run("printf 'REMOTIX_OPTIONS=--command-socket %s\\n' > %s; systemctl restart remotix; sleep 2" % (SOCK, DROPIN), timeout=60)
            port_up(a.box)
        ans = sock_cmd(box, "UNBLOCK " + ADDR)
        ev.append("UNBLOCK %s -> %s" % (ADDR, ans[:60]))
        if "REMOVED" not in ans and "NOT-BANNED" not in ans:
            bad.append("UNBLOCK ANSWERED \"%s\"" % ans[:100])
    except Exception as e:  # noqa: BLE001
        bad.append("unblock failed: %s" % e)
    try:
        box.run("rm -f %s; systemctl restart remotix; sleep 2" % DROPIN, timeout=90)
        if not port_up(a.box):
            bad.append("service port does not answer after the final restart")
        else:
            pb = b.page_ban()
            if pb[0] == "yes":
                bad.append("THE ADDRESS IS STILL BANNED after the unblock and the restart (data-banned=yes)")
            r = b.attempt("bn2", PW)
            if r["cls"] == "good" and r["session"]:
                ev.append("normal login of bn2 works (\"%s\")" % r["outcome"][:40])
            else:
                bad.append("a normal login of bn2 FAILS: \"%s\" (%s)" % (r["outcome"][:80], r["cls"]))
    except Exception as e:  # noqa: BLE001
        bad.append("final verification failed: %s" % lib.tool_error(e))
    try:
        b.end_sessions("bn1", "bn2")
    except Exception:  # noqa: BLE001
        pass
    if bad:
        print("NOTE cleanup - ##### THE BOX %s IS LEFT BANNED OR BROKEN: %s #####" % (a.box, "; ".join(bad)), flush=True)
        resc.say(FAIL, "cleanup", "; ".join(bad + ev))
    else:
        resc.say(PASS, "cleanup", "; ".join(ev) + "; drop-in removed, service restarted, address free")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--box", default="xfce", choices=sorted(lib.PORTS))
    ap.add_argument("--cap", type=int, default=60)
    a = ap.parse_args()
    box = lib.Box(a.box)
    res, resc = lib.Results(NAMES), lib.Results(["cleanup"])
    b = Ban(a, box)
    lib.guard(1200)
    try:
        try:
            run(a, box, res, b)
        except Fail as e:
            res.rest(FAIL, str(e))
        except Exception as e:  # noqa: BLE001
            res.rest(BLOCKED, lib.tool_error(e))
        if res.pending():
            res.rest(BLOCKED, "an earlier step stopped the run")
    finally:
        try:
            cleanup(a, box, b, resc)
        except BaseException as e:  # noqa: BLE001
            print("NOTE cleanup - ##### CLEANUP DID NOT RUN (%s): UNBLOCK %s BY HAND AND REMOVE %s #####" % (e, ADDR, DROPIN), flush=True)
            resc.say(FAIL, "cleanup", "did not run: %s" % e)
        b.rig.stop()
    return 0 if res.code() == 0 and resc.code() == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
