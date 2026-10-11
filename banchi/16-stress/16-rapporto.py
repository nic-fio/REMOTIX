#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
16-rapporto — THE PHASE 16 REPORT, GENERATED FROM THE REGISTER (never written by hand)

    python3 16-rapporto.py [--log banchi/16-stress/registro.jsonl]
                           [--html banchi/16-stress/rapporto.html] [--text]
    python3 16-rapporto.py --certify      (synthetic register in a folder of its own)

From the register of `16-classifica.py` (§10: one row per level, one per session):
- the FINAL MATRIX of §11, desktop × card: for every screen size
  (4K → 3K → 2K → Full HD) the last GREEN level, the first level in FAIL
  (the breaking point) and the first DEGRADED;
- the CURVE of every campaign per step: one row per level (the LAST
  recording of that level: the register is only appended to, and a
  repetition of §14 takes the place of the first — repetitions are counted),
  with the worst measures of the sessions and the resources; and a chart of the
  resources per step (machine CPU, drawing and video of the card,
  memory used — all in %, a single axis);
- the BOTTLENECKS: at the first non-GREEN level of every campaign (or
  at the last, if it is all green), the most loaded resource and the enclosures that
  consume it;
- for every non-GREEN level: the reasons of the sessions and the evidence.
"""
import argparse
import html
import json
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
DESKTOP = ("gnome", "kde", "xfce", "lxqt")
SIZES = ("4K", "3K", "2K", "FHD")
ORD = {"GREEN": 0, "DEGRADED": 1, "FAIL": 2}
SERIES = (("cpu", "machine CPU"), ("draw", "card: drawing"),
         ("video", "card: video"), ("mem", "memory used"))
SHORT = {"cpu": "CPU", "draw": "drawing", "video": "video", "mem": "memory"}

# ── the rows of the register written before the English rename (DECISIONI §10.38) keep the Italian
#    words: the register (*.jsonl, misure/) is never rewritten.  The first tuple is protected
#    (english-migration/protetti.tsv), the second is renamed with the code: after the rename
#    OLD_SPELLING maps every old word to the code's own, before it is empty.  Same order in both,
#    one word per position: the keys and the values of the rows of 16-classifica.py that are read here.
_OLD_WORDS = (
    "campagna", "livello", "tipo", "sessione", "scheda", "misura", "binario", "pagina", "nucleo",
    "classe", "significativo", "risorse", "disegno", "sessioni", "ragione", "evidenze", "inizio",
    "utente", "profilo", "inquilino", "misure", "saltati_pct", "buchi",
    "audio_udibile_pct", "blocco_max_s", "cpu_macchina_pct", "media", "mem_totale_mb", "mem_usata_mb",
    "nascita_s", "recinti", "ritardo_p95_ms", "strozzatura_frazione",
)  # end of the old words
_WORDS_NOW = (
    "campaign", "level", "type", "session", "card", "size", "binary", "page", "kernel",
    "class", "significant", "resources", "draw", "sessions", "rationale", "evidence", "started",
    "user", "profile", "tenant", "measurements", "skipped_pct", "holes",
    "audio_audible_pct", "block_max_s", "cpu_machine_pct", "mean", "mem_total_mb", "mem_used_mb",
    "birth_s", "enclosures", "delay_p95_ms", "throttling_fraction",
)
OLD_SPELLING = {a: b for a, b in zip(_OLD_WORDS, _WORDS_NOW) if a != b}


def current_spelling(x):
    """A row of an old register in the code's spelling: keys, and string values equal to a word."""
    if isinstance(x, dict):
        return {OLD_SPELLING.get(k, k): current_spelling(v) for k, v in x.items()}
    if isinstance(x, list):
        return [current_spelling(v) for v in x]
    return OLD_SPELLING.get(x, x) if isinstance(x, str) else x


def load(p):
    out = []
    if p and os.path.exists(p):
        for x in open(p, encoding="utf-8"):
            x = x.strip()
            if x:
                try:
                    out.append(current_spelling(json.loads(x)))
                except ValueError:
                    pass
    return out


def column_card(s):
    s = (s or "").lower()
    if "amd" in s or "radeon" in s or "rx" in s:
        return "radeon"
    if "intel" in s or "uhd" in s or "i915" in s:
        return "intel"
    return s or "?"


def size_of(m):
    m = str(m or "").lower().replace(" ", "")
    if m in ("4k", "3840x2160"):
        return "4K"
    if m in ("3k", "3200x1800"):
        return "3K"
    if m in ("2k", "2560x1440"):
        return "2K"
    if m in ("fhd", "fullhd", "1920x1080"):
        return "FHD"
    return m or "?"


