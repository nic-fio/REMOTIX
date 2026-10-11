#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f029 — F-029 DANGEROUS ENTRIES ABSENT

    python3 15-f029-voci-pericolose-assenti.py --box kde --browser chrome [--fault]

EXPECTED (`DECISIONI.md` §4.7 and §4.1-ter): in the desktop's exit menu there
are NO lock, suspend (and hibernate, hybrid sleep), restart, shut down
— nor «Switch user» (the user's decision of 21 Sep 2026: «the only entry
that must remain is logout»); «Exit» (Log Out) IS there.

HOW IT IS LOOKED AT — the menu is REALLY OPENED from the browser (real clicks on the canvas),
as the user does:
    gnome  system menu at the top right → power button
    kde    launcher (Kickoff) at the bottom left → «Leave»
    xfce   the panel's action button (the user's name, at the top right)
    lxqt   main menu at the bottom left → «Leave»
Every level is photographed (evidence for the user).

⭐ WHO JUDGES — THE OCR OF THE PHOTO (tesseract 5.5, extracted without root
   in /media/REMOTIX/strumenti/tesseract: see `15-g1b-comune.py`).  The menu
   is cut out as the blob that changes between the photo before and the one after the
   click, and is read; the forbidden entries are looked for in the lines read.
   ⚠ On GNOME the submenu has the TITLE «Power Off» (it is the header, not
     an entry): the topmost line saying only «Power Off» is discarded.
   ⚠ On GNOME the lock is an ICON without text, which the OCR does not read: for
     that one entry the FIELD judges — the entry appears only if GDM is on the
     system bus (`loginManager.js` canLock) and `disable-lock-screen` is
     false; read INSIDE the tenant's session.
   ⭐ And for all, the fields of belt 1 (`remotix-no-poweroff.rules`):
     logind CanPowerOff/CanReboot/CanSuspend/CanHibernate/CanHybridSleep
     asked AS THE TENANT must say «no» (or «na») — they are the answers
     from which GNOME and Plasma decide whether to show the entries.
   PASS = clean OCR + «Exit» read + right fields.  The menu that does not open
   (no blob) = BLOCKED; «Exit» not read in an open menu = FAIL.

FAULT (two, both must give red):
   A) the list of forbidden entries that includes «Log Out/Exit»: the same text
      read from the real menu must give RED;
   B) the field read from the wrong place: logind asked by ROOT
      (which has CAP_SYS_BOOT and is told «yes», see the polkit rule) —
      the fields judge must give RED.
