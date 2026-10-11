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
(key, click, notch → frame that contains it: `REMOTIX.round_trip`), and the actor
wrote it in every row of `state.jsonl`.

What it does, for every level of `climb.jsonl`:
  1. in the rows of the profiles that type (not D) with work, the freeze becomes
     min(previous freeze, the slowest round of the NEW samples of those 5 s).
     ⇒ a real freeze stays (the round of a stuck key is long too; and a
     key that never comes back gives no samples, so the row is not touched);
  2. redoes the judgement with 16-classifica.py --dry-run on a COPY of the level
     (links to the real files, only the state.jsonl rewritten);
  3. writes ALONGSIDE, without touching the data: `level-NN/ranking-reclassified.log`
     and, in the climb, `reclassified.json` (class before/now of every level,
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
    "giro", "visti", "campioni", "profilo", "lavoro", "utente-", "classifica", "blocco_max_ms",
)  # end of the old words
_WORDS_NOW = (
    "name", "level", "class", "class_rationale", "interrupted", "campaign", "check_min",
    "round_trip", "seen", "samples", "profile", "work", "user-", "ranking", "block_max_ms",
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


def _module(name, file):
    s = _iu.spec_from_file_location(name, os.path.join(HERE, file))
    m = _iu.module_from_spec(s)
    s.loader.exec_module(m)
    return m


new_samples = _module("attore16", "16-attore.py").new_samples


def fix_lines(lines):
    """⇒ (corrected rows, how many touched).  Pure: the rows are dicts of state.jsonl."""
    out, touched, prev = [], 0, None
    for r in lines:
        r = dict(r)
        round_trip = r.get("round_trip")
        newcomers = new_samples(prev, round_trip) if isinstance(round_trip, dict) else []
        if isinstance(round_trip, dict):
            prev = round_trip
        b = r.get("block_max_ms")
        if (r.get("profile") != "D" and r.get("work", True) is not False and b is not None
                and newcomers and max(newcomers) < b):
            r["blocco_ricalcolato"] = {"prima_ms": b, "giro_max_ms": round(max(newcomers), 1),
                                       "samples": len(newcomers)}
            r["block_max_ms"] = int(round(max(newcomers)))
            touched += 1
        out.append(r)
    return out, touched


def last_green(lines):
    """Like `last_green` of 16-coda.sh: the highest level with class GREEN, not interrupted."""
    g = [int(r.get("level") or 0) for r in lines if r.get("class") == "GREEN" and not r.get("interrupted")]
    return max(g) if g else None


def class_imposed(r):
    """The class of the climb that does not come from the judgement of the thresholds.
    ⚠ Both forms: the climb.jsonl of the running campaign is written by the old
    (Italian) 16-salita.py, the new one writes in English."""
    why = str(r.get("class_rationale") or "")
    return (r.get("interrupted") or r.get("class") not in CLASSES
            or why.startswith(("ENTRATA FALLITA", "ENTRY FAILED"))
            or why.startswith(("⛔ RISORSE DELL'OSPITE", "⛔ HOST RESOURCES")))


def copy_corrected(level_path, dest):
    """The copy of the level: links, except the rewritten state.jsonl.  ⇒ rows touched."""
    touched = 0
    for entry in os.listdir(level_path):
        src = os.path.join(level_path, entry)
        if entry.startswith(spellings("user-")) and os.path.isdir(src):
            # the copy is in the code's spelling: an old user-NN folder takes the current prefix
            entry_now = "user-" + entry.split("-", 1)[1]
            os.makedirs(os.path.join(dest, entry_now))
            for f in os.listdir(src):
                if f in ("state.jsonl", "stato.jsonl"):     # and its old name
                    lines = []
                    for line in open(os.path.join(src, f), encoding="utf-8", errors="replace"):
                        try:
                            lines.append(current_spelling(json.loads(line)))
                        except ValueError:
                            continue
                    new_ones, n = fix_lines(lines)
                    touched += n
                    with open(os.path.join(dest, entry_now, f), "w", encoding="utf-8") as o:
                        for r in new_ones:
                            o.write(json.dumps(r, ensure_ascii=False) + "\n")
                else:
                    os.symlink(os.path.join(src, f), os.path.join(dest, entry_now, f))
        elif not entry.startswith(spellings("ranking")):
            os.symlink(src, os.path.join(dest, entry))
    return touched


def judge_again(level_path, line, fps_video, prog):
    """⇒ (new class or None, rows touched, output of the classifier)."""
    tmp = tempfile.mkdtemp(prefix="16-riclassifica-")
    try:
        dest = os.path.join(tmp, os.path.basename(level_path))
        os.makedirs(dest)
        touched = copy_corrected(level_path, dest)
        cmd = [sys.executable, prog, "--level-dir", dest, "--dry-run", "--json",
               "--campaign", str(line.get("campaign") or ""), "--level", str(line.get("level") or 0),
               "--window-s", str(int(float(line.get("check_min") or 2) * 60))]
        if fps_video:
            cmd += ["--fps-video", str(fps_video)]
        r = subprocess.run(cmd, capture_output=True, text=True, errors="replace", timeout=900, cwd=HERE)
        output = r.stdout + r.stderr
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    grade = None
    for l in output.splitlines():
        i = l.find("{")
        if i < 0:
            continue
        try:
            d = json.loads(l[i:])
        except ValueError:
            continue
        if isinstance(d, dict) and d.get("type") == "level" and d.get("class") in CLASSES:
            grade = d["class"]
    return grade, touched, output


def reclassify(climb, fps_video=None, prog=None):
    prog = prog or os.path.join(HERE, "16-classifica.py")
    lines = []
    p = os.path.join(climb, "climb.jsonl")
    p = p if os.path.exists(p) else os.path.join(climb, "salita.jsonl")    # a climb before the rename
    for l in open(p, encoding="utf-8", errors="replace"):
        try:
            lines.append(current_spelling(json.loads(l)))
        except ValueError:
            continue
    new_ones, levels = [], []
    for r in lines:
        level_path = os.path.join(climb, str(r.get("name") or ""))
        n = dict(r)
        entry = {"name": r.get("name"), "level": r.get("level"), "class_before": r.get("class")}
        if class_imposed(r) or not r.get("name") or not os.path.isdir(level_path):
            entry.update(class_now=r.get("class"), touched=0, note="class imposed by the climb: unchanged")
        else:
            grade, touched, output = judge_again(level_path, r, fps_video, prog)
            with open(os.path.join(level_path, "ranking-reclassified.log"), "w", encoding="utf-8") as f:
                f.write("# 16-riclassifica.py: the freeze with the page's round (fasi/20 §3-bis.2); "
                        "rows touched: %d\n%s" % (touched, output))
            n["class"] = grade or "?"
            entry.update(class_now=n["class"], touched=touched)
            if touched == 0 and n["class"] != r.get("class"):
                # ⚠ without rows touched the judgement MUST come back the same: otherwise the
                #   redone judgement is not that of the climb (arguments, missing files), and it does not count
                entry["incoerente"] = True
        new_ones.append(n)
        levels.append(entry)
    outcome = {"climb": os.path.basename(os.path.normpath(climb)),
             "last_green_before": last_green(lines), "last_green_now": last_green(new_ones),
             "levels": levels}
    with open(os.path.join(climb, "reclassified.json"), "w", encoding="utf-8") as f:
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
    g = lambda v, c: {"seen": v, "samples": c}  # noqa: E731
    lines = [{"profile": "C", "work": True, "block_max_ms": 40, "round_trip": g(10, [20.0] * 10)},
             # ⛔ FAULT seen on 7 Oct: 1111 ms from the estimate, the page in the same interval 47.5
             {"profile": "C", "work": True, "block_max_ms": 1111, "round_trip": g(14, [20.0] * 10 + [30, 47.5, 25, 22])},
             # a REAL freeze: the round is long too ⇒ almost all of it stays
             {"profile": "A", "work": True, "block_max_ms": 2500, "round_trip": g(15, [20.0] * 14 + [2400.0])},
             # no new sample (the key never came back) ⇒ not touched
             {"profile": "A", "work": True, "block_max_ms": 3000, "round_trip": g(15, [20.0] * 14 + [2400.0])},
             # the video is not touched
             {"profile": "D", "work": True, "block_max_ms": 1200, "round_trip": g(20, [20.0] * 20)}]
    new_ones, n = fix_lines(lines)
    b = [r["block_max_ms"] for r in new_ones]
    prova("FAULT seen: Firefox's 1.1 s freeze becomes the page's round (48 ms)",
          b[1] == 48 and new_ones[1]["blocco_ricalcolato"]["prima_ms"] == 1111, str(b))
    prova("a real freeze stays (2.4 s)", b[2] == 2400, str(b))
    prova("without new samples the row is not touched", b[3] == 3000 and "blocco_ricalcolato" not in new_ones[3])
    prova("the video (D) is not touched", b[4] == 1200)
    prova("rows touched counted", n == 2, str(n))
    prova("the starting rows do not change", lines[1]["block_max_ms"] == 1111)
    prova("the first row (without a previous reading) is not touched", b[0] == 40)

    print("── the climb")
    sr = [{"level": 1, "class": "GREEN"}, {"level": 4, "class": "DEGRADED"},
          {"level": 8, "class": "GREEN", "interrupted": True}]
    prova("last true GREEN as in 16-coda.sh", last_green(sr) == 1)
    # ⚠ the two rows below are an OLD climb.jsonl, word for word (protected from the rename)
    prova("imposed class: entry failed, host, interrupted, «?»",
          class_imposed(current_spelling({"class": "FAIL", "class_rationale": "ENTRATA FALLITA (1 entrati su 4)"}))
          and class_imposed(current_spelling({"class": "FAIL", "class_rationale": "⛔ RISORSE DELL'OSPITE (§7.7): x"}))
          and class_imposed({"class": "GREEN", "interrupted": True}) and class_imposed({"class": "?"})
          and not class_imposed({"class": "DEGRADED", "class_rationale": "block"}))

    print("── end to end, with a fake classifier (the real thresholds are tested by 16-classifica)")
    tmp = tempfile.mkdtemp(prefix="16-riclassifica-cert-")
    try:
        fake = os.path.join(tmp, "fake.py")
        # ⭐ the fake judges only the freeze, like the threshold of §9: > 1000 ms ⇒ DEGRADED
        open(fake, "w").write(
            "import sys, json, glob, os\n"
            "d = sys.argv[sys.argv.index('--level-dir') + 1]\n"
            "b = [json.loads(l)['block_max_ms'] for f in glob.glob(os.path.join(d, 'user-*', 'state.jsonl'))"
            " for l in open(f)]\n"
            "print('LIVELLO')\n"
            "print(json.dumps({'type': 'level', 'class': 'DEGRADED' if max(b) > 1000 else 'GREEN'}))\n")
        sal = os.path.join(tmp, "intel-f20-fhd-xfce")
        for name, blocks in (("level-01", [40]), ("level-04", [40, 1111]), ("level-08", [40, 1063]),
                              ("level-12", [5000])):
            os.makedirs(os.path.join(sal, name, "user-01"))
            open(os.path.join(sal, name, "server.log"), "w").write("x\n")
            open(os.path.join(sal, name, "ranking.log"), "w").write("originale\n")
            with open(os.path.join(sal, name, "user-01", "state.jsonl"), "w") as f:
                for k, bl in enumerate(blocks):
                    f.write(json.dumps({"profile": "C", "work": True, "block_max_ms": bl,
                                        "round_trip": g(10 + k, [25.0] * (10 + k))}) + "\n")
        with open(os.path.join(sal, "climb.jsonl"), "w") as f:
            for n_, name, cl in ((1, "level-01", "GREEN"), (4, "level-04", "DEGRADED"),
                                 (8, "level-08", "DEGRADED"), (12, "level-12", "DEGRADED")):
                f.write(json.dumps({"campaign": "cert", "level": n_, "name": name, "class": cl,
                                    "check_min": 2}) + "\n")
        before = open(os.path.join(sal, "level-04", "user-01", "state.jsonl")).read()
        e = reclassify(sal, prog=fake)
        prova("FAULT seen: «good 12, true green 1» ⇒ last true GREEN 8",
              e["last_green_before"] == 1 and e["last_green_now"] == 8, json.dumps(e)[:300])
        prova("the level with the real freeze (5 s without new samples) stays DEGRADED",
              e["levels"][3]["class_now"] == "DEGRADED")
        prova("the original data do not change",
              open(os.path.join(sal, "level-04", "user-01", "state.jsonl")).read() == before
              and open(os.path.join(sal, "level-04", "ranking.log")).read() == "originale\n")
        prova("alongside: ranking-reclassified.log and reclassified.json",
              os.path.exists(os.path.join(sal, "level-04", "ranking-reclassified.log"))
              and os.path.exists(os.path.join(sal, "reclassified.json")))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("⭐ CERTIFIED" if not failed else "⛔ NOT CERTIFIED: %d" % len(failed))
    return 0 if not failed else 1


def main():
    a = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--climb", help="the folder of the climb (with climb.jsonl)")
    a.add_argument("--fps-video", type=float, default=None)
    a.add_argument("--certify", action="store_true")
    o = a.parse_args()
    if o.certify:
        return certify()
    if not o.climb:
        a.error("--climb or --certify")
    e = reclassify(o.climb, o.fps_video)
    for v in e["levels"]:
        print("  %-26s %-9s → %-9s rows touched %s" % (v["name"], v["class_before"], v["class_now"],
                                                        v.get("touched")))
    print("%s: last true GREEN %s → %s" % (e["climb"], e["last_green_before"], e["last_green_now"]))
    if any(v.get("incoerente") for v in e["levels"]):
        print("⛔ levels without rows touched with the class changed: the redone judgement is not that "
              "of the climb, the reclassification does NOT count")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
