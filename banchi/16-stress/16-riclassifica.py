#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
16-riclassifica — THE «FREEZE» REDONE WITH THE PAGE'S ROUND, WITHOUT REDOING THE CLIMB (fasi/20 §3-bis.2)

    python3 16-riclassifica.py --climb /media/REMOTIX/misure/fase16/intel-f20-fhd-xfce [--fps-video 30]
    python3 16-riclassifica.py --certify

Until the commit of the cure, the actor set the time of the keys typed by Firefox
with `key_times`, from the return of the Marionette chain: a held-back
chain moved the keys AFTER their own echo, and the «longest freeze of the
image» entry took the next paint (the blinking cursor,
~1.1 s).  ⭐ The page, meanwhile, measured by itself the delay of every command
(key, click, notch → frame that contains it: `REMOTIX.lap`), and the actor
wrote it in every row of `stato.jsonl`.

What it does, for every level of `salita.jsonl`:
  1. in the rows of the profiles that type (not D) with work, the freeze becomes
     min(previous freeze, the slowest round of the NEW samples of those 5 s).
     ⇒ a real freeze stays (the round of a stuck key is long too; and a
     key that never comes back gives no samples, so the row is not touched);
  2. redoes the judgement with 16-classifica.py --dry on a COPY of the level
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

HERE = os.path.dirname(os.path.abspath(__file__))
CLASSES = ("GREEN", "DEGRADED", "FAIL")

# ── the registers of the campaigns before the English rename (DECISIONI §10.38) keep the Italian
#    words: misure/ is never rewritten.  The first tuple is protected (english-migration/protetti.tsv),
#    the second is renamed with the code: after the rename OLD_SPELLING maps every old word to the
#    code's own, before it is empty.  Same order in both, one word per position.
_OLD_WORDS = (
    "nome", "livello", "classe", "ragione_classe", "interrotto", "campagna", "controllo_min",
    "giro", "visti", "campioni", "profilo", "lavoro", "utente-", "classifica",
)  # end of the old words
_WORDS_NOW = (
    "label_name", "level", "cls_name", "reason_class", "interrupted", "campaign", "check_min",
    "lap", "seen_items", "samples", "profile_v", "work", "username-", "ranking",
)
OLD_SPELLING = {a: b for a, b in zip(_OLD_WORDS, _WORDS_NOW) if a != b}


def current_spelling(x):
    """A record of an old register in the code's spelling: keys, and string values equal to a word."""
    if isinstance(x, dict):
        return {OLD_SPELLING.get(k, k): current_spelling(v) for k, v in x.items()}
    if isinstance(x, list):
        return [current_spelling(v) for v in x]
    return OLD_SPELLING.get(x, x) if isinstance(x, str) else x


def spellings(word):
    """The word and its old spellings, for names on disk (folder prefixes)."""
    return (word,) + tuple(a for a, b in OLD_SPELLING.items() if b == word)


def _module(label_name, file):
    s = _iu.spec_from_file_location(label_name, os.path.join(HERE, file))
    m = _iu.module_from_spec(s)
    s.loader.exec_module(m)
    return m


new_samples = _module("attore16", "16-attore.py").new_samples


def fix_lines(line_list):
    """⇒ (corrected rows, how many touched).  Pure: the rows are dicts of stato.jsonl."""
    out, touched, prev = [], 0, None
    for r in line_list:
        r = dict(r)
        lap = r.get("lap")
        newcomers = new_samples(prev, lap) if isinstance(lap, dict) else []
        if isinstance(lap, dict):
            prev = lap
        b = r.get("blocco_max_ms")
        if (r.get("profile_v") != "D" and r.get("work", True) is not False and b is not None
                and newcomers and max(newcomers) < b):
            r["blocco_ricalcolato"] = {"prima_ms": b, "giro_max_ms": round(max(newcomers), 1),
                                       "samples": len(newcomers)}
            r["blocco_max_ms"] = int(round(max(newcomers)))
            touched += 1
        out.append(r)
    return out, touched


def last_green(line_list):
    """Like `last_green` of 16-coda.sh: the highest level with class GREEN, not interrupted."""
    g = [int(r.get("level") or 0) for r in line_list if r.get("cls_name") == "GREEN" and not r.get("interrupted")]
    return max(g) if g else None


