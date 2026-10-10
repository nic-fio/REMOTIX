#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
11-c16 — ⭐⭐ «THE DOCUMENTS DO NOT LIE» — the mesh that looks at THE PAPERS
===========================================================================

    python3 11-c16-i-documenti-non-mentono.py
    python3 11-c16-i-documenti-non-mentono.py --certifica
    python3 11-c16-i-documenti-non-mentono.py --radice /other/repository

⛔ This mesh tests neither the product nor the net: it tests that **the
   documents still tell the truth about the repository they live in**.

---------------------------------------------------------------------------
⛔⛔ THE FAULT IT CATCHES — *the coordinate that rots by itself*
---------------------------------------------------------------------------

On 28 August 2026 this came out, and it is the reason the mesh
exists.  `MASTERPLAN.md` cited `src/figlio.c:3290` with the mark `[M]` and the
date.  ⭐ **On 25 August at 15:18 `MOVIMENTO_FPS` really was at line
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
     ⇒ The NAME is cited (`src/figlio.c` · `MOVIMENTO_FPS`), which moves with the
     code.

  2  every **cited path** exists in the repository — or carries a mark that says
     why not: `⟨v1⟩` (the papers of the superseded product), `⟨mutter⟩`/`⟨gnome⟩`/
     `⟨lsquic⟩`… (other people's trees, in `.gitignore`).

  3  no **markdown link** `[text](path)` that leads
     nowhere.  ⚠ A broken link is worse than a citation: it promises to open.

  4  ⛔ **one single** «DA QUI SI RIPRENDE» heading in the whole
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

MARCHE_ESTERNE = ("⟨v1⟩", "⟨mutter⟩", "⟨gnome⟩", "⟨lsquic⟩", "⟨quiche⟩",
                  "⟨ngtcp2⟩", "⟨kwin⟩", "⟨xrdp⟩", "⟨esterno⟩")
# the historical papers: photographs of what was, they are not chased
ESCLUSE = ("fondamenta/", "memoria/")

# ⭐ THE REPORTS REMOVED ON PURPOSE — 94 files, taken out on 16 August 2026 by the user's
#    decision, and ⛔ **not lost**: they live in `0c85e5c` and `FASI.md` §0 has the
#    recipe to get one out.  ⇒ Citing them is PROVENANCE and it is kept: it says
#    where a measurement comes from.  ⛔ **Linking them** is not: a link promises to open.
#    That is why they are here and not in check 3, which catches the links anyway.
TOLTI_APPOSTA = ("fasi/rapporti/", "web/rapporti/")

ECCEZIONI = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "11-c16-eccezioni.txt")


def eccezioni_dichiarate(percorso=ECCEZIONI):
    """⛔ the exceptions live in a file, not in the code: so they are COUNTED"""
    fuori = []
    try:
        with open(percorso, encoding="utf-8") as f:
            for riga in f:
                riga = riga.rstrip("\n")
                if not riga.strip() or riga.lstrip().startswith("#"):
                    continue
                chiave = riga.split("\t")[0].strip()
                if chiave:
                    fuori.append(chiave)
    except OSError:
        return []
    return fuori

# ⛔ The first draft asked for the `src/` prefix, and ⭐ **let 222 coordinates
#    out of 272 slip** — those written `figlio.c:1145`, without a folder.
#    ⇒ Now it takes any `name.ext:number`, and what decides whether it counts is whether the
#    file **exists and moves** (see CONGELATO below).
RX_RIGA  = re.compile(r'`([A-Za-z0-9_./-]+\.(?:c|h|py|sh|html)):([0-9]+)`')