def campaigns(lines):
    """{campagna: {"meta":…, "levels": {n: level row}, "sessions": {n: [rows]},
    "ripetizioni": {n: k}}} — the last recording of every level wins."""
    c = {}
    for r in lines:
        k = r.get("campaign") or "?"
        cc = c.setdefault(k, {"meta": {}, "levels": {}, "sessions": {}, "ripetizioni": {}})
        n = r.get("level")
        if r.get("type") == "level":
            cc["ripetizioni"][n] = cc["ripetizioni"].get(n, 0) + 1
            cc["levels"][n] = r
            cc["sessions"][n] = []
            for f in ("desktop", "card", "driver", "size", "commit", "binary", "page", "kernel"):
                if r.get(f):
                    cc["meta"][f] = r[f]
        elif r.get("type") == "session":
            cc["sessions"].setdefault(n, []).append(r)
    return c


def worst(sess, entry, which_way="max"):
    v = [s.get("measurements", {}).get(entry) for s in sess]
    v = [x for x in v if isinstance(x, (int, float))]
    if not v:
        return None
    return max(v) if which_way == "max" else min(v)


def summary(liv):
    r = liv.get("resources") or {}
    out = {"cpu": (r.get("cpu_machine_pct") or {}).get("mean")}
    dis = vid = None
    for g in (r.get("gpu") or {}).values():
        d = (g.get("draw") or {}).get("mean")
        v = (g.get("video") or {}).get("mean")
        if d is not None and (dis is None or d > dis):
            dis = d
        if v is not None and (vid is None or v > vid):
            vid = v
    out["draw"], out["video"] = dis, vid
    mu, mt = (r.get("mem_used_mb") or {}).get("max"), r.get("mem_total_mb")
    out["mem"] = round(100.0 * mu / mt, 1) if mu and mt else None
    return out


def outcomes_campaign(cc):
    liv = sorted(cc["levels"])
    greens = [n for n in liv if cc["levels"][n]["class"] == "GREEN"]
    broken = [n for n in liv if cc["levels"][n]["class"] == "FAIL"]
    degr = [n for n in liv if cc["levels"][n]["class"] == "DEGRADED"]
    # ⭐ «holds» (holds) is the climb's stop rule (§6, §9): the highest level
    #   before the first FAIL or SIGNIFICANT DEGRADED — a non-significant DEGRADED holds.
    holds = None
    for n in liv:
        r = cc["levels"][n]
        if r["class"] == "FAIL" or (r["class"] == "DEGRADED" and r.get("significant")):
            break
        holds = n
    return {"holds": holds,
            "ultimo_verde": max(greens) if greens else None,
            "breakage": min(broken) if broken else None,
            "primo_degradato": min(degr) if degr else None,
            "maximum": max(liv) if liv else None}


def bottleneck(cc):
    liv = sorted(cc["levels"])
    if not liv:
        return None
    ugly = [n for n in liv if cc["levels"][n]["class"] != "GREEN"]
    n = ugly[0] if ugly else liv[-1]
    L = cc["levels"][n]
    s = summary(L)
    cand = [(k, v) for k, v in s.items() if v is not None]
    if not cand:
        return {"level": n, "risorsa": None}
    k, v = max(cand, key=lambda kv: kv[1])
    r = L.get("resources") or {}
    rec = []
    for name, x in (r.get("enclosures") or {}).items():
        if k == "cpu":
            val = (x.get("cpu_core") or {}).get("mean")
            if val is not None:
                rec.append((name, "%.2f core" % val, val))
        elif k in ("draw", "video"):
            val = (x.get("gpu", {}).get(k) or {}).get("mean")
            if val is not None:
                rec.append((name, "%.1f %%" % val, val))
        elif k == "mem":
            val = (x.get("pss_mb") or {}).get("max")
            if val is not None:
                rec.append((name, "%.0f MB" % val, val))
    rec.sort(key=lambda t: -t[2])
    throttle = sorted({x for g in (r.get("gpu") or {}).values()
                    for x, f in (g.get("throttling_fraction") or {}).items() if f >= 0.1})
    temp = max([((g.get("temp_c") or {}).get("max") or 0) for g in (r.get("gpu") or {}).values()] or [0])
    return {"level": n, "class": L["class"], "risorsa": dict(SERIES)[k], "value": v,
            "enclosures": rec[:3], "strozzatura": throttle, "temp_max": temp or None}