def class_imposed(r):
    """The class of the climb that does not come from the judgement of the thresholds.
    ⚠ Both forms: the salita.jsonl of the running campaign is written by the old
    (Italian) 16-salita.py, the new one writes in English."""
    reason_text = str(r.get("reason_class") or "")
    return (r.get("interrupted") or r.get("cls_name") not in CLASSES
            or reason_text.startswith(("ENTRATA FALLITA", "ENTRY FAILED"))
            or reason_text.startswith(("⛔ RISORSE DELL'OSPITE", "⛔ HOST RESOURCES")))


def copy_corrected(level_path, dest):
    """The copy of the level: links, except the rewritten stato.jsonl.  ⇒ rows touched."""
    touched = 0
    for entry in os.listdir(level_path):
        src = os.path.join(level_path, entry)
        if entry.startswith(spellings("username-")) and os.path.isdir(src):
            # the copy is in the code's spelling: an old utente-NN folder takes the current prefix
            entry_now = "username-" + entry.split("-", 1)[1]
            os.makedirs(os.path.join(dest, entry_now))
            for f in os.listdir(src):
                if f == "stato.jsonl":
                    line_list = []
                    for row in open(os.path.join(src, f), encoding="utf-8", errors="replace"):
                        try:
                            line_list.append(current_spelling(json.loads(row)))
                        except ValueError:
                            continue
                    new_ones, n = fix_lines(line_list)
                    touched += n
                    with open(os.path.join(dest, entry_now, f), "w", encoding="utf-8") as o:
                        for r in new_ones:
                            o.write(json.dumps(r, ensure_ascii=False) + "\n")
                else:
                    os.symlink(os.path.join(src, f), os.path.join(dest, entry_now, f))
        elif not entry.startswith(spellings("ranking")):
            os.symlink(src, os.path.join(dest, entry))
    return touched


def judge_again(level_path, row, fps_video, prog):
    """⇒ (new class or None, rows touched, output of the classifier)."""
    tmp = tempfile.mkdtemp(prefix="16-riclassifica-")
    try:
        dest = os.path.join(tmp, os.path.basename(level_path))
        os.makedirs(dest)
        touched = copy_corrected(level_path, dest)
        cmd = [sys.executable, prog, "--level-dir", dest, "--dry", "--json",
               "--campaign", str(row.get("campaign") or ""), "--level", str(row.get("level") or 0),
               "--window-s", str(int(float(row.get("check_min") or 2) * 60))]
        if fps_video:
            cmd += ["--fps-video", str(fps_video)]
        r = subprocess.run(cmd, capture_output=True, text=True, errors="replace", timeout=900, cwd=HERE)
        out_dir = r.stdout + r.stderr
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    cls_name = None
    for l in out_dir.splitlines():
        i = l.find("{")
        if i < 0:
            continue
        try:
            d = json.loads(l[i:])
        except ValueError:
            continue
        if isinstance(d, dict) and d.get("kind") == "level" and d.get("cls_name") in CLASSES:
            cls_name = d["cls_name"]
    return cls_name, touched, out_dir


