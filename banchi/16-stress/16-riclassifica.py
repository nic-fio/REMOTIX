#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
16-riclassifica — THE «FREEZE» REDONE WITH THE PAGE'S ROUND, WITHOUT REDOING THE CLIMB (fasi/20 §3-bis.2)

    python3 16-riclassifica.py --salita /media/REMOTIX/misure/fase16/intel-f20-fhd-xfce [--fps-video 30]
    python3 16-riclassifica.py --certifica

Until the commit of the cure, the actor set the time of the keys typed by Firefox
with `ore_dei_tasti`, from the return of the Marionette chain: a held-back
chain moved the keys AFTER their own echo, and the «longest freeze of the
image» entry took the next paint (the blinking cursor,
~1.1 s).  ⭐ The page, meanwhile, measured by itself the delay of every command
(key, click, notch → frame that contains it: `REMOTIX.giro`), and the actor
wrote it in every row of `stato.jsonl`.

What it does, for every level of `salita.jsonl`:
  1. in the rows of the profiles that type (not D) with work, the freeze becomes
     min(previous freeze, the slowest round of the NEW samples of those 5 s).
     ⇒ a real freeze stays (the round of a stuck key is long too; and a
     key that never comes back gives no samples, so the row is not touched);
  2. redoes the judgement with 16-classifica.py --secco on a COPY of the level
     (links to the real files, only the stato.jsonl rewritten);
  3. writes ALONGSIDE, without touching the data: `livello-NN/classifica-riclassificata.log`
     and, in the climb, `riclassificata.json` (class before/now of every level,
     «last true GREEN» before/now).
⛔ The classes that the climb had imposed (entry failed, host resources,
   level interrupted, unreadable class) stay as they are: they are not about the freeze.
