#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-rapporto — IL RAPPORTO DELLA SUITE, GENERATO DAL REGISTRO (mai scritto a mano)

    python3 15-rapporto.py --registro registro.jsonl [--difetti difetti.jsonl]
                           [--giro 1] [--html rapporto.html] [--testo]

- la MATRICE funzione × desktop × browser: per ogni casella l'ULTIMO esito del
  giro scelto (passata sana), col segno del guasto (visto / non visto);
- l'elenco dei DIFETTI col loro stato (da difetti.jsonl);
- per ogni casella FAIL o BLOCKED: la ragione, e le evidenze;
- in testa: binario, pagina, commit su cui e' stato misurato, e i conti.
Serve alla BONIFICA, non all'utente.
"""
import argparse
import html
import json
import os
import re
import sys

DESKTOP = ("gnome", "kde", "xfce", "lxqt")
BROWSER = ("firefox", "chrome")
NOMI = {
    "F-001": "accesso e creazione della sessione", "F-002": "prima immagine",
    "F-003": "aggiornamento dello schermo", "F-004": "mouse", "F-005": "forma del puntatore",
    "F-006": "ridimensionare dal bordo", "F-007": "tastiera: caratteri e tasti speciali",
    "F-008": "modificatori e combinazioni", "F-009": "disposizione, accenti, AltGr",
    "F-010": "scorciatoie del desktop", "F-011": "la tela all'attacco", "F-012": "audio",
    "F-013": "video", "F-014": "appunti, browser → sessione",
    "F-015": "appunti, sessione → browser", "F-016": "stacco",
    "F-017": "riattacco alla stessa misura", "F-018": "riattacco a misura diversa",
    "F-019": "perdita di rete e rientro", "F-020": "browser chiuso di colpo",
    "F-021": "«Esci» dal menu", "F-022": "orologio del silenzio",
    "F-023": "orologio d'inattività", "F-024": "orologio d'abbandono",
    "F-025": "stesso utente da due schede", "F-026": "più utenti insieme",
    "F-027": "parola sbagliata", "F-028": "ban", "F-029": "voci pericolose assenti",
    "F-030": "lo schermo non si spegne da solo", "F-031": "tocco (Android)",
    "P-A": "percorso A: stacco e riattacco con input", "P-B": "percorso B: perdita di rete",
    "P-C": "percorso C: misura diversa e ritorno", "P-D": "percorso D: rete persa col video",
    "P-E": "percorso E: browser chiuso, nuova connessione",
    "P-F": "percorso F: applicazione ritrovata",
    "C7": "tecnico: non resta niente", "C9": "tecnico: il registro dice di chi",
    "C14": "tecnico: le scatole non si disturbano", "C18": "tecnico: i gruppi della scheda",
    "C19": "tecnico: la scatola resta pulita",
}


def ordine(f):
    m = re.match(r"([A-Z])-?(\d+)?", f)
    pref = {"F": 0, "P": 1, "N": 2, "C": 3}.get(f[0], 4)
    num = int(m.group(2)) if m and m.group(2) else 0
    return (pref, num, f)


def leggi(p):
    righe = []
    if p and os.path.exists(p):
        for x in open(p, encoding="utf-8"):
            x = x.strip()
            if x:
                try:
                    righe.append(json.loads(x))
                except ValueError:
                    pass
    return righe


def matrice(righe):
    """{(funzione, desktop, browser, passata): ultima riga} — l'ordine del file
    e' l'ordine del tempo (il registro si aggiunge soltanto)."""
    m = {}
    for r in righe:
        m[(r.get("funzione"), r.get("desktop"), r.get("browser"), r.get("passata", "sana"))] = r
    return m


def colonne(righe):
    col = []
    for d in DESKTOP:
        for b in BROWSER:
            col.append((d, b))
    if any(r.get("browser") == "-" for r in righe):
        for d in DESKTOP:
            col.append((d, "-"))
    return col


def testo(righe, difetti, giro):
    m = matrice(righe)
    funzioni = sorted({r["funzione"] for r in righe}, key=ordine)
    col = [(d, b) for d, b in colonne(righe) if any(k[1] == d and k[2] == b for k in m)]
    conto = {}
    for k, r in m.items():
        if k[3] == "sana":
            conto[r["esito"]] = conto.get(r["esito"], 0) + 1
    out = ["GIRO %s · %s" % (giro, " ".join("%s=%d" % kv for kv in sorted(conto.items())))]
    out.append("%-8s " % "" + " ".join("%-7s" % (d[:3] + "/" + b[:2]) for d, b in col))
    for f in funzioni:
        celle = []
        for d, b in col:
            r = m.get((f, d, b, "sana"))
            g = m.get((f, d, b, "guasto"))
            s = {"PASS": "ok", "FAIL": "FAIL", "BLOCKED": "BLOC"}.get(r["esito"], "?") if r else "·"
            if g:
                s += {"PASS": "", "FAIL": "!g", "BLOCKED": "?g"}.get(g["esito"], "")
            celle.append("%-7s" % s)
        out.append("%-8s " % f + " ".join(celle))
    rosse = [r for k, r in m.items() if r["esito"] != "PASS"]
    if rosse:
        out.append("\nNON VERDI:")
        for r in sorted(rosse, key=lambda r: (ordine(r["funzione"]), r["desktop"], r["browser"])):
            out.append("  %s %s/%s [%s] %s: %s" % (r["funzione"], r["desktop"], r["browser"],
                                                  r.get("passata"), r["esito"],
                                                  (r.get("ragione") or "")[:220]))
    if difetti:
        out.append("\nDIFETTI:")
        for dd in difetti:
            out.append("  %s [%s, classe %s] %s — %s" % (dd.get("id"), dd.get("stato"),
                                                        dd.get("classe"), dd.get("titolo", ""),
                                                        ", ".join(dd.get("dove") or [])))
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


def pagina(righe, difetti, giro):
    e = html.escape
    m = matrice(righe)
    funzioni = sorted({r["funzione"] for r in righe}, key=ordine)
    col = [(d, b) for d, b in colonne(righe) if any(k[1] == d and k[2] == b for k in m)]
    conto = {}
    for k, r in m.items():
        if k[3] == "sana":
            conto[r["esito"]] = conto.get(r["esito"], 0) + 1
    guasti = [r for k, r in m.items() if k[3] == "guasto"]
    visti = sum(1 for r in guasti if r["esito"] == "PASS")
    impronte = sorted({(r.get("binario"), r.get("pagina"), r.get("commit")) for r in righe})
    h = ["<!doctype html><html lang='it'><head><meta charset='utf-8'>",
         "<meta name='viewport' content='width=device-width,initial-scale=1'>",
         "<title>Suite REMOTIX, giro %s</title><style>%s</style></head><body><main>" % (e(str(giro)), CSS),
         "<h1>Suite funzionale — giro %s</h1>" % e(str(giro)),
         "<p class='tenue'>Generato dal registro. Misurato su: %s.</p>" % e("; ".join(
             "binario %s · pagina %s · commit %s" % x for x in impronte)),
         "<div class='conti'>"]
    for k, cls in (("PASS", "PASS"), ("FAIL", "FAIL"), ("BLOCKED", "BLOCKED")):
        h.append("<div class='conto'><span class='%s' style='background:none'>%s</span><b>%d</b></div>"
                 % (cls, k, conto.get(k, 0)))
    h.append("<div class='conto'>guasti visti<b>%d/%d</b></div>" % (visti, len(guasti)))
    h.append("<div class='conto'>difetti aperti<b>%d</b></div></div>" % sum(
        1 for d in difetti if d.get("stato") not in ("verificato",)))
    h.append("<h2>La matrice</h2><div class='scorre'><table><thead><tr><th>funzione</th>")
    for d, b in col:
        h.append("<th>%s<br><span class='tenue'>%s</span></th>" % (e(d), e(b)))
    h.append("</tr></thead><tbody>")
    for f in funzioni:
        h.append("<tr><th>%s <span class='tenue'>%s</span></th>" % (e(f), e(NOMI.get(f, ""))))
        for d, b in col:
            r = m.get((f, d, b, "sana"))
            g = m.get((f, d, b, "guasto"))
            if not r:
                h.append("<td class='c vuoto'>·</td>")
                continue
            gs = ""
            if g:
                gs = "<br><span class='g'>guasto %s</span>" % {"PASS": "visto", "FAIL": "NON visto",
                                                              "BLOCKED": "?"}.get(g["esito"], "?")
            h.append("<td class='c %s' title='%s'>%s%s</td>" % (r["esito"], e(r.get("ragione") or ""),
                                                            r["esito"], gs))
        h.append("</tr>")
    h.append("</tbody></table></div>")
    if difetti:
        h.append("<h2>I difetti</h2><div class='scorre'><table><thead><tr><th>id</th><th>che cosa si vede</th>"
                 "<th>dove</th><th>classe</th><th>stato</th><th>cura</th><th>prova</th></tr></thead><tbody>")
        for dd in difetti:
            h.append("<tr><th>%s</th><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"
                     % tuple(e(str(x or "")) for x in (dd.get("id"), dd.get("titolo"),
                                                         ", ".join(dd.get("dove") or []),
                                                         dd.get("classe"), dd.get("stato"),
                                                         dd.get("commit_cura"), dd.get("prova"))))
        h.append("</tbody></table></div>")
    rosse = sorted([r for k, r in m.items() if r["esito"] != "PASS"],
                   key=lambda r: (ordine(r["funzione"]), r["desktop"], r["browser"]))
    if rosse:
        h.append("<h2>Le caselle non verdi</h2>")
        for r in rosse:
            h.append("<details><summary><b class='%s' style='background:none'>%s</b> %s · %s/%s · %s</summary>"
                     % (r["esito"], r["esito"], e(r["funzione"]), e(r["desktop"]), e(r["browser"]),
                        e(r.get("passata", ""))))
            h.append("<p>%s</p>" % e(r.get("ragione") or ""))
            if r.get("atteso"):
                h.append("<p class='tenue'>atteso: %s<br>osservato: %s</p>" % (e(r["atteso"]),
                                                                            e(r.get("osservato") or "")))
            for x in r.get("evidenze") or []:
                h.append("<code>%s</code><br>" % e(x))
            h.append("<p class='tenue'>%s · %s s · %s</p></details>" % (e(r.get("inizio") or ""),
                                                                      r.get("durata_s"),
                                                                      e(r.get("versione") or "")))
    h.append("</main></body></html>")
    return "".join(h)


def main():
    a = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--registro", required=True)
    a.add_argument("--difetti", default="")
    a.add_argument("--giro", default="")
    a.add_argument("--html", default="")
    a.add_argument("--testo", action="store_true")
    o = a.parse_args()
    righe = leggi(o.registro)
    giri = [str(r.get("giro")) for r in righe]
    giro = o.giro or (giri[-1] if giri else "?")
    righe = [r for r in righe if str(r.get("giro")) == giro]
    difetti = leggi(o.difetti)
    if o.html:
        with open(o.html, "w", encoding="utf-8") as f:
            f.write(pagina(righe, difetti, giro))
    if o.testo or not o.html:
        print(testo(righe, difetti, giro))
    return 0


if __name__ == "__main__":
    sys.exit(main())
