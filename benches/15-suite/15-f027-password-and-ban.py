#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f027 — F-027 WRONG PASSWORD · N-1 NONEXISTENT USER · F-028 THE BAN

    python3 15-f027-password-and-ban.py --box kde --browser firefox --base-port 4910 [--fault]

⛔ ON THE G8 GROUP'S SERVER (port 8621 gnome · 8622 kde · 8623 xfce · 8624 lxqt,
   `15-g8-server.sh`), NEVER on the 85xx: five wrong passwords of one user, or twelve of the
   address, ban 192.168.0.2 (15 minutes the first time).
   If the G8 server is off the test starts it; at the beginning and at the end it
   UNBLOCKS it from the command socket.  Two browsers of the same type: A (porte-base)
   and B (porte-base+50).

F-027  (§4.2, src/rcp.c `rcp_verdict`) real user, wrong password ⇒ the page
       says «incorrect username or password» (REASON_TEXT 0x07), the server
       writes «PAM … refused» and «failed attempt from [192.168.0.2] as <user>: N of 5
       for the user, …» (§4.4-bis), and NO
       session: no «session open user=…», no «child spawned for
       «…»», no process of the tenant in the box.
N-1    a user who does not exist ⇒ the SAME sentence, word for word (§4.2: «nonexistent
       user and wrong password are the same thing»: no list of the
       users), the attempt is counted, no session.
F-028  (§4.2, `DECISIONS.md` §1.9, src/rcp.c `mark_failed`) —
       · ALREADY_ACTIVE_REMOTELY does NOT count: two errors, then B with the RIGHT password
         while A is in and alive ⇒ B receives «taken by another client»
         (0x0F), and the ban does NOT fire (if it counted, it would be the third);
       · the product's REAL limits (rcp.c LIMIT = 5 user / 12 address / 30 IPv6 /48);
         the counters are unblocked between the parts so they do not carry over:
         (a) USER level: 5 wrong passwords for one user ⇒ «⛔ BANNED user on this
             address of [192.168.0.2] as <user>»; the 6th attempt, with the RIGHT
             password, receives 0x08 WITHOUT PAM («BANNED: … PAM is not queried», no
             «PAM answered» after the ban); the page of the address is NOT banned;
         (b) ADDRESS level: 12 wrong passwords with different users ⇒ «⛔ BANNED address
             of [192.168.0.2]»; the RIGHT password receives 0x08; the reloaded page
             LOADS ANYWAY and says «attempts exhausted» with the minutes
             (data-banned="yes"); the ban file of the G8 server carries [192.168.0.2];
       · ⛔ the 85xx server is NOT touched: its page says
         data-banned="no" and its ban file does not carry the address;
       · the unblock from the command socket («REMOVED») reopens the page.
       ⚠ The mandate said «the port closes»: the product (§4.2) does NOT close it,
         it serves the page and makes it speak — that is what is judged.

FAULTS (after the healthy pass, same session):
  F-028  twelve real errors (address level) ⇒ banned; then the ban is REMOVED secretly (UNBLOCK)
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

G = S._load("g8", os.path.join(S.HERE, "15-g8-common.py"))
FUNCTIONS = ("F-027", "N-1", "F-028")
PER_BROWSER = False
SERVER = "15-g8-server.sh"
# «failed attempt from [ip] as USER: 1 of 5 for the user, 5 of 12 for the address, 0 of 30 for the IPv6 /48 within the window»
RE_FAILED = re.compile(r"failed attempt from \[([0-9.]+)\] as (\S+): (\d+) of (\d+) for the user, "
                       r"(\d+) of (\d+) for the address")
USER_LIMIT, ADDRESS_LIMIT = 5, 12      # rcp.c LIMIT[]: the product's, not lowered for the test
ADDR = "[%s]" % G.ADDRESS


# ═══════════════════════════════════════════════════════════════════════════
#  THE JUDGES — pure
# ═══════════════════════════════════════════════════════════════════════════
def failed_counts(lines):
    """The USER counter of every «failed attempt» line of this address."""
    return [int(m.group(3)) for r in lines for m in [RE_FAILED.search(r)]
            if m and m.group(1) == G.ADDRESS]