# ⭐ THE FROZEN CODE — `fondamenta/` is the v1 product, closed and still.
#    A coordinate in there **does not age**, because there is nothing that
#    moves it.  ⇒ Forbidding those too would be a rule without a defect behind it.
CONGELATO = ("fondamenta/",)
RX_PERC  = re.compile(r'`([A-Za-z0-9_][A-Za-z0-9_./-]*\.(?:c|h|py|sh|md|html|json|jsonl|pam|rs))`')
RX_LINK  = re.compile(r'\[[^\]]+\]\(([A-Za-z0-9_][A-Za-z0-9_./-]*\.(?:md|png|jpg|sh|py|c|h))\)')
RX_RIPR  = re.compile(r'DA QUI SI RIPRENDE')


def documenti(radice):
    try:
        fuori = subprocess.check_output(["git", "-C", radice, "ls-files", "*.md"],
                                        text=True, stderr=subprocess.DEVNULL)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return [f for f in fuori.split() if not f.startswith(ESCLUSE)]


def elenco_file(radice):
    fuori = subprocess.check_output(["git", "-C", radice, "ls-files"], text=True)
    tutti = set(fuori.split())
    nomi = set(p.rsplit("/", 1)[-1] for p in tutti)
    return tutti, nomi


def guarda(radice, eccezioni=None):
    """returns (coordinate, percorsi_morti, link_rotti, riprese) — each a list"""
    scusati = eccezioni if eccezioni is not None else eccezioni_dichiarate()
    docs = documenti(radice)
    if docs is None:
        return None
    tutti, nomi = elenco_file(radice)
    coord, morti, rotti, riprese = [], [], [], []
    for d in docs:
        p = os.path.join(radice, d)
        try:
            with open(p, encoding="utf-8") as f:
                righe = f.read().split("\n")
        except OSError:
            continue
        for n, riga in enumerate(righe, 1):
            for m in RX_RIGA.finditer(riga):
                f_cit = m.group(1)
                if f_cit.startswith(CONGELATO):
                    continue
                vivo = any(os.path.exists(os.path.join(radice, x))
                           for x in (f_cit, "src/" + f_cit, "banchi/" + f_cit))
                if vivo:
                    coord.append(f"{d}:{n}  {m.group(0)}")
            if RX_RIPR.search(riga) and riga.lstrip("> ").startswith("#"):
                riprese.append(f"{d}:{n}")
            # the paths marked ⟨…⟩ are declared as other people's: they are not chased
            ripulita = riga
            for marca in MARCHE_ESTERNE:
                ripulita = re.sub(re.escape(marca) + r'\s*[A-Za-z0-9_./-]+', "", ripulita)
            for m in RX_PERC.finditer(ripulita):
                c = m.group(1)
                if c in tutti or c.rsplit("/", 1)[-1] in nomi:
                    continue
                if os.path.exists(os.path.join(radice, c)):
                    continue
                if c.startswith(TOLTI_APPOSTA):
                    continue
                if any(s in c for s in scusati):
                    continue
                morti.append(f"{d}:{n}  {c}")
            for m in RX_LINK.finditer(riga):
                c = m.group(1)
                if c.startswith(("http", "#")):
                    continue
                base = os.path.dirname(d)
                if c in tutti or os.path.exists(os.path.join(radice, c)) \
                   or os.path.exists(os.path.join(radice, base, c)):
                    continue
                rotti.append(f"{d}:{n}  {c}")
    return coord, morti, rotti, riprese


def stampa(nome, brutti, tetto, spiega):
    if not brutti:
        print(f"  \033[1;32mOK\033[0m  {nome}")
        return True
    print(f"  \033[1;31mNO\033[0m  {nome} — {len(brutti)}")
    print(f"      ⛔ {spiega}")
    for b in brutti[:tetto]:
        print(f"        {b}")
    if len(brutti) > tetto:
        print(f"        … and {len(brutti) - tetto} more")
    return False


