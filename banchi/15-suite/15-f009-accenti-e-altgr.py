#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f009 — F-009 LAYOUT, ACCENTS, AltGr (Italian layout)

    python3 15-f009-accenti-e-altgr.py --box gnome --browser chrome [--fault]

⭐ WHAT THE PRODUCT PROMISES (verified in the code, 24 Sep 2026):
   · the page declares the layout in `ATTACH` from the browser's LANGUAGE
     (`pagina.html` `disposizione()`: `navigator.language` «it-IT» ⇒ «it»);
   · letters travel as LETTERS (`LETTER`, the character of `ev.key`);
     Shift, CapsLock and AltGr are not sent: «they serve to make the letter»
     (`cl_su_keydown`, SPECIFICHE §7.3);
   · the server looks up the character in the session's layout
     (`tastiera.c` `keyboard_positions_for`, all the levels) and presses its
     keys; the negotiated layout is put into the session (`input.c`
     `input_layout`: GSettings on GNOME, keymap of the virtual keyboard
     on wlroots);
   · ⛔ a character the layout does NOT have does not come out and the server WRITES it
     in the log («U+XXXX is not producible with layout …»): never a
     different letter, never a silence (SPECIFICHE §7.3, RCP §7.3).
   ⇒ With «it» (xkb `it` basic): è à ò ù (level 1), é ç ° § (Shift),
     @ # [ ] € (AltGr) ARE typed; «È» is NOT on any key ⇒ the expectation is
     that it does not come out AND that the log declares it (it is not a FAIL).

⭐ HOW: the browser in Italian (Firefox `intl.accept_languages`, Chrome
   `Emulation.setUserAgentOverride acceptLanguage`), we log in, and in the known
   scene (`15-g2-scena.py`, field «a» in firefox-esr inside the session) we
   type with REAL KEYS the characters as an Italian keyboard sends them:
   `key` = the character, `code` = the position (BracketLeft, Semicolon, Quote,
   Backslash, KeyE…), preceded by Shift / AltGr / CapsLock where needed.
   ⚠ DECLARED LIMIT: WebDriver (Marionette) has neither AltGraph nor CapsLock:
     with Firefox those two presses are not sent, and only the
     character the real keyboard would have given arrives (the page sends it anyway
     as a LETTER: it is the same path).  With Chrome (CDP) they are sent.
   The judgment: the value of the field READ IN THE SESSION, and for «È» the
   server log line; the photo is saved.

⭐ AND THE USER'S SETTINGS ARE NOT TOUCHED (D-015, the user's decision
   of 25 Sep 2026, on all the desktops): the negotiated layout holds for the
   SESSION, it is not written where the user would find it again logging in at the monitor.
   They are read FROM DISK, like the user, before the login and after the pass:
   `org.gnome.desktop.input-sources` (sources, mru-sources, current,
   xkb-options) of the user's dconf — read with a profile that has ONLY
   `user-db:user`, that is `~/.config/dconf/user` and nothing else — the
   `[Layout]` group of `~/.config/kxkbrc`.  They must be the ones from BEFORE, or F-009 is red
   even with all the right letters.

FAULT (--fault, same session), two injections and a single verdict:
   1. a simulated PERSISTENT WRITE — `sources` = de in the user's
      dconf (with their profile) and `[Layout] LayoutList=de` at the end
      of `~/.config/kxkbrc` — ⇒ the settings judge must give red;
   2. the browser goes back to ENGLISH (en-US) and REATTACHES: the page declares
      «us», the session takes the American layout, and the accents are not
      there ⇒ the letters judge must give red.
   Seen = both red.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suite as S                                                     # noqa: E402

G2 = S._load("g2scena", os.path.join(S.HERE, "15-g2-scena.py"))

FUNCTIONS = ("F-009",)
#   character, code of the position (Italian keyboard), keyCode, modifier
KEYBOARD_IT = (
    ("è", "BracketLeft", 219, None), ("à", "Quote", 222, None),
    ("ò", "Semicolon", 186, None), ("ù", "Backslash", 220, None),
    ("é", "BracketLeft", 219, "Shift"), ("ç", "Semicolon", 186, "Shift"),
    ("°", "Quote", 222, "Shift"), ("§", "Backslash", 220, "Shift"),
    ("@", "Semicolon", 186, "AltGraph"), ("#", "Quote", 222, "AltGraph"),
    ("[", "BracketLeft", 219, "AltGraph"), ("]", "BracketRight", 221, "AltGraph"),
    ("€", "KeyE", 69, "AltGraph"),
    ("È", "BracketLeft", 219, "CapsLock"),
)
DECLARED_UNWRITABLE = {"È"}     # xkb `it` basic has no Egrave on any level
WRITABLE = "".join(c for c, _k, _v, _m in KEYBOARD_IT if c not in DECLARED_UNWRITABLE)
ALL = "".join(c for c, _k, _v, _m in KEYBOARD_IT)
WAIT_S = 8.0
# ⛔ Phase 16 §12 (25 Sep 2026): the log no longer writes WHICH character — it was
#    the user's keystroke.  It says «a character is not producible…»: in the scene
#    the non-producible one is only one (È), and it is counted.  The old form is still read.
PRODUCIBLE = re.compile(r"(?:U\+([0-9A-Fa-f]{4,6})|a character) is not producible with "
                         r"layout ([^:]*)")
