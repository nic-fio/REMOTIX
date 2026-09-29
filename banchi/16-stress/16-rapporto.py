#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
16-rapporto — IL RAPPORTO DELLA FASE 16, GENERATO DAL REGISTRO (mai scritto a mano)

    python3 16-rapporto.py [--registro banchi/16-stress/registro.jsonl]
                           [--html banchi/16-stress/rapporto.html] [--testo]
    python3 16-rapporto.py --certifica      (registro sintetico in una cartella sua)

Dal registro di `16-classifica.py` (§10: una riga per livello, una per sessione):
- la MATRICE FINALE di §11, desktop × scheda: per ogni misura dello schermo
  (4K → 3K → 2K → Full HD) l'ultimo livello GREEN, il primo livello in FAIL
  (il punto di rottura) e il primo DEGRADED;
- la CURVA di ogni campagna per gradino: una riga per livello (l'ULTIMA
  registrazione di quel livello: il registro si aggiunge soltanto, e una
  ripetizione di §14 prende il posto della prima — le ripetizioni si contano),
  con le misure peggiori delle sessioni e le risorse; e un grafico delle
  risorse per gradino (CPU della macchina, disegno e video della scheda,
  memoria usata — tutte in %, un solo asse);
- i COLLI DI BOTTIGLIA: al primo livello non GREEN di ogni campagna (o
  all'ultimo, se e' tutta verde), la risorsa piu' carica e i recinti che la
  consumano;
- per ogni livello non GREEN: le ragioni delle sessioni e le evidenze.
"""
import argparse
import html
import json
import os
import shutil
import sys
import tempfile

QUI = os.path.dirname(os.path.abspath(__file__))
DESKTOP = ("gnome", "kde", "xfce", "lxqt")
MISURE = ("4K", "3K", "2K", "FHD")
ORD = {"GREEN": 0, "DEGRADED": 1, "FAIL": 2}
SERIE = (("cpu", "CPU della macchina"), ("disegno", "scheda: disegno"),
         ("video", "scheda: video"), ("mem", "memoria usata"))
BREVI = {"cpu": "CPU", "disegno": "disegno", "video": "video", "mem": "memoria"}


def leggi(p):
    out = []
    if p and os.path.exists(p):
        for x in open(p, encoding="utf-8"):
            x = x.strip()
            if x:
                try:
                    out.append(json.loads(x))
                except ValueError:
                    pass
    return out


def colonna_scheda(s):
    s = (s or "").lower()
    if "amd" in s or "radeon" in s or "rx" in s:
        return "radeon"
    if "intel" in s or "uhd" in s or "i915" in s:
        return "intel"
    return s or "?"


def misura_di(m):
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


def campagne(righe):
    """{campagna: {"meta":…, "livelli": {n: riga di livello}, "sessioni": {n: [righe]},
    "ripetizioni": {n: k}}} — l'ultima registrazione di ogni livello vince."""
    c = {}
    for r in righe:
        k = r.get("campagna") or "?"
        cc = c.setdefault(k, {"meta": {}, "livelli": {}, "sessioni": {}, "ripetizioni": {}})
        n = r.get("livello")
        if r.get("tipo") == "livello":
            cc["ripetizioni"][n] = cc["ripetizioni"].get(n, 0) + 1
            cc["livelli"][n] = r
            cc["sessioni"][n] = []
            for f in ("desktop", "scheda", "driver", "misura", "commit", "binario", "pagina", "nucleo"):
                if r.get(f):
                    cc["meta"][f] = r[f]
        elif r.get("tipo") == "sessione":
            cc["sessioni"].setdefault(n, []).append(r)
    return c


def peggiore(sess, voce, verso="max"):
    v = [s.get("misure", {}).get(voce) for s in sess]
    v = [x for x in v if isinstance(x, (int, float))]
    if not v:
        return None
    return max(v) if verso == "max" else min(v)


def sommario(liv):
    r = liv.get("risorse") or {}
    out = {"cpu": (r.get("cpu_macchina_pct") or {}).get("media")}
    dis = vid = None
    for g in (r.get("gpu") or {}).values():
        d = (g.get("disegno") or {}).get("media")
        v = (g.get("video") or {}).get("media")
        if d is not None and (dis is None or d > dis):
            dis = d
        if v is not None and (vid is None or v > vid):
            vid = v
    out["disegno"], out["video"] = dis, vid
    mu, mt = (r.get("mem_usata_mb") or {}).get("max"), r.get("mem_totale_mb")
    out["mem"] = round(100.0 * mu / mt, 1) if mu and mt else None
    return out