def giro(radice, silenzioso=False, eccezioni=None):
    visto = guarda(radice, eccezioni)
    if visto is None:
        if not silenzioso:
            print("  ⛔ I could not look: the root is not a git repository")
        return 3
    coord, morti, rotti, riprese = visto
    if silenzioso:
        return 1 if (coord or morti or rotti or len(riprese) > 1) else 0
    print("== C16 — the documents do not lie ==")
    verdi = [
        stampa("no line coordinate towards our code", coord, 8,
               "a coordinate right today is wrong next week: the NAME is cited"),
        stampa("every cited path exists (or carries the ⟨…⟩ mark)", morti, 8,
               "the document points to a file that is not in the repository"),
        stampa("no broken markdown link", rotti, 8,
               "a broken link is worse than a citation: it promises to open"),
        stampa("one single «DA QUI SI RIPRENDE» heading",
               riprese if len(riprese) > 1 else [], 8,
               "more than one, and whoever reopens does not know which one holds"),
    ]
    print()
    if all(verdi):
        print("  ⭐ the four checks hold.")
        print("  ⚠ and this mesh says the ADDRESSES hold, ⛔ not that the")
        print("    papers are right: a wrong measurement passes through here intact.")
        return 0
    return 1


def certifica():
    """⛔ a mesh that has never been seen failing is not a mesh"""
    print("== certification of C16 — can it give red? ==\n")
    # ⚠ 28 Aug 2026: the terrain of the first fault must REALLY contain `src/main.c`.
    #    ⛔ When check 1 went from «any coordinate» to «only towards
    #    files that exist and move», the fake fault stopped being seen
    #    — and ⭐ **the certification noticed at once**: it is exactly its
    #    job, and it is the reason a mesh is not written without one.
    guasti = {
        "a line coordinate":           ("g1.md", "see `src/main.c:111` for the rest.\n"),
        "a path that does not exist":  ("g2.md", "it is in `src/inventato_dal_nulla.c`.\n"),
        "a broken markdown link":      ("g3.md", "the report is [here](fasi/rapporti/mai-esistito.md).\n"),
        "two «DA QUI SI RIPRENDE»":    ("g4.md", "# DA QUI SI RIPRENDE — ieri\n\n# DA QUI SI RIPRENDE — oggi\n"),
    }
    esiti = []
    for nome, (file, testo) in guasti.items():
        with tempfile.TemporaryDirectory() as t:
            subprocess.run(["git", "-C", t, "init", "-q"], check=True)
            with open(os.path.join(t, "sano.md"), "w", encoding="utf-8") as f:
                f.write("An honest document: it cites `sano.md` and that is all.\n")
            os.makedirs(os.path.join(t, "src"), exist_ok=True)
            with open(os.path.join(t, "src", "main.c"), "w", encoding="utf-8") as f:
                f.write("int main(void) { return 0; }\n" * 200)
            subprocess.run(["git", "-C", t, "add", "sano.md", "src/main.c"], check=True)
            if giro(t, silenzioso=True, eccezioni=[]) != 0:
                print(f"  ⛔ the HEALTHY terrain is not green: the certification is not valid")
                return 2
            with open(os.path.join(t, file), "w", encoding="utf-8") as f:
                f.write(testo)
            subprocess.run(["git", "-C", t, "add", file], check=True)
            rosso = giro(t, silenzioso=True, eccezioni=[]) == 1
            esiti.append(rosso)
            print(f"  {'✓ SEEN    ' if rosso else '⛔ NOT SEEN'}  {nome}")
    print()
    if all(esiti):
        print("  ⭐ C16 can give red on all four faults, and the healthy")
        print("    terrain stays green. ⇒ A green of it means something.")
        return 0
    print("  ⛔ at least one injected fault was NOT seen: the mesh is silent.")
    return 1


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--radice", default=None, help="the repository to look at")
    p.add_argument("--certifica", action="store_true")
    a = p.parse_args()
    if a.certifica:
        return certifica()
    radice = a.radice or subprocess.run(
        ["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True
    ).stdout.strip()
    if not radice:
        print("  ⛔ I am not inside a git repository, and --radice was not given")
        return 2
    return giro(radice)


if __name__ == "__main__":
    sys.exit(main())