IN_EFFECT = re.compile(r"layout in force[^:]*: (.*)$")

# ── D-015: the user's settings, read FROM DISK as they would read them
IS_KEYS = ("sources", "mru-sources", "current", "xkb-options")
READ_SETTINGS = (
    "export HOME=/home/%(c)s; p=$(mktemp); echo user-db:user > \"$p\"; "
    "for k in " + " ".join(IS_KEYS) + "; do "
    "v=$(DCONF_PROFILE=\"$p\" gsettings get org.gnome.desktop.input-sources \"$k\" "
    "2>/dev/null) || v='(non letta)'; echo \"is.$k=$v\"; done; rm -f \"$p\"; "
    # ⚠ of kxkbrc only the [Layout] group (the layout): Plasma can create
    #   the file by itself at first login, and the rest is not ours
    "v=$(sed -n '/^\\[Layout\\]/,/^\\[/p' \"$HOME/.config/kxkbrc\" 2>/dev/null | "
    "grep -v '^\\[' | grep -v '^[#;]' | grep . | sort | tr '\\n' ' '); "
    "echo \"kxkbrc=${v:-assente}\"")
WRITE_FAULT = (
    "export HOME=/home/%(c)s; p=$(mktemp); echo user-db:user > \"$p\"; "
    "DCONF_PROFILE=\"$p\" gsettings set org.gnome.desktop.input-sources sources "
    "\"[('xkb','de')]\" 2>&1 | head -2; rm -f \"$p\"; mkdir -p \"$HOME/.config\"; "
    "printf '\\n[Layout]\\nLayoutList=de\\n' >> \"$HOME/.config/kxkbrc\"; "
    "echo scritto")


def read_settings(text):
    """{key: value} from the «name=value» lines; None if there is nothing."""
    d = {}
    for r in (text or "").splitlines():
        if "=" in r and (r.startswith("is.") or r.startswith("kxkbrc=")):
            k, v = r.split("=", 1)
            d[k] = v.strip()
    return d or None


def judge_settings(before, after):
    """(outcome, sentence): the user's settings must be the ones from BEFORE."""
    if before is None or after is None:
        return S.BLOCKED, "the user's settings could not be read (%s)" % (
            "before" if before is None else "after")
    changed = ["%s: %s → %s" % (k, before.get(k, "?"), after.get(k, "?"))
                for k in sorted(set(before) | set(after)) if before.get(k) != after.get(k)]
    if changed:
        return S.FAIL, ("⛔ USER'S SETTINGS TOUCHED (D-015): %s" % "; ".join(changed))
    return S.PASS, "user's settings intact (%s)" % ", ".join(
        "%s=%s" % (k, v) for k, v in sorted(before.items()))


def settings(s):
    c, t = s.as_user("sh -c %s" % S._q(READ_SETTINGS % {"c": s.chi}), 60)
    return read_settings(t) if c == 0 else None


def sequence():
    p = []
    for c, code, vk, mod in KEYBOARD_IT:
        keystroke = G2.press(c, code, vk)
        if mod == "CapsLock":
            p += G2.press("CapsLock") + keystroke + G2.press("CapsLock")
        elif mod:
            p += G2.clr(mod, keystroke)
        else:
            p += keystroke
    return p


def declared(lines):
    """{character: layout} from the «is not producible» lines of the log."""
    d = {}
    anonymous = 0
    for r in lines:
        m = PRODUCIBLE.search(r)
        if m and m.group(1):
            d[chr(int(m.group(1), 16))] = m.group(2).strip()
        elif m:
            # ⭐ without a name: it holds for the first of the declared ones not yet seen
            rest = sorted(c for c in DECLARED_UNWRITABLE if c not in d)
            ch = rest[0] if rest else "?%d" % anonymous
            anonymous += 1
            d[ch] = m.group(2).strip()
    return d