def esiti_campagna(cc):
    liv = sorted(cc["livelli"])
    verdi = [n for n in liv if cc["livelli"][n]["classe"] == "GREEN"]
    rotti = [n for n in liv if cc["livelli"][n]["classe"] == "FAIL"]
    degr = [n for n in liv if cc["livelli"][n]["classe"] == "DEGRADED"]
    # ⭐ «regge» e' la regola di non-prosecuzione della salita (§6, §9): il livello piu' alto
    #   prima del primo FAIL o DEGRADED SIGNIFICATIVO — un DEGRADED non significativo regge.
    regge = None
    for n in liv:
        r = cc["livelli"][n]
        if r["classe"] == "FAIL" or (r["classe"] == "DEGRADED" and r.get("significativo")):
            break
        regge = n
    return {"regge": regge,
            "ultimo_verde": max(verdi) if verdi else None,
            "rottura": min(rotti) if rotti else None,
            "primo_degradato": min(degr) if degr else None,
            "massimo": max(liv) if liv else None}


def collo(cc):
    liv = sorted(cc["livelli"])
    if not liv:
        return None
    brutti = [n for n in liv if cc["livelli"][n]["classe"] != "GREEN"]
    n = brutti[0] if brutti else liv[-1]
    L = cc["livelli"][n]
    s = sommario(L)
    cand = [(k, v) for k, v in s.items() if v is not None]
    if not cand:
        return {"livello": n, "risorsa": None}
    k, v = max(cand, key=lambda kv: kv[1])
    r = L.get("risorse") or {}
    rec = []
    for nome, x in (r.get("recinti") or {}).items():
        if k == "cpu":
            val = (x.get("cpu_core") or {}).get("media")
            if val is not None:
                rec.append((nome, "%.2f core" % val, val))
        elif k in ("disegno", "video"):
            val = (x.get("gpu", {}).get(k) or {}).get("media")
            if val is not None:
                rec.append((nome, "%.1f %%" % val, val))
        elif k == "mem":
            val = (x.get("pss_mb") or {}).get("max")
            if val is not None:
                rec.append((nome, "%.0f MB" % val, val))
    rec.sort(key=lambda t: -t[2])
    stroz = sorted({x for g in (r.get("gpu") or {}).values()
                    for x, f in (g.get("strozzatura_frazione") or {}).items() if f >= 0.1})
    temp = max([((g.get("temp_c") or {}).get("max") or 0) for g in (r.get("gpu") or {}).values()] or [0])
    return {"livello": n, "classe": L["classe"], "risorsa": dict(SERIE)[k], "valore": v,
            "recinti": rec[:3], "strozzatura": stroz, "temp_max": temp or None}


# ─────────────────────────────── testo ─────────────────────────────────────
def testo(righe):
    c = campagne(righe)
    out = ["FASE 16 — %d campagne" % len(c)]
    for k, cc in sorted(c.items()):
        e = esiti_campagna(cc)
        out.append("\n%s (%s · %s · %s) — regge %s · ultimo GREEN %s · rottura %s" % (
            k, cc["meta"].get("desktop"), cc["meta"].get("scheda"), cc["meta"].get("misura"),
            e["regge"], e["ultimo_verde"], e["rottura"]))
        for n in sorted(cc["livelli"]):
            L = cc["livelli"][n]
            s = sommario(L)
            out.append("  %3s utenti  %-8s %s  cpu %s%% disegno %s%% video %s%% mem %s%%%s" % (
                n, L["classe"], "SIG" if L.get("significativo") and L["classe"] == "DEGRADED" else "   ",
                s["cpu"], s["disegno"], s["video"], s["mem"],
                "  (%d registrazioni)" % cc["ripetizioni"][n] if cc["ripetizioni"].get(n, 0) > 1 else ""))
        co = collo(cc)
        if co and co.get("risorsa"):
            out.append("  collo a %s utenti: %s %.0f %% — %s" % (
                co["livello"], co["risorsa"], co["valore"],
                ", ".join("%s %s" % (a, b) for a, b, _ in co["recinti"])))
    return "\n".join(out)


# ─────────────────────────────── pagina ────────────────────────────────────
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