"""
import argparse
import glob
import importlib.util as _iu
import json
import os
import shutil
import subprocess
import sys
import tempfile

QUI = os.path.dirname(os.path.abspath(__file__))
CLASSI = ("GREEN", "DEGRADED", "FAIL")


def _modulo(nome, file):
    s = _iu.spec_from_file_location(nome, os.path.join(QUI, file))
    m = _iu.module_from_spec(s)
    s.loader.exec_module(m)
    return m


campioni_nuovi = _modulo("attore16", "16-attore.py").campioni_nuovi


def correggi_righe(righe):
    """⇒ (corrected rows, how many touched).  Pure: the rows are dicts of stato.jsonl."""
    out, toccate, prec = [], 0, None
    for r in righe:
        r = dict(r)
        giro = r.get("giro")
        nuovi = campioni_nuovi(prec, giro) if isinstance(giro, dict) else []
        if isinstance(giro, dict):
            prec = giro
        b = r.get("blocco_max_ms")
        if (r.get("profilo") != "D" and r.get("lavoro", True) is not False and b is not None
                and nuovi and max(nuovi) < b):
            r["blocco_ricalcolato"] = {"prima_ms": b, "giro_max_ms": round(max(nuovi), 1),
                                       "campioni": len(nuovi)}
            r["blocco_max_ms"] = int(round(max(nuovi)))
            toccate += 1
        out.append(r)
    return out, toccate


def ultimo_green(righe):
    """Like `ultimo_green` of 16-coda.sh: the highest level with class GREEN, not interrupted."""
    g = [int(r.get("livello") or 0) for r in righe if r.get("classe") == "GREEN" and not r.get("interrotto")]
    return max(g) if g else None


def classe_imposta(r):
    """The class of the climb that does not come from the judgement of the thresholds.
    ⚠ Both forms: the salita.jsonl of the running campaign is written by the old
    (Italian) 16-salita.py, the new one writes in English."""
    perche = str(r.get("ragione_classe") or "")
    return (r.get("interrotto") or r.get("classe") not in CLASSI
            or perche.startswith(("ENTRATA FALLITA", "ENTRY FAILED"))
            or perche.startswith(("⛔ RISORSE DELL'OSPITE", "⛔ HOST RESOURCES")))


def copia_corretta(dirliv, dest):
    """The copy of the level: links, except the rewritten stato.jsonl.  ⇒ rows touched."""
    toccate = 0
    for voce in os.listdir(dirliv):
        src = os.path.join(dirliv, voce)
        if voce.startswith("utente-") and os.path.isdir(src):
            os.makedirs(os.path.join(dest, voce))
            for f in os.listdir(src):
                if f == "stato.jsonl":
                    righe = []
                    for riga in open(os.path.join(src, f), encoding="utf-8", errors="replace"):
                        try:
                            righe.append(json.loads(riga))
                        except ValueError:
                            continue
                    nuove, n = correggi_righe(righe)
                    toccate += n
                    with open(os.path.join(dest, voce, f), "w", encoding="utf-8") as o:
                        for r in nuove:
                            o.write(json.dumps(r, ensure_ascii=False) + "\n")
                else:
                    os.symlink(os.path.join(src, f), os.path.join(dest, voce, f))
        elif not voce.startswith("classifica"):
            os.symlink(src, os.path.join(dest, voce))
    return toccate


def giudica_di_nuovo(dirliv, riga, fps_video, prog):
    """⇒ (new class or None, rows touched, output of the classifier)."""
    tmp = tempfile.mkdtemp(prefix="16-riclassifica-")
    try:
        dest = os.path.join(tmp, os.path.basename(dirliv))
        os.makedirs(dest)
        toccate = copia_corretta(dirliv, dest)
        cmd = [sys.executable, prog, "--livello-dir", dest, "--secco", "--json",
               "--campagna", str(riga.get("campagna") or ""), "--livello", str(riga.get("livello") or 0),
               "--finestra-s", str(int(float(riga.get("controllo_min") or 2) * 60))]
        if fps_video:
            cmd += ["--fps-video", str(fps_video)]
        r = subprocess.run(cmd, capture_output=True, text=True, errors="replace", timeout=900, cwd=QUI)
        uscita = r.stdout + r.stderr
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    classe = None
    for l in uscita.splitlines():
        i = l.find("{")
        if i < 0:
            continue
        try:
            d = json.loads(l[i:])
        except ValueError:
            continue
        if isinstance(d, dict) and d.get("tipo") == "livello" and d.get("classe") in CLASSI:
            classe = d["classe"]
    return classe, toccate, uscita


def riclassifica(salita, fps_video=None, prog=None):
    prog = prog or os.path.join(QUI, "16-classifica.py")
    righe = []
    for l in open(os.path.join(salita, "salita.jsonl"), encoding="utf-8", errors="replace"):
        try:
            righe.append(json.loads(l))
        except ValueError:
            continue
    nuove, livelli = [], []
    for r in righe:
        dirliv = os.path.join(salita, str(r.get("nome") or ""))
        n = dict(r)
        voce = {"nome": r.get("nome"), "livello": r.get("livello"), "classe_prima": r.get("classe")}
        if classe_imposta(r) or not r.get("nome") or not os.path.isdir(dirliv):
            voce.update(classe_ora=r.get("classe"), toccate=0, nota="class imposed by the climb: unchanged")
        else:
            classe, toccate, uscita = giudica_di_nuovo(dirliv, r, fps_video, prog)
            with open(os.path.join(dirliv, "classifica-riclassificata.log"), "w", encoding="utf-8") as f:
                f.write("# 16-riclassifica.py: the freeze with the page's round (fasi/20 §3-bis.2); "
                        "rows touched: %d\n%s" % (toccate, uscita))
            n["classe"] = classe or "?"
            voce.update(classe_ora=n["classe"], toccate=toccate)
            if toccate == 0 and n["classe"] != r.get("classe"):
                # ⚠ without rows touched the judgement MUST come back the same: otherwise the
                #   redone judgement is not that of the climb (arguments, missing files), and it does not count
                voce["incoerente"] = True
        nuove.append(n)
        livelli.append(voce)
    esito = {"salita": os.path.basename(os.path.normpath(salita)),
             "ultimo_green_prima": ultimo_green(righe), "ultimo_green_ora": ultimo_green(nuove),
             "livelli": livelli}
    with open(os.path.join(salita, "riclassificata.json"), "w", encoding="utf-8") as f:
        json.dump(esito, f, ensure_ascii=False, indent=1)
    return esito


# ═══════════════════════════════════════════════════════════════════════════
def certifica():
    falliti = []

    def prova(cosa, vero, det=""):
        print("   %s  %s%s" % ("⭐ ok" if vero else "⛔ NO", cosa, (" — " + det) if det else ""))
        if not vero:
            falliti.append(cosa)

    print("── the rows")
    g = lambda v, c: {"visti": v, "campioni": c}  # noqa: E731
    righe = [{"profilo": "C", "lavoro": True, "blocco_max_ms": 40, "giro": g(10, [20.0] * 10)},
             # ⛔ FAULT seen on 7 Oct: 1111 ms from the estimate, the page in the same interval 47.5
             {"profilo": "C", "lavoro": True, "blocco_max_ms": 1111, "giro": g(14, [20.0] * 10 + [30, 47.5, 25, 22])},
             # a REAL freeze: the round is long too ⇒ almost all of it stays
             {"profilo": "A", "lavoro": True, "blocco_max_ms": 2500, "giro": g(15, [20.0] * 14 + [2400.0])},
             # no new sample (the key never came back) ⇒ not touched
             {"profilo": "A", "lavoro": True, "blocco_max_ms": 3000, "giro": g(15, [20.0] * 14 + [2400.0])},
             # the video is not touched
             {"profilo": "D", "lavoro": True, "blocco_max_ms": 1200, "giro": g(20, [20.0] * 20)}]
    nuove, n = correggi_righe(righe)
    b = [r["blocco_max_ms"] for r in nuove]
    prova("FAULT seen: Firefox's 1.1 s freeze becomes the page's round (48 ms)",
          b[1] == 48 and nuove[1]["blocco_ricalcolato"]["prima_ms"] == 1111, str(b))
    prova("a real freeze stays (2.4 s)", b[2] == 2400, str(b))
    prova("without new samples the row is not touched", b[3] == 3000 and "blocco_ricalcolato" not in nuove[3])
    prova("the video (D) is not touched", b[4] == 1200)
    prova("rows touched counted", n == 2, str(n))
    prova("the starting rows do not change", righe[1]["blocco_max_ms"] == 1111)
    prova("the first row (without a previous reading) is not touched", b[0] == 40)

    print("── the climb")
    sr = [{"livello": 1, "classe": "GREEN"}, {"livello": 4, "classe": "DEGRADED"},
          {"livello": 8, "classe": "GREEN", "interrotto": True}]
    prova("last true GREEN as in 16-coda.sh", ultimo_green(sr) == 1)
    prova("imposed class: entry failed, host, interrupted, «?»",
          classe_imposta({"classe": "FAIL", "ragione_classe": "ENTRATA FALLITA (1 entrati su 4)"})
          and classe_imposta({"classe": "FAIL", "ragione_classe": "⛔ RISORSE DELL'OSPITE (§7.7): x"})
          and classe_imposta({"classe": "GREEN", "interrotto": True}) and classe_imposta({"classe": "?"})
          and not classe_imposta({"classe": "DEGRADED", "ragione_classe": "blocco"}))

    print("── end to end, with a fake classifier (the real thresholds are tested by 16-classifica)")
    tmp = tempfile.mkdtemp(prefix="16-riclassifica-cert-")
    try:
        finto = os.path.join(tmp, "finto.py")
        # ⭐ the fake judges only the freeze, like the threshold of §9: > 1000 ms ⇒ DEGRADED
        open(finto, "w").write(
            "import sys, json, glob, os\n"
            "d = sys.argv[sys.argv.index('--livello-dir') + 1]\n"
            "b = [json.loads(l)['blocco_max_ms'] for f in glob.glob(os.path.join(d, 'utente-*', 'stato.jsonl'))"
            " for l in open(f)]\n"
            "print('LIVELLO')\n"
            "print(json.dumps({'tipo': 'livello', 'classe': 'DEGRADED' if max(b) > 1000 else 'GREEN'}))\n")
        sal = os.path.join(tmp, "intel-f20-fhd-xfce")
        for nome, blocchi in (("livello-01", [40]), ("livello-04", [40, 1111]), ("livello-08", [40, 1063]),
                              ("livello-12", [5000])):
            os.makedirs(os.path.join(sal, nome, "utente-01"))
            open(os.path.join(sal, nome, "server.log"), "w").write("x\n")
            open(os.path.join(sal, nome, "classifica.log"), "w").write("originale\n")
            with open(os.path.join(sal, nome, "utente-01", "stato.jsonl"), "w") as f:
                for k, bl in enumerate(blocchi):
                    f.write(json.dumps({"profilo": "C", "lavoro": True, "blocco_max_ms": bl,
                                        "giro": g(10 + k, [25.0] * (10 + k))}) + "\n")
        with open(os.path.join(sal, "salita.jsonl"), "w") as f:
            for n_, nome, cl in ((1, "livello-01", "GREEN"), (4, "livello-04", "DEGRADED"),
                                 (8, "livello-08", "DEGRADED"), (12, "livello-12", "DEGRADED")):
                f.write(json.dumps({"campagna": "cert", "livello": n_, "nome": nome, "classe": cl,
                                    "controllo_min": 2}) + "\n")
        prima = open(os.path.join(sal, "livello-04", "utente-01", "stato.jsonl")).read()
        e = riclassifica(sal, prog=finto)
        prova("FAULT seen: «good 12, true green 1» ⇒ last true GREEN 8",
              e["ultimo_green_prima"] == 1 and e["ultimo_green_ora"] == 8, json.dumps(e)[:300])
        prova("the level with the real freeze (5 s without new samples) stays DEGRADED",
              e["livelli"][3]["classe_ora"] == "DEGRADED")
        prova("the original data do not change",
              open(os.path.join(sal, "livello-04", "utente-01", "stato.jsonl")).read() == prima
              and open(os.path.join(sal, "livello-04", "classifica.log")).read() == "originale\n")
        prova("alongside: classifica-riclassificata.log and riclassificata.json",
              os.path.exists(os.path.join(sal, "livello-04", "classifica-riclassificata.log"))
              and os.path.exists(os.path.join(sal, "riclassificata.json")))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("⭐ CERTIFIED" if not falliti else "⛔ NOT CERTIFIED: %d" % len(falliti))
    return 0 if not falliti else 1


def main():
    a = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--salita", help="the folder of the climb (with salita.jsonl)")
    a.add_argument("--fps-video", type=float, default=None)
    a.add_argument("--certifica", action="store_true")
    o = a.parse_args()
    if o.certifica:
        return certifica()
    if not o.salita:
        a.error("--salita or --certifica")
    e = riclassifica(o.salita, o.fps_video)
    for v in e["livelli"]:
        print("  %-26s %-9s → %-9s rows touched %s" % (v["nome"], v["classe_prima"], v["classe_ora"],
                                                        v.get("toccate")))
    print("%s: last true GREEN %s → %s" % (e["salita"], e["ultimo_green_prima"], e["ultimo_green_ora"]))
    if any(v.get("incoerente") for v in e["livelli"]):
        print("⛔ levels without rows touched with the class changed: the redone judgement is not that "
              "of the climb, the reclassification does NOT count")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