def address_counts(lines):
    """The ADDRESS counter of every «failed attempt» line of this address."""
    return [int(m.group(5)) for r in lines for m in [RE_FAILED.search(r)]
            if m and m.group(1) == G.ADDRESS]


def judge_refusal(admitted, outcome, lines, chi, processes):
    """F-027: (outcome, reason).  `lines` = G8 server log from the attempt,
    `processes` = how many processes the tenant has in the box (None = don't know)."""
    if admitted is True:
        return S.FAIL, "wrong password and the page says ADMITTED («%s»)" % outcome
    if admitted is None:
        return S.BLOCKED, "no verdict from the page: «%s»" % outcome
    sess = [r for r in lines if "session open user=%s " % chi in r + " "
            or "child spawned for «%s»" % chi in r]
    if sess:
        return S.FAIL, "refused but the server opened a session: %s" % sess[0][:160]
    if G.SENTENCE[0x07] not in (outcome or ""):
        return S.FAIL, "refused but the sentence is not clear: «%s»" % outcome
    if not any("refused" in r and "PAM answered" in r for r in lines):
        return S.FAIL, "the page refuses but the server does not say «PAM … refused»"
    if not failed_counts(lines):
        return S.FAIL, "the server does not count the failed attempt (§4.2)"
    if processes:
        return S.FAIL, "refused but the tenant has %d processes in the box" % processes
    return S.PASS, ("«%s» · failed %s of %d for the user (%s of %d for the address) · "
                    "no session, %s processes" % (
                        outcome, failed_counts(lines)[-1], USER_LIMIT,
                        address_counts(lines)[-1], ADDRESS_LIMIT, processes))


def judge_nonexistent(admitted, outcome, outcome_f027, lines, fake, path_exists):
    """N-1: (esito, ragione)."""
    if admitted is True:
        return S.FAIL, "nonexistent user and the page says ADMITTED"
    if admitted is None:
        return S.BLOCKED, "no verdict from the page: «%s»" % outcome
    if path_exists:
        return S.FAIL, "the user «%s» exists: it is not the nonexistent-user test" % fake
    if (outcome or "").strip() != (outcome_f027 or "").strip():
        return S.FAIL, ("the sentence differs from the wrong-password one: «%s» against "
                        "«%s» (§4.2: they are the same thing)" % (outcome, outcome_f027))
    if any("session open user=%s" % fake in r for r in lines):
        return S.FAIL, "the server opened a session for a nonexistent user"
    if not failed_counts(lines):
        return S.FAIL, "the attempt with the nonexistent user is not counted (§4.2)"
    return S.PASS, "«%s», identical to the wrong password · failed %d of %d for the user" % (
        outcome, failed_counts(lines)[-1], USER_LIMIT)


def judge_already_active(admitted, outcome, page_after, lines):
    """F-028, half 1: the 0x0F refusal does not count as an error."""
    if admitted is True:
        return S.BLOCKED, "the second got in: A was not alive, there is no 0x0F to look at"
    if admitted is None or G.SENTENCE[0x0F] not in (outcome or ""):
        return S.BLOCKED, "the refusal is not 0x0F («%s»): I am not looking at what I wanted" % outcome
    if any("⛔ BANNED" in r for r in lines):
        return S.FAIL, "0x0F after two errors BANNED: the second one's refusal counts (§4.2)"
    if page_after.get("banned") != "no":
        return S.FAIL, "after 0x0F the page says data-banned=%s" % page_after.get("banned")
    return S.PASS, "two errors + 0x0F «%s» ⇒ no ban" % outcome