def judge(st, lines):
    """(outcome, sentence) from the value of the field and the log lines."""
    if not st or st.get("a") is None:
        return S.BLOCKED, "the scene did not tell the value of the field"
    a = st["a"]
    decl = declared(lines)
    if a == ALL:
        return S.PASS, "a=%r (even «È» came out)" % a
    if a == WRITABLE:
        declared_missing = [c for c in DECLARED_UNWRITABLE if c in decl]
        if len(declared_missing) == len(DECLARED_UNWRITABLE):
            return S.PASS, ("a=%r; «%s» not typeable with «%s» and it is DECLARED in the log"
                            % (a, "".join(declared_missing), decl[declared_missing[0]]))
        return S.FAIL, ("a=%r: «%s» vanished SILENTLY (no «is not producible» line)"
                        % (a, "".join(DECLARED_UNWRITABLE)))
    missing = [c for c in WRITABLE if c not in a]
    return S.FAIL, ("a=%r instead of %r · missing %s · declared not producible by the server: %s"
                    % (a, WRITABLE, "".join(missing) or "-",
                       ", ".join("%s (%s)" % kv for kv in decl.items()) or "none"))


def certify():
    troubles = []

    def prova(what, real, det=""):
        print("   %s %s%s" % ("⭐ ok " if real else "⛔ NO ", what, (" — " + det) if det else ""))
        if not real:
            troubles.append(what)
    line_e = ("21:00:00.000 keyboard [c15009u1] U+00C8 is not producible with layout "
              "it [Italian]: NOTHING sent (RCP.md §7.3)")
    line_u = line_e.replace("U+00C8", "U+00E8").replace("it [Italian]", "us [English (US)]")
    prova("reading the log", declared([line_e]) == {"È": "it [Italian]"},
          repr(declared([line_e])))
    line_n = ("21:00:00.000 keyboard [c15009u1] a character is not producible with "
              "layout it [Italian]: NOTHING sent (RCP.md §7.3; which one, is not written — phase 16 §12)")
    prova("reading the form without character (phase 16 §12)",
          declared([line_n]) == {"È": "it [Italian]"}, repr(declared([line_n])))
    prova("form without character, È declared ⇒ PASS",
          judge({"a": WRITABLE}, [line_n])[0] == S.PASS)
    prova("form without character, È vanished silently ⇒ FAIL",
          judge({"a": WRITABLE}, [])[0] == S.FAIL)
    prova("all typed, È declared ⇒ PASS", judge({"a": WRITABLE}, [line_e])[0] == S.PASS)
    prova("È typed too ⇒ PASS", judge({"a": ALL}, [])[0] == S.PASS)
    prova("È vanished silently ⇒ FAIL", judge({"a": WRITABLE}, [])[0] == S.FAIL)
    prova("with «us» (è not producible) ⇒ FAIL",
          judge({"a": WRITABLE.replace("è", "")}, [line_e, line_u])[0] == S.FAIL)
    prova("a different letter ⇒ FAIL", judge({"a": WRITABLE.replace("@", "\"")}, [line_e])[0]
          == S.FAIL)
    prova("no field ⇒ BLOCKED", judge(None, [])[0] == S.BLOCKED)
    seq = sequence()
    prova("the sequence carries every character", all(any(p[1] == c for p in seq)
                                                  for c in ALL))
    prova("AltGr down before «@»", seq[seq.index(("giu", "@", "Semicolon", 186)) - 1][1]
          == "AltGraph")
    # D-015
    output = ("is.sources=@a(ss) []\nis.mru-sources=@a(ss) []\nis.current=uint32 0\n"
              "is.xkb-options=@as []\nkxkbrc=assente\n")
    pr = read_settings(output)
    prova("reading the settings", pr and pr["is.sources"] == "@a(ss) []"
          and pr["kxkbrc"] == "assente", repr(pr))
    prova("equal settings ⇒ PASS", judge_settings(pr, dict(pr))[0] == S.PASS)
    written = dict(pr, **{"is.sources": "[('xkb', 'it')]"})
    prova("input-sources written in the user ⇒ FAIL",
          judge_settings(pr, written)[0] == S.FAIL)
    prova("user's kxkbrc born ⇒ FAIL",
          judge_settings(pr, dict(pr, kxkbrc="LayoutList=it"))[0] == S.FAIL)
    prova("not read ⇒ BLOCKED", judge_settings(None, pr)[0] == S.BLOCKED)
    prova("nothing to read ⇒ None", read_settings("sh: errore") is None)
    print("⛔ CERTIFICATION FAILED" if troubles else "⭐ CERTIFIED")
    return 1 if troubles else 0