SEGNO = {"GREEN": "✓", "DEGRADED": "▲", "FAIL": "✕"}


def bollo(c, sig=False):
    return "<span class='bollo %s'>%s %s%s</span>" % (c, SEGNO.get(c, ""), c, " sig." if sig else "")


def grafico(cc):
    liv = sorted(cc["livelli"])
    if not liv:
        return ""
    e = html.escape
    L, A, sx, sy = 44, 30, 640, 220          # margini e area
    W, H = L + sx + 80, 14 + sy + A + 26
    xmax = max(liv)
    xmin = min(0, min(liv))

    def X(n):
        return L + (n - xmin) / float(max(1, xmax - xmin)) * sx

    def Y(v):
        return 14 + sy - v / 100.0 * sy
    s = ["<svg viewBox='0 0 %d %d' role='img' aria-label='risorse per gradino'>" % (W, H)]
    for g in (0, 25, 50, 75, 100):
        s.append("<line x1='%d' x2='%d' y1='%.1f' y2='%.1f' stroke='var(--griglia)' stroke-width='1'/>"
                 % (L, L + sx, Y(g), Y(g)))
        s.append("<text x='%d' y='%.1f' font-size='11' text-anchor='end' fill='var(--tenue)'>%d %%</text>"
                 % (L - 6, Y(g) + 4, g))
    for n in liv:
        c = cc["livelli"][n]["classe"]
        s.append("<text x='%.1f' y='%d' font-size='11' text-anchor='middle' fill='var(--tenue)'>%s</text>"
                 % (X(n), 14 + sy + 16, n))
        s.append("<text x='%.1f' y='%d' font-size='11' text-anchor='middle' class='%s' "
                 "style='background:none' fill='currentColor'>%s</text>" % (X(n), 14 + sy + 32, c, SEGNO[c]))
    s.append("<text x='%d' y='%d' font-size='11' text-anchor='end' fill='var(--tenue)'>utenti →</text>"
             % (L + sx, 14 + sy + 46))
    etichette = []
    for i, (k, nome) in enumerate(SERIE):
        pts = [(n, sommario(cc["livelli"][n])[k]) for n in liv]
        pts = [(n, v) for n, v in pts if v is not None]
        if not pts:
            continue
        col = "var(--s%d)" % (i + 1)
        s.append("<polyline fill='none' stroke='%s' stroke-width='2' stroke-linejoin='round' points='%s'/>"
                 % (col, " ".join("%.1f,%.1f" % (X(n), Y(min(v, 100))) for n, v in pts)))
        for n, v in pts:
            s.append("<circle cx='%.1f' cy='%.1f' r='4' fill='%s' stroke='var(--carta)' stroke-width='2'>"
                     "<title>%s utenti · %s: %.1f %%</title></circle>" % (X(n), Y(min(v, 100)), col, n, e(nome), v))
        n, v = pts[-1]
        etichette.append([Y(min(v, 100)) + 4, X(n) + 10, BREVI[k]])
    # le etichette in fondo alle linee non si pestano: almeno 13 px fra l'una e l'altra
    etichette.sort()
    for j in range(1, len(etichette)):
        etichette[j][0] = max(etichette[j][0], etichette[j - 1][0] + 13)
    for y, x, t in etichette:
        s.append("<text x='%.1f' y='%.1f' font-size='11' fill='var(--testo)'>%s</text>" % (x, y, e(t)))
    s.append("</svg>")
    leg = "".join("<span><i style='background:var(--s%d)'></i>%s</span>" % (i + 1, e(n)) for i, (_, n) in enumerate(SERIE))
    return ("<div class='grafico'>%s<div class='legenda'>%s<span>sotto l'asse: la classe del livello "
            "(✓ GREEN · ▲ DEGRADED · ✕ FAIL)</span></div></div>" % ("".join(s), leg))


def fmt(v, suf=""):
    return "—" if v is None else ("%s%s" % (round(v, 1) if isinstance(v, float) else v, suf))