def judge_ban_user(lines, sixth, page):
    """F-028 (a), USER level: `lines` = the server log from the first of the 5 wrong
    passwords to the 6th attempt (the RIGHT password), `sixth` = the page's outcome of
    that attempt, `page` = read_page of the address's page afterwards.  (outcome, reason)."""
    ban = [k for k, r in enumerate(lines) if "⛔ BANNED user on this address of %s" % ADDR in r]
    if not ban:
        return S.FAIL, "%d wrong passwords of one user and the server does not say «BANNED user»" % USER_LIMIT
    if failed_counts(lines)[-1:] != [USER_LIMIT]:
        return S.FAIL, "the ban is not at the %dth failure of the user: counters %s" % (
            USER_LIMIT, failed_counts(lines))
    after = lines[ban[0] + 1:]
    if not any("BANNED:" in r and "PAM is not queried" in r for r in after):
        return S.FAIL, "the 6th attempt was not refused by the ban («BANNED: … PAM is not queried»)"
    if any("PAM answered" in r for r in after):
        return S.FAIL, "the 6th attempt (right password) reached PAM although the user was banned"
    if G.SENTENCE[0x08] not in (sixth or ""):
        return S.FAIL, "the 6th attempt did not receive 0x08: «%s»" % sixth
    if page.get("banned") != "no":
        return S.FAIL, "a USER-level ban banned the whole address (data-banned=%s)" % page.get("banned")
    return S.PASS, "banned at %d failures, the right password refused with 0x08 and without PAM" % USER_LIMIT


def judge_ban_address(page, my_file, lines):
    """F-028 (b), ADDRESS level, after 12 wrong passwords of different users.  (outcome, reason)."""
    if not any("⛔ BANNED address of %s" % ADDR in r for r in lines):
        return S.FAIL, ("%d failed attempts of different users and the server does not say "
                        "«BANNED address»" % ADDRESS_LIMIT)
    if page.get("banned") != "yes":
        return S.FAIL, ("the reloaded page does not say the ban (data-banned=%s, outcome «%s»)"
                        % (page.get("banned"), page.get("outcome")))
    if "attempts exhausted" not in (page.get("warning") or ""):
        return S.FAIL, "the page is banned but the notice does not say so: «%s»" % page.get("warning")
    if page.get("hours") != "0" or not (page.get("minutes") or "").isdigit() \
            or not 1 <= int(page.get("minutes")) <= 15:
        return S.FAIL, "the notice says %s hours and %s minutes, not 15 minutes at most (first ban)" % (
            page.get("hours"), page.get("minutes"))
    if ADDR not in (my_file or ""):
        return S.FAIL, "the server's ban file does not carry %s: «%s»" % (ADDR, my_file)
    return S.PASS, "banned: the page loads and says «attempts exhausted», %s hours %s min" % (
        page.get("hours"), page.get("minutes"))


