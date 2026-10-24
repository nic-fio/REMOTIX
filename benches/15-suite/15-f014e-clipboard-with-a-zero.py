#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f014e — A TEXT WITH A ZERO IN THE MIDDLE, COPIED BY AN APPLICATION OF THE SESSION

    python3 15-f014e-clipboard-with-a-zero.py --box kde --browser chrome [--fault]
    python3 15-f014e-clipboard-with-a-zero.py --certify

WHY IT EXISTS (24 Oct 2026, open defect of PIANO.md, fixed in `clipboard_kde.c` by 8031958d).  A zero byte is valid
UTF-8, but the text travels as a zero-terminated string: kept, it was announced shorter than its length and the reply
for «paste» read past the buffer.  The rule (as in `clipboard.c`, GNOME): a text with a zero in the middle is NOT
announced — one log line says so — and the session's clipboard process goes on.

The scene is the box's own desktop: `wl-copy` runs INSIDE the tenant's graphical session (`Session.in_session()`, the
way 15-f014 runs its programs) and the judgment is the tenant's server log (`log_mark()` / `log_from()`).

F-014E  (P1) the case.
        1. `printf 'abc\\0def' | wl-copy -t text/plain;charset=utf-8` ⇒ the log says «with a zero in the middle — not
           announced» and does NOT say «the session copied»; the tenant's child process (`--internal-child`) is the
           SAME one, alive.
        2. right after, a normal text with accents ⇒ «the session copied N bytes of text», N = its UTF-8 length
           (the clipboard goes on working).

FAULT (same session, after the healthy pass) — the CONTRAST, because the product has no bench switch that turns the
check off (neither `clipboard_kde.c` nor `clipboard.c` has BENCH code or getenv): what the 1.0 does is a text that
IS announced.  So:
  · a normal text (no zero) is copied and judged with the SAME judgment of the zero case ⇒ it is announced ⇒ RED;
  · and the judgment given the log of an announced zero text (what the 1.0 prints) ⇒ RED.
  Both RED ⇒ the fault pass is PASS (the test can give red).  The real contrast with the 1.0 binary is the other
  run (`REMOTIX_SUITE=<1.0 tree>` on a 1.0 box): there F-014E must be RED.

⚠ Applicability.  Written for KDE (wlr-data-control: `wl-copy` works in the session).  On the other desktops the same
case is tried: if the product writes NO line at all about the copy within 10 s (Mutter has no data-control, so
`wl-copy` is never served; or the desktop's module is another), the outcome is N/A (`S.NA`: neither green nor red, it
does not count for the exit code) on a suite that has `NA` (branch banchi-1-5); on the suite of package 1, which has
not, it falls back to BLOCKED.  Where a line does come («not announced»
in `clipboard.c`) the test is a real one.  Only Firefox and Chrome on the server (the phone has no `wl-copy`).
"""
import base64
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suite as S                                                     # noqa: E402

FUNCTIONS = ("F-014E",)
TYPE = "text/plain;charset=utf-8"
NOT_ANNOUNCED = "with a zero in the middle — not announced"
COPIED = "the session copied"
WAIT_LOG_S = 10.0
# «does not apply here»: the suite of branch banchi-1-5 has `S.NA` (N/A, neither green nor red); the suite of package 1
# has not, and there the outcome is BLOCKED (it is what package 1 uses for what cannot be judged).
NA = getattr(S, "NA", S.BLOCKED)


# ═══════════════════════════════════════════════════════════════════════════
#  THE PURE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════
def copied_lines(lines):
    return [l for l in lines if COPIED in l]


def refused_lines(lines):
    return [l for l in lines if NOT_ANNOUNCED in l]


def judge_zero(lines_zero, lines_normal, pids_before, pids_after, normal_bytes):
    """(outcome, why).  lines_zero: server-log lines after the zero copy; lines_normal: after the normal copy
    that follows; pids_*: the tenant's child process(es) before and after; normal_bytes: its UTF-8 length."""
    no, yes = refused_lines(lines_zero), copied_lines(lines_zero)
    if not no and not yes:
        return NA, ("not applicable on this desktop: the product wrote no line at all about the copy (no «%s», no «%s») "
                    "within %.0f s: wl-copy is not served here, or its clipboard module is another"
                    % (NOT_ANNOUNCED, COPIED, WAIT_LOG_S))
    if yes and not no:
        return S.FAIL, "the text with a zero was ANNOUNCED (what the 1.0 does): %s" % yes[0][-90:].strip()
    if yes:
        return S.FAIL, "«not announced» but ALSO «%s»: it was announced, cut" % COPIED
    if not pids_before or pids_after != pids_before:
        return S.FAIL, "the tenant's child process is not the same / not alive: before %r, after %r" % (pids_before, pids_after)
    want = "%s %d bytes of text" % (COPIED, normal_bytes)
    if not any(want in l for l in lines_normal):
        return S.FAIL, ("the zero text is refused, but the clipboard does not go on: «%s» is not in the log after a "
                        "normal copy" % want)
    return S.PASS, "zero text «not announced», child %s alive, and the next normal text is announced («%s»)" % (pids_after, want)


