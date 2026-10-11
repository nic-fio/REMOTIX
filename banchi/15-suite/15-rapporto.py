#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-rapporto — THE SUITE REPORT, GENERATED FROM THE REGISTER (never written by hand)

    python3 15-rapporto.py --log registro.jsonl [--defects difetti.jsonl]
                           [--round 1] [--html rapporto.html] [--text]

- the MATRIX function × desktop × browser: for each cell the LAST outcome of the
  chosen round (healthy pass), with the fault mark (seen / not seen);
- the list of DEFECTS with their state (from difetti.jsonl);
- for each FAIL or BLOCKED cell: the reason, and the evidence;
- at the top: binary, page, commit it was measured on, and the counts.
It serves the CLEAN-UP, not the user.
"""
import argparse
import html
import json
import os
import re
import sys

DESKTOP = ("gnome", "kde", "xfce", "lxqt")
BROWSER = ("firefox", "chrome", "phone")   # phone: Chrome on the real phone (phase 19 §5)
NAMES = {
    "F-001": "login and session creation", "F-002": "first image",
    "F-003": "screen update", "F-004": "mouse", "F-005": "pointer shape",
    "F-006": "resizing from the edge", "F-007": "keyboard: characters and special keys",
    "F-008": "modifiers and combinations", "F-009": "layout, accents, AltGr",
    "F-010": "desktop shortcuts", "F-011": "the canvas at attach", "F-012": "audio",
    "F-012B": "audio after «Exit» and an immediate re-entry (PulseAudio client)",
    "F-013": "video", "F-014": "clipboard, browser → session",
    "F-015": "clipboard, session → browser", "F-016": "detach",
    "F-015C": "clipboard, session → computer, without recent gestures",
    "F-014C": "clipboard, copied outside the browser, a single Ctrl+V",
    "F-014D": "clipboard, the same text copied twice",
    "F-017": "reattach at the same size", "F-018": "reattach at a different size",
    "F-019": "network loss and re-entry", "F-020": "browser closed abruptly",
    "F-021": "«Exit» from the menu", "F-022": "silence clock",
    "F-023": "inactivity clock", "F-024": "abandonment clock",
    "F-025": "same user from two tabs", "F-026": "several users together",
    "F-027": "wrong password", "F-028": "ban", "F-029": "dangerous entries absent",
    "F-030": "the screen does not turn off by itself", "F-031": "touch (Android)",
    "F-024b": "abandonment without any gesture",
    "P-A": "path A: detach and reattach with input", "P-B": "path B: network loss",
    "P-C": "path C: different size and back", "P-D": "path D: network lost with video",
    "P-E": "path E: browser closed, new connection",
    "P-F": "path F: application found again",
    "C7": "technical: nothing remains", "C9": "technical: the log says whose",
    "C14": "technical: the boxes do not disturb each other", "C18": "technical: the card's groups",
    "C19": "technical: the box stays clean",
}


# ── the registers written before the English rename (DECISIONI §10.38) keep the Italian words,
#    and registro.jsonl is append-only: old Italian rows, then new ones.  The first tuple is
#    protected (english-migration/protetti.tsv), the second is renamed with the code: after the
#    rename OLD_SPELLING maps every old word to the code's own, before it is empty.  Same order
#    in both, one word per position.  Keys of registro.jsonl and difetti.jsonl, and the values
#    compared here (the fault pass, the phone browser, the verified state).
_OLD_WORDS = (
    "giro", "funzione", "passata", "esito", "ragione", "binario", "pagina", "atteso", "osservato",
    "evidenze", "inizio", "durata_s", "versione", "guasto", "telefono", "classe", "titolo",
    "verificato",
)  # end of the old words
_WORDS_NOW = (
    "round", "function", "pass", "outcome", "rationale", "binary", "page", "expected", "observed",
    "evidence", "started", "duration_s", "version", "fault", "phone", "class", "title",
    "verificato",
)
OLD_SPELLING = {a: b for a, b in zip(_OLD_WORDS, _WORDS_NOW) if a != b}


def current_spelling(x):
    """A record of an old register in the code's spelling: keys, and string values equal to a word."""
    if isinstance(x, dict):
        return {OLD_SPELLING.get(k, k): current_spelling(v) for k, v in x.items()}
    if isinstance(x, list):
        return [current_spelling(v) for v in x]
    return OLD_SPELLING.get(x, x) if isinstance(x, str) else x


