#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f027 — F-027 WRONG PASSWORD · N-1 NONEXISTENT USER · F-028 THE BAN

    python3 15-f027-parola-e-ban.py --container_box kde --browser firefox --base-ports 4910 [--fault]

⛔ ON THE G8 GROUP'S SERVER (port 8621 gnome · 8622 kde · 8623 xfce · 8624 lxqt,
   `15-g8-server.sh`), NEVER on the 85xx: three errors ban 192.168.0.2 for 12 hours.
   If the G8 server is off the test starts it; at the beginning and at the end it
   UNBLOCKS it from the command socket.  Two browsers of the same type: A (base-ports)
   and B (base-ports+50).

F-027  (§4.2, src/rcp.c `rcp_verdict`) real user, wrong password ⇒ the page
       says «incorrect username or password» (REASON_TEXT 0x07), the server
       writes «PAM … refused» and «failed attempt from [192.168.0.2]», and NO
       session: no «session open username=…», no «child spawned for
       «…»», no process of the tenant in the box.
N-1    a user who does not exist ⇒ the SAME sentence, word for word (§4.2: «nonexistent
       user and wrong password are the same thing»: no list of the
       users), the attempt is counted, no session.
F-028  (§4.2, `DECISIONI.md` §1.9, src/rcp.c `mark_failed`) —
       · ALREADY_ACTIVE_REMOTELY does NOT count: two errors, then B with the RIGHT password
         while A is in and alive ⇒ B receives «taken by another client»
         (0x0F), and the ban does NOT fire (if it counted, it would be the third);
       · three errors ⇒ «⛔ BANNED address [192.168.0.2] for 12 hours»; the
         RIGHT password from that address receives «the attempts … are used up»
         (0x08); the reloaded page LOADS ANYWAY and says «attempts
         exhausted» with the hours (data-banned="si"); the ban file of the
         G8 server carries [192.168.0.2];
       · ⛔ the 85xx server is NOT touched: its page says
         data-banned="no" and its ban file does not carry the address;
       · the unblock from the command socket («REMOVED») reopens the page.
       ⚠ The mandate said «the port closes»: the product (§4.2) does NOT close it,
         it serves the page and makes it speak — that is what is judged.

FAULTS (after the healthy pass, same session):
  F-028  three real errors ⇒ banned; then the ban is REMOVED secretly (UNBLOCK)
         before the judge looks ⇒ the judge must say «not banned».
  F-027  A says farewell, and the «wrong» password that B sends is actually RIGHT
         ⇒ B is admitted ⇒ the judge must say red.
  N-1    the «nonexistent» user is the real one with the right password (while B is
         in) ⇒ the sentence is not that of 0x07 and the user exists ⇒ red.