# ─────────────────────────────── text ──────────────────────────────────────
def text(lines):
    c = campaigns(lines)
    out = ["PHASE 16 — %d campaigns" % len(c)]
    for k, cc in sorted(c.items()):
        e = outcomes_campaign(cc)
        out.append("\n%s (%s · %s · %s) — holds %s · last GREEN %s · break %s" % (
            k, cc["meta"].get("desktop"), cc["meta"].get("card"), cc["meta"].get("size"),
            e["holds"], e["ultimo_verde"], e["breakage"]))
        for n in sorted(cc["levels"]):
            L = cc["levels"][n]
            s = summary(L)
            out.append("  %3s users  %-8s %s  cpu %s%% drawing %s%% video %s%% mem %s%%%s" % (
                n, L["class"], "SIG" if L.get("significant") and L["class"] == "DEGRADED" else "   ",
                s["cpu"], s["draw"], s["video"], s["mem"],
                "  (%d recordings)" % cc["ripetizioni"][n] if cc["ripetizioni"].get(n, 0) > 1 else ""))
        co = bottleneck(cc)
        if co and co.get("risorsa"):
            out.append("  bottleneck at %s users: %s %.0f %% — %s" % (
                co["level"], co["risorsa"], co["value"],
                ", ".join("%s %s" % (a, b) for a, b, _ in co["enclosures"])))
    return "\n".join(out)


# ─────────────────────────────── page ──────────────────────────────────────
CSS = """
:root{--sfondo:#f7f7f5;--carta:#fff;--testo:#1d1d1b;--tenue:#6b6b66;--riga:#e3e2dd;
--pass:#1f7a3a;--pass-f:#e3f3e7;--fail:#b3261e;--fail-f:#fbe4e2;--bloc:#8a5a00;--bloc-f:#fdf0d5;--vuoto:#f0efeb;
--s1:#2a78d6;--s2:#eb6834;--s3:#1baf7a;--s4:#eda100;--griglia:#e3e2dd}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--sfondo:#161615;--carta:#1f1f1d;
--testo:#ecebe6;--tenue:#a3a29c;--riga:#34332f;--pass:#7fd494;--pass-f:#1c3322;--fail:#ff9a90;
--fail-f:#3d1d1a;--bloc:#f2c26b;--bloc-f:#3a2d12;--vuoto:#262624;
--s1:#3987e5;--s2:#d95926;--s3:#199e70;--s4:#c98500;--griglia:#34332f}}
:root[data-theme="dark"]{--sfondo:#161615;--carta:#1f1f1d;--testo:#ecebe6;--tenue:#a3a29c;--riga:#34332f;
--pass:#7fd494;--pass-f:#1c3322;--fail:#ff9a90;--fail-f:#3d1d1a;--bloc:#f2c26b;--bloc-f:#3a2d12;--vuoto:#262624;
--s1:#3987e5;--s2:#d95926;--s3:#199e70;--s4:#c98500;--griglia:#34332f}
*{box-sizing:border-box}
body{margin:0;background:var(--sfondo);color:var(--testo);font:15px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:1200px;margin:0 auto;padding:24px 16px 64px}
h1{font-size:1.6rem;margin:0 0 4px}h2{font-size:1.15rem;margin:32px 0 8px}h3{font-size:1rem;margin:20px 0 6px}
.tenue{color:var(--tenue)}
.scorre{overflow-x:auto;border:1px solid var(--riga);border-radius:8px;background:var(--carta)}
table{border-collapse:collapse;width:100%;font-size:13px}
th,td{padding:6px 8px;border-bottom:1px solid var(--riga);text-align:left;vertical-align:top}
th{font-weight:600;white-space:nowrap}td.c{text-align:center;white-space:nowrap}td.n{text-align:right;font-variant-numeric:tabular-nums}
.GREEN{background:var(--pass-f);color:var(--pass)}.FAIL{background:var(--fail-f);color:var(--fail);font-weight:600}
.DEGRADED{background:var(--bloc-f);color:var(--bloc)}.vuoto{background:var(--vuoto);color:var(--tenue)}
.bollo{display:inline-block;padding:0 6px;border-radius:4px;font-size:12px;font-weight:600}
code{font-size:12px;word-break:break-all}
details{background:var(--carta);border:1px solid var(--riga);border-radius:8px;margin:8px 0;padding:8px 12px}
summary{cursor:pointer}
.grafico{background:var(--carta);border:1px solid var(--riga);border-radius:8px;padding:8px 8px 4px;margin:8px 0}
.grafico svg{display:block;width:100%;height:auto}
.legenda{display:flex;gap:14px;flex-wrap:wrap;font-size:12px;color:var(--tenue);margin:4px 8px}
.legenda i{display:inline-block;width:14px;height:3px;border-radius:2px;vertical-align:middle;margin-right:5px}
.riepilogo{border-collapse:separate;border-spacing:4px;width:100%;font-size:14px}.riepilogo th{text-align:center;padding:4px;border:0}.riepilogo th.d{text-align:left;padding-left:8px}.riepilogo th.m{font-size:15px;border-bottom:2px solid var(--riga)}.riepilogo th.s{font-weight:500;color:var(--tenue);font-size:12px}.riepilogo td{text-align:center;border:0;border-radius:8px;padding:10px 4px;min-width:64px;background:color-mix(in oklab,var(--pass-f) calc(var(--q)*100%),var(--fail-f));color:color-mix(in oklab,var(--pass) calc(var(--q)*100%),var(--fail))}.riepilogo td b{display:block;font-size:26px;line-height:1.1;font-variant-numeric:tabular-nums}.riepilogo td small{display:block;font-size:11px;opacity:.8}.riepilogo td.no{background:var(--vuoto);color:var(--tenue)}
.collo{background:var(--carta);border:1px solid var(--riga);border-radius:8px;padding:8px 12px;margin:8px 0}
"""