def pagina(righe):
    e = html.escape
    c = campagne(righe)
    impronte = sorted({(str(cc["meta"].get("commit")), str(cc["meta"].get("binario")),
                        str(cc["meta"].get("pagina"))) for cc in c.values()})
    h = ["<!doctype html><html lang='it'><head><meta charset='utf-8'>",
         "<meta name='viewport' content='width=device-width,initial-scale=1'>",
         "<title>Stress e capacità</title><style>%s</style></head><body><main>" % CSS,
         "<h1>Fase 16 — stress e capacità</h1>",
         "<p class='tenue'>Generato dal registro. Misurato su: %s. Soglie di §9 (approvate il 25 set 2026). "
         "⚠ I browser girano sullo stesso server: ogni numero è un limite <b>inferiore</b>.</p>"
         % e("; ".join("commit %s · binario %s · pagina %s" % x for x in impronte) or "—")]
    # ── ⭐ il RIEPILOGO (proposta dell'utente, 29 set): desktop in riga, misure in colonna, Intel
    #    e Radeon affiancate; il numero GRANDE e' il severo (tutti GREEN), la tolleranza sotto ──
    trova = {}
    for k, cc in c.items():
        m = cc["meta"]
        trova[(m.get("desktop"), colonna_scheda(m.get("scheda")), misura_di(m.get("misura")))] = (k, esiti_campagna(cc))
    h.append("<h2>Riepilogo: quanti utenti insieme</h2><p class='tenue'>Il numero grande: utenti "
             "insieme con <b>tutti</b> sotto i 50 ms e ogni altra misura GREEN (§9). Sotto, «regge»: "
             "il livello in cui al massimo un utente su quattro è appena oltre (mai sopra 100 ms) e "
             "nessuno fallisce. Livelli provati: 1, 4, 8, 12, 16, e la ricerca fra due gradini "
             "solo dove la salita si è rotta.</p>")
    h.append("<div class='scorre'><table class='riepilogo'><thead><tr><th></th>%s</tr><tr><th></th>%s</tr></thead><tbody>"
             % ("".join("<th class='m' colspan='2'>%s</th>" % {"FHD": "Full HD"}.get(m, m) for m in MISURE),
                "".join("<th class='s'>Intel</th><th class='s'>Radeon</th>" for _ in MISURE)))
    for d in DESKTOP:
        h.append("<tr><th class='d'>%s</th>" % e(d.upper() if d != "lxqt" else "LXQt"))
        for m in MISURE:
            for sc in ("intel", "radeon"):
                t = trova.get((d, sc, m))
                if not t:
                    h.append("<td class='no'><b>·</b><small>non misurato</small></td>")
                    continue
                k, es = t
                v, r = es["ultimo_verde"] or 0, es["regge"] or 0
                h.append("<td style='--q:%.3f' title='%s'><a href='#%s' style='color:inherit;text-decoration:none'>"
                         "<b>%d</b><small>regge %d</small></a></td>" % (min(v, 16) / 16.0, e(k), e(k), v, r))
        h.append("</tr>")
    h.append("</tbody></table></div>")
    # ── la matrice §11 ──
    schede = sorted({colonna_scheda(cc["meta"].get("scheda")) for cc in c.values()} | {"intel", "radeon"})
    h.append("<h2>La matrice finale</h2><p class='tenue'>Per ogni misura dello schermo: l'ultimo livello "
             "GREEN · il punto di rottura (primo FAIL). Ogni riga rimanda alla sua salita.</p>")
    h.append("<div class='scorre'><table><thead><tr><th>desktop</th>%s</tr></thead><tbody>"
             % "".join("<th>%s</th>" % e({"intel": "Intel iGPU", "radeon": "Radeon RX 6800"}.get(s, s))
                       for s in schede))
    for d in DESKTOP:
        h.append("<tr><th>%s</th>" % e(d.upper() if d != "lxqt" else "LXQt"))
        for sc in schede:
            celle = []
            for k, cc in sorted(c.items(), key=lambda kv: MISURE.index(misura_di(kv[1]["meta"].get("misura")))
                                if misura_di(kv[1]["meta"].get("misura")) in MISURE else 9):
                if cc["meta"].get("desktop") != d or colonna_scheda(cc["meta"].get("scheda")) != sc:
                    continue
                es = esiti_campagna(cc)
                cl = "GREEN" if es["rottura"] is None and es["primo_degradato"] is None else (
                    "FAIL" if es["rottura"] is not None else "DEGRADED")
                celle.append("<a href='#%s' class='bollo %s'>%s</a> regge <b>%s</b> · ultimo GREEN <b>%s</b> · rottura <b>%s</b>"
                             % (e(k), cl, e(misura_di(cc["meta"].get("misura"))), fmt(es["regge"]),
                                fmt(es["ultimo_verde"]), fmt(es["rottura"])))
            h.append("<td>%s</td>" % ("<br>".join(celle) if celle else "<span class='tenue'>·</span>"))
        h.append("</tr>")
    h.append("</tbody></table></div>")
    # ── colli di bottiglia ──
    h.append("<h2>I colli di bottiglia</h2><p class='tenue'>Al primo livello non GREEN di ogni campagna (o "
             "all'ultimo, se è tutta verde): la risorsa più carica, e i recinti che la consumano. Una "
             "risorsa alta da sola non è un FAIL: spiega il comportamento, non lo giudica.</p>")
    for k, cc in sorted(c.items()):
        co = collo(cc)
        if not co or not co.get("risorsa"):
            continue
        h.append("<div class='collo'><b>%s</b> a %s utenti %s — <b>%s %.0f %%</b>%s%s%s</div>" % (
            e(k), co["livello"], bollo(co["classe"]), e(co["risorsa"]), co["valore"],
            (" · " + ", ".join("%s %s" % (e(a), e(b)) for a, b, _ in co["recinti"])) if co["recinti"] else "",
            (" · strozzatura: " + e(", ".join(co["strozzatura"]))) if co["strozzatura"] else "",
            (" · %.0f °C" % co["temp_max"]) if co["temp_max"] else ""))
    # ── le curve ──
    h.append("<h2>Le salite</h2>")
    for k, cc in sorted(c.items()):
        m = cc["meta"]
        h.append("<h3 id='%s'>%s</h3><p class='tenue'>%s · %s %s · %s · commit %s · nucleo %s</p>" % (
            e(k), e(k), e(str(m.get("desktop"))), e(str(m.get("scheda"))), e(str(m.get("driver") or "")),
            e(str(m.get("misura"))), e(str(m.get("commit"))), e(str(m.get("nucleo")))))
        h.append(grafico(cc))
        h.append("<div class='scorre'><table><thead><tr><th>utenti</th><th>classe</th><th>sessioni</th>"
                 "<th>ritardo p95</th><th>saltati</th><th>blocco</th><th>buchi/min</th><th>video</th>"
                 "<th>audio</th><th>nascita</th><th>CPU</th><th>disegno</th><th>video (scheda)</th>"
                 "<th>memoria</th></tr></thead><tbody>")
        for n in sorted(cc["livelli"]):
            L, ss = cc["livelli"][n], cc["sessioni"].get(n, [])
            s = sommario(L)
            co = L.get("sessioni") or {}
            rip = cc["ripetizioni"].get(n, 1)
            h.append("<tr><th>%s%s</th><td>%s</td><td class='n'>%s/%s/%s</td>" % (
                n, "<br><span class='tenue'>%d volte</span>" % rip if rip > 1 else "",
                bollo(L["classe"], L.get("significativo") and L["classe"] == "DEGRADED"),
                co.get("GREEN", 0), co.get("DEGRADED", 0), co.get("FAIL", 0)))
            for voce, suf, verso in (("ritardo_p95_ms", " ms", "max"), ("saltati_pct", " %", "max"),
                                     ("blocco_max_s", " s", "max"), ("buchi", "", "max"),
                                     ("video_fps", "/s", "min"), ("audio_udibile_pct", " %", "min"),
                                     ("nascita_s", " s", "max")):
                h.append("<td class='n'>%s</td>" % fmt(peggiore(ss, voce, verso), suf))
            for kk in ("cpu", "disegno", "video", "mem"):
                h.append("<td class='n'>%s</td>" % fmt(s[kk], " %"))
            h.append("</tr>")
        h.append("</tbody></table></div><p class='tenue'>Le misure delle sessioni sono le PEGGIORI del "
                 "livello; le risorse sono medie nella finestra di controllo (la memoria: il massimo).</p>")
        for n in sorted(cc["livelli"]):
            L = cc["livelli"][n]
            if L["classe"] == "GREEN":
                continue
            h.append("<details><summary>%s %s utenti — %s</summary><p>%s</p>" % (
                bollo(L["classe"], L.get("significativo")), n, e(k), e(L.get("ragione") or "")))
            for r in cc["sessioni"].get(n, []):
                if r.get("classe") != "GREEN":
                    h.append("<p>%s utente %s (%s, %s, %s): %s</p>" % (
                        bollo(r["classe"]), r.get("utente"), e(str(r.get("profilo"))), e(str(r.get("browser"))),
                        e(str(r.get("inquilino"))), e(r.get("ragione") or "")))
            for x in L.get("evidenze") or []:
                h.append("<code>%s</code><br>" % e(x))
            h.append("</details>")
    h.append("</main></body></html>")
    return "".join(h)