"""
import json
import os
import random
import re
import secrets
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suite as S                                                     # noqa: E402

G = S._load("g8", os.path.join(S.HERE, "15-g8-comune.py"))
FUNCTIONS = ("F-027", "N-1", "F-028")
PER_BROWSER = False
SERVER = "15-g8-server.sh"
RE_FAILED = re.compile(r"failed attempt from \[([0-9.]+)\]: (\d) of (\d)")
ADDR = "[%s]" % G.ADDRESS


# ═══════════════════════════════════════════════════════════════════════════
#  THE JUDGES — pure
# ═══════════════════════════════════════════════════════════════════════════
def failed_counts(line_list):
    return [int(m.group(2)) for r in line_list for m in [RE_FAILED.search(r)]
            if m and m.group(1) == G.ADDRESS]


def judge_refusal(admitted, outcome, line_list, chi, processes):
    """F-027: (outcome, reason).  `line_list` = G8 server log from the attempt,
    `processes` = how many processes the tenant has in the box (None = don't know)."""
    if admitted is True:
        return S.FAIL, "wrong password and the page says ADMITTED («%s»)" % outcome
    if admitted is None:
        return S.BLOCKED, "no verdict from the page: «%s»" % outcome
    sess = [r for r in line_list if "session open username=%s " % chi in r + " "
            or "child spawned for «%s»" % chi in r]
    if sess:
        return S.FAIL, "refused but the server opened a session: %s" % sess[0][:160]
    if G.SENTENCE[0x07] not in (outcome or ""):
        return S.FAIL, "refused but the sentence is not clear: «%s»" % outcome
    if not any("refused" in r and "PAM answered" in r for r in line_list):
        return S.FAIL, "the page refuses but the server does not say «PAM … refused»"
    if not failed_counts(line_list):
        return S.FAIL, "the server does not count the failed attempt (§4.2)"
    if processes:
        return S.FAIL, "refused but the tenant has %d processes in the box" % processes
    return S.PASS, "«%s» · failed %s of 3 · no session, %s processes" % (
        outcome, failed_counts(line_list)[-1], processes)


def judge_nonexistent(admitted, outcome, outcome_f027, line_list, fake, path_exists):
    """N-1: (outcome, rationale)."""
    if admitted is True:
        return S.FAIL, "nonexistent user and the page says ADMITTED"
    if admitted is None:
        return S.BLOCKED, "no verdict from the page: «%s»" % outcome
    if path_exists:
        return S.FAIL, "the user «%s» exists: it is not the nonexistent-user test" % fake
    if (outcome or "").strip() != (outcome_f027 or "").strip():
        return S.FAIL, ("the sentence differs from the wrong-password one: «%s» against "
                        "«%s» (§4.2: they are the same thing)" % (outcome, outcome_f027))
    if any("session open username=%s" % fake in r for r in line_list):
        return S.FAIL, "the server opened a session for a nonexistent user"
    if not failed_counts(line_list):
        return S.FAIL, "the attempt with the nonexistent user is not counted (§4.2)"
    return S.PASS, "«%s», identical to the wrong password · failed %d of 3" % (
        outcome, failed_counts(line_list)[-1])


def judge_already_active(admitted, outcome, page_after, line_list):
    """F-028, half 1: the 0x0F refusal does not count as an error."""
    if admitted is True:
        return S.BLOCKED, "the second got in: A was not alive, there is no 0x0F to look at"
    if admitted is None or G.SENTENCE[0x0F] not in (outcome or ""):
        return S.BLOCKED, "the refusal is not 0x0F («%s»): I am not looking at what I wanted" % outcome
    if any("BANNED address %s" % ADDR in r for r in line_list):
        return S.FAIL, "0x0F after two errors BANNED: the second one's refusal counts (§4.2)"
    if page_after.get("banned") != "no":
        return S.FAIL, "after 0x0F the page says data-banned=%s" % page_after.get("banned")
    return S.PASS, "two errors + 0x0F «%s» ⇒ no ban" % outcome


def judge_ban(page_v, my_file, line_list):
    """F-028, half 2: after three errors.  (outcome, reason)."""
    if not any("BANNED address %s" % ADDR in r for r in line_list):
        return S.FAIL, "three failed attempts and the server does not say «BANNED»"
    if page_v.get("banned") != "si":
        return S.FAIL, ("the reloaded page does not say the ban (data-banned=%s, outcome «%s»)"
                        % (page_v.get("banned"), page_v.get("outcome")))
    if "attempts exhausted" not in (page_v.get("warning") or ""):
        return S.FAIL, "the page is banned but the notice does not say so: «%s»" % page_v.get("warning")
    if page_v.get("ore") not in ("11", "12"):
        return S.FAIL, "the notice says %s hours and %s minutes, not ~12 hours" % (
            page_v.get("ore"), page_v.get("minutes"))
    if ADDR not in (my_file or ""):
        return S.FAIL, "the server's ban file does not carry %s: «%s»" % (ADDR, my_file)
    return S.PASS, "banned: the page loads and says «attempts exhausted», %s hours %s min" % (
        page_v.get("ore"), page_v.get("minutes"))


def certify():
    ok = True

    def prova(what, real):
        nonlocal ok
        ok &= bool(real)
        print("%s %s" % ("⭐" if real else "⛔", what))
    ch = "c15027u1"
    fr = G.SENTENCE[0x07]
    line_list = ["PAM answered (request 3): refused", "failed attempt from [192.168.0.2]: 1 of 3 within the 5 minutes"]
    prova("clear refusal ⇒ PASS", judge_refusal(False, fr, line_list, ch, 0)[0] == S.PASS)
    prova("admitted ⇒ FAIL", judge_refusal(True, "Admitted", line_list, ch, 0)[0] == S.FAIL)
    prova("session open ⇒ FAIL", judge_refusal(
        False, fr, line_list + ["session open username=%s via=x" % ch], ch, 0)[0] == S.FAIL)
    prova("different sentence ⇒ FAIL", judge_refusal(False, "sent away", line_list, ch, 0)[0] == S.FAIL)
    prova("processes ⇒ FAIL", judge_refusal(False, fr, line_list, ch, 3)[0] == S.FAIL)
    prova("nonexistent, same sentence ⇒ PASS",
          judge_nonexistent(False, fr, fr, line_list, "c15027u9", False)[0] == S.PASS)
    prova("nonexistent, different sentence ⇒ FAIL",
          judge_nonexistent(False, "unknown user", fr, line_list, "c15027u9", False)[0] == S.FAIL)
    prova("nonexistent but exists ⇒ FAIL",
          judge_nonexistent(False, fr, fr, line_list, "c15027u9", True)[0] == S.FAIL)
    g0f = "refused: this session's slot shows as " + G.SENTENCE[0x0F]
    prova("0x0F without ban ⇒ PASS", judge_already_active(False, g0f, {"banned": "no"}, line_list)[0] == S.PASS)
    prova("0x0F with ban ⇒ FAIL", judge_already_active(
        False, g0f, {"banned": "si"}, line_list + ["⛔ BANNED address [192.168.0.2] for 12 hours"])[0] == S.FAIL)
    rb = ["⛔ BANNED address [192.168.0.2] for 12 hours"]
    pb = {"banned": "si", "warning": "attempts exhausted: … There are still 12 hours", "ore": "12", "minutes": "0"}
    prova("ban seen ⇒ PASS", judge_ban(pb, "[192.168.0.2] 1790000000", rb)[0] == S.PASS)
    prova("page not banned ⇒ FAIL", judge_ban(dict(pb, banned="no"), "[192.168.0.2] 1", rb)[0] == S.FAIL)
    prova("no BANNED line ⇒ FAIL", judge_ban(pb, "[192.168.0.2] 1", [])[0] == S.FAIL)
    prova("file without address ⇒ FAIL", judge_ban(pb, "", rb)[0] == S.FAIL)
    return 0 if ok else 1


# ═══════════════════════════════════════════════════════════════════════════
#  THE TEST
# ═══════════════════════════════════════════════════════════════════════════
def processes_of(sc, chi):
    c, t = G.inside(sc, "pgrep -u %s 2>/dev/null | wc -l; true" % chi, 30)
    try:
        return int(t.split()[-1])
    except (ValueError, IndexError):
        return None


def path_exists(sc, chi):
    c, t = G.inside(sc, "id %s >/dev/null 2>&1 && echo si || echo no" % chi, 30)
    return t.strip().endswith("si")


def send_without_reload(s, username, password, ceiling=30):
    r = s.g.js(S.REAL.JS_ENTER, username, password)
    if r != "mandato":
        return None, {"outcome": "form not filled in: %s" % r}
    fine = time.time() + ceiling
    st = {}
    while time.time() < fine:
        time.sleep(0.5)
        st = s.state()
        if st.get("esito_classe") == "all_ok" and (st.get("outcome") or "").startswith("Admitted"):
            return True, st
        if st.get("esito_classe") == "male" and G.SENTENCE[0x07] not in (st.get("outcome") or "") \
                and "Collego" not in (st.get("outcome") or ""):
            return False, st
    return (False if st.get("esito_classe") == "male" else None), st


def body_el(o, E):
    srv = G.MyServer(o.container_box)
    if not srv.lit():
        ok, t = srv.turn_on()
        print("   G8 server: %s" % t, flush=True)
        if not ok:
            raise S.Blocked("the G8 server on %d does not start: %s" % (srv.port, t))
    o.port = srv.port
    o.url = "https://%s:%d/" % (o.host, srv.port)
    print("   ⭐ G8 server %s · initial unblock: %s" % (o.url, srv.unblock()), flush=True)
    ban85 = srv.file_ban(G.BAN_85XX)
    wrong = lambda: "wrong-" + secrets.token_hex(4)   # noqa: E731
    ev_texts = {}

    with S.Session(o, "027", E) as A:
        chi = A.chi
        ok, m = A.pr.open_it()
        if not ok:
            raise S.Blocked("the G8 server's page does not open: " + m)

        # ── F-027: wrong password ───────────────────────────────────────────
        sign = srv.log_line_list()
        accepted, st = G.attempt(A, chi, wrong())
        time.sleep(1)
        line_list = srv.log_from(sign)
        outcome_f027 = st.get("outcome")
        e, r = judge_refusal(accepted, outcome_f027, line_list, chi, processes_of(A.sc, chi))
        ev = [A.save_text("f027-server.txt", line_list)]
        E.put("F-027", e, r, expected_val="«%s», no session, attempt counted" % G.SENTENCE[0x07],
                observed=r, evidence=[x for x in ev if x])

        # ── N-1: nonexistent user ───────────────────────────────────────────
        fake = "c15027u%d" % random.randint(10000, 99999)
        sign = srv.log_line_list()
        accepted, st = G.attempt(A, fake, wrong())
        time.sleep(1)
        line_list = srv.log_from(sign)
        e, r = judge_nonexistent(accepted, st.get("outcome"), outcome_f027, line_list, fake,
                                   path_exists(A.sc, fake))
        ev = [A.save_text("n1-server.txt", line_list)]
        E.put("N-1", e, r, expected_val="the same sentence as the wrong password, counted, no session",
                observed=r, evidence=ev)

        # ── A gets in (the count goes back to zero) ─────────────────────────
        sign = srv.log_line_list()
        ok, m = A.enter()
        if not ok:
            raise S.Blocked("the tenant with the RIGHT password does not get into the G8 server: " + m)
        reset = [x for x in srv.log_from(sign) if "the count of failures goes back to zero" in x]
        print("   ⭐ A in: %s · %s" % (m[:80], reset[0][-90:] if reset else "(no reset written)"),
              flush=True)

        with S.Session(G.o_per(o, 1), "027", E, tenant=False, chi=chi,
                        password=A.password) as B:
            # ── F-028 (1): ALREADY_ACTIVE_REMOTELY does not count ─────────────────
            sign = srv.log_line_list()
            for _ in range(2):
                G.attempt(B, chi, wrong())
            G.nudge(A)
            accepted, st = G.attempt(B, chi, A.password)
            time.sleep(1.5)
            page_v = G.load(B.g, o.url)
            line_list = srv.log_from(sign)
            ev_texts["f028-gia-attiva-server.txt"] = line_list
            e1, r1 = judge_already_active(accepted, st.get("outcome"), page_v, line_list)
            print("   F-028 (0x0F does not count): %s — %s" % (e1, r1), flush=True)
            if page_v.get("banned") == "si":
                print("   ⚠ banned already here: unblocking to be able to look at the rest: %s"
                      % srv.unblock(), flush=True)

            # ── F-028 (2): three errors ⇒ ban ───────────────────────────────
            sign = srv.log_line_list()
            for _ in range(3):
                accepted, st = G.attempt(B, chi, wrong())
            fourth_admitted, fourth = send_without_reload(B, chi, A.password)
            time.sleep(1)
            page_v = G.load(B.g, o.url)
            line_list = srv.log_from(sign)
            ev_texts["f028-ban-server.txt"] = line_list
            my_file = srv.file_ban()
            e2, r2 = judge_ban(page_v, my_file, line_list)
            # the fourth attempt, with the RIGHT password
            if e2 == S.PASS and (fourth_admitted is not False
                                 or G.SENTENCE[0x08] not in (fourth.get("outcome") or "")):
                e2, r2 = S.FAIL, ("banned, but the RIGHT password from that address receives: "
                                  "admitted=%s «%s» (expected 0x08)" % (fourth_admitted, fourth.get("outcome")))
            # ⛔ the 85xx not touched
            p85 = G.load(B.g, "https://%s:%d/" % (o.host, S.PORTS[o.container_box]))
            ban85_after = srv.file_ban(G.BAN_85XX)
            if e2 == S.PASS and (p85.get("banned") != "no" or ADDR in ban85_after):
                e2, r2 = S.FAIL, ("the G8 server's ban touched %d: data-banned=%s, file «%s»"
                                  % (S.PORTS[o.container_box], p85.get("banned"), ban85_after))
            alive_a = G.read_page(A.g)
            # the unblock
            unb = srv.unblock()
            page2 = G.load(B.g, o.url)
            if e2 == S.PASS and (not unb.startswith("REMOVED") or page2.get("banned") != "no"):
                e2, r2 = S.FAIL, "the unblock from the socket does not reopen: «%s», data-banned=%s" % (
                    unb, page2.get("banned"))
            counts = failed_counts(line_list)
            oss = ("%s · failures counted %s · fourth (right password): «%s» · %d data-banned=%s, "
                   "file «%s» (before «%s») · A during the ban: session_v=%s «%s» · unblock «%s»"
                   % (r2, counts, (fourth.get("outcome") or "")[:90], S.PORTS[o.container_box],
                      p85.get("banned"), ban85_after, ban85, alive_a.get("session_v"),
                      (alive_a.get("outcome") or "")[:40], unb))
            if e1 == S.FAIL or e2 == S.FAIL:
                ef = S.FAIL
            elif e1 == S.BLOCKED or e2 == S.BLOCKED:
                ef = S.BLOCKED
            else:
                ef = S.PASS
            ev = [B.save_text(n, t) for n, t in ev_texts.items()]
            ev.append(B.save_text("f028-pagine.json", json.dumps(
                {"bannata": page_v, "fourth": fourth, "85xx": p85, "sbloccata": page2},
                ensure_ascii=False, indent=1)))
            E.put("F-028", ef, "0x0F does not count: %s · ban: %s" % (r1, r2),
                    expected_val="0x0F does not count; 3 errors ⇒ 12 h ban said by the page, 0x08 on the "
                           "right password, 85xx intact, the unblock reopens",
                    observed=oss, evidence=ev)

            if o.fault:
                # F-028: the ban is removed secretly before the judge looks
                sign = srv.log_line_list()
                for _ in range(3):
                    G.attempt(B, chi, wrong())
                line_list = srv.log_from(sign)
                real = any("BANNED address %s" % ADDR in x for x in line_list)
                srv.unblock()                                   # ⛔ the fault
                page_v = G.load(B.g, o.url)
                eg, rg = judge_ban(page_v, srv.file_ban(), line_list)
                E.fault("F-028", (eg != S.PASS) if real else None,
                         "real ban (%s), removed before the judgment ⇒ the judge says %s: %s"
                         % (real, eg, rg))
                srv.unblock()
                # F-027: the «wrong» password is the right one (A says farewell first)
                A.g.go_to("about:blank")
                time.sleep(3)
                sign = srv.log_line_list()
                accepted, st = G.attempt(B, chi, B.password)
                time.sleep(1)
                line_list = srv.log_from(sign)
                eg, rg = judge_refusal(accepted, st.get("outcome"), line_list, chi, processes_of(A.sc, chi))
                E.fault("F-027", eg == S.FAIL if accepted is not None else None,
                         "right password passed off as wrong ⇒ the judge says %s: %s" % (eg, rg))
                # N-1: the «nonexistent» one is the real user with the right password
                sign = srv.log_line_list()
                accepted, st = G.attempt(A, chi, A.password)
                time.sleep(1)
                line_list = srv.log_from(sign)
                eg, rg = judge_nonexistent(accepted, st.get("outcome"), outcome_f027, line_list, chi,
                                             path_exists(A.sc, chi))
                E.fault("N-1", eg == S.FAIL if accepted is not None else None,
                         "real user instead of the nonexistent one ⇒ the judge says %s: %s" % (eg, rg))
    print("   final unblock: %s" % srv.unblock(), flush=True)


if __name__ == "__main__":
    sys.exit(S.execute(__doc__, FUNCTIONS, body_el, certify))