SIGN = {"GREEN": "✓", "DEGRADED": "▲", "FAIL": "✕"}


def stamp(c, sig=False):
    return "<span class='bollo %s'>%s %s%s</span>" % (c, SIGN.get(c, ""), c, " sig." if sig else "")


def graphical(cc):
    liv = sorted(cc["levels"])
    if not liv:
        return ""
    e = html.escape
    L, A, sx, sy = 44, 30, 640, 220          # margins and area
    W, H = L + sx + 80, 14 + sy + A + 26
    xmax = max(liv)
    xmin = min(0, min(liv))

    def X(n):
        return L + (n - xmin) / float(max(1, xmax - xmin)) * sx

    def Y(v):
        return 14 + sy - v / 100.0 * sy
    s = ["<svg viewBox='0 0 %d %d' role='img' aria-label='resources per step'>" % (W, H)]
    for g in (0, 25, 50, 75, 100):
        s.append("<line x1='%d' x2='%d' y1='%.1f' y2='%.1f' stroke='var(--griglia)' stroke-width='1'/>"
                 % (L, L + sx, Y(g), Y(g)))
        s.append("<text x='%d' y='%.1f' font-size='11' text-anchor='end' fill='var(--tenue)'>%d %%</text>"
                 % (L - 6, Y(g) + 4, g))
    for n in liv:
        c = cc["levels"][n]["class"]
        s.append("<text x='%.1f' y='%d' font-size='11' text-anchor='middle' fill='var(--tenue)'>%s</text>"
                 % (X(n), 14 + sy + 16, n))
        s.append("<text x='%.1f' y='%d' font-size='11' text-anchor='middle' class='%s' "
                 "style='background:none' fill='currentColor'>%s</text>" % (X(n), 14 + sy + 32, c, SIGN[c]))
    s.append("<text x='%d' y='%d' font-size='11' text-anchor='end' fill='var(--tenue)'>users →</text>"
             % (L + sx, 14 + sy + 46))
    labels = []
    for i, (k, name) in enumerate(SERIES):
        pts = [(n, summary(cc["levels"][n])[k]) for n in liv]
        pts = [(n, v) for n, v in pts if v is not None]
        if not pts:
            continue
        clr = "var(--s%d)" % (i + 1)
        s.append("<polyline fill='none' stroke='%s' stroke-width='2' stroke-linejoin='round' points='%s'/>"
                 % (clr, " ".join("%.1f,%.1f" % (X(n), Y(min(v, 100))) for n, v in pts)))
        for n, v in pts:
            s.append("<circle cx='%.1f' cy='%.1f' r='4' fill='%s' stroke='var(--carta)' stroke-width='2'>"
                     "<title>%s users · %s: %.1f %%</title></circle>" % (X(n), Y(min(v, 100)), clr, n, e(name), v))
        n, v = pts[-1]
        labels.append([Y(min(v, 100)) + 4, X(n) + 10, SHORT[k]])
    # the labels at the end of the lines do not overlap: at least 13 px between one and the next
    labels.sort()
    for j in range(1, len(labels)):
        labels[j][0] = max(labels[j][0], labels[j - 1][0] + 13)
    for y, x, t in labels:
        s.append("<text x='%.1f' y='%.1f' font-size='11' fill='var(--testo)'>%s</text>" % (x, y, e(t)))
    s.append("</svg>")
    leg = "".join("<span><i style='background:var(--s%d)'></i>%s</span>" % (i + 1, e(n)) for i, (_, n) in enumerate(SERIES))
    return ("<div class='grafico'>%s<div class='legenda'>%s<span>below the axis: the class of the level "
            "(✓ GREEN · ▲ DEGRADED · ✕ FAIL)</span></div></div>" % ("".join(s), leg))