def reclassify(climb, fps_video=None, prog=None):
    prog = prog or os.path.join(HERE, "16-classifica.py")
    line_list = []
    for l in open(os.path.join(climb, "salita.jsonl"), encoding="utf-8", errors="replace"):
        try:
            line_list.append(current_spelling(json.loads(l)))
        except ValueError:
            continue
    new_ones, levels = [], []
    for r in line_list:
        level_path = os.path.join(climb, str(r.get("label_name") or ""))
        n = dict(r)
        entry = {"label_name": r.get("label_name"), "level": r.get("level"), "classe_prima": r.get("cls_name")}
        if class_imposed(r) or not r.get("label_name") or not os.path.isdir(level_path):
            entry.update(class_now=r.get("cls_name"), touched=0, remark="class imposed by the climb: unchanged")
        else:
            cls_name, touched, out_dir = judge_again(level_path, r, fps_video, prog)
            with open(os.path.join(level_path, "classifica-riclassificata.log"), "w", encoding="utf-8") as f:
                f.write("# 16-riclassifica.py: the freeze with the page's round (fasi/20 §3-bis.2); "
                        "rows touched: %d\n%s" % (touched, out_dir))
            n["cls_name"] = cls_name or "?"
            entry.update(class_now=n["cls_name"], touched=touched)
            if touched == 0 and n["cls_name"] != r.get("cls_name"):
                # ⚠ without rows touched the judgement MUST come back the same: otherwise the
                #   redone judgement is not that of the climb (arguments, missing files), and it does not count
                entry["incoerente"] = True
        new_ones.append(n)
        levels.append(entry)
    outcome = {"climb": os.path.basename(os.path.normpath(climb)),
             "ultimo_green_prima": last_green(line_list), "ultimo_green_ora": last_green(new_ones),
             "levels": levels}
    with open(os.path.join(climb, "riclassificata.json"), "w", encoding="utf-8") as f:
        json.dump(outcome, f, ensure_ascii=False, indent=1)
    return outcome


