#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
11-c16 — ⭐⭐ «THE DOCUMENTS DO NOT LIE» — the mesh that looks at THE PAPERS
===========================================================================

    python3 11-c16-i-documenti-non-mentono.py
    python3 11-c16-i-documenti-non-mentono.py --certify
    python3 11-c16-i-documenti-non-mentono.py --root /other/repository

⛔ This mesh tests neither the product nor the net: it tests that **the
   documents still tell the truth about the repository they live in**.

---------------------------------------------------------------------------
⛔⛔ THE FAULT IT CATCHES — *the coordinate that rots by itself*
---------------------------------------------------------------------------

On 28 August 2026 this came out, and it is the reason the mesh
exists.  `MASTERPLAN.md` cited `src/figlio.c:3290` with the mark `[M]` and the
date.  ⭐ **On 25 August at 15:18 `MOTION_FPS` really was at line
3290** — checked commit by commit.  Then on the 27th the code moved, and the
coordinate became false **without anybody having touched it**.

⇒ ⛔ It is the worst form of wrong document: **nobody did anything
  wrong**.  There is no commit to blame, no oversight, no
  line written lightly.  The document stood still and the truth
  moved.  ⭐ Every other statement of this project has something that
  watches it — a measurement, a bench, a certification.  The papers do not.