# ─────────────────────────────── certifica ─────────────────────────────────
def sintetico(p):
    """Due campagne finte: kde Intel 4K che si rompe a 12, e kde Intel FHD tutta verde;
    il livello 8 della prima ripetuto (§14)."""
    with open(p, "w", encoding="utf-8") as f:
        def liv(camp, misura, n, classe, cpu, dis, vid, sig=False):
            f.write(json.dumps({"tipo": "livello", "campagna": camp, "livello": n, "desktop": "kde",
                                "scheda": "Intel UHD 770", "driver": "i915", "misura": misura,
                                "commit": "abc1234", "binario": "b1443a0b", "pagina": "c5279e66",
                                "nucleo": "7.0", "classe": classe, "significativo": sig,
                                "sessioni": {"GREEN": n if classe == "GREEN" else n - 1,
                                             "DEGRADED": 1 if classe == "DEGRADED" else 0,
                                             "FAIL": 1 if classe == "FAIL" else 0},
                                "ragione": "sintetico", "evidenze": ["/media/REMOTIX/misure/fase16/x"],
                                "risorse": {"cpu_macchina_pct": {"media": cpu}, "mem_usata_mb": {"max": 1000 * n},
                                            "mem_totale_mb": 32000,
                                            "recinti": {"remotix": {"cpu_core": {"media": 0.1 * n},
                                                                    "gpu": {"video": {"media": vid}}},
                                                        "sessioni": {"cpu_core": {"media": 0.5 * n},
                                                                     "gpu": {"disegno": {"media": dis * 0.4}}},
                                                        "browser": {"cpu_core": {"media": 0.3 * n},
                                                                    "gpu": {"disegno": {"media": dis * 0.6}}}},
                                            "gpu": {"0000:00:02.0": {"scheda": "card0", "disegno": {"media": dis},
                                                                     "video": {"media": vid},
                                                                     "temp_c": {"max": 70},
                                                                     "strozzatura_frazione": {"pl1": 0.5}
                                                                     if dis > 90 else {}}}}},
                               ensure_ascii=False) + "\n")
            for u in range(1, n + 1):
                cl = "FAIL" if classe == "FAIL" and u == n else ("DEGRADED" if classe == "DEGRADED" and u == n
                                                                else "GREEN")
                f.write(json.dumps({"tipo": "sessione", "campagna": camp, "livello": n, "utente": u,
                                    "profilo": "ABCD"[(u - 1) % 4], "browser": "firefox" if u % 2 else "chrome",
                                    "inquilino": "c16u%02d" % u, "classe": cl,
                                    "ragione": "sintetico: blocco 4 s" if cl == "FAIL" else "",
                                    "misure": {"ritardo_p95_ms": 20 + 3 * n, "saltati_pct": 0.1 * n,
                                               "blocco_max_s": 4.0 if cl == "FAIL" else 0.3,
                                               "nascita_s": 1 + 0.2 * n,
                                               "video_fps": 30 - n if u % 4 == 0 else None}},
                                   ensure_ascii=False) + "\n")
        liv("intel-4k-kde", "4K", 1, "GREEN", 8, 12, 5)
        liv("intel-4k-kde", "4K", 4, "GREEN", 25, 40, 18)
        liv("intel-4k-kde", "4K", 8, "DEGRADED", 45, 80, 35, True)
        liv("intel-4k-kde", "4K", 8, "GREEN", 44, 78, 34)          # la ripetizione vince
        liv("intel-4k-kde", "4K", 12, "FAIL", 70, 99, 52)
        liv("intel-4k-kde", "4K", 10, "GREEN", 55, 88, 44)
        liv("intel-4k-kde", "4K", 11, "FAIL", 62, 95, 48)
        liv("intel-fhd-kde", "FHD", 1, "GREEN", 4, 5, 2)
        liv("intel-fhd-kde", "FHD", 16, "GREEN", 50, 60, 30)