def fmt(v, suf=""):
    return "—" if v is None else ("%s%s" % (round(v, 1) if isinstance(v, float) else v, suf))


def page(lines):
    e = html.escape
    c = campaigns(lines)
    fingerprints = sorted({(str(cc["meta"].get("commit")), str(cc["meta"].get("binary")),
                        str(cc["meta"].get("page"))) for cc in c.values()})
    h = ["<!doctype html><html lang='en'><head><meta charset='utf-8'>",
         "<meta name='viewport' content='width=device-width,initial-scale=1'>",
         "<title>Stress and capacity</title><style>%s</style></head><body><main>" % CSS,
         "<h1>Phase 16 — stress and capacity</h1>",
         "<p class='tenue'>Generated from the register. Measured on: %s. Thresholds of §9 (approved on 25 Sep 2026). "
         "⚠ The browsers run on the same server: every number is a <b>lower</b> bound.</p>"
         % e("; ".join("commit %s · binary %s · page %s" % x for x in fingerprints) or "—")]
    # ── ⭐ the SUMMARY (the user's proposal, 29 Sep): desktops in rows, sizes in columns, Intel
    #    and Radeon side by side; the BIG number is the strict one (all GREEN), the tolerance below ──
    find = {}
    for k, cc in c.items():
        m = cc["meta"]
        find[(m.get("desktop"), column_card(m.get("card")), size_of(m.get("size")))] = (k, outcomes_campaign(cc))
    h.append("<h2>Summary: how many users together</h2><p class='tenue'>The big number: users "
             "together with <b>all</b> under 50 ms and every other measure GREEN (§9). Below, «holds»: "
             "the level at which at most one user in four is just over (never above 100 ms) and "
             "nobody fails. Levels tried: 1, 4, 8, 12, 16, and the search between two steps "
             "only where the climb broke.</p>")
    h.append("<div class='scorre'><table class='riepilogo'><thead><tr><th></th>%s</tr><tr><th></th>%s</tr></thead><tbody>"
             % ("".join("<th class='m' colspan='2'>%s</th>" % {"FHD": "Full HD"}.get(m, m) for m in SIZES),
                "".join("<th class='s'>Intel</th><th class='s'>Radeon</th>" for _ in SIZES)))
    for d in DESKTOP:
        h.append("<tr><th class='d'>%s</th>" % e(d.upper() if d != "lxqt" else "LXQt"))
        for m in SIZES:
            for sc in ("intel", "radeon"):
                t = find.get((d, sc, m))
                if not t:
                    h.append("<td class='no'><b>·</b><small>not measured</small></td>")
                    continue
                k, es = t
                v, r = es["ultimo_verde"] or 0, es["holds"] or 0
                h.append("<td style='--q:%.3f' title='%s'><a href='#%s' style='color:inherit;text-decoration:none'>"
                         "<b>%d</b><small>holds %d</small></a></td>" % (min(v, 16) / 16.0, e(k), e(k), v, r))
        h.append("</tr>")
    h.append("</tbody></table></div>")
    # ── the §11 matrix ──
    cards = sorted({column_card(cc["meta"].get("card")) for cc in c.values()} | {"intel", "radeon"})
    h.append("<h2>The final matrix</h2><p class='tenue'>For every screen size: the last level "
             "in GREEN · the breaking point (first FAIL). Every row links to its climb.</p>")
    h.append("<div class='scorre'><table><thead><tr><th>desktop</th>%s</tr></thead><tbody>"
             % "".join("<th>%s</th>" % e({"intel": "Intel iGPU", "radeon": "Radeon RX 6800"}.get(s, s))
                       for s in cards))
    for d in DESKTOP:
        h.append("<tr><th>%s</th>" % e(d.upper() if d != "lxqt" else "LXQt"))
        for sc in cards:
            cells = []
            for k, cc in sorted(c.items(), key=lambda kv: SIZES.index(size_of(kv[1]["meta"].get("size")))
                                if size_of(kv[1]["meta"].get("size")) in SIZES else 9):
                if cc["meta"].get("desktop") != d or column_card(cc["meta"].get("card")) != sc:
                    continue
                es = outcomes_campaign(cc)
                cl = "GREEN" if es["breakage"] is None and es["primo_degradato"] is None else (
                    "FAIL" if es["breakage"] is not None else "DEGRADED")
                cells.append("<a href='#%s' class='bollo %s'>%s</a> holds <b>%s</b> · last GREEN <b>%s</b> · break <b>%s</b>"
                             % (e(k), cl, e(size_of(cc["meta"].get("size"))), fmt(es["holds"]),
                                fmt(es["ultimo_verde"]), fmt(es["breakage"])))
            h.append("<td>%s</td>" % ("<br>".join(cells) if cells else "<span class='tenue'>·</span>"))
        h.append("</tr>")
    h.append("</tbody></table></div>")
    # ── bottlenecks ──
    h.append("<h2>The bottlenecks</h2><p class='tenue'>At the first non-GREEN level of every campaign (or "
             "at the last, if it is all green): the most loaded resource, and the enclosures that consume it. A "
             "high resource on its own is not a FAIL: it explains the behaviour, it does not judge it.</p>")
    for k, cc in sorted(c.items()):
        co = bottleneck(cc)
        if not co or not co.get("risorsa"):
            continue
        h.append("<div class='collo'><b>%s</b> at %s users %s — <b>%s %.0f %%</b>%s%s%s</div>" % (
            e(k), co["level"], stamp(co["class"]), e(co["risorsa"]), co["value"],
            (" · " + ", ".join("%s %s" % (e(a), e(b)) for a, b, _ in co["enclosures"])) if co["enclosures"] else "",
            (" · throttling: " + e(", ".join(co["strozzatura"]))) if co["strozzatura"] else "",
            (" · %.0f °C" % co["temp_max"]) if co["temp_max"] else ""))
    # ── the curves ──
    h.append("<h2>The climbs</h2>")
    for k, cc in sorted(c.items()):
        m = cc["meta"]
        h.append("<h3 id='%s'>%s</h3><p class='tenue'>%s · %s %s · %s · commit %s · kernel %s</p>" % (
            e(k), e(k), e(str(m.get("desktop"))), e(str(m.get("card"))), e(str(m.get("driver") or "")),
            e(str(m.get("size"))), e(str(m.get("commit"))), e(str(m.get("kernel")))))
        h.append(graphical(cc))
        h.append("<div class='scorre'><table><thead><tr><th>users</th><th>class</th><th>sessions</th>"
                 "<th>delay p95</th><th>skipped</th><th>freeze</th><th>gaps/min</th><th>video</th>"
                 "<th>audio</th><th>birth</th><th>CPU</th><th>drawing</th><th>video (card)</th>"
                 "<th>memory</th></tr></thead><tbody>")
        for n in sorted(cc["levels"]):
            L, ss = cc["levels"][n], cc["sessions"].get(n, [])
            s = summary(L)
            co = L.get("sessions") or {}
            rip = cc["ripetizioni"].get(n, 1)
            h.append("<tr><th>%s%s</th><td>%s</td><td class='n'>%s/%s/%s</td>" % (
                n, "<br><span class='tenue'>%d times</span>" % rip if rip > 1 else "",
                stamp(L["class"], L.get("significant") and L["class"] == "DEGRADED"),
                co.get("GREEN", 0), co.get("DEGRADED", 0), co.get("FAIL", 0)))
            for entry, suf, which_way in (("delay_p95_ms", " ms", "max"), ("skipped_pct", " %", "max"),
                                     ("block_max_s", " s", "max"), ("holes", "", "max"),
                                     ("video_fps", "/s", "min"), ("audio_audible_pct", " %", "min"),
                                     ("birth_s", " s", "max")):
                h.append("<td class='n'>%s</td>" % fmt(worst(ss, entry, which_way), suf))
            for kk in ("cpu", "draw", "video", "mem"):
                h.append("<td class='n'>%s</td>" % fmt(s[kk], " %"))
            h.append("</tr>")
        h.append("</tbody></table></div><p class='tenue'>The session measures are the WORST of the "
                 "level; the resources are averages in the check window (memory: the maximum).</p>")
        for n in sorted(cc["levels"]):
            L = cc["levels"][n]
            if L["class"] == "GREEN":
                continue
            h.append("<details><summary>%s %s users — %s</summary><p>%s</p>" % (
                stamp(L["class"], L.get("significant")), n, e(k), e(L.get("rationale") or "")))
            for r in cc["sessions"].get(n, []):
                if r.get("class") != "GREEN":
                    h.append("<p>%s user %s (%s, %s, %s): %s</p>" % (
                        stamp(r["class"]), r.get("user"), e(str(r.get("profile"))), e(str(r.get("browser"))),
                        e(str(r.get("tenant"))), e(r.get("rationale") or "")))
            for x in L.get("evidence") or []:
                h.append("<code>%s</code><br>" % e(x))
            h.append("</details>")
    h.append("</main></body></html>")
    return "".join(h)


