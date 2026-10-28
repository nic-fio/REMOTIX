#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-fschede — F-SCHEDE ONE REAL SESSION ON A SERVER WITH TWO CARDS

    bash 15-one.sh 15-fschede-two-cards.py --box xfce --browser chrome [--fault]
    (the box is the TEMPORARY `rete11-due-<desktop>` of benches/11-boxes/11-two-cards.sh, already started;
     the port, the container and the cards are read from its state file)

Not picked up by 15-round.py (its name has no digit after «15-f»): it needs the two-card box, the round has the four.

F-SCHEDE  expected: ONE real session (tenant, real browser, login) in the two-card box, and
          1. the first image arrives (desktop drawn, not degenerate);
          2. the encoder's node == the compositor's node, as CARDS (PCI address), not as names: no cross-card;
          3. XFCE / LXQt / KDE: the compositor's card == the server's BIOS primary card (boot_vga=1; without any, the
             lowest PCI address), WITH and WITHOUT --swap (the names renderD128/129 exchanged must not change it);
             GNOME chooses by itself: consistency is judged, and which card Mutter chose is REPORTED (expected = primary);
          4. if the box got `--render-node X` (secondary, the encoder's fallback): when X is not the compositor's card
             the «is NOT the compositor's card» warning is there, and when it is, it is not.
          The log texts judged are the product's own: «the card I give wlroots is» (before 1.5 card_pick) or «the card I give the compositor is» (session.c, XFCE/LXQt), «the encoding card»
          (child.c, from the compositor's linux-dmabuf main_device), «encoder N OPENED» with «in HARDWARE · /dev/dri/renderDN»,
          and the two declared fallbacks (pixman; «falls back to the startup card» = cross-card import).

FAULT: the same judge on the real lines in which the encoder is made to open on the OTHER card ⇒ it must say FAIL.
"""
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suite as S                                                     # noqa: E402

FUNCTIONS = ("F-SCHEDE",)
OWN = ("xfce", "lxqt", "kde")          # the desktops whose card REMOTIX chooses (labwc / KWin's host); GNOME chooses by itself
DEFAULT_ROOT = "/media/REMOTIX-15/lavori/due-schede"

RE_ENC = re.compile(r"the encoding card: (/dev/dri/renderD\d+) \((\S+), driver (\S+), [^)]*\) — from (.*)$")
RE_WLR = re.compile(r"the card I give (?:wlroots|the compositor) is (/dev/dri/renderD\d+)")
RE_OPEN = re.compile(r"encoder \d+ OPENED.*?(/dev/dri/renderD\d+)")
RE_OPENED_NODE = re.compile(r"(OPENED.*?)(/dev/dri/renderD\d+)")
WARN = "is NOT the compositor's card"
XCARD = "falls back to the startup card"
PIXMAN = "CANNOT create the output buffer"


# ═══════════════════════════════════════════════════════════════════════════
#  THE STATE OF THE BOX AND THE JUDGE (pure functions: certified without a box)
# ═══════════════════════════════════════════════════════════════════════════
def read_state(path):
    """The box's state file (KEY=VALUE) as a dict: cards = [{label, pci, driver, render, card, boot}]."""
    kv = {}
    with open(path) as f:
        for r in f:
            if "=" in r:
                k, _, v = r.rstrip("\n").partition("=")
                kv[k] = v
    cards = []
    for i in range(2):
        label, pci, drv, rend, card, boot = kv["CARD_%d" % i].split("|")
        cards.append({"label": label, "pci": pci, "driver": drv, "render": "/dev/dri/" + rend,
                      "card": "/dev/dri/" + card, "boot": boot == "1"})
    return {"name": kv["NAME"], "desktop": kv["DESKTOP"], "port": int(kv["PORT"]), "swap": kv["SWAP"] == "1",
            "req": kv.get("RENDER_NODE", ""), "devt": kv.get("SWAP_DEVT", "1") == "1", "cards": cards}


def primary_pci(st):
    """The card the product must choose: boot_vga=1; otherwise the lowest PCI address (both assumed capable)."""
    boot = [c for c in st["cards"] if c["boot"]]
    return boot[0]["pci"] if boot else min(c["pci"] for c in st["cards"])


def pci_of(st, node):
    for c in st["cards"]:
        if node in (c["render"], c["card"]):
            return c["pci"]
    return None


def label_of(st, pci):
    for c in st["cards"]:
        if c["pci"] == pci:
            return c["label"]
    return "?"


def parse(lines):
    """The facts in the box's server log (new lines only)."""
    f = {"enc": None, "wlr": None, "opened": [], "warn": False, "xcard": False, "pixman": False}
    for r in lines:
        m = RE_ENC.search(r)
        if m:
            f["enc"] = {"node": m.group(1), "pci": m.group(2), "driver": m.group(3), "source": m.group(4)}
        m = RE_WLR.search(r)
        if m:
            f["wlr"] = m.group(1)
        m = RE_OPEN.search(r)
        if m:
            f["opened"].append(m.group(1))
        f["warn"] = f["warn"] or WARN in r
        f["xcard"] = f["xcard"] or XCARD in r
        f["pixman"] = f["pixman"] or PIXMAN in r
    return f


def judge(desktop, st, lines, image_ok):
    """(outcome, reason, facts).  THE one judgment of F-SCHEDE (see the header)."""
    f = parse(lines)
    facts = {"compositor_card": "?", "encoder_card": "?", "primary_card": label_of(st, primary_pci(st)),
             "swap": st["swap"], "render_node": st["req"]}
    if not image_ok:
        return S.FAIL, "the first image did not arrive", facts
    if f["pixman"]:
        return S.FAIL, "the compositor fell back to pixman (the chosen card cannot create the buffer): not a card choice", facts
    if not st.get("devt", True):
        # --swap NOT faithful on the dev_t (11-two-cards.sh): the encoder/compositor comparison cannot be trusted, so it is never
        # judged here; only the card the product GIVES the compositor is, against the BIOS primary
        if f["wlr"] is None:
            return S.BLOCKED, "I could not look: no «the card I give … is» line (simulazione --swap non fedele sul dev_t)", facts
        given = pci_of(st, f["wlr"])
        facts["compositor_card"] = label_of(st, given)
        if given is not None and given != primary_pci(st) and desktop in OWN:
            return S.FAIL, "%s was given %s (%s), not the BIOS primary card %s (%s) [names exchanged]" % (
                desktop, f["wlr"], facts["compositor_card"], label_of(st, primary_pci(st)), primary_pci(st)), facts
        return S.BLOCKED, ("simulazione --swap non fedele sul dev_t: the card given (%s, %s) is %s the BIOS primary; the "
                           "encoder/compositor comparison is not judged" % (f["wlr"], facts["compositor_card"],
                                                                           "the" if given == primary_pci(st) else "NOT the")), facts
    if f["xcard"]:
        return S.FAIL, "cross-card: the encoder fell back to the startup card, not the compositor's (\"%s\")" % XCARD, facts
    enc = f["enc"]
    if not enc or not f["opened"]:
        return S.BLOCKED, "I could not look: the log has no «the encoding card» line (%s) or no «encoder OPENED» node (%s)" % (
            "found" if enc else "missing", "found" if f["opened"] else "missing"), facts
    # the compositor's card: what REMOTIX gave wlroots (XFCE/LXQt), or what the compositor itself announced (all)
    from_comp = enc["source"].startswith("the compositor's card")
    if desktop in ("xfce", "lxqt") and f["wlr"]:
        comp_node = f["wlr"]
    elif from_comp:
        comp_node = enc["node"]
    else:
        return S.BLOCKED, "I could not look: the compositor did not say its card (the encoding card is «%s»)" % enc["source"][:80], facts
    comp_pci, enc_pci = pci_of(st, comp_node), pci_of(st, f["opened"][-1])
    if comp_pci is None or enc_pci is None:
        return S.BLOCKED, "I could not look: the node %s / %s is not one of the box's cards" % (comp_node, f["opened"][-1]), facts
    if pci_of(st, enc["node"]) != enc["pci"]:
        return S.BLOCKED, "I could not look: the log describes %s as PCI %s but the box says %s (the /sys view does not follow the names)" % (
            enc["node"], enc["pci"], pci_of(st, enc["node"])), facts
    facts["compositor_card"], facts["encoder_card"] = label_of(st, comp_pci), label_of(st, enc_pci)
    if desktop in ("xfce", "lxqt") and from_comp and pci_of(st, enc["node"]) != comp_pci:
        return S.FAIL, "cross-card: REMOTIX gave labwc %s (%s) but the compositor announces %s" % (
            comp_node, facts["compositor_card"], enc["node"]), facts
    if enc_pci != comp_pci:
        return S.FAIL, "cross-card: the encoder opened on %s (%s) and the compositor is on %s (%s)" % (
            f["opened"][-1], facts["encoder_card"], comp_node, facts["compositor_card"]), facts
    if enc["pci"] != comp_pci:
        return S.FAIL, "cross-card: «the encoding card» says %s, the compositor is on %s" % (enc["pci"], comp_pci), facts
    note = ""
    want = primary_pci(st)
    if desktop in OWN:
        if comp_pci != want:
            return S.FAIL, "%s drew on %s (%s), not on the BIOS primary card %s (%s)%s" % (
                desktop, comp_node, facts["compositor_card"], want, facts["primary_card"],
                " [names exchanged]" if st["swap"] else ""), facts
    else:
        note = "; GNOME chose by itself: %s (%s)%s" % (
            facts["compositor_card"], comp_pci, "= the primary card" if comp_pci == want else " ≠ the primary card %s (REPORT)" % want)
    if st["req"]:
        req_pci = pci_of(st, st["req"])
        if req_pci != comp_pci and not f["warn"]:
            return S.FAIL, "--render-node %s is not the compositor's card and the log has no warning" % st["req"], facts
        if req_pci == comp_pci and f["warn"]:
            return S.FAIL, "--render-node %s IS the compositor's card and the log warns anyway" % st["req"], facts
        note += "; --render-node %s: %s" % (st["req"], "warning there" if f["warn"] else "same card, no warning")
    return S.PASS, "one card for desktop and encoder: %s (%s, PCI %s)%s; primary %s%s%s" % (
        comp_node, facts["compositor_card"], comp_pci, " [names exchanged]" if st["swap"] else "",
        facts["primary_card"], note, ""), facts


def swap_encoder_node(lines, st):
    """FAULT: the same lines with the encoder's «encoder OPENED» node changed to the OTHER card's."""
    names = {st["cards"][0]["render"]: st["cards"][1]["render"], st["cards"][1]["render"]: st["cards"][0]["render"]}
    out = []
    for r in lines:
        if "OPENED" in r:
            r = RE_OPENED_NODE.sub(lambda m: m.group(1) + names.get(m.group(2), m.group(2)), r, count=1)
        out.append(r)
    return out


# ── the synthetic cases for the certification
def fake_state(swap=False, req="", boot_intel=True, devt=True):
    a = {"label": "intel", "pci": "0000:00:02.0", "driver": "i915", "render": "/dev/dri/renderD128", "card": "/dev/dri/card0", "boot": boot_intel}
    b = {"label": "amd", "pci": "0000:03:00.0", "driver": "amdgpu", "render": "/dev/dri/renderD129", "card": "/dev/dri/card1", "boot": not boot_intel}
    if swap:
        a["render"], b["render"] = b["render"], a["render"]
        a["card"], b["card"] = b["card"], a["card"]
    return {"name": "rete11-due-xfce", "desktop": "xfce", "port": 8533, "swap": swap, "req": req, "devt": devt, "cards": [a, b]}


def fake_lines(st, comp, enc, source="the compositor's card (linux-dmabuf main_device)", wlr=True, extra=()):
    c = {x["label"]: x for x in st["cards"]}
    L = []
    if wlr:
        L.append("12:00:00.001 session [u] ⭐ xfce: the card I give wlroots is %s (opened, and the test buffer is born)" % c[comp]["render"])
    L.append("12:00:01.001 child   [u] ⭐ the encoding card: %s (%s, driver %s, 8086:a780) — from %s" % (
        c[comp]["render"], c[comp]["pci"], c[comp]["driver"], source))
    L.append("12:00:02.001 child   [u] ⭐ PHASE 3: encoder 1 OPENED and KEPT ALIVE · route vaapi (requested «card») · in force: "
             "h264 8 bit via h264_vaapi (in HARDWARE · %s · Intel iHD)" % c[enc]["render"])
    return L + list(extra)


def certify():
    troubles = []

    def prova(what, got, want):
        real = got == want
        print("   %s %s" % ("⭐ ok " if real else "⛔ NO ", what + ("" if real else "  (got %s)" % (got,))))
        if not real:
            troubles.append(what)

    st, sw = fake_state(), fake_state(swap=True)
    ra = fake_state(boot_intel=False)
    prova("all on the primary card, XFCE ⇒ PASS", judge("xfce", st, fake_lines(st, "intel", "intel"), True)[0], S.PASS)
    prova("same, names exchanged ⇒ PASS", judge("xfce", sw, fake_lines(sw, "intel", "intel"), True)[0], S.PASS)
    prova("primary is the Radeon (boot_vga on it), all on it ⇒ PASS", judge("lxqt", ra, fake_lines(ra, "amd", "amd"), True)[0], S.PASS)
    nl = [r.replace("wlroots is", "the compositor is") + " (0000:00:02.0, driver i915) — BIOS primary" for r in fake_lines(st, "intel", "intel")]
    prova("the new text «the card I give the compositor is» ⇒ PASS", judge("xfce", st, nl, True)[0], S.PASS)
    nd = fake_state(swap=True, devt=False)
    prova("dev_t not faithful, card given = primary ⇒ BLOCKED, never PASS/FAIL", judge("xfce", nd, fake_lines(nd, "intel", "intel"), True)[0], S.BLOCKED)
    prova("dev_t not faithful, the encoder on the other card ⇒ still BLOCKED (not judged)", judge("xfce", nd, fake_lines(nd, "intel", "amd"), True)[0], S.BLOCKED)
    prova("dev_t not faithful + «falls back to the startup card», card given = primary ⇒ BLOCKED", judge("xfce", nd, fake_lines(nd, "intel", "intel", extra=[
        "x ⛔ codec 1 at 8 bits does NOT encode on the compositor's card /dev/dri/renderD129: no.  ⇒ It falls back to the startup card"]), True)[0], S.BLOCKED)
    prova("dev_t not faithful, card given NOT the primary ⇒ FAIL", judge("xfce", nd, fake_lines(nd, "amd", "amd"), True)[0], S.FAIL)
    prova("dev_t not faithful, no image ⇒ FAIL", judge("xfce", nd, fake_lines(nd, "intel", "intel"), False)[0], S.FAIL)
    prova("dev_t not faithful, GNOME (no given-card line) ⇒ BLOCKED", judge("gnome", nd, fake_lines(nd, "intel", "intel", wlr=False), True)[0], S.BLOCKED)
    prova("XFCE on the non-primary card ⇒ FAIL", judge("xfce", st, fake_lines(st, "amd", "amd"), True)[0], S.FAIL)
    prova("names exchanged and the product follows the NAME (lowest) ⇒ FAIL", judge(
        "xfce", sw, fake_lines(sw, "amd", "amd"), True)[0], S.FAIL)
    prova("encoder on the other card ⇒ FAIL (cross-card)", judge("xfce", st, fake_lines(st, "intel", "amd"), True)[0], S.FAIL)
    prova("encoder fell back to the startup card ⇒ FAIL", judge("kde", st, fake_lines(st, "intel", "intel", wlr=False, extra=[
        "x ⛔ codec 1 at 8 bits does NOT encode on the compositor's card /dev/dri/renderD129: no.  ⇒ It falls back to the startup card"]), True)[0], S.FAIL)
    prova("pixman fallback ⇒ FAIL", judge("xfce", st, fake_lines(st, "intel", "intel", extra=[
        "x ⛔ xfce: the card /dev/dri/renderD128 opens but CANNOT create the output buffer (no)"]), True)[0], S.FAIL)
    prova("no first image ⇒ FAIL", judge("xfce", st, fake_lines(st, "intel", "intel"), False)[0], S.FAIL)
    prova("no log lines ⇒ BLOCKED", judge("xfce", st, [], True)[0], S.BLOCKED)
    prova("compositor did not answer (encoder on the default) ⇒ BLOCKED", judge(
        "kde", st, fake_lines(st, "intel", "intel", source="the default /dev/dri/renderD128", wlr=False), True)[0], S.BLOCKED)
    prova("KDE: the compositor's own announcement is the compositor's card ⇒ PASS", judge(
        "kde", st, fake_lines(st, "intel", "intel", wlr=False), True)[0], S.PASS)
    prova("GNOME on the non-primary card, consistent ⇒ PASS (reported)", judge(
        "gnome", st, fake_lines(st, "amd", "amd", wlr=False), True)[0], S.PASS)
    prova("GNOME with encoder on the other card ⇒ FAIL", judge("gnome", st, fake_lines(st, "amd", "intel", wlr=False), True)[0], S.FAIL)
    sr = fake_state(req="/dev/dri/renderD129")
    warn = ["x ⚠ --render-node /dev/dri/renderD129 is NOT the compositor's card (/dev/dri/renderD128): the frames are on the compositor's"]
    prova("--render-node on the other card + warning ⇒ PASS", judge("xfce", sr, fake_lines(sr, "intel", "intel", extra=warn), True)[0], S.PASS)
    prova("--render-node on the other card, NO warning ⇒ FAIL", judge("xfce", sr, fake_lines(sr, "intel", "intel"), True)[0], S.FAIL)
    sq = fake_state(req="/dev/dri/renderD128")
    prova("--render-node on the compositor's card + warning ⇒ FAIL", judge("xfce", sq, fake_lines(sq, "intel", "intel", extra=warn), True)[0], S.FAIL)
    prova("the log describes a PCI the box does not have for that name ⇒ BLOCKED", judge(
        "xfce", sw, [r.replace("0000:00:02.0", "0000:03:00.0") for r in fake_lines(sw, "intel", "intel")], True)[0], S.BLOCKED)
    prova("the FAULT (encoder moved to the other card) is seen ⇒ FAIL", judge(
        "xfce", st, swap_encoder_node(fake_lines(st, "intel", "intel"), st), True)[0], S.FAIL)
    print("⛔ CERTIFICATION FAILED" if troubles else "⭐ CERTIFIED")
    return 1 if troubles else 0


# ═══════════════════════════════════════════════════════════════════════════
#  THE TEST
# ═══════════════════════════════════════════════════════════════════════════
def extra(a):
    a.add_argument("--due-root", default=os.environ.get("REMOTIX_DUE_ROOT", DEFAULT_ROOT),
                   help="where 11-two-cards.sh keeps the state (stato/<desktop>.env)")


def body(o, E):
    path = os.path.join(o.due_root, "stato", "%s.env" % o.box)
    try:
        st = read_state(path)
    except (OSError, KeyError, ValueError) as e:
        raise S.Blocked("the two-card box is not started (%s: %s): bash 11-two-cards.sh start %s" % (path, e, o.box))
    o.url = "https://%s:%d/" % (o.host, st["port"])      # before the Session: the browser driver takes it at turn-on
    s = S.Session(o, "095", E)
    s.sc.container = st["name"]                          # the Box of the suite points at rete11-<desktop>: here, the two-card one
    with s:
        sign = s.log_mark()
        if sign is None:
            raise S.Blocked("I cannot read the box's server log")
        ok, m = s.enter()
        png, dove = s.photo("prima-immagine") if ok else (None, "")
        image_ok = bool(ok)
        # the card lines come with the first frame; wait (cap) until the encoder has said where it opened
        lines, t_end = [], time.time() + 30
        while True:
            _c, t = s.sc.inside("tail -n +%d %s" % (sign + 1, S.C20V.LOG), 60)
            lines = t.splitlines()
            f = parse(lines)
            if (f["enc"] and f["opened"]) or time.time() > t_end or not image_ok:
                break
            time.sleep(2)
        ev = [s.save_text("server-fschede.txt", lines)] + ([dove] if png and dove else [])
        outcome, why, facts = judge(o.box, st, lines, image_ok)
        if not image_ok:
            why += ": " + m
        E.put("F-SCHEDE", outcome, why,
              expected="first image; encoder card == compositor card; %s" % (
                  "compositor card == BIOS primary %s" % label_of(st, primary_pci(st)) if o.box in OWN else "GNOME: consistency, card reported"),
              observed=why, evidence=ev, **facts)
        if o.fault:
            bad = swap_encoder_node(lines, st)
            if not parse(lines)["opened"]:
                E.fault("F-SCHEDE", None, "no «encoder OPENED» line to start from")
            else:
                got = judge(o.box, st, bad, True)[0]
                E.fault("F-SCHEDE", got == S.FAIL, "encoder moved to the other card ⇒ the judge says %s" % got)


if __name__ == "__main__":
    sys.exit(S.run(__doc__, FUNCTIONS, body, certify, extra))