---------------------------------------------------------------------------
⭐ THE FOUR THINGS IT LOOKS AT
---------------------------------------------------------------------------

  1  ⛔ **no line coordinate** towards our code (`src/x.c:123`).
     Not «it is wrong»: **it is there**.  A coordinate right today is a
     coordinate wrong next week, and the two cannot be told apart.
     ⇒ The NAME is cited (`src/figlio.c` · `MOTION_FPS`), which moves with the
     code.

  2  every **cited path** exists in the repository — or carries a mark that says
     why not: `⟨v1⟩` (the papers of the superseded product), `⟨mutter⟩`/`⟨gnome⟩`/
     `⟨lsquic⟩`… (other people's trees, in `.gitignore`).

  3  no **markdown link** `[text](path)` that leads
     nowhere.  ⚠ A broken link is worse than a citation: it promises to open.

  4  ⛔ **one single** «RESUME FROM HERE» heading in the whole
     documentation.  It had six, with six different dates.

---------------------------------------------------------------------------
⚠ WHAT THIS MESH CANNOT DO, and it must be said
---------------------------------------------------------------------------

⛔ **It does not know whether a document tells the truth.**  It only knows whether its *references*
   hold.  A wrong measurement, an invented date, a conclusion the
   code contradicts: ⭐ **they all pass through here without it noticing**.
   ⇒ Whoever reads a green from C16 should know that it means «the addresses hold»,
   not «the papers are right».  It is the reverse of `LEZIONI.md` §1.3 applied
   to documents.

---------------------------------------------------------------------------
THE OUTCOMES (§4.5 of the phase document)
---------------------------------------------------------------------------

  0  ⭐ the four checks hold
  1  ⛔ at least one does not hold ⇒ red
  3  ⛔ I could not look (the root is not a git repository)
  2  the terrain does not hold, or the usage is wrong
===========================================================================
"""
import argparse
import os
import re
import subprocess
import sys
import tempfile

EXTERNAL_MARKS = ("⟨v1⟩", "⟨mutter⟩", "⟨gnome⟩", "⟨lsquic⟩", "⟨quiche⟩",
                  "⟨ngtcp2⟩", "⟨kwin⟩", "⟨xrdp⟩", "⟨esterno⟩")
# the historical papers: photographs of what was, they are not chased
EXCLUDED = ("fondamenta/", "memoria/")

# ⭐ THE REPORTS REMOVED ON PURPOSE — 94 files, taken out on 16 August 2026 by the user's
#    decision, and ⛔ **not lost**: they live in `0c85e5c` and `FASI.md` §0 has the
#    recipe to get one out.  ⇒ Citing them is PROVENANCE and it is kept: it says
#    where a measurement comes from.  ⛔ **Linking them** is not: a link promises to open.
#    That is why they are here and not in check 3, which catches the links anyway.
DELIBERATELY_REMOVED = ("fasi/rapporti/", "web/rapporti/")

EXCEPTIONS = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "11-c16-eccezioni.txt")


def declared_exceptions(fpath=EXCEPTIONS):
    """⛔ the exceptions live in a file, not in the code: so they are COUNTED"""
    report = []
    try:
        with open(fpath, encoding="utf-8") as f:
            for line in f:
                line = line.rstrip("\n")
                if not line.strip() or line.lstrip().startswith("#"):
                    continue
                key = line.split("\t")[0].strip()
                if key:
                    report.append(key)
    except OSError:
        return []
    return report

# ⛔ The first draft asked for the `src/` prefix, and ⭐ **let 222 coordinates
#    out of 272 slip** — those written `figlio.c:1145`, without a folder.
#    ⇒ Now it takes any `name.ext:number`, and what decides whether it counts is whether the
#    file **exists and moves** (see CONGELATO below).
RX_LINE  = re.compile(r'`([A-Za-z0-9_./-]+\.(?:c|h|py|sh|html)):([0-9]+)`')

# ⭐ THE FROZEN CODE — `fondamenta/` is the v1 product, closed and still.
#    A coordinate in there **does not age**, because there is nothing that
#    moves it.  ⇒ Forbidding those too would be a rule without a defect behind it.
FROZEN_V = ("fondamenta/",)
RX_PATH  = re.compile(r'`([A-Za-z0-9_][A-Za-z0-9_./-]*\.(?:c|h|py|sh|md|html|json|jsonl|pam|rs))`')
RX_LINK  = re.compile(r'\[[^\]]+\]\(([A-Za-z0-9_][A-Za-z0-9_./-]*\.(?:md|png|jpg|sh|py|c|h))\)')
# ⚠ 11 Oct 2026: the documents went to English (§10.38) and the heading with them,
#   «DA HERE SI RIPRENDE» → «RESUME FROM HERE»: looking only for the Italian one, rule 4
#   could no longer turn red.  Both spellings count, so old texts are judged too.
RX_RESUME  = re.compile(r'RESUME FROM HERE|DA QUI SI RIPRENDE')


def documents(root):
    try:
        report = subprocess.check_output(["git", "-C", root, "ls-files", "*.md"],
                                        text=True, stderr=subprocess.DEVNULL)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return [f for f in report.split() if not f.startswith(EXCLUDED)]


def file_list(root):
    report = subprocess.check_output(["git", "-C", root, "ls-files"], text=True)
    all_items = set(report.split())
    names = set(p.rsplit("/", 1)[-1] for p in all_items)
    return all_items, names


def look(root, exceptions=None):
    """returns (coordinate, percorsi_morti, link_rotti, riprese) — each a list"""
    excused = exceptions if exceptions is not None else declared_exceptions()
    docs = documents(root)
    if docs is None:
        return None
    all_items, names = file_list(root)
    coord, dead, broken, resumed = [], [], [], []
    for d in docs:
        p = os.path.join(root, d)
        try:
            with open(p, encoding="utf-8") as f:
                lines = f.read().split("\n")
        except OSError:
            continue
        for n, line in enumerate(lines, 1):
            for m in RX_LINE.finditer(line):
                f_cited = m.group(1)
                if f_cited.startswith(FROZEN_V):
                    continue
                alive = any(os.path.exists(os.path.join(root, x))
                           for x in (f_cited, "src/" + f_cited, "banchi/" + f_cited))
                if alive:
                    coord.append(f"{d}:{n}  {m.group(0)}")
            if RX_RESUME.search(line) and line.lstrip("> ").startswith("#"):
                resumed.append(f"{d}:{n}")
            # the paths marked ⟨…⟩ are declared as other people's: they are not chased
            cleaned = line
            for mark in EXTERNAL_MARKS:
                cleaned = re.sub(re.escape(mark) + r'\s*[A-Za-z0-9_./-]+', "", cleaned)
            for m in RX_PATH.finditer(cleaned):
                c = m.group(1)
                if c in all_items or c.rsplit("/", 1)[-1] in names:
                    continue
                if os.path.exists(os.path.join(root, c)):
                    continue
                if c.startswith(DELIBERATELY_REMOVED):
                    continue
                if any(s in c for s in excused):
                    continue
                dead.append(f"{d}:{n}  {c}")
            for m in RX_LINK.finditer(line):
                c = m.group(1)
                if c.startswith(("http", "#")):
                    continue
                base = os.path.dirname(d)
                if c in all_items or os.path.exists(os.path.join(root, c)) \
                   or os.path.exists(os.path.join(root, base, c)):
                    continue
                broken.append(f"{d}:{n}  {c}")
    return coord, dead, broken, resumed


def show(name, ugly, cap, explain):
    if not ugly:
        print(f"  \033[1;32mOK\033[0m  {name}")
        return True
    print(f"  \033[1;31mNO\033[0m  {name} — {len(ugly)}")
    print(f"      ⛔ {explain}")
    for b in ugly[:cap]:
        print(f"        {b}")
    if len(ugly) > cap:
        print(f"        … and {len(ugly) - cap} more")
    return False


def cur_round(root, silent=False, exceptions=None):
    seen = look(root, exceptions)
    if seen is None:
        if not silent:
            print("  ⛔ I could not look: the root is not a git repository")
        return 3
    coord, dead, broken, resumed = seen
    if silent:
        return 1 if (coord or dead or broken or len(resumed) > 1) else 0
    print("== C16 — the documents do not lie ==")
    greens = [
        show("no line coordinate towards our code", coord, 8,
               "a coordinate right today is wrong next week: the NAME is cited"),
        show("every cited path exists (or carries the ⟨…⟩ mark)", dead, 8,
               "the document points to a file that is not in the repository"),
        show("no broken markdown link", broken, 8,
               "a broken link is worse than a citation: it promises to open"),
        show("one single «RESUME FROM HERE» heading",
               resumed if len(resumed) > 1 else [], 8,
               "more than one, and whoever reopens does not know which one holds"),
    ]
    print()
    if all(greens):
        print("  ⭐ the four checks hold.")
        print("  ⚠ and this mesh says the ADDRESSES hold, ⛔ not that the")
        print("    papers are right: a wrong measurement passes through here intact.")
        return 0
    return 1


def certify():
    """⛔ a mesh that has never been seen failing is not a mesh"""
    print("== certification of C16 — can it give red? ==\n")
    # ⚠ 28 Aug 2026: the terrain of the first fault must REALLY contain `src/main.c`.
    #    ⛔ When check 1 went from «any coordinate» to «only towards
    #    files that exist and move», the fake fault stopped being seen
    #    — and ⭐ **the certification noticed at once**: it is exactly its
    #    job, and it is the reason a mesh is not written without one.
    faults = {
        "a line coordinate":           ("g1.md", "see `src/main.c:111` for the rest.\n"),
        "a path that does not exist":  ("g2.md", "it is in `src/inventato_dal_nulla.c`.\n"),
        "a broken markdown link":      ("g3.md", "the report is [here](fasi/rapporti/mai-esistito.md).\n"),
        "two «RESUME FROM HERE»":      ("g4.md", "# RESUME FROM HERE — yesterday\n\n# DA QUI SI RIPRENDE — today\n"),
    }
    outcomes = []
    for name, (file, text) in faults.items():
        with tempfile.TemporaryDirectory() as t:
            subprocess.run(["git", "-C", t, "init", "-q"], check=True)
            with open(os.path.join(t, "sano.md"), "w", encoding="utf-8") as f:
                f.write("An honest document: it cites `sano.md` and that is all.\n")
            os.makedirs(os.path.join(t, "src"), exist_ok=True)
            with open(os.path.join(t, "src", "main.c"), "w", encoding="utf-8") as f:
                f.write("int main(void) { return 0; }\n" * 200)
            subprocess.run(["git", "-C", t, "add", "sano.md", "src/main.c"], check=True)
            if cur_round(t, silent=True, exceptions=[]) != 0:
                print(f"  ⛔ the HEALTHY terrain is not green: the certification is not valid")
                return 2
            with open(os.path.join(t, file), "w", encoding="utf-8") as f:
                f.write(text)
            subprocess.run(["git", "-C", t, "add", file], check=True)
            red = cur_round(t, silent=True, exceptions=[]) == 1
            outcomes.append(red)
            print(f"  {'✓ SEEN    ' if red else '⛔ NOT SEEN'}  {name}")
    print()
    if all(outcomes):
        print("  ⭐ C16 can give red on all four faults, and the healthy")
        print("    terrain stays green. ⇒ A green of it means something.")
        return 0
    print("  ⛔ at least one injected fault was NOT seen: the mesh is silent.")
    return 1


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", default=None, help="the repository to look at")
    p.add_argument("--certify", action="store_true")
    a = p.parse_args()
    if a.certify:
        return certify()
    root = a.root or subprocess.run(
        ["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True
    ).stdout.strip()
    if not root:
        print("  ⛔ I am not inside a git repository, and --root was not given")
        return 2
    return cur_round(root)


if __name__ == "__main__":
    sys.exit(main())