# ─────────────────────────────── certify ───────────────────────────────────
def synthetic(p):
    """Two fake campaigns: kde Intel 4K that breaks at 12, and kde Intel FHD all green;
    level 8 of the first one repeated (§14)."""
    with open(p, "w", encoding="utf-8") as f:
        def liv(camp, size, n, grade, cpu, dis, vid, sig=False):
            f.write(json.dumps({"type": "level", "campaign": camp, "level": n, "desktop": "kde",
                                "card": "Intel UHD 770", "driver": "i915", "size": size,
                                "commit": "abc1234", "binary": "b1443a0b", "page": "c5279e66",
                                "kernel": "7.0", "class": grade, "significant": sig,
                                "sessions": {"GREEN": n if grade == "GREEN" else n - 1,
                                             "DEGRADED": 1 if grade == "DEGRADED" else 0,
                                             "FAIL": 1 if grade == "FAIL" else 0},
                                "rationale": "synthetic", "evidence": ["/media/REMOTIX/misure/fase16/x"],
                                "resources": {"cpu_machine_pct": {"mean": cpu}, "mem_used_mb": {"max": 1000 * n},
                                            "mem_total_mb": 32000,
                                            "enclosures": {"remotix": {"cpu_core": {"mean": 0.1 * n},
                                                                    "gpu": {"video": {"mean": vid}}},
                                                        "sessions": {"cpu_core": {"mean": 0.5 * n},
                                                                     "gpu": {"draw": {"mean": dis * 0.4}}},
                                                        "browser": {"cpu_core": {"mean": 0.3 * n},
                                                                    "gpu": {"draw": {"mean": dis * 0.6}}}},
                                            "gpu": {"0000:00:02.0": {"card": "card0", "draw": {"mean": dis},
                                                                     "video": {"mean": vid},
                                                                     "temp_c": {"max": 70},
                                                                     "throttling_fraction": {"pl1": 0.5}
                                                                     if dis > 90 else {}}}}},
                               ensure_ascii=False) + "\n")
            for u in range(1, n + 1):
                cl = "FAIL" if grade == "FAIL" and u == n else ("DEGRADED" if grade == "DEGRADED" and u == n
                                                                else "GREEN")
                f.write(json.dumps({"type": "session", "campaign": camp, "level": n, "user": u,
                                    "profile": "ABCD"[(u - 1) % 4], "browser": "firefox" if u % 2 else "chrome",
                                    "tenant": "c16u%02d" % u, "class": cl,
                                    "rationale": "synthetic: freeze 4 s" if cl == "FAIL" else "",
                                    "measurements": {"delay_p95_ms": 20 + 3 * n, "skipped_pct": 0.1 * n,
                                               "block_max_s": 4.0 if cl == "FAIL" else 0.3,
                                               "birth_s": 1 + 0.2 * n,
                                               "video_fps": 30 - n if u % 4 == 0 else None}},
                                   ensure_ascii=False) + "\n")
        liv("intel-4k-kde", "4K", 1, "GREEN", 8, 12, 5)
        liv("intel-4k-kde", "4K", 4, "GREEN", 25, 40, 18)
        liv("intel-4k-kde", "4K", 8, "DEGRADED", 45, 80, 35, True)
        liv("intel-4k-kde", "4K", 8, "GREEN", 44, 78, 34)          # the repetition wins
        liv("intel-4k-kde", "4K", 12, "FAIL", 70, 99, 52)
        liv("intel-4k-kde", "4K", 10, "GREEN", 55, 88, 44)
        liv("intel-4k-kde", "4K", 11, "FAIL", 62, 95, 48)
        liv("intel-fhd-kde", "FHD", 1, "GREEN", 4, 5, 2)
        liv("intel-fhd-kde", "FHD", 16, "GREEN", 50, 60, 30)


