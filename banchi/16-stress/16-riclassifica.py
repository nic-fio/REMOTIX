#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
16-riclassifica — IL «BLOCCO» RIFATTO COL GIRO DELLA PAGINA, SENZA RIFARE LA SALITA (fasi/20 §3-bis.2)

    python3 16-riclassifica.py --salita /media/REMOTIX/misure/fase16/intel-f20-fhd-xfce [--fps-video 30]
    python3 16-riclassifica.py --certifica

Fino al commit della cura, l'attore metteva l'ora dei tasti battuti da Firefox
con `ore_dei_tasti`, dal ritorno della catena di Marionette: una catena
trattenuta spostava i tasti DOPO il loro stesso eco, e la voce «blocco piu'
lungo dell'immagine» prendeva il dipinto successivo (il cursore che lampeggia,
~1,1 s).  ⭐ La pagina, intanto, misurava da se' il ritardo di ogni comando
(tasto, clic, tacca → fotogramma che lo contiene: `REMOTIX.giro`), e l'attore
lo scriveva in ogni riga di `stato.jsonl`.

Che cosa fa, per ogni livello di `salita.jsonl`:
  1. nelle righe dei profili che battono (non D) con lavoro, il blocco diventa
     min(blocco di prima, il giro piu' lento dei campioni NUOVI di quei 5 s).
     ⇒ un blocco vero resta (il giro di un tasto fermo e' lungo anche lui; e un
     tasto che non torna mai non da' campioni, quindi la riga non si tocca);
  2. rifa' il giudizio con 16-classifica.py --secco su una COPIA del livello
     (collegamenti ai file veri, solo gli stato.jsonl riscritti);
  3. scrive ACCANTO, senza toccare i dati: `livello-NN/classifica-riclassificata.log`
     e, nella salita, `riclassificata.json` (classe prima/ora di ogni livello,
     «ultimo GREEN vero» prima/ora).
⛔ Le classi che la salita aveva imposto (entrata fallita, risorse dell'ospite,
   livello interrotto, classe illeggibile) restano quelle: non sono del blocco.
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
    """⇒ (righe corrette, quante toccate).  Pura: le righe sono dict di stato.jsonl."""
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
    """Come `ultimo_green` di 16-coda.sh: il livello piu' alto con classe GREEN, non interrotto."""
    g = [int(r.get("livello") or 0) for r in righe if r.get("classe") == "GREEN" and not r.get("interrotto")]
    return max(g) if g else None


def classe_imposta(r):
    """La classe della salita che non viene dal giudizio delle soglie."""
    perche = str(r.get("ragione_classe") or "")
    return (r.get("interrotto") or r.get("classe") not in CLASSI
            or perche.startswith("ENTRATA FALLITA") or perche.startswith("⛔ RISORSE DELL'OSPITE"))


def copia_corretta(dirliv, dest):
    """La copia del livello: collegamenti, salvo gli stato.jsonl riscritti.  ⇒ righe toccate."""
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
    """⇒ (classe nuova o None, righe toccate, uscita del classificatore)."""
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
            voce.update(classe_ora=r.get("classe"), toccate=0, nota="classe imposta dalla salita: invariata")
        else:
            classe, toccate, uscita = giudica_di_nuovo(dirliv, r, fps_video, prog)
            with open(os.path.join(dirliv, "classifica-riclassificata.log"), "w", encoding="utf-8") as f:
                f.write("# 16-riclassifica.py: il blocco col giro della pagina (fasi/20 §3-bis.2); "
                        "righe toccate: %d\n%s" % (toccate, uscita))
            n["classe"] = classe or "?"
            voce.update(classe_ora=n["classe"], toccate=toccate)
            if toccate == 0 and n["classe"] != r.get("classe"):
                # ⚠ senza righe toccate il giudizio DEVE tornare uguale: se no il giudizio
                #   rifatto non e' quello della salita (argomenti, file mancanti), e non vale
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

    print("── le righe")
    g = lambda v, c: {"visti": v, "campioni": c}  # noqa: E731
    righe = [{"profilo": "C", "lavoro": True, "blocco_max_ms": 40, "giro": g(10, [20.0] * 10)},
             # ⛔ GUASTO visto il 7 ott: 1111 ms dalla stima, la pagina nello stesso intervallo 47,5
             {"profilo": "C", "lavoro": True, "blocco_max_ms": 1111, "giro": g(14, [20.0] * 10 + [30, 47.5, 25, 22])},
             # un blocco VERO: anche il giro e' lungo ⇒ resta quasi tutto
             {"profilo": "A", "lavoro": True, "blocco_max_ms": 2500, "giro": g(15, [20.0] * 14 + [2400.0])},
             # nessun campione nuovo (il tasto non e' mai tornato) ⇒ non si tocca
             {"profilo": "A", "lavoro": True, "blocco_max_ms": 3000, "giro": g(15, [20.0] * 14 + [2400.0])},
             # il video non si tocca
             {"profilo": "D", "lavoro": True, "blocco_max_ms": 1200, "giro": g(20, [20.0] * 20)}]
    nuove, n = correggi_righe(righe)
    b = [r["blocco_max_ms"] for r in nuove]
    prova("GUASTO visto: il blocco di 1,1 s di Firefox diventa il giro della pagina (48 ms)",
          b[1] == 48 and nuove[1]["blocco_ricalcolato"]["prima_ms"] == 1111, str(b))
    prova("un blocco vero resta (2,4 s)", b[2] == 2400, str(b))
    prova("senza campioni nuovi la riga non si tocca", b[3] == 3000 and "blocco_ricalcolato" not in nuove[3])
    prova("il video (D) non si tocca", b[4] == 1200)
    prova("contate le righe toccate", n == 2, str(n))
    prova("le righe di partenza non cambiano", righe[1]["blocco_max_ms"] == 1111)
    prova("la prima riga (senza lettura prima) non si tocca", b[0] == 40)

    print("── la salita")
    sr = [{"livello": 1, "classe": "GREEN"}, {"livello": 4, "classe": "DEGRADED"},
          {"livello": 8, "classe": "GREEN", "interrotto": True}]
    prova("ultimo GREEN vero come 16-coda.sh", ultimo_green(sr) == 1)
    prova("classe imposta: entrata fallita, ospite, interrotto, «?»",
          classe_imposta({"classe": "FAIL", "ragione_classe": "ENTRATA FALLITA (1 entrati su 4)"})
          and classe_imposta({"classe": "FAIL", "ragione_classe": "⛔ RISORSE DELL'OSPITE (§7.7): x"})
          and classe_imposta({"classe": "GREEN", "interrotto": True}) and classe_imposta({"classe": "?"})
          and not classe_imposta({"classe": "DEGRADED", "ragione_classe": "blocco"}))

    print("── da capo a fondo, con un classificatore finto (le soglie vere le prova 16-classifica)")
    tmp = tempfile.mkdtemp(prefix="16-riclassifica-cert-")
    try:
        finto = os.path.join(tmp, "finto.py")
        # ⭐ il finto giudica solo il blocco, come la soglia di §9: > 1000 ms ⇒ DEGRADED
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
        prova("GUASTO visto: «buono 12, verde vero 1» ⇒ ultimo GREEN vero 8",
              e["ultimo_green_prima"] == 1 and e["ultimo_green_ora"] == 8, json.dumps(e)[:300])
        prova("il livello col blocco vero (5 s senza campioni nuovi) resta DEGRADED",
              e["livelli"][3]["classe_ora"] == "DEGRADED")
        prova("i dati originali non cambiano",
              open(os.path.join(sal, "livello-04", "utente-01", "stato.jsonl")).read() == prima
              and open(os.path.join(sal, "livello-04", "classifica.log")).read() == "originale\n")
        prova("accanto: classifica-riclassificata.log e riclassificata.json",
              os.path.exists(os.path.join(sal, "livello-04", "classifica-riclassificata.log"))
              and os.path.exists(os.path.join(sal, "riclassificata.json")))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("⭐ CERTIFICATO" if not falliti else "⛔ NON CERTIFICATO: %d" % len(falliti))
    return 0 if not falliti else 1


def main():
    a = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--salita", help="la cartella della salita (con salita.jsonl)")
    a.add_argument("--fps-video", type=float, default=None)
    a.add_argument("--certifica", action="store_true")
    o = a.parse_args()
    if o.certifica:
        return certifica()
    if not o.salita:
        a.error("--salita o --certifica")
    e = riclassifica(o.salita, o.fps_video)
    for v in e["livelli"]:
        print("  %-26s %-9s → %-9s righe toccate %s" % (v["nome"], v["classe_prima"], v["classe_ora"],
                                                        v.get("toccate")))
    print("%s: ultimo GREEN vero %s → %s" % (e["salita"], e["ultimo_green_prima"], e["ultimo_green_ora"]))
    if any(v.get("incoerente") for v in e["livelli"]):
        print("⛔ livelli senza righe toccate con la classe cambiata: il giudizio rifatto non e' quello "
              "della salita, la riclassificazione NON vale")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