def certify():
    ok = True

    def prova(what, real):
        nonlocal ok
        ok &= bool(real)
        print("%s %s" % ("⭐" if real else "⛔", what))
    ch = "c15027u1"
    fr = G.SENTENCE[0x07]
    def fl(user, n, a):
        return ("failed attempt from [192.168.0.2] as %s: %d of 5 for the user, %d of 12 for the address, "
                "0 of 30 for the IPv6 /48 within the window (§4.4-bis)" % (user, n, a))
    lines = ["PAM answered (request 3): refused", fl(ch, 1, 1)]
    prova("clear refusal ⇒ PASS", judge_refusal(False, fr, lines, ch, 0)[0] == S.PASS)
    prova("old line format (no counters) ⇒ FAIL", judge_refusal(
        False, fr, ["PAM answered (request 3): refused", "failed attempt from [192.168.0.2]: 1 of 3"], ch, 0)[0] == S.FAIL)
    prova("admitted ⇒ FAIL", judge_refusal(True, "Admitted", lines, ch, 0)[0] == S.FAIL)
    prova("session open ⇒ FAIL", judge_refusal(
        False, fr, lines + ["session open user=%s via=x" % ch], ch, 0)[0] == S.FAIL)
    prova("different sentence ⇒ FAIL", judge_refusal(False, "sent away", lines, ch, 0)[0] == S.FAIL)
    prova("processes ⇒ FAIL", judge_refusal(False, fr, lines, ch, 3)[0] == S.FAIL)
    prova("nonexistent, same sentence ⇒ PASS",
          judge_nonexistent(False, fr, fr, lines, "c15027u9", False)[0] == S.PASS)
    prova("nonexistent, different sentence ⇒ FAIL",
          judge_nonexistent(False, "unknown user", fr, lines, "c15027u9", False)[0] == S.FAIL)
    prova("nonexistent but exists ⇒ FAIL",
          judge_nonexistent(False, fr, fr, lines, "c15027u9", True)[0] == S.FAIL)
    g0f = "refused: this session's slot shows as " + G.SENTENCE[0x0F]
    prova("0x0F without ban ⇒ PASS", judge_already_active(False, g0f, {"banned": "no"}, lines)[0] == S.PASS)
    prova("0x0F with ban ⇒ FAIL", judge_already_active(
        False, g0f, {"banned": "yes"}, lines + ["⛔ BANNED address of [192.168.0.2] for 15 minutes"])[0] == S.FAIL)
    s8 = G.SENTENCE[0x08]
    lu = [fl(ch, k, k) for k in range(1, 6)] + [
        "⛔ BANNED user on this address of [192.168.0.2] as %s for 15 minutes (ban number 1)" % ch,
        "⛔ user on this address of [192.168.0.2] BANNED: 15 minutes remain, PAM is not queried (§4.4-bis)"]
    pn = {"banned": "no"}
    prova("user ban seen ⇒ PASS", judge_ban_user(lu, s8, pn)[0] == S.PASS)
    prova("user ban: 6th reached PAM ⇒ FAIL",
          judge_ban_user(lu + ["PAM answered (request 9): refused"], s8, pn)[0] == S.FAIL)
    prova("user ban: no BANNED line ⇒ FAIL", judge_ban_user(lu[:5], s8, pn)[0] == S.FAIL)
    prova("user ban: 6th without 0x08 ⇒ FAIL", judge_ban_user(lu, fr, pn)[0] == S.FAIL)
    prova("user ban banned the address ⇒ FAIL", judge_ban_user(lu, s8, {"banned": "yes"})[0] == S.FAIL)
    rb = [fl("c15027u%d" % k, 1, k) for k in range(1, 13)] + [
        "⛔ BANNED address of [192.168.0.2] for 15 minutes (ban number 1)"]
    pb = {"banned": "yes", "warning": "attempts exhausted: … There are still", "hours": "0", "minutes": "15"}
    prova("address ban seen ⇒ PASS", judge_ban_address(pb, "[192.168.0.2] 1790000000", rb)[0] == S.PASS)
    prova("page not banned ⇒ FAIL", judge_ban_address(dict(pb, banned="no"), "[192.168.0.2] 1", rb)[0] == S.FAIL)
    prova("no BANNED line ⇒ FAIL", judge_ban_address(pb, "[192.168.0.2] 1", [])[0] == S.FAIL)
    prova("12 hours (the 1.0) ⇒ FAIL",
          judge_ban_address(dict(pb, hours="12", minutes="0"), "[192.168.0.2] 1", rb)[0] == S.FAIL)
    prova("file without address ⇒ FAIL", judge_ban_address(pb, "", rb)[0] == S.FAIL)
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
    return t.strip().endswith("yes")


def send_without_reload(s, user, password, cap=30):
    r = s.g.js(S.VERI.JS_ENTER, user, password)
    if r != "sent":
        return None, {"outcome": "form not filled in: %s" % r}
    fine = time.time() + cap
    st = {}
    while time.time() < fine:
        time.sleep(0.5)
        st = s.state()
        if st.get("outcome_class") == "good" and (st.get("outcome") or "").startswith("Admitted"):
            return True, st
        if st.get("outcome_class") == "bad" and G.SENTENCE[0x07] not in (st.get("outcome") or "") \
                and "Collego" not in (st.get("outcome") or ""):
            return False, st
    return (False if st.get("outcome_class") == "bad" else None), st