def certify():
    outcomes = []

    def look(name, ok, d=""):
        outcomes.append(ok)
        print("  %s %s%s" % ("PASS" if ok else "FAIL", name, (" — " + d) if d else ""))
    print("16-rapporto --certify")
    tmp = tempfile.mkdtemp(prefix="16-rapporto-cert-")
    try:
        reg = os.path.join(tmp, "registro.jsonl")
        synthetic(reg)
        lines = load(reg)
        c = campaigns(lines)
        e = outcomes_campaign(c["intel-4k-kde"])
        look("the bisection: last GREEN 10, break 11", e["ultimo_verde"] == 10 and e["breakage"] == 11,
               str(e))
        look("the repetition of §14 takes the place of the first",
               c["intel-4k-kde"]["levels"][8]["class"] == "GREEN" and c["intel-4k-kde"]["ripetizioni"][8] == 2)
        co = bottleneck(c["intel-4k-kde"])
        look("the bottleneck: the card (drawing) at the first non-GREEN, with the browser enclosure on top",
               co["level"] == 11 and co["risorsa"] == "card: drawing" and co["enclosures"][0][0] == "browser"
               and co["strozzatura"] == ["pl1"], str(co))
        p = page(lines)
        pp = os.path.join(tmp, "rapporto.html")
        open(pp, "w").write(p)
        look("the page: matrix, curve, bottlenecks, details",
               "The final matrix" in p and "<svg" in p and "The bottlenecks" in p and "<details>" in p
               and "last GREEN <b>10</b> · break <b>11</b>" in p and "last GREEN <b>16</b>" in p,
               "%d byte" % len(p))
        look("⛔ FAULT: an empty register does not invent cells", "last GREEN" not in page([]))
        # ⭐ the same register as a campaign before the English rename wrote it (Italian keys and
        #   values; before the rename the two are the same) ⇒ the same report
        antica = {b: a for a, b in OLD_SPELLING.items()}

        def all_antica(x):
            if isinstance(x, dict):
                return {antica.get(k, k): all_antica(v) for k, v in x.items()}
            if isinstance(x, list):
                return [all_antica(v) for v in x]
            return antica.get(x, x) if isinstance(x, str) else x
        reg_v = os.path.join(tmp, "registro-vecchio.jsonl")
        with open(reg_v, "w", encoding="utf-8") as f:
            for x in open(reg, encoding="utf-8"):
                f.write(json.dumps(all_antica(json.loads(x)), ensure_ascii=False) + "\n")
        rv = load(reg_v)
        look("an OLD register (Italian keys and values) ⇒ the same report", rv == lines
               and page(rv) == p and text(rv) == text(lines))
        print(text(lines))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    n, ok = len(outcomes), sum(outcomes)
    print("CERTIFY %s — %d of %d" % ("PASS" if ok == n else "FAIL", ok, n))
    return 0 if ok == n else 1