def certifica():
    esiti = []

    def guarda(nome, ok, d=""):
        esiti.append(ok)
        print("  %s %s%s" % ("PASS" if ok else "FAIL", nome, (" — " + d) if d else ""))
    print("16-rapporto --certifica")
    tmp = tempfile.mkdtemp(prefix="16-rapporto-cert-")
    try:
        reg = os.path.join(tmp, "registro.jsonl")
        sintetico(reg)
        righe = leggi(reg)
        c = campagne(righe)
        e = esiti_campagna(c["intel-4k-kde"])
        guarda("la ricerca a meta': ultimo GREEN 10, rottura 11", e["ultimo_verde"] == 10 and e["rottura"] == 11,
               str(e))
        guarda("la ripetizione di §14 prende il posto della prima",
               c["intel-4k-kde"]["livelli"][8]["classe"] == "GREEN" and c["intel-4k-kde"]["ripetizioni"][8] == 2)
        co = collo(c["intel-4k-kde"])
        guarda("il collo: la scheda (disegno) al primo non GREEN, col recinto browser in testa",
               co["livello"] == 11 and co["risorsa"] == "scheda: disegno" and co["recinti"][0][0] == "browser"
               and co["strozzatura"] == ["pl1"], str(co))
        p = pagina(righe)
        pp = os.path.join(tmp, "rapporto.html")
        open(pp, "w").write(p)
        guarda("la pagina: matrice, curva, colli, dettagli",
               "La matrice finale" in p and "<svg" in p and "I colli di bottiglia" in p and "<details>" in p
               and "ultimo GREEN <b>10</b> · rottura <b>11</b>" in p and "ultimo GREEN <b>16</b>" in p,
               "%d byte" % len(p))
        guarda("⛔ GUASTO: un registro vuoto non inventa caselle", "ultimo GREEN" not in pagina([]))
        print(testo(righe))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    n, ok = len(esiti), sum(esiti)
    print("CERTIFICA %s — %d su %d" % ("PASS" if ok == n else "FAIL", ok, n))
    return 0 if ok == n else 1