def order(f):
    m = re.match(r"([A-Z])-?(\d+)?", f)
    pref = {"F": 0, "P": 1, "N": 2, "C": 3}.get(f[0], 4)
    num = int(m.group(2)) if m and m.group(2) else 0
    return (pref, num, f)


def load(p):
    lines = []
    if p and os.path.exists(p):
        for x in open(p, encoding="utf-8"):
            x = x.strip()
            if x:
                try:
                    lines.append(current_spelling(json.loads(x)))
                except ValueError:
                    pass
    return lines


def matrix(lines):
    """{(funzione, desktop, browser, passata): last line} — the order of the file
    is the order of time (the register is append only)."""
    m = {}
    for r in lines:
        m[(r.get("function"), r.get("desktop"), r.get("browser"), r.get("pass", "healthy"))] = r
    return m


def columns(lines):
    clr = []
    for d in DESKTOP:
        for b in BROWSER:
            clr.append((d, b))
    if any(r.get("browser") == "-" for r in lines):
        for d in DESKTOP:
            clr.append((d, "-"))
    return clr


def text(lines, defects, round_id):
    m = matrix(lines)
    functions = sorted({r["function"] for r in lines}, key=order)
    clr = [(d, b) for d, b in columns(lines) if any(k[1] == d and k[2] == b for k in m)]
    tally = {}
    for k, r in m.items():
        if k[3] == "healthy":
            tally[r["outcome"]] = tally.get(r["outcome"], 0) + 1
    out = ["ROUND %s · %s" % (round_id, " ".join("%s=%d" % kv for kv in sorted(tally.items())))]
    out.append("%-8s " % "" + " ".join("%-7s" % (d[:3] + "/" + b[:2]) for d, b in clr))
    for f in functions:
        cells = []
        for d, b in clr:
            r = m.get((f, d, b, "healthy"))
            g = m.get((f, d, b, "fault"))
            s = {"PASS": "ok", "FAIL": "FAIL", "BLOCKED": "BLOC"}.get(r["outcome"], "?") if r else "·"
            if g:
                s += {"PASS": "", "FAIL": "!g", "BLOCKED": "?g"}.get(g["outcome"], "")
            cells.append("%-7s" % s)
        out.append("%-8s " % f + " ".join(cells))
    red = [r for k, r in m.items() if r["outcome"] != "PASS"]
    if red:
        out.append("\nNOT GREEN:")
        for r in sorted(red, key=lambda r: (order(r["function"]), r["desktop"], r["browser"])):
            out.append("  %s %s/%s [%s] %s: %s" % (r["function"], r["desktop"], r["browser"],
                                                  r.get("pass"), r["outcome"],
                                                  (r.get("rationale") or "")[:220]))
    if defects:
        out.append("\nDEFECTS:")
        for dd in defects:
            out.append("  %s [%s, class %s] %s — %s" % (dd.get("id"), dd.get("state"),
                                                        dd.get("class"), dd.get("title", ""),
                                                        ", ".join(dd.get("where") or [])))
    return "\n".join(out)