# ═══════════════════════════════════════════════════════════════════════════
def test_one(s, sc, mp, name):
    """Types the sequence; returns (outcome, sentence, evidence, layouts in force)."""
    sign = s.log_mark()
    st, photo, skipped, why = G2.beat(
        s, sc, mp, sequence(), name, lambda q: q.get("a") in (ALL, WRITABLE), WAIT_S,
        skippable=("AltGraph", "CapsLock"))
    lines = s.log_from(sign) if sign is not None else []
    ev = [x for x in (photo, s.save_text("server-%s.txt" % name, lines)) if x]
    if why:
        return S.BLOCKED, why, ev, []
    e, m = judge(st, lines)
    if skipped:
        m += " · ⚠ not sent by this browser: %s" % ", ".join(
            sorted({x[1] for x in skipped}))
    return e, m, ev, lines


def active_layout(s, sign):
    lines = s.log_from(sign) if sign is not None else []
    v = [IN_EFFECT.search(r).group(1).strip() for r in lines if IN_EFFECT.search(r)]
    rip = [r for r in lines if "FALLBACK" in r and "layout" in r]
    return v[-1] if v else "?", rip


def body(o, E):
    with S.Session(o, "009", E) as s:
        mark0 = s.log_mark()
        # D-015: the user's settings BEFORE the session sees them
        before = settings(s)
        print("   user's settings, before: %s" % before, flush=True)
        sc, mp, geo, dove = G2.prepare(s, o.base_port + 7, language="it-IT")
        avail, rip = active_layout(s, mark0)
        print("   layout in force: %s%s" % (avail, " · ⚠ " + rip[-1][:200] if rip else ""),
              flush=True)
        e, m, ev, _r = test_one(s, sc, mp, "accenti-sana")
        if e == S.FAIL:
            print("   ⚠ red (%s): redoing it to confirm" % m, flush=True)
            e2, m2, ev2, _r = test_one(s, sc, mp, "accenti-sana-bis")
            ev += ev2
            if e2 == S.PASS:
                e, m = S.PASS, "⚠ RED at the first attempt (%s), green at the second: %s" % (m, m2)
            else:
                m = "red twice: %s · %s" % (m, m2)
        m = "[layout in force: %s%s] %s" % (
            avail, "; FALLBACK: " + rip[-1].split("] ", 1)[-1][:160] if rip else "", m)
        # D-015: and AFTER the pass, from disk, the same as before
        after = settings(s)
        ei, mi = judge_settings(before, after)
        p = s.save_text("impostazioni-utente.txt",
                          "before: %r\nafter:  %r\n%s" % (before, after, mi))
        if p:
            ev.append(p)
        m += " · " + mi
        if ei == S.FAIL or (ei == S.BLOCKED and e == S.PASS):
            e = ei
        E.put("F-009", e, m, expected="«%s» in the field; «È» not typeable and declared; "
                "user's settings (input-sources, kxkbrc) the ones from before"
                % WRITABLE, observed=m, evidence=([dove] if dove else []) + ev
                + ([s.save_console()] if e != S.PASS else []))
        if o.fault:
            # injection 1 (D-015): a simulated persistent write in the user
            _c, t = s.as_user("sh -c %s" % S._q(WRITE_FAULT % {"c": s.chi}), 60)
            after_g = settings(s)
            eig, mig = judge_settings(before, after_g)
            print("   FAULT 1, simulated persistent write (%s): %s"
                  % ((t or "").strip().replace("\n", " | ")[-120:], mig), flush=True)
            if eig == S.BLOCKED:
                E.fault("F-009", None, "injection 1 (simulated persistent write) not "
                         "observable: %s" % mig)
                return
            seen_1 = eig == S.FAIL
            # injection 2: the browser in English
            mark1 = s.log_mark()
            print("   FAULT: %s, and reattaching" % G2.set_language(s.g, "en-US"), flush=True)
            ok, mm = s.enter()
            nl = s.g.js("return navigator.language") if ok else "?"
            if not ok or nl != "en-US":
                E.fault("F-009", None, "the reattach in English did not succeed: %s (language %s)"
                         % (mm, nl))
                return
            avail_g, _rip = active_layout(s, mark1)
            eg, mg, evg, _r = test_one(s, sc, mp, "accenti-guasto")
            seen_2 = None if eg == S.BLOCKED else eg == S.FAIL
            E.fault("F-009", None if seen_2 is None else (seen_1 and seen_2),
                     "injection 1, simulated persistent write: %s — %s · injection 2, "
                     "browser in en-US, layout in force «%s»: %s"
                     % ("RED (seen)" if seen_1 else "⛔ NOT seen", mig, avail_g, mg),
                     expected="red both: the user's settings changed; with "
                     "«us» the accents are not there", observed=mig + " · " + mg,
                     evidence=evg)


if __name__ == "__main__":
    sys.exit(S.run(__doc__, FUNCTIONS, body, certify))