def certify():
    n = 30
    ok_zero = ["x ⛔ «text/plain;charset=utf-8»: 7 bytes with a zero in the middle — not announced.  Truncating here ..."]
    ok_norm = ["x ⭐ the session copied %d bytes of text" % n]
    old_zero = ["x ⭐ the session copied 7 bytes of text"]
    cases = [
        ("refused + alive + normal announced ⇒ PASS", judge_zero(ok_zero, ok_norm, "10 ", "10 ", n)[0] == S.PASS),
        ("announced zero (the 1.0) ⇒ FAIL", judge_zero(old_zero, ok_norm, "10 ", "10 ", n)[0] == S.FAIL),
        ("refused AND announced ⇒ FAIL", judge_zero(ok_zero + old_zero, ok_norm, "10 ", "10 ", n)[0] == S.FAIL),
        ("child changed ⇒ FAIL", judge_zero(ok_zero, ok_norm, "10 ", "11 ", n)[0] == S.FAIL),
        ("child gone ⇒ FAIL", judge_zero(ok_zero, ok_norm, "10 ", "", n)[0] == S.FAIL),
        ("no child before ⇒ FAIL", judge_zero(ok_zero, ok_norm, "", "", n)[0] == S.FAIL),
        ("normal copy not announced ⇒ FAIL", judge_zero(ok_zero, [], "10 ", "10 ", n)[0] == S.FAIL),
        ("normal copy with another length ⇒ FAIL", judge_zero(ok_zero, ok_norm, "10 ", "10 ", n + 1)[0] == S.FAIL),
        ("no line at all ⇒ N/A", judge_zero([], [], "10 ", "10 ", n)[0] == NA),
        ("N/A says so", judge_zero([], [], "10 ", "10 ", n)[1].startswith("not applicable")),
        ("log mark None ⇒ not usable (BLOCKED)", mark_ok(None) is False and mark_ok(0) is True),
        ("fault contrast: a normal text judged as the zero case ⇒ FAIL", judge_zero(ok_norm, ok_norm, "10 ", "10 ", n)[0] == S.FAIL),
    ]
    ok = True
    for name, real in cases:
        print("%s %s" % ("⭐" if real else "⛔", name))
        ok = ok and real
    return 0 if ok else 1


# ═══════════════════════════════════════════════════════════════════════════
#  THE SESSION
# ═══════════════════════════════════════════════════════════════════════════
def children(s):
    """pids of the tenant's child (`remotix --internal-child`), sorted, as a string."""
    c, t = s.sc.inside("pgrep -u %s -f -- --internal-child | sort -n | tr '\\n' ' '" % s.chi, 20)
    return (t or "").strip()


def copy_in_session(s, shell_line):
    # wl-copy forks to keep the selection: its stdout/stderr go to /dev/null, or the call would wait for them
    return s.in_session("( %s ) > /dev/null 2>&1" % shell_line, 40, background=False)


def wait_log(s, sign, needles, seconds=WAIT_LOG_S):
    """the tenant's server-log lines since `sign`, polled until one of `needles` is in them (or the time is up)."""
    end = time.time() + seconds
    lines = []
    while time.time() < end:
        lines = s.log_from(sign) or []
        if any(n in l for l in lines for n in needles):
            break
        time.sleep(0.5)
    time.sleep(1)                                          # a late «copied» line would be the failure
    return s.log_from(sign) or lines