def scegli(righe, prefissi):
    """⭐ Le campagne VALIDE (fasi/16 §11 e le anomalie): solo le etichette date (`intel-b`,
    `amd-b`, `intel-c` …), e per ogni casella desktop × scheda × misura la campagna **piu'
    recente** — una salita rifatta (attore curato, prodotto curato, ripresa dopo un blocco)
    prende il posto di quella di prima.  Le scartate si elencano, non spariscono in silenzio."""
    if not prefissi:
        return righe, []
    tieni = [r for r in righe if any((r.get("campagna") or "").startswith(x + "-") for x in prefissi)]
    quando, casella = {}, {}
    for r in tieni:
        if r.get("tipo") != "livello":
            continue
        k = r.get("campagna")
        quando[k] = max(quando.get(k, ""), r.get("inizio") or "")
        casella[k] = (r.get("desktop"), colonna_scheda(r.get("scheda")), misura_di(r.get("misura")))
    vince = {}
    for k, cas in casella.items():
        if cas not in vince or quando[k] > quando[vince[cas]]:
            vince[cas] = k
    buone = set(vince.values())
    scartate = sorted(k for k in casella if k not in buone)
    return [r for r in tieni if r.get("campagna") in buone], scartate


def main():
    a = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--registro", default=os.path.join(QUI, "registro.jsonl"))
    a.add_argument("--html", default=os.path.join(QUI, "rapporto.html"))
    a.add_argument("--testo", action="store_true")
    a.add_argument("--sintetico", help="scrive un registro sintetico di prova in questo percorso ed esce")
    a.add_argument("--certifica", action="store_true")
    a.add_argument("--campagne", nargs="*", default=[],
                   help="solo queste etichette (es. intel-b amd-b intel-c); per casella vince la piu' recente")
    o = a.parse_args()
    if o.certifica:
        return certifica()
    if o.sintetico:
        sintetico(o.sintetico)
        return 0
    righe = leggi(o.registro)
    righe, scartate = scegli(righe, o.campagne)
    if scartate:
        print("⚠ sostituite da una salita piu' recente: %s" % ", ".join(scartate))
    with open(o.html, "w", encoding="utf-8") as f:
        f.write(pagina(righe))
    if o.testo:
        print(testo(righe))
    print("→ %s (%d righe del registro)" % (o.html, len(righe)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
