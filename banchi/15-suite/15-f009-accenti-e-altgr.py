#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f009 — F-009 LAYOUT, ACCENTS, AltGr (Italian layout)

    python3 15-f009-accenti-e-altgr.py --scatola gnome --browser chrome [--guasto]

⭐ WHAT THE PRODUCT PROMISES (verified in the code, 24 Sep 2026):
   · the page declares the layout in `ATTACCA` from the browser's LANGUAGE
     (`pagina.html` `disposizione()`: `navigator.language` «it-IT» ⇒ «it»);
   · letters travel as LETTERS (`LETTERA`, the character of `ev.key`);
     Shift, CapsLock and AltGr are not sent: «they serve to make the letter»
     (`cl_su_keydown`, SPECIFICHE §7.3);
   · the server looks up the character in the session's layout
     (`tastiera.c` `tastiera_posizioni_per`, all the levels) and presses its
     keys; the negotiated layout is put into the session (`input.c`
     `input_disposizione`: GSettings on GNOME, keymap of the virtual keyboard
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

FAULT (--guasto, same session), two injections and a single verdict:
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

G2 = S._carica("g2scena", os.path.join(S.QUI, "15-g2-scena.py"))

FUNZIONI = ("F-009",)
#   character, code of the position (Italian keyboard), keyCode, modifier
TASTIERA_IT = (
    ("è", "BracketLeft", 219, None), ("à", "Quote", 222, None),
    ("ò", "Semicolon", 186, None), ("ù", "Backslash", 220, None),
    ("é", "BracketLeft", 219, "Shift"), ("ç", "Semicolon", 186, "Shift"),
    ("°", "Quote", 222, "Shift"), ("§", "Backslash", 220, "Shift"),
    ("@", "Semicolon", 186, "AltGraph"), ("#", "Quote", 222, "AltGraph"),
    ("[", "BracketLeft", 219, "AltGraph"), ("]", "BracketRight", 221, "AltGraph"),
    ("€", "KeyE", 69, "AltGraph"),
    ("È", "BracketLeft", 219, "CapsLock"),
)
DICHIARATI_NON_SCRIVIBILI = {"È"}     # xkb `it` basic has no Egrave on any level
SCRIVIBILI = "".join(c for c, _k, _v, _m in TASTIERA_IT if c not in DICHIARATI_NON_SCRIVIBILI)
TUTTI = "".join(c for c, _k, _v, _m in TASTIERA_IT)
ATTESA_S = 8.0
# ⛔ Phase 16 §12 (25 Sep 2026): the log no longer writes WHICH character — it was
#    the user's keystroke.  It says «a character is not producible…»: in the scene
#    the non-producible one is only one (È), and it is counted.  The old form is still read.
PRODUCIBILE = re.compile(r"(?:U\+([0-9A-Fa-f]{4,6})|a character) is not producible with "
                         r"layout ([^:]*)")
IN_VIGORE = re.compile(r"layout in force[^:]*: (.*)$")

# ── D-015: the user's settings, read FROM DISK as they would read them
CHIAVI_IS = ("sources", "mru-sources", "current", "xkb-options")
LEGGI_IMPOSTAZIONI = (
    "export HOME=/home/%(c)s; p=$(mktemp); echo user-db:user > \"$p\"; "
    "for k in " + " ".join(CHIAVI_IS) + "; do "
    "v=$(DCONF_PROFILE=\"$p\" gsettings get org.gnome.desktop.input-sources \"$k\" "
    "2>/dev/null) || v='(non letta)'; echo \"is.$k=$v\"; done; rm -f \"$p\"; "
    # ⚠ of kxkbrc only the [Layout] group (the layout): Plasma can create
    #   the file by itself at first login, and the rest is not ours
    "v=$(sed -n '/^\\[Layout\\]/,/^\\[/p' \"$HOME/.config/kxkbrc\" 2>/dev/null | "
    "grep -v '^\\[' | grep -v '^[#;]' | grep . | sort | tr '\\n' ' '); "
    "echo \"kxkbrc=${v:-assente}\"")
SCRIVI_GUASTO = (
    "export HOME=/home/%(c)s; p=$(mktemp); echo user-db:user > \"$p\"; "
    "DCONF_PROFILE=\"$p\" gsettings set org.gnome.desktop.input-sources sources "
    "\"[('xkb','de')]\" 2>&1 | head -2; rm -f \"$p\"; mkdir -p \"$HOME/.config\"; "
    "printf '\\n[Layout]\\nLayoutList=de\\n' >> \"$HOME/.config/kxkbrc\"; "
    "echo scritto")


def leggi_impostazioni(testo):
    """{key: value} from the «name=value» lines; None if there is nothing."""
    d = {}
    for r in (testo or "").splitlines():
        if "=" in r and (r.startswith("is.") or r.startswith("kxkbrc=")):
            k, v = r.split("=", 1)
            d[k] = v.strip()
    return d or None


def giudica_impostazioni(prima, dopo):
    """(outcome, sentence): the user's settings must be the ones from BEFORE."""
    if prima is None or dopo is None:
        return S.BLOCKED, "the user's settings could not be read (%s)" % (
            "prima" if prima is None else "dopo")
    cambiate = ["%s: %s → %s" % (k, prima.get(k, "?"), dopo.get(k, "?"))
                for k in sorted(set(prima) | set(dopo)) if prima.get(k) != dopo.get(k)]
    if cambiate:
        return S.FAIL, ("⛔ USER'S SETTINGS TOUCHED (D-015): %s" % "; ".join(cambiate))
    return S.PASS, "user's settings intact (%s)" % ", ".join(
        "%s=%s" % (k, v) for k, v in sorted(prima.items()))


def impostazioni(s):
    c, t = s.come_utente("sh -c %s" % S._q(LEGGI_IMPOSTAZIONI % {"c": s.chi}), 60)
    return leggi_impostazioni(t) if c == 0 else None


def sequenza():
    p = []
    for c, code, vk, mod in TASTIERA_IT:
        tasto = G2.premi(c, code, vk)
        if mod == "CapsLock":
            p += G2.premi("CapsLock") + tasto + G2.premi("CapsLock")
        elif mod:
            p += G2.col(mod, tasto)
        else:
            p += tasto
    return p


def dichiarati(righe):
    """{character: layout} from the «is not producible» lines of the log."""
    d = {}
    anonimi = 0
    for r in righe:
        m = PRODUCIBILE.search(r)
        if m and m.group(1):
            d[chr(int(m.group(1), 16))] = m.group(2).strip()
        elif m:
            # ⭐ without a name: it holds for the first of the declared ones not yet seen
            resto = sorted(c for c in DICHIARATI_NON_SCRIVIBILI if c not in d)
            ch = resto[0] if resto else "?%d" % anonimi
            anonimi += 1
            d[ch] = m.group(2).strip()
    return d


def giudica(st, righe):
    """(outcome, sentence) from the value of the field and the log lines."""
    if not st or st.get("a") is None:
        return S.BLOCKED, "the scene did not tell the value of the field"
    a = st["a"]
    dic = dichiarati(righe)
    if a == TUTTI:
        return S.PASS, "a=%r (even «È» came out)" % a
    if a == SCRIVIBILI:
        mancanti_dichiarati = [c for c in DICHIARATI_NON_SCRIVIBILI if c in dic]
        if len(mancanti_dichiarati) == len(DICHIARATI_NON_SCRIVIBILI):
            return S.PASS, ("a=%r; «%s» not typeable with «%s» and it is DECLARED in the log"
                            % (a, "".join(mancanti_dichiarati), dic[mancanti_dichiarati[0]]))
        return S.FAIL, ("a=%r: «%s» vanished SILENTLY (no «is not producible» line)"
                        % (a, "".join(DICHIARATI_NON_SCRIVIBILI)))
    mancano = [c for c in SCRIVIBILI if c not in a]
    return S.FAIL, ("a=%r instead of %r · missing %s · declared not producible by the server: %s"
                    % (a, SCRIVIBILI, "".join(mancano) or "-",
                       ", ".join("%s (%s)" % kv for kv in dic.items()) or "none"))


def certifica():
    guai = []

    def prova(cosa, vero, det=""):
        print("   %s %s%s" % ("⭐ ok " if vero else "⛔ NO ", cosa, (" — " + det) if det else ""))
        if not vero:
            guai.append(cosa)
    riga_e = ("21:00:00.000 tastiera [c15009u1] U+00C8 is not producible with layout "
              "it [Italian]: NOTHING sent (RCP.md §7.3)")
    riga_u = riga_e.replace("U+00C8", "U+00E8").replace("it [Italian]", "us [English (US)]")
    prova("reading the log", dichiarati([riga_e]) == {"È": "it [Italian]"},
          repr(dichiarati([riga_e])))
    riga_n = ("21:00:00.000 tastiera [c15009u1] a character is not producible with "
              "layout it [Italian]: NOTHING sent (RCP.md §7.3; which one, is not written — phase 16 §12)")
    prova("reading the form without character (phase 16 §12)",
          dichiarati([riga_n]) == {"È": "it [Italian]"}, repr(dichiarati([riga_n])))
    prova("form without character, È declared ⇒ PASS",
          giudica({"a": SCRIVIBILI}, [riga_n])[0] == S.PASS)
    prova("form without character, È vanished silently ⇒ FAIL",
          giudica({"a": SCRIVIBILI}, [])[0] == S.FAIL)
    prova("all typed, È declared ⇒ PASS", giudica({"a": SCRIVIBILI}, [riga_e])[0] == S.PASS)
    prova("È typed too ⇒ PASS", giudica({"a": TUTTI}, [])[0] == S.PASS)
    prova("È vanished silently ⇒ FAIL", giudica({"a": SCRIVIBILI}, [])[0] == S.FAIL)
    prova("with «us» (è not producible) ⇒ FAIL",
          giudica({"a": SCRIVIBILI.replace("è", "")}, [riga_e, riga_u])[0] == S.FAIL)
    prova("a different letter ⇒ FAIL", giudica({"a": SCRIVIBILI.replace("@", "\"")}, [riga_e])[0]
          == S.FAIL)
    prova("no field ⇒ BLOCKED", giudica(None, [])[0] == S.BLOCKED)
    seq = sequenza()
    prova("the sequence carries every character", all(any(p[1] == c for p in seq)
                                                  for c in TUTTI))
    prova("AltGr down before «@»", seq[seq.index(("giu", "@", "Semicolon", 186)) - 1][1]
          == "AltGraph")
    # D-015
    uscita = ("is.sources=@a(ss) []\nis.mru-sources=@a(ss) []\nis.current=uint32 0\n"
              "is.xkb-options=@as []\nkxkbrc=assente\n")
    pr = leggi_impostazioni(uscita)
    prova("reading the settings", pr and pr["is.sources"] == "@a(ss) []"
          and pr["kxkbrc"] == "assente", repr(pr))
    prova("equal settings ⇒ PASS", giudica_impostazioni(pr, dict(pr))[0] == S.PASS)
    scritta = dict(pr, **{"is.sources": "[('xkb', 'it')]"})
    prova("input-sources written in the user ⇒ FAIL",
          giudica_impostazioni(pr, scritta)[0] == S.FAIL)
    prova("user's kxkbrc born ⇒ FAIL",
          giudica_impostazioni(pr, dict(pr, kxkbrc="LayoutList=it"))[0] == S.FAIL)
    prova("not read ⇒ BLOCKED", giudica_impostazioni(None, pr)[0] == S.BLOCKED)
    prova("nothing to read ⇒ None", leggi_impostazioni("sh: errore") is None)
    print("⛔ CERTIFICATION FAILED" if guai else "⭐ CERTIFIED")
    return 1 if guai else 0


# ═══════════════════════════════════════════════════════════════════════════
def prova_una(s, sc, mp, nome):
    """Types the sequence; returns (outcome, sentence, evidence, layouts in force)."""
    segno = s.segno_registro()
    st, foto, saltati, perche = G2.batti(
        s, sc, mp, sequenza(), nome, lambda q: q.get("a") in (TUTTI, SCRIVIBILI), ATTESA_S,
        saltabili=("AltGraph", "CapsLock"))
    righe = s.registro_da(segno) if segno is not None else []
    ev = [x for x in (foto, s.salva_testo("server-%s.txt" % nome, righe)) if x]
    if perche:
        return S.BLOCKED, perche, ev, []
    e, m = giudica(st, righe)
    if saltati:
        m += " · ⚠ not sent by this browser: %s" % ", ".join(
            sorted({x[1] for x in saltati}))
    return e, m, ev, righe


def disposizione_in_vigore(s, segno):
    righe = s.registro_da(segno) if segno is not None else []
    v = [IN_VIGORE.search(r).group(1).strip() for r in righe if IN_VIGORE.search(r)]
    rip = [r for r in righe if "FALLBACK" in r and "layout" in r]
    return v[-1] if v else "?", rip


def corpo(o, E):
    with S.Sessione(o, "009", E) as s:
        segno0 = s.segno_registro()
        # D-015: the user's settings BEFORE the session sees them
        prima = impostazioni(s)
        print("   user's settings, before: %s" % prima, flush=True)
        sc, mp, geo, dove = G2.prepara(s, o.porte_base + 7, lingua="it-IT")
        disp, rip = disposizione_in_vigore(s, segno0)
        print("   layout in force: %s%s" % (disp, " · ⚠ " + rip[-1][:200] if rip else ""),
              flush=True)
        e, m, ev, _r = prova_una(s, sc, mp, "accenti-sana")
        if e == S.FAIL:
            print("   ⚠ red (%s): redoing it to confirm" % m, flush=True)
            e2, m2, ev2, _r = prova_una(s, sc, mp, "accenti-sana-bis")
            ev += ev2
            if e2 == S.PASS:
                e, m = S.PASS, "⚠ RED at the first attempt (%s), green at the second: %s" % (m, m2)
            else:
                m = "red twice: %s · %s" % (m, m2)
        m = "[layout in force: %s%s] %s" % (
            disp, "; FALLBACK: " + rip[-1].split("] ", 1)[-1][:160] if rip else "", m)
        # D-015: and AFTER the pass, from disk, the same as before
        dopo = impostazioni(s)
        ei, mi = giudica_impostazioni(prima, dopo)
        p = s.salva_testo("impostazioni-utente.txt",
                          "before: %r\nafter:  %r\n%s" % (prima, dopo, mi))
        if p:
            ev.append(p)
        m += " · " + mi
        if ei == S.FAIL or (ei == S.BLOCKED and e == S.PASS):
            e = ei
        E.metti("F-009", e, m, atteso="«%s» in the field; «È» not typeable and declared; "
                "user's settings (input-sources, kxkbrc) the ones from before"
                % SCRIVIBILI, osservato=m, evidenze=([dove] if dove else []) + ev
                + ([s.salva_console()] if e != S.PASS else []))
        if o.guasto:
            # injection 1 (D-015): a simulated persistent write in the user
            _c, t = s.come_utente("sh -c %s" % S._q(SCRIVI_GUASTO % {"c": s.chi}), 60)
            dopo_g = impostazioni(s)
            eig, mig = giudica_impostazioni(prima, dopo_g)
            print("   FAULT 1, simulated persistent write (%s): %s"
                  % ((t or "").strip().replace("\n", " | ")[-120:], mig), flush=True)
            if eig == S.BLOCKED:
                E.guasto("F-009", None, "injection 1 (simulated persistent write) not "
                         "observable: %s" % mig)
                return
            visto_1 = eig == S.FAIL
            # injection 2: the browser in English
            segno1 = s.segno_registro()
            print("   FAULT: %s, and reattaching" % G2.metti_lingua(s.g, "en-US"), flush=True)
            ok, mm = s.entra()
            nl = s.g.js("return navigator.language") if ok else "?"
            if not ok or nl != "en-US":
                E.guasto("F-009", None, "the reattach in English did not succeed: %s (language %s)"
                         % (mm, nl))
                return
            disp_g, _rip = disposizione_in_vigore(s, segno1)
            eg, mg, evg, _r = prova_una(s, sc, mp, "accenti-guasto")
            visto_2 = None if eg == S.BLOCKED else eg == S.FAIL
            E.guasto("F-009", None if visto_2 is None else (visto_1 and visto_2),
                     "injection 1, simulated persistent write: %s — %s · injection 2, "
                     "browser in en-US, layout in force «%s»: %s"
                     % ("RED (seen)" if visto_1 else "⛔ NOT seen", mig, disp_g, mg),
                     atteso="red both: the user's settings changed; with "
                     "«us» the accents are not there", osservato=mig + " · " + mg,
                     evidenze=evg)


if __name__ == "__main__":
    sys.exit(S.esegui(__doc__, FUNZIONI, corpo, certifica))