CSS = """
:root{--sfondo:#f7f7f5;--carta:#fff;--testo:#1d1d1b;--tenue:#6b6b66;--riga:#e3e2dd;
--pass:#1f7a3a;--pass-f:#e3f3e7;--fail:#b3261e;--fail-f:#fbe4e2;--bloc:#8a5a00;--bloc-f:#fdf0d5;--vuoto:#f0efeb}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--sfondo:#161615;--carta:#1f1f1d;
--testo:#ecebe6;--tenue:#a3a29c;--riga:#34332f;--pass:#7fd494;--pass-f:#1c3322;--fail:#ff9a90;
--fail-f:#3d1d1a;--bloc:#f2c26b;--bloc-f:#3a2d12;--vuoto:#262624}}
:root[data-theme="dark"]{--sfondo:#161615;--carta:#1f1f1d;--testo:#ecebe6;--tenue:#a3a29c;--riga:#34332f;
--pass:#7fd494;--pass-f:#1c3322;--fail:#ff9a90;--fail-f:#3d1d1a;--bloc:#f2c26b;--bloc-f:#3a2d12;--vuoto:#262624}
*{box-sizing:border-box}
body{margin:0;background:var(--sfondo);color:var(--testo);font:15px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:1200px;margin:0 auto;padding:24px 16px 64px}
h1{font-size:1.6rem;margin:0 0 4px}h2{font-size:1.15rem;margin:32px 0 8px}
.tenue{color:var(--tenue)}.conti{display:flex;gap:12px;flex-wrap:wrap;margin:16px 0}
.conto{background:var(--carta);border:1px solid var(--riga);border-radius:8px;padding:10px 14px;min-width:110px}
.conto b{display:block;font-size:1.5rem;font-variant-numeric:tabular-nums}
.scorre{overflow-x:auto;border:1px solid var(--riga);border-radius:8px;background:var(--carta)}
table{border-collapse:collapse;width:100%;font-size:13px}
th,td{padding:6px 8px;border-bottom:1px solid var(--riga);text-align:left;vertical-align:top}
th{font-weight:600;white-space:nowrap}td.c{text-align:center;white-space:nowrap}
.PASS{background:var(--pass-f);color:var(--pass)}.FAIL{background:var(--fail-f);color:var(--fail);font-weight:600}
.BLOCKED{background:var(--bloc-f);color:var(--bloc)}.vuoto{background:var(--vuoto);color:var(--tenue)}
.g{font-size:11px;opacity:.85}code{font-size:12px;word-break:break-all}
details{background:var(--carta);border:1px solid var(--riga);border-radius:8px;margin:8px 0;padding:8px 12px}
summary{cursor:pointer}
"""