def choose(lines, prefixes):
    """⭐ The VALID campaigns (fasi/16 §11 and the anomalies): only the given labels (`intel-b`,
    `amd-b`, `intel-c` …), and for every desktop × card × size cell the **most
    recent** campaign — a redone climb (actor cured, product cured, resumed after a block)
    takes the place of the earlier one.  The discarded ones are listed, they do not vanish silently."""
    if not prefixes:
        return lines, []
    keep = [r for r in lines if any((r.get("campaign") or "").startswith(x + "-") for x in prefixes)]
    when, cell = {}, {}
    for r in keep:
        if r.get("type") != "level":
            continue
        k = r.get("campaign")
        when[k] = max(when.get(k, ""), r.get("started") or "")
        cell[k] = (r.get("desktop"), column_card(r.get("card")), size_of(r.get("size")))
    wins = {}
    for k, cas in cell.items():
        if cas not in wins or when[k] > when[wins[cas]]:
            wins[cas] = k
    good = set(wins.values())
    discarded = sorted(k for k in cell if k not in good)
    return [r for r in keep if r.get("campaign") in good], discarded


def main():
    a = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--log", default=os.path.join(HERE, "registro.jsonl"))
    a.add_argument("--html", default=os.path.join(HERE, "rapporto.html"))
    a.add_argument("--text", action="store_true")
    a.add_argument("--synthetic", help="writes a synthetic test register at this path and exits")
    a.add_argument("--certify", action="store_true")
    a.add_argument("--campaigns", nargs="*", default=[],
                   help="only these labels (e.g. intel-b amd-b intel-c); per cell the most recent wins")
    o = a.parse_args()
    if o.certify:
        return certify()
    if o.synthetic:
        synthetic(o.synthetic)
        return 0
    lines = load(o.log)
    lines, discarded = choose(lines, o.campaigns)
    if discarded:
        print("⚠ replaced by a more recent climb: %s" % ", ".join(discarded))
    with open(o.html, "w", encoding="utf-8") as f:
        f.write(page(lines))
    if o.text:
        print(text(lines))
    print("→ %s (%d register rows)" % (o.html, len(lines)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