def body(o, E):
    srv = G.MyServer(o.box)
    if not srv.is_on():
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
        ok, m = A.pr.do_open()
        if not ok:
            raise S.Blocked("the G8 server's page does not open: " + m)

        # ── F-027: wrong password ───────────────────────────────────────────
        sign = srv.log_line_list()
        adm, st = G.try_login(A, chi, wrong())
        time.sleep(1)
        lines = srv.log_from(sign)
        outcome_f027 = st.get("outcome")
        e, r = judge_refusal(adm, outcome_f027, lines, chi, processes_of(A.sc, chi))
        ev = [A.save_text("f027-server.txt", lines)]
        E.put("F-027", e, r, expected="«%s», no session, attempt counted" % G.SENTENCE[0x07],
                observed=r, evidence=[x for x in ev if x])

        # ── N-1: nonexistent user ───────────────────────────────────────────
        fake = "c15027u%d" % random.randint(10000, 99999)
        sign = srv.log_line_list()
        adm, st = G.try_login(A, fake, wrong())
        time.sleep(1)
        lines = srv.log_from(sign)
        e, r = judge_nonexistent(adm, st.get("outcome"), outcome_f027, lines, fake,
                                   path_exists(A.sc, fake))
        ev = [A.save_text("n1-server.txt", lines)]
        E.put("N-1", e, r, expected="the same sentence as the wrong password, counted, no session",
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
                G.try_login(B, chi, wrong())
            G.nudge(A)
            adm, st = G.try_login(B, chi, A.password)
            time.sleep(1.5)
            page = G.load(B.g, o.url)
            lines = srv.log_from(sign)
            ev_texts["f028-gia-attiva-server.txt"] = lines
            e1, r1 = judge_already_active(adm, st.get("outcome"), page, lines)
            print("   F-028 (0x0F does not count): %s — %s" % (e1, r1), flush=True)
            if page.get("banned") == "yes":
                print("   ⚠ banned already here: unblocking to be able to look at the rest: %s"
                      % srv.unblock(), flush=True)

            # the counters of the product are REAL (5 user / 12 address): everything the
            # tests before left is taken back to zero, so the parts do not carry over
            print("   counters back to zero: %s" % srv.unblock(), flush=True)

            # ── F-028 (2a): USER level — 5 wrong passwords ⇒ ban of the user, the 6th
            #    (RIGHT password) is refused without PAM; the address's page is NOT banned
            sign = srv.log_line_list()
            for _ in range(USER_LIMIT):
                G.try_login(B, chi, wrong())
            sixth_admitted, sixth_reply = send_without_reload(B, chi, A.password)
            time.sleep(1)
            page_u = G.load(B.g, o.url)
            lines_u = srv.log_from(sign)
            ev_texts["f028-ban-user-server.txt"] = lines_u
            eu, ru = judge_ban_user(lines_u, sixth_reply.get("outcome"), page_u)
            if sixth_admitted is True:
                eu, ru = S.FAIL, "the RIGHT password was admitted although the user was banned"
            print("   F-028 (user level): %s — %s" % (eu, ru), flush=True)
            print("   counters back to zero: %s" % srv.unblock(), flush=True)

            # ── F-028 (2b): ADDRESS level — 12 wrong passwords of DIFFERENT users ⇒ ban
            sign = srv.log_line_list()
            others = set()
            while len(others) < ADDRESS_LIMIT:
                others.add("c15027u%d" % random.randint(10000, 99999))
            for u in sorted(others):
                adm, st = G.try_login(B, u, wrong())
            fourth_admitted, fourth_reply = send_without_reload(B, chi, A.password)
            time.sleep(1)
            page = G.load(B.g, o.url)
            lines = srv.log_from(sign)
            ev_texts["f028-ban-server.txt"] = lines
            my_file = srv.file_ban()
            e2, r2 = judge_ban_address(page, my_file, lines)
            # the next attempt, with the RIGHT password
            if e2 == S.PASS and (fourth_admitted is not False
                                 or G.SENTENCE[0x08] not in (fourth_reply.get("outcome") or "")):
                e2, r2 = S.FAIL, ("banned, but the RIGHT password from that address receives: "
                                  "admitted=%s «%s» (expected 0x08)" % (fourth_admitted, fourth_reply.get("outcome")))
            # ⛔ the 85xx not touched
            p85 = G.load(B.g, "https://%s:%d/" % (o.host, S.PORTS[o.box]))
            ban85_after = srv.file_ban(G.BAN_85XX)
            if e2 == S.PASS and (p85.get("banned") != "no" or ADDR in ban85_after):
                e2, r2 = S.FAIL, ("the G8 server's ban touched %d: data-banned=%s, file «%s»"
                                  % (S.PORTS[o.box], p85.get("banned"), ban85_after))
            alive_a = G.read_page(A.g)
            # the unblock
            unb = srv.unblock()
            page2 = G.load(B.g, o.url)
            if e2 == S.PASS and (not unb.startswith("REMOVED") or page2.get("banned") != "no"):
                e2, r2 = S.FAIL, "the unblock from the socket does not reopen: «%s», data-banned=%s" % (
                    unb, page2.get("banned"))
            r2 = "user level: %s: %s · address level: %s" % (eu, ru, r2)
            if eu != S.PASS and e2 == S.PASS:
                e2 = eu
            counts = address_counts(lines)
            oss = ("%s · address counter %s · fourth (right password): «%s» · %d data-banned=%s, "
                   "file «%s» (before «%s») · A during the ban: session=%s «%s» · unblock «%s»"
                   % (r2, counts, (fourth_reply.get("outcome") or "")[:90], S.PORTS[o.box],
                      p85.get("banned"), ban85_after, ban85, alive_a.get("session"),
                      (alive_a.get("outcome") or "")[:40], unb))
            if e1 == S.FAIL or e2 == S.FAIL:
                ef = S.FAIL
            elif e1 == S.BLOCKED or e2 == S.BLOCKED:
                ef = S.BLOCKED
            else:
                ef = S.PASS
            ev = [B.save_text(n, t) for n, t in ev_texts.items()]
            ev.append(B.save_text("f028-pagine.json", json.dumps(
                {"banned_page": page, "user_page": page_u, "sixth": sixth_reply, "fourth": fourth_reply, "85xx": p85, "sbloccata": page2},
                ensure_ascii=False, indent=1)))
            E.put("F-028", ef, "0x0F does not count: %s · ban: %s" % (r1, r2),
                    expected="0x0F does not count; 5 errors of a user ⇒ user ban (0x08, no PAM); 12 errors of the "
                           "address ⇒ address ban said by the page, 0x08 on the right password, 85xx intact, "
                           "the unblock reopens",
                    observed=oss, evidence=ev)

            if o.fault:
                # F-028: the ban is removed secretly before the judge looks
                sign = srv.log_line_list()
                for k in range(ADDRESS_LIMIT):
                    G.try_login(B, "c15027u%d" % (90000 + k), wrong())
                lines = srv.log_from(sign)
                real = any("⛔ BANNED address of %s" % ADDR in x for x in lines)
                srv.unblock()                                   # ⛔ the fault
                page = G.load(B.g, o.url)
                eg, rg = judge_ban_address(page, srv.file_ban(), lines)
                E.fault("F-028", (eg != S.PASS) if real else None,
                         "real ban (%s), removed before the judgment ⇒ the judge says %s: %s"
                         % (real, eg, rg))
                srv.unblock()
                # F-027: the «wrong» password is the right one (A says farewell first)
                A.g.navigate("about:blank")
                time.sleep(3)
                sign = srv.log_line_list()
                adm, st = G.try_login(B, chi, B.password)
                time.sleep(1)
                lines = srv.log_from(sign)
                eg, rg = judge_refusal(adm, st.get("outcome"), lines, chi, processes_of(A.sc, chi))
                E.fault("F-027", eg == S.FAIL if adm is not None else None,
                         "right password passed off as wrong ⇒ the judge says %s: %s" % (eg, rg))
                # N-1: the «nonexistent» one is the real user with the right password
                sign = srv.log_line_list()
                adm, st = G.try_login(A, chi, A.password)
                time.sleep(1)
                lines = srv.log_from(sign)
                eg, rg = judge_nonexistent(adm, st.get("outcome"), outcome_f027, lines, chi,
                                             path_exists(A.sc, chi))
                E.fault("N-1", eg == S.FAIL if adm is not None else None,
                         "real user instead of the nonexistent one ⇒ the judge says %s: %s" % (eg, rg))
    print("   final unblock: %s" % srv.unblock(), flush=True)


if __name__ == "__main__":
    sys.exit(S.run(__doc__, FUNCTIONS, body, certify))