def page(lines, defects, round_id):
    e = html.escape
    m = matrix(lines)
    functions = sorted({r["function"] for r in lines}, key=order)
    clr = [(d, b) for d, b in columns(lines) if any(k[1] == d and k[2] == b for k in m)]
    tally = {}
    for k, r in m.items():
        if k[3] == "healthy":
            tally[r["outcome"]] = tally.get(r["outcome"], 0) + 1
    faults = [r for k, r in m.items() if k[3] == "fault"]
    seen_items = sum(1 for r in faults if r["outcome"] == "PASS")
    fingerprints = sorted({(str(r.get("binary")), str(r.get("page")), str(r.get("commit"))) for r in lines
                       if r.get("binary")})
    h = ["<!doctype html><html lang='en'><head><meta charset='utf-8'>",
         "<meta name='viewport' content='width=device-width,initial-scale=1'>",
         "<title>REMOTIX suite, round %s</title><style>%s</style></head><body><main>" % (e(str(round_id)), CSS),
         "<h1>Functional suite — round %s</h1>" % e(str(round_id)),
         "<p class='tenue'>Generated from the register. Measured on: %s.</p>" % e("; ".join(
             "binary %s · page %s · commit %s" % x for x in fingerprints)),
         "<div class='counts'>"]
    for k, cls in (("PASS", "PASS"), ("FAIL", "FAIL"), ("BLOCKED", "BLOCKED")):
        h.append("<div class='conto'><span class='%s' style='background:none'>%s</span><b>%d</b></div>"
                 % (cls, k, tally.get(k, 0)))
    h.append("<div class='conto'>faults seen<b>%d/%d</b></div>" % (seen_items, len(faults)))
    h.append("<div class='conto'>open defects<b>%d</b></div></div>" % sum(
        1 for d in defects if d.get("state") not in ("verificato",)))
    h.append("<h2>The matrix</h2><div class='scorre'><table><thead><tr><th>function</th>")
    for d, b in clr:
        h.append("<th>%s<br><span class='tenue'>%s</span></th>" % (e(d), e(b)))
    h.append("</tr></thead><tbody>")
    for f in functions:
        h.append("<tr><th>%s <span class='tenue'>%s</span></th>" % (e(f), e(NAMES.get(f, ""))))
        for d, b in clr:
            r = m.get((f, d, b, "healthy"))
            g = m.get((f, d, b, "fault"))
            if not r:
                h.append("<td class='c vuoto'>·</td>")
                continue
            gs = ""
            if g:
                gs = "<br><span class='g'>fault %s</span>" % {"PASS": "seen", "FAIL": "NOT seen",
                                                              "BLOCKED": "?"}.get(g["outcome"], "?")
            h.append("<td class='c %s' title='%s'>%s%s</td>" % (r["outcome"], e(r.get("rationale") or ""),
                                                            r["outcome"], gs))
        h.append("</tr>")
    h.append("</tbody></table></div>")
    if defects:
        h.append("<h2>The defects</h2><div class='scorre'><table><thead><tr><th>id</th><th>what is seen</th>"
                 "<th>where</th><th>class</th><th>state</th><th>cure</th><th>test</th></tr></thead><tbody>")
        for dd in defects:
            h.append("<tr><th>%s</th><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"
                     % tuple(e(str(x or "")) for x in (dd.get("id"), dd.get("title"),
                                                         ", ".join(dd.get("where") or []),
                                                         dd.get("class"), dd.get("state"),
                                                         dd.get("fix_commit"), dd.get("prova"))))
        h.append("</tbody></table></div>")
    red = sorted([r for k, r in m.items() if r["outcome"] != "PASS"],
                   key=lambda r: (order(r["function"]), r["desktop"], r["browser"]))
    if red:
        h.append("<h2>The non-green cells</h2>")
        for r in red:
            h.append("<details><summary><b class='%s' style='background:none'>%s</b> %s · %s/%s · %s</summary>"
                     % (r["outcome"], r["outcome"], e(r["function"]), e(r["desktop"]), e(r["browser"]),
                        e(r.get("pass", ""))))
            h.append("<p>%s</p>" % e(r.get("rationale") or ""))
            if r.get("expected"):
                h.append("<p class='tenue'>expected: %s<br>observed: %s</p>" % (e(r["expected"]),
                                                                            e(r.get("observed") or "")))
            for x in r.get("evidence") or []:
                h.append("<code>%s</code><br>" % e(x))
            h.append("<p class='tenue'>%s · %s s · %s</p></details>" % (e(r.get("started") or ""),
                                                                      r.get("duration_s"),
                                                                      e(r.get("version") or "")))
    h.append("</main></body></html>")
    return "".join(h)


def main():
    a = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--log", required=True)
    a.add_argument("--defects", default="")
    a.add_argument("--round", default="")
    a.add_argument("--html", default="")
    a.add_argument("--text", action="store_true")
    o = a.parse_args()
    lines = load(o.log)
    rounds = [str(r.get("round")) for r in lines]
    round_id = o.round or (rounds[-1] if rounds else "?")
    lines = [r for r in lines if str(r.get("round")) == round_id]
    defects = load(o.defects)
    if o.html:
        with open(o.html, "w", encoding="utf-8") as f:
            f.write(page(lines, defects, round_id))
    if o.text or not o.html:
        print(text(lines, defects, round_id))
    return 0


if __name__ == "__main__":
    sys.exit(main())