"""
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suite as S                                                     # noqa: E402

G1B = S._load("g1b", os.path.join(S.HERE, "15-g1b-comune.py"))
FUNCTIONS = ("F-029",)

FORBIDDEN = [
    ("block", r"\block\b|lock\s*screen|screen\s*lock|\bblocca"),
    ("sospensione", r"suspend|sospendi|sospensione|\bsleep\b|standby"),
    ("ibernazione", r"hibernat|iberna"),
    ("riavvio", r"restart|reboot|riavvia"),
    ("spegnimento", r"shut\s*down|power\s*off|spegni|arresta"),
    ("cambia utente", r"switch\s*user|cambia\s*utente"),
]
EXIT = r"log\s*-?\s*out|esci|disconnetti"
FORBIDDEN_WITH_FAULT = FORBIDDEN + [("esci (GUASTO)", EXIT)]

# logind: the right answers, asked as the tenant
LOGIND = ("CanPowerOff", "CanReboot", "CanSuspend", "CanHibernate", "CanHybridSleep")
# ⚠ «negato»: `[M]` 24 Sep 2026, CanPowerOff and CanReboot asked by the tenant
#   answer «Call failed: Access denied» (the polkit rule says NO), while
#   from root they say «yes».  GNOME and Plasma treat the error as «cannot».
LOGIND_GOOD = ("no", "na", "negato")


# ═══════════════════════════════════════════════════════════════════════════
#  THE JUDGE (pure functions)
# ═══════════════════════════════════════════════════════════════════════════
def judge_lines(lines, desktop, forbidden=FORBIDDEN):
    """righe = [(sentence, x, y)].  Returns (found [(family, sentence)], esci_read,
    discarded_lines)."""
    discarded = []
    lines = list(lines)
    if desktop == "gnome":
        titles = [r for r in lines if re.fullmatch(r"\W*\w?\W*power\s*off\W*", r[0], re.I)]
        if titles:
            y0 = min(r[2] for r in titles)
            discarded = [r for r in titles if abs(r[2] - y0) < 15]
            lines = [r for r in lines if r not in discarded]
    found = []
    for sentence, _x, _y in lines:
        for fam, rx in forbidden:
            if re.search(rx, sentence, re.I):
                found.append((fam, sentence))
    logout = any(re.search(EXIT, f, re.I) for f, _x, _y in lines)
    return found, logout, discarded


def judge_fields(fields, desktop):
    """campi = {name: value read}.  Returns [defects]."""
    troubles = []
    for k in LOGIND:
        v = fields.get(k)
        if v is None:
            troubles.append("%s not read" % k)
        elif v not in LOGIND_GOOD:
            troubles.append("%s=%s (expected no/na)" % (k, v))
    if desktop == "gnome":
        gdm, dis = fields.get("gdm_on_bus"), fields.get("disable-lock-screen")
        if gdm is None:
            troubles.append("GDM on the bus: not read")
        elif gdm and dis != "true":
            troubles.append("GDM is there and disable-lock-screen=%s: the lock icon is there" % dis)
    return troubles


def certify():
    troubles = []

    def prova(what, real):
        print("%s %s" % ("⭐" if real else "⛔", what))
        if not real:
            troubles.append(what)

    menu_gnome = [("(Power Off", 3500, 140), ("Log Out...", 3490, 212)]
    t, e, sc = judge_lines(menu_gnome, "gnome")
    prova("gnome: the title «Power Off» is discarded, «Log Out» is there", not t and e and sc)
    t, e, _ = judge_lines(menu_gnome + [("Power Off...", 3490, 180)], "gnome")
    prova("gnome: the ENTRY «Power Off…» under the title is red", bool(t) and e)
    t, e, _ = judge_lines(menu_gnome, "kde")
    prova("kde: «Power Off» is not a title, it is red", bool(t))
    for entry in ("Lock Screen", "Suspend", "Sleep", "Hibernate", "Restart", "Shut Down",
                 "Switch User", "Blocca schermo", "Riavvia"):
        t, e, _ = judge_lines([(entry, 10, 10), ("Logout", 10, 40)], "lxqt")
        prova("«%s» is forbidden" % entry, bool(t) and e)
    t, e, _ = judge_lines([("Accessories", 1, 1), ("Leave", 1, 30), ("Logout", 80, 30)],
                            "lxqt")
    prova("LXQt's clean menu is green", not t and e)
    t, e, _ = judge_lines([("Workspace 1", 1, 1)], "xfce")
    prova("without «Log Out» ⇒ exit not read", not e)
    t, e, _ = judge_lines([("Log Out...", 1, 1)], "xfce", FORBIDDEN_WITH_FAULT)
    prova("FAULT A: with «Exit» in the list the right menu is red", bool(t))
    good_n = {k: "no" for k in LOGIND}
    prova("fields: all «no» ⇒ no defects", not judge_fields(good_n, "xfce"))
    prova("FAULT B: CanPowerOff=yes ⇒ defect",
          bool(judge_fields(dict(good_n, CanPowerOff="yes"), "kde")))
    prova("gnome: GDM present without disable-lock-screen ⇒ defect",
          bool(judge_fields(dict(good_n, gdm_on_bus=True,
                                  **{"disable-lock-screen": "false"}), "gnome")))
    prova("gnome: no GDM ⇒ no icon", not judge_fields(
        dict(good_n, gdm_on_bus=False, **{"disable-lock-screen": "false"}), "gnome"))
    print("⛔ %d problems" % len(troubles) if troubles else "⭐ CERTIFIED")
    return 1 if troubles else 0


# ═══════════════════════════════════════════════════════════════════════════
#  THE FIELDS, inside the box
# ═══════════════════════════════════════════════════════════════════════════
def read_logind(s, come_root=False):
    """{CanX: "no"|...} asked as the tenant (or as root, for the fault)."""
    chi = "" if come_root else "runuser -u %s -- " % s.chi
    line = "; ".join(
        "printf '%s=' ; %sbusctl call org.freedesktop.login1 /org/freedesktop/login1 "
        "org.freedesktop.login1.Manager %s 2>&1 | tail -n 1" % (k, chi, k) for k in LOGIND)
    _c, t = s.sc.inside(line, 60)
    fields = {}
    for r in t.splitlines():
        m = re.match(r'(Can\w+)=(?:s "(\w+)"|(Call failed: Access denied))', r.strip())
        if m:
            fields[m.group(1)] = m.group(2) or "negato"
    return fields, t


def read_gnome_block(s):
    c, t = s.sc.inside("busctl --system list 2>/dev/null | grep -c '^org.gnome.DisplayManager '",
                       30)
    gdm = None
    try:
        gdm = int(t.strip().split()[-1]) > 0
    except (ValueError, IndexError):
        pass
    _c, t2 = G1B.in_session(s, "gsettings get org.gnome.desktop.lockdown "
                                   "disable-lock-screen")
    return gdm, (t2.strip().splitlines() or [""])[-1], t + "\n" + t2


# ═══════════════════════════════════════════════════════════════════════════
#  THE GESTURES, per desktop (desktop coordinates: W, H = canvas size)
# ═══════════════════════════════════════════════════════════════════════════
def first_click(desktop, W, H):
    return {"gnome": (W - 30, 14), "kde": (28, H - 27),
            "xfce": (W - 64, 10), "lxqt": (12, H - 18)}[desktop]


def second_click(desktop, W, H, words):
    """The second level: (X, Y, how) or None if the menu has one level.
    `words` = [(text, x, y, w, h, confidence)] of the first level."""
    if desktop == "gnome":
        return W - 45, 75, "the power icon of the system menu (fixed position)"
    if desktop == "xfce":
        return None
    for text, x, y, w, h, _f in sorted(words, key=lambda p: -p[5]):
        if re.fullmatch(r"\W*(leave|esci)\W*", text, re.I):
            return x + w / 2, y + h / 2, "«%s» read by the OCR" % text
    return ({"kde": (600, H - 80), "lxqt": (52, H - 43)}[desktop] +
            ("«Leave» not read: fallback position",))


def body(o, E):
    d = o.box
    with S.Session(o, "029", E) as s:
        G1B.step("tenant and browser ready")
        ok, m = s.enter()
        G1B.step("inside: %s" % m[:80])
        if not ok:
            raise S.Blocked(m)
        if not G1B.ocr_available():
            raise S.Blocked("tesseract is not there (%s): without OCR the menu cannot be read"
                             % G1B.TESSERACT)
        time.sleep(6 if d != "kde" else 10)      # the panel finishes being born
        geo = s.geometry()
        W, H = geo["tl"], geo["ta"]
        ev = []
        png0, p0 = G1B.photo(s, "prima-del-menu")
        if not png0:
            raise S.Blocked("no photo before the menu: " + p0)
        ev.append(p0)

        X, Y = first_click(d, W, H)
        G1B.click_desktop(s, geo, X, Y)
        png1, p1, r1 = G1B.wait_open(s, png0, "menu-livello-1", (X, Y, 1300))
        if not png1:
            raise S.Blocked("no photo of the menu: " + p1)
        ev.append(p1)
        if not r1:
            raise S.Blocked("the click at (%d, %d) opened nothing: the photo does not "
                             "change" % (X, Y))
        G1B.reset_words()
        lines, _text1 = G1B.read_rect(png1, r1)
        print("   level 1 %s: %s" % (r1, [f for f, _x, _y in lines]), flush=True)

        all_of = list(lines)
        sec = second_click(d, W, H, G1B.words_read())
        r2 = None
        if sec:
            X2, Y2, come = sec
            print("   second click at (%d, %d): %s" % (X2, Y2, come), flush=True)
            G1B.click_desktop(s, geo, X2, Y2)
            png2, p2, r2 = G1B.wait_open(s, png1, "menu-livello-2", (X2, Y2, 1300),
                                                min_side=40)
            if png2:
                ev.append(p2)
                if r2:
                    lines2, _t2 = G1B.read_rect(png2, r2)
                    print("   level 2 %s: %s" % (r2, [f for f, _x, _y in lines2]),
                          flush=True)
                    all_of += lines2
        # the menu closes (two ESC), to leave the desktop as it was found
        for _ in range(2):
            G1B.combination(s.g, ["Escape"])
            time.sleep(0.4)

        found, logout, discarded = judge_lines(all_of, d)
        fields, raw = read_logind(s)
        fields_text = "logind as %s: %s" % (s.chi, ", ".join(
            "%s=%s" % (k, fields.get(k, "?")) for k in LOGIND))
        if d == "gnome":
            gdm, dis, g_raw = read_gnome_block(s)
            fields["gdm_on_bus"], fields["disable-lock-screen"] = gdm, dis
            fields_text += " · GDM on the system bus=%s · disable-lock-screen=%s" % (gdm, dis)
            raw += "\n" + g_raw
        field_troubles = judge_fields(fields, d)
        ev.append(s.save_text("f029-letto.txt",
                                ["lines read by the OCR:"] + ["  %s  (x=%d y=%d)" % r
                                                             for r in all_of]
                                + ["discarded (GNOME title): %s" % discarded,
                                   "fields: " + fields_text, "", raw]))
        read = " | ".join(f for f, _x, _y in all_of)
        oss = "OCR: «%s» · %s" % (read[:300], fields_text)
        expected = ("in the exit menu only «Exit» (Log Out): no lock, suspend, "
                  "hibernate, restart, shut down, switch user; logind «no» for "
                  "the tenant")
        if found:
            E.put("F-029", S.FAIL, "forbidden entries in the menu: %s" % "; ".join(
                "%s («%s»)" % t for t in found), expected=expected, observed=oss, evidence=ev)
        elif not logout:
            E.put("F-029", S.FAIL, "the menu opened but «Exit/Log Out» can NOT be read",
                    expected=expected, observed=oss, evidence=ev)
        elif field_troubles:
            E.put("F-029", S.FAIL, "the menu is clean but the fields are not: %s"
                    % "; ".join(field_troubles), expected=expected, observed=oss, evidence=ev)
        else:
            E.put("F-029", S.PASS, "in the menu only «Exit» (OCR), and logind says no",
                    expected=expected, observed=oss, evidence=ev)

        if o.fault:
            ta, _e, _s = judge_lines(all_of, d, FORBIDDEN_WITH_FAULT)
            seen_a = bool(ta)
            root, _g = read_logind(s, come_root=True)
            if d == "gnome":
                root["gdm_on_bus"] = fields.get("gdm_on_bus")
                root["disable-lock-screen"] = fields.get("disable-lock-screen")
            gb = judge_fields(root, d)
            seen_b = bool(gb)
            E.fault("F-029", seen_a and seen_b,
                     "A) «Exit» among the forbidden ⇒ %s · B) logind asked by root (%s) ⇒ %s"
                     % ("RED" if seen_a else "verde (NOT seen)",
                        ", ".join("%s=%s" % (k, root.get(k, "?")) for k in LOGIND),
                        "RED" if seen_b else "verde (NOT seen)"),
                     evidence=ev)


if __name__ == "__main__":
    sys.exit(S.run(__doc__, FUNCTIONS, body, certify))