def mark_ok(sign):
    """the pure part of need_mark(): a log mark that is None cannot delimit the lines of one copy."""
    return sign is not None


def need_mark(s):
    sign = s.log_mark()
    if not mark_ok(sign):
        raise S.Blocked("server log mark not readable")
    return sign


def zero_case(s):
    """copies b'abc\\0def' in the session; (lines)"""
    sign = need_mark(s)
    copy_in_session(s, "printf 'abc\\0def' | timeout 10 wl-copy -t '%s'" % TYPE)
    return wait_log(s, sign, (NOT_ANNOUNCED, COPIED))


def normal_case(s, tag):
    """copies a normal text with accents; (lines, its UTF-8 length)"""
    text = "%s àèìòù €ß→ «ÀÉ» %s" % (tag, os.urandom(3).hex())
    sign = need_mark(s)
    copy_in_session(s, "printf %%s %s | base64 -d | timeout 10 wl-copy -t '%s'" % (base64.b64encode(text.encode()).decode(), TYPE))
    n = len(text.encode())
    return wait_log(s, sign, ("%s %d bytes of text" % (COPIED, n),)), n


def body(o, E):
    if o.browser in ("phone", "android"):
        raise S.Blocked("the phone has no `wl-copy`: this test runs only on the server")
    with S.Session(o, "919", E) as s:
        ok, m = s.enter()
        if not ok:
            raise S.Blocked(m)
        time.sleep(3)                                     # the child hooks the session's clipboard
        c, t = s.in_session("command -v wl-copy", 20, background=False)
        if c != 0 or "wl-copy" not in (t or ""):
            why = "not applicable on this desktop: no wl-copy in the %s session: %s" % (o.box, (t or "")[-120:])
            E.put("F-014E", NA, why)
            if o.fault:
                E.put("F-014E", NA, why, passed="fault")
            return
        pids0 = children(s)
        print("   child process(es) before: %s" % pids0, flush=True)

        # ── P1 · F-014E, healthy ──────────────────────────────────────────
        lz = zero_case(s)
        pids1 = children(s)
        ln, nbytes = normal_case(s, "F014E")
        ev = [s.save_text("f014e-zero.txt", lz), s.save_text("f014e-normale.txt", ln)]
        e, why = judge_zero(lz, ln, pids0, pids1, nbytes)
        print("   zero case: refused lines %d · copied lines %d · child after: %s" % (len(refused_lines(lz)), len(copied_lines(lz)), pids1), flush=True)
        E.put("F-014E", e, why, expected="«%s», no «%s», child alive, next text announced" % (NOT_ANNOUNCED, COPIED),
              observed="; ".join(l[-100:] for l in lz[-3:]), evidence=[x for x in ev if x])
        if not o.fault:
            return
        if e == NA:                                        # nothing to contrast where the product says nothing
            E.put("F-014E", NA, why, passed="fault")
            return

        # ── THE FAULT: what the 1.0 does is a text that IS announced ──────
        lg, ng = normal_case(s, "F014EG")                  # a normal text, judged with the zero case's judgment
        s.save_text("f014e-guasto.txt", lg)
        red_live = judge_zero(lg, ln, pids0, children(s), ng)[0] == S.FAIL
        red_old = judge_zero(["x ⭐ %s 7 bytes of text" % COPIED], ln, pids0, pids0, nbytes)[0] == S.FAIL
        # red_old is only a REMINDER of what the 1.0 prints (judge_zero given that log); it does not decide the live
        # verdict. The real contrast with the 1.0 is the run on the 1.0 binary.
        E.fault("F-014E", red_live,
                "a text that IS announced (live: a normal copy judged as the zero case ⇒ %s; reminder, the log the 1.0 prints ⇒ %s)"
                % ("RED" if red_live else "GREEN", "RED" if red_old else "GREEN"),
                expected="RED", observed="live %s · 1.0 log %s" % (red_live, red_old))


if __name__ == "__main__":
    sys.exit(S.run(__doc__, FUNCTIONS, body, certify))