# ═══════════════════════════════════════════════════════════════════════════
def certify():
    failed = []

    def prova(what, real, det=""):
        print("   %s  %s%s" % ("⭐ ok" if real else "⛔ NO", what, (" — " + det) if det else ""))
        if not real:
            failed.append(what)

    print("── the rows")
    g = lambda v, c: {"seen_items": v, "samples": c}  # noqa: E731
    line_list = [{"profile_v": "C", "work": True, "blocco_max_ms": 40, "lap": g(10, [20.0] * 10)},
             # ⛔ FAULT seen on 7 Oct: 1111 ms from the estimate, the page in the same interval 47.5
             {"profile_v": "C", "work": True, "blocco_max_ms": 1111, "lap": g(14, [20.0] * 10 + [30, 47.5, 25, 22])},
             # a REAL freeze: the round is long too ⇒ almost all of it stays
             {"profile_v": "A", "work": True, "blocco_max_ms": 2500, "lap": g(15, [20.0] * 14 + [2400.0])},
             # no new sample (the key never came back) ⇒ not touched
             {"profile_v": "A", "work": True, "blocco_max_ms": 3000, "lap": g(15, [20.0] * 14 + [2400.0])},
             # the video is not touched
             {"profile_v": "D", "work": True, "blocco_max_ms": 1200, "lap": g(20, [20.0] * 20)}]
    new_ones, n = fix_lines(line_list)
    b = [r["blocco_max_ms"] for r in new_ones]
    prova("FAULT seen: Firefox's 1.1 s freeze becomes the page's round (48 ms)",
          b[1] == 48 and new_ones[1]["blocco_ricalcolato"]["prima_ms"] == 1111, str(b))
    prova("a real freeze stays (2.4 s)", b[2] == 2400, str(b))
    prova("without new samples the row is not touched", b[3] == 3000 and "blocco_ricalcolato" not in new_ones[3])
    prova("the video (D) is not touched", b[4] == 1200)
    prova("rows touched counted", n == 2, str(n))
    prova("the starting rows do not change", line_list[1]["blocco_max_ms"] == 1111)
    prova("the first row (without a previous reading) is not touched", b[0] == 40)

    print("── the climb")
    sr = [{"level": 1, "cls_name": "GREEN"}, {"level": 4, "cls_name": "DEGRADED"},
          {"level": 8, "cls_name": "GREEN", "interrupted": True}]
    prova("last true GREEN as in 16-coda.sh", last_green(sr) == 1)
    # ⚠ the two rows below are an OLD salita.jsonl, word for word (protected from the rename)
    prova("imposed class: entry failed, host, interrupted, «?»",
          class_imposed(current_spelling({"classe": "FAIL", "ragione_classe": "ENTRATA FALLITA (1 entrati su 4)"}))
          and class_imposed(current_spelling({"classe": "FAIL", "ragione_classe": "⛔ RISORSE DELL'OSPITE (§7.7): x"}))
          and class_imposed({"cls_name": "GREEN", "interrupted": True}) and class_imposed({"cls_name": "?"})
          and not class_imposed({"cls_name": "DEGRADED", "reason_class": "block"}))

    print("── end to end, with a fake classifier (the real thresholds are tested by 16-classifica)")
    tmp = tempfile.mkdtemp(prefix="16-riclassifica-cert-")
    try:
        fake = os.path.join(tmp, "finto.py")
        # ⭐ the fake judges only the freeze, like the threshold of §9: > 1000 ms ⇒ DEGRADED
        open(fake, "w").write(
            "import sys, json, glob, os\n"
            "d = sys.argv[sys.argv.index('--level-dir') + 1]\n"
            "b = [json.loads(l)['blocco_max_ms'] for f in glob.glob(os.path.join(d, 'username-*', 'stato.jsonl'))"
            " for l in open(f)]\n"
            "print('LIVELLO')\n"
            "print(json.dumps({'kind': 'level', 'cls_name': 'DEGRADED' if max(b) > 1000 else 'GREEN'}))\n")
        sal = os.path.join(tmp, "intel-f20-fhd-xfce")
        for label_name, blocks in (("livello-01", [40]), ("livello-04", [40, 1111]), ("livello-08", [40, 1063]),
                              ("livello-12", [5000])):
            os.makedirs(os.path.join(sal, label_name, "utente-01"))
            open(os.path.join(sal, label_name, "server.log"), "w").write("x\n")
            open(os.path.join(sal, label_name, "classifica.log"), "w").write("original\n")
            with open(os.path.join(sal, label_name, "utente-01", "stato.jsonl"), "w") as f:
                for k, bl in enumerate(blocks):
                    f.write(json.dumps({"profile_v": "C", "work": True, "blocco_max_ms": bl,
                                        "lap": g(10 + k, [25.0] * (10 + k))}) + "\n")
        with open(os.path.join(sal, "salita.jsonl"), "w") as f:
            for n_, label_name, cl in ((1, "livello-01", "GREEN"), (4, "livello-04", "DEGRADED"),
                                 (8, "livello-08", "DEGRADED"), (12, "livello-12", "DEGRADED")):
                f.write(json.dumps({"campaign": "cert", "level": n_, "label_name": label_name, "cls_name": cl,
                                    "check_min": 2}) + "\n")
        before = open(os.path.join(sal, "livello-04", "utente-01", "stato.jsonl")).read()
        e = reclassify(sal, prog=fake)
        prova("FAULT seen: «good 12, true green 1» ⇒ last true GREEN 8",
              e["ultimo_green_prima"] == 1 and e["ultimo_green_ora"] == 8, json.dumps(e)[:300])
        prova("the level with the real freeze (5 s without new samples) stays DEGRADED",
              e["levels"][3]["class_now"] == "DEGRADED")
        prova("the original data do not change",
              open(os.path.join(sal, "livello-04", "utente-01", "stato.jsonl")).read() == before
              and open(os.path.join(sal, "livello-04", "classifica.log")).read() == "original\n")
        prova("alongside: classifica-riclassificata.log and riclassificata.json",
              os.path.exists(os.path.join(sal, "livello-04", "classifica-riclassificata.log"))
              and os.path.exists(os.path.join(sal, "riclassificata.json")))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("⭐ CERTIFIED" if not failed else "⛔ NOT CERTIFIED: %d" % len(failed))
    return 0 if not failed else 1


def main():
    a = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--climb", help="the folder of the climb (with salita.jsonl)")
    a.add_argument("--fps-video", type=float, default=None)
    a.add_argument("--certify", action="store_true")
    o = a.parse_args()
    if o.certify:
        return certify()
    if not o.climb:
        a.error("--climb or --certify")
    e = reclassify(o.climb, o.fps_video)
    for v in e["levels"]:
        print("  %-26s %-9s → %-9s rows touched %s" % (v["label_name"], v["classe_prima"], v["class_now"],
                                                        v.get("touched")))
    print("%s: last true GREEN %s → %s" % (e["climb"], e["ultimo_green_prima"], e["ultimo_green_ora"]))
    if any(v.get("incoerente") for v in e["levels"]):
        print("⛔ levels without rows touched with the class changed: the redone judgement is not that "
              "of the climb, the reclassification does NOT count")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
