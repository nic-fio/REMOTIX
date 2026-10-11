"""fase_c.py — step 2 of the English migration: the file and directory names (RINOMINA.md, step 2).

The move table is `english-migration/fase-c-moves.tsv` (or --moves): rows `old_path <TAB> new_path <TAB> why`,
a directory row ending in «/».  A row whose new equals old keeps the name.  The table was written against one
tree; this tool never trusts its line numbers: every command recomputes the moves and the references on the
tree it is given.

  python3 fase_c.py plan  --root TREE [--out DIR]
        the effective moves of the tracked files, every reference found (file:line, kind, old text → new text),
        the ambiguous ones resolved by directory context, and the unresolved ones.  Read only.
  python3 fase_c.py apply --root COPY [--dry-run]
        1. rewrites the references (relative paths, includes, Makefile/script paths, Go import paths and
           -X flags, packaging lists, links in documents, the manual's sources and file map, a few named
           sites listed in SITES), and the two identifier families the move renames with its file
           (scrittore_bit.c → bit_writer.c: sb_* → bw_*; ritrovo.c → rediscover.c: rediscover_*);
        2. `git mv` of the whole directories first (top-down), then of the files;
        3. writes the old → new map next to C16 (`11-c16-old-paths.tsv`) and teaches C16 to read it, so
           the history lines of the documents, which keep the paths they were written with, stay alive.
        Never touched: the registers and every *.jsonl, `git show <commit>:<path>` (history), misure/,
        memoria/, fondamenta/, english-migration/, installatore/vendor/, the bench reports rapporto-giro*,
        the frozen snapshot banchi/prodotto/, the generated manuals (regenerate them), installed system paths
        (/etc, /usr, /var, /run, /lib: phase B's disco table owns those), and in the history documents
        (FASI, DECISIONI, LEZIONI, STUDI, PIANO, MASTERPLAN, fasi/) everything but the links.
  python3 fase_c.py map --root COPY [--paths [--back]]
        stdin → stdout with the old path names (paths, folder and file names, bench stems) of the applied
        manifest replaced by the new ones; --paths maps only whole tokens that are tracked paths.
  python3 fase_c.py check --root COPY
        every move done (the manifest apply left in .git), no tracked path under a moved-away name, and no
        reference to an old path left outside the allowed list.  Exit 1 otherwise.

Paths: a path is a run of [A-Za-z0-9_./${}*?-].  Its «/»-components are aligned with the tracked paths of
the tree (longest run of components that is the tail of a tracked path or folder); each aligned component
takes its new name.  A lone folder name (no «/») counts only as a top-level folder in shell, Make and
packaging text, or as a whole quoted string in code; a lone name of a sub-folder must be followed by a
tracked child.  Globs and $VARIABLES in a component are matched with fnmatch; the new glob is the old one
with the words of the renamed files swapped, and it is kept only if it matches exactly the new names of what
the old one matched.  Where the candidates disagree, the one nearest the citing file wins (same folder,
same top folder); a tie is left alone and listed as unresolved.
"""
import argparse
import collections
import fnmatch
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MOVES = os.path.join(HERE, "fase-c-moves.tsv")

# never scanned, never rewritten
SKIP_PREFIX = ("misure/", "memoria/", "fondamenta/", "installatore/vendor/", "english-migration/",
               "banchi/prodotto/", "installer/vendor/", "benches/prodotto/")
SKIP_FILES = {"docs/Technical Manual.html", "docs/User Manual.html"}   # generated: regenerate them
SKIP_RX = re.compile(r"(\.jsonl$|/rapporto-giro[^/]*$)")
# the logs: their dated lines describe the tree as it was; only their links are rewritten
HIST_DOC = re.compile(r"^(fasi/|FASI\.md$|DECISIONI\.md$|LEZIONI\.md$|STUDI\.md$|PIANO\.md$|MASTERPLAN\.md$|"
                      r"phases/|PHASES\.md$|DECISIONS\.md$|LESSONS\.md$|STUDIES\.md$|PLAN\.md$)")
BINARY = re.compile(r"\.(png|jpg|jpeg|gif|webp|ico|wasm|gz|tgz|zst|pdf|xz|bin|ttf|otf|woff2?|mp4|webm|o|so|a|"
                    r"zip|deb|rpm|iso|qcow2|raw|h264|hevc|ivf|y4m|wav|opus|pkt|f32|rcpreg|run|svgz)$", re.I)
# installed names belong to phase B (disco.tsv): an absolute path under these is never rewritten
SYSTEM_ROOTS = ("/etc/", "/usr/", "/var/", "/run/", "/lib/", "/lib64/", "/proc/", "/sys/", "/dev/")
# a path under an install root (spec macros, $pkgdir, $DESTDIR) is an installed name: phase B's
INSTALL_ROOT = re.compile(r"^(\{_?\w+\}|\{buildroot\}|\$\{?(pkgdir|DESTDIR|buildroot|RPM_BUILD_ROOT)\}?)(/|$)")
# old paths that name something deliberately removed (C16's DELIBERATELY_REMOVED): they stay as written
KEEP_OLD = ("fasi/rapporti/", "web/rapporti/")
HISTORY_DIRS = {"fondamenta", "misure", "memoria", "english-migration"}
GITSHOW = re.compile(r"\b[0-9a-f]{7,40}\^?(~\d+)?:[\"']?$")
RUN_RX = re.compile(r"[\w./${}*-]+")
GLOBCH = re.compile(r"[*]|\$\{?\w+\}?")

C16_MAP = "11-c16-old-paths.tsv"

# identifiers that follow the file they live in (coordinator's ruling, step 2)
IDENTS = [
    (re.compile(r"\b(?:ritrovo|finding_again)_(cerca|search)\b"), "rediscover_search", ("src/", "docs/sources/")),
    (re.compile(r"\b(?:ritrovo|finding_again)_(vivo|alive)\b"), "rediscover_alive", ("src/", "docs/sources/")),
    (re.compile(r"\b(?:Ritrovo|FindingAgain)Desktop\b"), "RediscoveredDesktop", ("src/", "docs/sources/")),
    # the Go package of installatore/interfaccia/ is ui/ (interface is a keyword): its clause and every qualifier
    (re.compile(r"^package interfaccia$", re.M), "package ui", ("installatore/",)),
    (re.compile(r"^// Package interfaccia\b", re.M), "// Package ui", ("installatore/",)),
    (re.compile(r"\binterfaccia\.(?=[A-Z])"), "ui.", ("installatore/", "docs/sources/")),
]
IDENT_EXT = (".c", ".h", ".py", ".go")

# named sites a path scan cannot see (hazards.md): (file old path, line regex, [(regex, replacement)]).
# Each is applied on the lines of that file matching the line regex; one that matches nothing is reported.
BLACKLIST_SUBS = [(r"\bprovisiona\b", "provision"), (r"riavvia-", "restart-"), (r"/prova\b", "/test"),
                  (r"(?<![\w/])prova\b", "/test"), (r"\bbanchi\b", "benches"), (r"\bContenitore\b", "Containerfile"),
                  (r"\bcostruisci\b", r"build(-[a-z]+)?\\.sh")]
SITES = [
    ("packaging/rpm/costruisci-rpm.sh", r"sudoers.*gpu-udev|gpu-udev.*sudoers", BLACKLIST_SUBS),
    ("src/costruzione/costruisci-deb.sh", r"sudoers.*gpu-udev|gpu-udev.*sudoers", BLACKLIST_SUBS),
    ("packaging/arch/costruisci.sh", r"sudoers.*gpu-udev|gpu-udev.*sudoers", BLACKLIST_SUBS),
    ("installatore/costruisci.sh", r"\bgofmt\b", [(r"\bmotore\b", "engine"), (r"\binterfaccia\b", "ui"),
                                                  (r"\bcatalogo\b", "catalog"), (r"\bprove\b", "tests")]),
    ("banchi/11-scatole/11-gancio.sh", r"##\*Contenitore\.", [(r"##\*Contenitore\.", "##*Containerfile.")]),
    ("banchi/16-stress/16-salita.py", r"\[1\]6-risorse", [(r"\[1\]6-risorse\.py", "[1]6-NEW(banchi/16-stress/16-risorse.py)")]),
    # en-57 dry run: folders joined to a variable, files copied under /var/tmp by their name, page URLs
    ("banchi/02-sessione-lancia.sh", r"/02-sessione-scene\}", [(r"/02-sessione-scene\}", "/02-session-scenes}")]),
    ("banchi/17-distro/17-t10.sh", r"/scatole\}", [(r"/scatole\}", "/boxes}")]),
    ("banchi/17-distro/17-vm.sh", r'/iso-risposte"', [(r'/iso-risposte"', '/iso-answers"')]),
    ("banchi/17-distro/iso-differenze.md", r"`iso-risposte/`", [(r"`iso-risposte/`", "`iso-answers/`")]),
    ("banchi/17-distro/17-t3-rpm.sh", r"/var/tmp/17-t3-", [(r"/var/tmp/17-t3-impronta-rpm\.sh", "/var/tmp/17-t3-fingerprint-rpm.sh"),
                                                          (r"/var/tmp/17-t3-gruppi\.sh", "/var/tmp/17-t3-groups.sh")]),
    ("banchi/17-distro/17-t3-pacchetto.sh", r"/var/tmp/17-t3-impronta-arch\.sh",
     [(r"/var/tmp/17-t3-impronta-arch\.sh", "/var/tmp/17-t3-fingerprint-arch.sh")]),
    ("banchi/01-b2-raccogli.py", r"/01-b2-sonda\.html", [(r"/01-b2-sonda\.html", "/01-b2-probe.html")]),
    ("banchi/01-s7-raccogli.py", r"/01-s7-pagina\.html", [(r"/01-s7-pagina\.html", "/01-s7-page.html")]),
    ("banchi/02-figlio-lancia.sh", r"costruisci\.sh", [(r"\bcostruisci\.sh\b", "build.sh")]),
    ("banchi/01-casa-7448.sh", r"bash costruisci\.sh", [(r"bash costruisci\.sh", "bash build.sh")]),
    ("grafica/sito-mockup/autocontenuta.py", r'"pubblica"|schermate-vere\|icone',
     [(r'QUI / "pubblica"', 'QUI / "public"'), (r"\(\?:schermate-vere\|icone\)/", "(?:screenshots|icons)/")]),
    ("grafica/sito-mockup/LEGGIMI.md", r"`icone/`", [(r"`icone/`", "`icons/`"), (r"`schermate-vere/`", "`screenshots/`")]),
    ("README.md", r"Between one step and the next TWO things", [(r"`costruisci\.sh`", "`build.sh`")]),
    ("docs/sources/technical/ch01_introduction.py", r'c\("costruisci\.sh"\)', [(r'c\("costruisci\.sh"\)', 'c("build.sh")')]),
    ("docs/sources/technical/ch15_installer.py", r"\(cmd, motore, interfaccia,|catalogo, run\.sh, costruisci\.sh\)|── costruisci\.sh",
     [(r"\(cmd, motore, interfaccia,", "(cmd, engine, ui,"), (r"catalogo, run\.sh, costruisci\.sh\)", "catalog, run.sh, build.sh)"),
      (r"── costruisci\.sh  ", "── build.sh       ")]),
    ("docs/sources/technical/ch17_build.py", r'src/costruisci\*\.sh|c\("costruisci\.sh( test)?"\)|arch, motore, archivio,',
     [(r"src/costruisci\*\.sh", "src/build*.sh"), (r'c\("costruisci\.sh', 'c("build.sh'),
      (r"arch, motore, archivio,", "arch, engine, archive,")]),
    ("docs/sources/technical/ch22_map.py", r'\(S \+ "costruisci\.sh"', [(r'\(S \+ "costruisci\.sh"', '(S + "build.sh"')]),
]
# the build images: the script is copied and run under its own name
SITES += [("src/costruzione/Contenitore." + d, r"/usr/local/bin/quic-statiche\.sh",
           [(r"/usr/local/bin/quic-statiche\.sh", "/usr/local/bin/quic-static.sh")])
          for d in ("alma10", "arch", "debian13", "fedora44", "leap16", "tumbleweed", "ubuntu2404", "ubuntu2604")]
TOP_WORD_KINDS = {"shell", "make", "packaging", "gitignore", "containerfile", "rules"}
CODE_KINDS = {"python", "shell", "make", "c", "c-include", "go", "go-import", "go-embed", "go-module", "web",
              "packaging", "containerfile", "gitignore", "manual-source", "manual-file-map", "other", "data",
              "licence-list"}


def git(root, *args):
    return subprocess.run(["git", "-C", root] + list(args), capture_output=True, check=True).stdout.decode()


def tracked(root):
    return [t for t in git(root, "ls-files", "-z").split("\0") if t]


def read_moves(path):
    rows = []
    for ln in open(path, encoding="utf-8"):
        if not ln.strip() or ln.startswith("#") or ln.startswith("old_path\t"):
            continue
        o, n, *w = ln.rstrip("\n").split("\t")
        rows.append((o, n))
    return rows


def skipped(p):
    return p.startswith(SKIP_PREFIX) or p in SKIP_FILES or bool(SKIP_RX.search(p))


class Plan:
    """the effective moves of one tree, and the maps the scanner needs"""

    def __init__(self, root, moves_path, files=None):
        self.root = root
        self.rows = read_moves(moves_path)
        self.files = files if files is not None else tracked(root)
        self.dir_rows = {o.rstrip("/"): n.rstrip("/") for o, n in self.rows if o.endswith("/")}
        self.file_rows = {o: n for o, n in self.rows if not o.endswith("/")}
        self.errors, self.warnings = [], []
        self.map = {}                  # tracked old file → new file
        fset = set(self.files)
        for f in self.files:
            self.map[f] = self.new_path(f)
        for o in self.file_rows:
            if o not in fset:
                self.warnings.append("table row for a file the tree no longer has: " + o)
        for d in self.dir_rows:
            if not any(f.startswith(d + "/") for f in self.files):
                self.warnings.append("table row for a folder the tree no longer has: " + d + "/")
        # prefix map, component by component (moves keep the depth)
        self.pmap = {}
        news = collections.Counter()
        for o, n in self.map.items():
            oc, nc = o.split("/"), n.split("/")
            if len(oc) != len(nc):
                self.errors.append("a move changes the depth: %s → %s" % (o, n))
                continue
            news[n] += 1
            for k in range(1, len(oc) + 1):
                po, pn = "/".join(oc[:k]), "/".join(nc[:k])
                if self.pmap.setdefault(po, pn) != pn:
                    self.errors.append("folder %s goes to two places: %s and %s" % (po, self.pmap[po], pn))
        for n, c in news.items():
            if c > 1:
                self.errors.append("two files move to " + n)
        lower = collections.defaultdict(set)
        for n in news:
            lower[n.lower()].add(n)
        for k, v in lower.items():
            if len(v) > 1:
                self.errors.append("case clash: " + " ".join(sorted(v)))
        self.moved = {o: n for o, n in self.pmap.items() if o != n}
        # the candidates of the alignment: every tracked path or folder outside the skipped areas
        self.tail = collections.defaultdict(set)     # "a/b" (tail of components) → old prefixes
        self.dirs = set()
        for po in self.pmap:
            if po.startswith(SKIP_PREFIX):
                continue
            if po not in self.map:
                self.dirs.add(po)
            c = po.split("/")
            for k in range(len(c)):
                self.tail["/".join(c[k:])].add(po)
        # stems of renamed files with a distinctive name (binaries, process names, test ids)
        for o, n in self.map.items():
            if o == n or skipped(o):
                continue
            bo, bn = os.path.basename(o), os.path.basename(n)
            so, sn = os.path.splitext(bo)[0], os.path.splitext(bn)[0]
            if so != sn and re.match(r"^[a-z]?\d+[a-z]?\d*-", so) and so not in self.tail:
                stem = os.path.join(os.path.dirname(o), so)
                self.pmap.setdefault(stem, os.path.join(os.path.dirname(n), sn))
                self.tail[so].add(stem)
        self.top = {o for o in self.moved if "/" not in o and o not in self.map}
        # words of the renamed basenames, for globs: old word → new word when one-to-one
        pairs = collections.defaultdict(set)
        for o, n in self.moved.items():
            wo, wn = re.split(r"([-_.])", os.path.basename(o)), re.split(r"([-_.])", os.path.basename(n))
            if len(wo) == len(wn):
                for a, b in zip(wo, wn):
                    if a != b:
                        pairs[a].add(b)
        self.words = {a: next(iter(b)) for a, b in pairs.items() if len(b) == 1}
        self.known = set(self.tail) | self.top
        # sb_* → bw_*: the functions the bit writer's header declares (not the X cursor names sb_h_double_arrow)
        self.idents = []
        for h in ("src/scrittore_bit.h", "src/bit_writer.h"):
            try:
                hs = open(os.path.join(root, h), encoding="utf-8").read()
            except OSError:
                continue
            names = sorted(set(re.findall(r"\bsb_(\w+)\s*\(", hs)), key=len, reverse=True)
            if names:
                self.idents.append((re.compile(r"\bsb_(?=(?:%s)\b)" % "|".join(names)), "bw_",
                                    ("src/", "banchi/", "benches/", "docs/sources/")))
        self.new_set = set(self.map.values())

    def new_path(self, f):
        if f in self.file_rows:
            return self.file_rows[f]
        c = f.split("/")
        for k in range(len(c) - 1, 0, -1):
            d = "/".join(c[:k])
            if d in self.dir_rows:
                return self.dir_rows[d] + "/" + "/".join(c[k:])
        return f

    def np(self, po):
        """new spelling of an old path or folder (folders not tracked as such fall back to their parent)"""
        if po in self.pmap:
            return self.pmap[po]
        c = po.split("/")
        for k in range(len(c) - 1, 0, -1):
            d = "/".join(c[:k])
            if d in self.pmap:
                return self.pmap[d] + "/" + "/".join(c[k:])
        return po


def kind_of(path, root):
    b = os.path.basename(path)
    if path == "docs/sources/technical/ch22_map.py":
        return "manual-file-map"
    if path.startswith("docs/sources/"):
        return "manual-source"
    if b == "Makefile" or b.endswith(".mk"):
        return "make"
    if b == "THIRD-PARTY-LICENSES":
        return "licence-list"
    if b in (".gitignore", ".gitattributes"):
        return "gitignore"
    if b.startswith(("Contenitore", "Containerfile")) or b.endswith(".systemd"):
        return "containerfile"
    if path.startswith("packaging/") and not b.endswith((".py", ".sh")):
        return "rules" if b == "rules" else "packaging"
    if b.endswith((".c", ".h")):
        return "c"
    if b.endswith(".go"):
        return "go"
    if b == "go.mod":
        return "go-module"
    if b.endswith(".py"):
        return "python"
    if b.endswith(".sh"):
        return "shell"
    if b.endswith((".html", ".js", ".mjs", ".css", ".svg")):
        return "web"
    if b.endswith(".md"):
        return "doc-history" if HIST_DOC.match(path) else "doc"
    if b.endswith((".txt", ".tsv", ".json", ".csv", ".conf", ".rules", ".pam", ".service", ".spec")):
        return "data"
    try:
        with open(os.path.join(root, path), "rb") as fh:
            head = fh.read(64).split(b"\n")[0]
    except OSError:
        return "other"
    if head.startswith(b"#!") and b"python" in head:
        return "python"
    if head.startswith(b"#!") and b"sh" in head:
        return "shell"
    return "other"


def comment(line):
    return line.lstrip().startswith(("#", "//", "/*", "* ", "--", ";"))


def is_glob(comp):
    return bool(GLOBCH.search(comp))


def glob_rx(comp):
    """a component with * ? $VAR ${VAR} as an fnmatch pattern"""
    return re.sub(r"\$\{?\w+\}?", "*", comp)


class Scanner:
    def __init__(self, plan):
        self.p = plan
        self.unresolved = []

    def candidates(self, tail):
        return self.p.tail.get(tail, ())

    def choose(self, cands, src, texts):
        """cands: old prefixes; texts: their new spelling of the aligned piece.  One answer or None."""
        if len(set(texts.values())) == 1:
            return next(iter(texts.values())), ""
        sd = os.path.dirname(src)
        for test, how in ((lambda c: os.path.dirname(c) == sd, "same-dir"),
                          (lambda c: sd == c or sd.startswith(c + "/") or c.startswith(sd + "/"), "same-tree"),
                          (lambda c: c.split("/")[0] == src.split("/")[0], "same-top")):
            pick = {c for c in cands if test(c)}
            if pick and len({texts[c] for c in pick}) == 1:
                return texts[next(iter(pick))], how
        return None, "AMBIGUOUS"

    def translate(self, s, src, kind, quoted, ctx):
        """s: a path-like run.  Returns (new string, notes) — new None when nothing changes."""
        if s.startswith(SYSTEM_ROOTS) or INSTALL_ROOT.match(s) or \
                re.match(r"(etc|usr|var)/", s) and kind in ("packaging", "rules", "data", "shell"):
            return None, []
        comps = s.split("/")
        if any(c in HISTORY_DIRS for c in comps):
            return None, []
        out = list(comps)
        notes = []
        i = 0
        changed = False
        while i < len(comps):
            c = comps[i]
            if not c or c in (".", "..") or re.fullmatch(r"\$\{?\w+\}?", c):
                i += 1
                continue
            # longest literal alignment starting at i
            best = None
            for j in range(len(comps), i, -1):
                piece = comps[i:j]
                if any(is_glob(x) for x in piece):
                    continue
                cands = self.candidates("/".join(piece))
                if cands:
                    best = (j, cands)
                    break
            if best is None:
                # a glob alignment: components i..j with wildcards
                g = self.glob_align(comps, i, src) if kind not in ("doc", "doc-history") else None
                if g:
                    j, newpiece, note = g
                    if newpiece is not None:
                        out[i:j] = newpiece
                        changed = changed or newpiece != comps[i:j]
                    if note:
                        notes.append(note)
                    i = j
                    continue
                i += 1
                continue
            j, cands = best
            piece = comps[i:j]
            if "/".join(comps[i:]).startswith(KEEP_OLD):
                i = len(comps)
                continue
            k = j - i
            # lone components need more evidence than a full path
            if k == 1:
                name = piece[0]
                is_dir = all(c2 in self.p.dirs for c2 in cands)
                if is_dir:
                    top = name in self.p.top
                    follows = j < len(comps) and comps[j] != ""
                    lead = all(not x or x in (".", "..") or re.fullmatch(r"\$\{?\w+\}?", x) for x in comps[:i])
                    if follows:              # «x/child»: the child must be tracked (or a glob)
                        nxt = comps[j]
                        ok = top or is_glob(nxt) or any(c2 + "/" + nxt in self.p.pmap for c2 in cands)
                    elif j < len(comps):     # «x/» alone: a folder named as such, at the start of the path
                        ok = top or (lead and kind in CODE_KINDS)
                    else:                    # a bare word: top folders in shell-like text, or a whole string
                        ok = (top and (kind in TOP_WORD_KINDS or quoted) and not comment(ctx)) or \
                             (quoted and kind in CODE_KINDS and bool(re.search(r"[\d-]", name)))
                    if not ok:
                        i = j
                        continue
            texts = {}
            for c2 in cands:
                nc = self.p.np(c2).split("/")
                texts[c2] = "/".join(nc[len(nc) - k:])
            new, how = self.choose(cands, src, texts)
            if new is None:
                notes.append(("UNRESOLVED", "/".join(piece), sorted(cands)))
                i = j
                continue
            if how:
                notes.append((how, "/".join(piece), new))
            newc = new.split("/")
            if newc != piece:
                out[i:j] = newc
                changed = True
            # below an aligned folder: tracked children keep translating
            base = [c2 for c2 in cands if texts[c2] == new]
            i = j
            while i < len(comps) and base:
                nxt = comps[i]
                if not nxt or is_glob(nxt):
                    break
                kids = [b + "/" + nxt for b in base if b + "/" + nxt in self.p.pmap]
                if not kids:
                    break
                nn = {self.p.np(x).split("/")[-1] for x in kids}
                if len(nn) != 1:
                    break
                v = nn.pop()
                if v != nxt:
                    out[i] = v
                    changed = True
                base = kids
                i += 1
        return ("/".join(out) if changed else None), notes

    def glob_align(self, comps, i, src):
        """comps[i..j) holds a wildcard: match it against the tracked tails; the new glob swaps words."""
        for j in range(len(comps), i, -1):
            piece = comps[i:j]
            if not any(is_glob(x) for x in piece):
                continue
            if all(re.fullmatch(r"[*?]+|\$\{?\w+\}?", x) or not x for x in piece):
                continue
            if any("**" in x for x in piece) or (k1 := len(piece)) == 1 and piece[0].startswith("*") \
                    and not re.search(r"[-_.]", piece[0]):
                continue
            lits = [w for x in piece for w in re.split(r"\$\{?\w+\}?|[*?]|[-_.]", x) if w]
            if not any(w in self.p.words for w in lits) and not any(
                    x in self.p.known for x in piece if not is_glob(x)):
                continue
            pat = "/".join(glob_rx(x) for x in piece)
            k = len(piece)
            matched = set()
            for po in self.p.pmap:
                c = po.split("/")
                if len(c) >= k and fnmatch.fnmatchcase("/".join(c[len(c) - k:]), pat) \
                        and not po.startswith(SKIP_PREFIX):
                    matched.add(po)
            if not matched:
                continue
            if not any(self.p.np(m) != m for m in matched):
                return j, None, None
            want = {self.p.np(m) for m in matched}
            parents = {"/".join(w.split("/")[:-k]) for w in want}
            news = set(self.p.pmap.values())
            got = set()
            for swap in (False, True):
                newpiece = [self.swap_words(x) if swap else x for x in piece]
                # the literal folders of the piece: their new spelling from the matched paths
                for t in range(k):
                    if not is_glob(piece[t]):
                        vals = {self.p.np(m).split("/")[len(m.split("/")) - k + t] for m in matched}
                        if len(vals) == 1:
                            newpiece[t] = vals.pop()
                npat = "/".join(glob_rx(x) for x in newpiece)
                got = set()
                for po in news:
                    c = po.split("/")
                    par = "/".join(c[:len(c) - k])
                    if len(c) >= k and par in parents and fnmatch.fnmatchcase("/".join(c[len(c) - k:]), npat):
                        got.add(po)
                if got == want:
                    return j, newpiece, None
            return j, None, ("UNRESOLVED-GLOB", "/".join(piece), sorted(want - got)[:3] + sorted(got - want)[:3])
        return None

    def swap_words(self, comp):
        parts = re.split(r"(\$\{?\w+\}?|[*?]|[-_.])", comp)
        return "".join(self.p.words.get(x, x) for x in parts)

    # ---- one file ------------------------------------------------------------------------------------
    def edits(self, path, text, kind):
        """[(start, end, new, line, old, notes)] for one file's text"""
        out = []
        taken = []
        lines = text.split("\n")
        off = 0
        hist = kind == "doc-history"
        for no, line in enumerate(lines, 1):
            # 1. links of documents and pages, resolved relative to the citing file
            if kind in ("doc", "doc-history", "web"):
                for m in re.finditer(r"\]\(([^)\s#]+)(#[^)\s]*)?\)|\b(?:src|href)=\"([^\"#?]+)", line):
                    t = m.group(1) or m.group(3)
                    a = m.start(1) if m.group(1) else m.start(3)
                    new = self.link(path, t)
                    if new and new != t:
                        out.append((off + a, off + a + len(t), new, no, t, [("link", t, new)]))
                        taken.append((off + a, off + a + len(t)))
            if hist:
                off += len(line) + 1
                continue
            # 2. Go module and import paths, -X flags (remotix/installatore/<pkg>.Symbol)
            for m in re.finditer(r"\bremotix/(installatore(?:/[A-Za-z0-9_]+)*)", line):
                a, z = off + m.start(1), off + m.end(1)
                old = m.group(1)
                new = self.p.np(old)
                if new != old and not overlaps(taken, a, z):
                    out.append((a, z, new, no, old, [("go-path", old, new)]))
                    taken.append((a, z))
            # 3. a path written as pieces: "a" / "b" / "c" (pathlib) or join(…, "a", "b")
            if kind in ("python", "manual-source", "manual-file-map"):
                for chain in chains(line):
                    if len(chain) < 2 or any(overlaps(taken, off + a, off + z) for a, z, _ in chain):
                        continue
                    s = "/".join(x for _, _, x in chain)
                    new, notes = self.translate(s, path, kind, True, line)
                    if new is None or len(new.split("/")) != len(chain):
                        continue
                    for (a, z, x), y in zip(chain, new.split("/")):
                        if x != y:
                            out.append((off + a, off + z, y, no, x, [("pieces", s, new)]))
                        taken.append((off + a, off + z))
            # 4. every path-like run
            for m in RUN_RX.finditer(line):
                a, z = m.start(), m.end()
                s = m.group(0)
                while s and (s[-1] in ".,;:" and not s.endswith(("..", "/.")) or
                             s[-1] == "}" and s.count("}") > s.count("{")):
                    s = s[:-1]
                    z -= 1
                while s and (s[0] == "{" and s.count("{") > s.count("}") or s.startswith("-/")):
                    s = s[1:]
                    a += 1
                if not s or overlaps(taken, off + a, off + z):
                    continue
                parts = set(re.split(r"[/]", s))
                if not (parts & self.p.known) and not (GLOBCH.search(s) and self.maybe_glob(s)):
                    continue
                if GITSHOW.search(line[:a]):
                    continue
                q = line[a - 1:a] if a else ""
                quoted = q in "\"'`" and q != "" and line[z:z + 1] == q
                new, notes = self.translate(s, path, kind, quoted, line)
                for n in notes:
                    if n[0].startswith("UNRESOLVED"):
                        self.unresolved.append((path, no, kind, n[1], " ".join(map(str, n[2]))))
                if new is not None and new != s:
                    out.append((off + a, off + z, new, no, s, notes))
                    taken.append((off + a, off + z))
            off += len(line) + 1
        return out

    def maybe_glob(self, s):
        return any(w in self.p.words or w in self.p.known for w in re.split(r"[-_./*?${}]+", s) if w)

    def link(self, doc, t):
        if re.match(r"^[a-z]+:", t) or t.startswith(("/", "#", "mailto")):
            return None
        base = os.path.dirname(doc)
        for cand in (os.path.normpath(os.path.join(base, t)), os.path.normpath(t)):
            if cand.startswith(".."):
                continue
            n = self.p.np(cand.rstrip("/"))
            if cand.rstrip("/") in self.p.pmap and n != cand.rstrip("/"):
                nd = os.path.dirname(self.p.np(doc)) if doc in self.p.map else base
                if cand == os.path.normpath(t) and cand != os.path.normpath(os.path.join(base, t)):
                    r = n                                  # written from the root: stays from the root
                else:
                    r = os.path.relpath(n, nd or ".")
                if t.startswith("./") and not r.startswith("."):
                    r = "./" + r
                return r + ("/" if t.endswith("/") else "")
        return None


def where(old, done_dirs):
    """where an old path is now: under the deepest folder already moved (its new place is final)"""
    best = None
    for pd, pn in done_dirs:
        if old.startswith(pd + "/") and (best is None or len(pd) > len(best[0])):
            best = (pd, pn)
    return best[1] + old[len(best[0]):] if best else old


CHAIN_SLASH = re.compile(r"(?:\"[^\"\s/]+\"|'[^'\s/]+')(?:\s*/\s*(?:\"[^\"\s/]+\"|'[^'\s/]+'))+")


def chains(line):
    """[(start, end, text)] of the quoted pieces of one path written in pieces"""
    out = []
    for m in CHAIN_SLASH.finditer(line):
        out.append([(q.start() + 1, q.end() - 1, q.group(0)[1:-1])
                    for q in re.finditer(r"\"[^\"\s/]+\"|'[^'\s/]+'", m.group(0))])
        out[-1] = [(m.start() + a, m.start() + z, x) for a, z, x in out[-1]]
    for m in re.finditer(r"\bjoin\(([^()]*)\)", line):
        cur = []
        for q in re.finditer(r"\s*(\"[^\"\s/]+\"|'[^'\s/]+'|[^,]+)\s*(,|$)", m.group(1)):
            g = q.group(1)
            if g[:1] in "\"'" and g[-1:] == g[:1]:
                a = m.start(1) + q.start(1) + 1
                cur.append((a, a + len(g) - 2, g[1:-1]))
            else:
                if len(cur) > 1:
                    out.append(cur)
                cur = []
        if len(cur) > 1:
            out.append(cur)
    return out


def overlaps(taken, a, z):
    return any(a < tz and ta < z for ta, tz in taken)


def text_files(root, files):
    for f in files:
        if skipped(f) or BINARY.search(f):
            continue
        full = os.path.join(root, f)
        try:
            data = open(full, "rb").read()
        except (IsADirectoryError, FileNotFoundError):
            continue
        if b"\0" in data[:8000]:
            continue
        try:
            yield f, data.decode("utf-8")
        except UnicodeDecodeError:
            continue


def scan(plan):
    sc = Scanner(plan)
    edits = {}
    for f, text in text_files(plan.root, plan.files):
        kind = kind_of(f, plan.root)
        e = sc.edits(f, text, kind)
        if e:
            edits[f] = (kind, text, e)
    return sc, edits


def apply_text(text, edits):
    for a, z, new, *_ in sorted(edits, key=lambda e: -e[0]):
        text = text[:a] + new + text[z:]
    return text


def sort_go_imports(text):
    """gofmt sorts each group of an import block by path: a renamed path may change the order"""
    def block(m):
        groups = m.group(2).split("\n\n")
        out = []
        for g in groups:
            lines = g.split("\n")
            if all(re.fullmatch(r"\t(\w+ |_ |\. )?\"[^\"]+\"", ln) for ln in lines if ln):
                lines = sorted((ln for ln in lines if ln), key=lambda ln: ln.split("\"")[1]) + \
                        [ln for ln in lines if not ln]
            out.append("\n".join(lines))
        return m.group(1) + "\n\n".join(out) + m.group(3)
    return re.sub(r"(\nimport \(\n)(.*?)(\n\))", block, text, flags=re.S)


def site_subs(plan, f, text, report):
    """the named SITES and the identifier families; returns the new text"""
    for sf, line_rx, subs in SITES:
        if plan.np(sf) != plan.np(f) and sf != f:
            continue
        hit = False
        lines = text.split("\n")
        for i, ln in enumerate(lines):
            if re.search(line_rx, ln):
                for rx, rep in subs:
                    rep = re.sub(r"NEW\(([^)]+)\)", lambda m: os.path.basename(plan.np(m.group(1)))[3:]
                                 if "16-risorse" in m.group(1) else os.path.basename(plan.np(m.group(1))), rep)
                    n2 = re.sub(rx, rep, lines[i])
                    if n2 != lines[i]:
                        hit = True
                        lines[i] = n2
        if not hit:
            report.append("⚠ site not found (already done, or the line changed): %s /%s/" % (sf, line_rx))
        text = "\n".join(lines)
    if f.endswith(".go"):
        text = sort_go_imports(text)
    if f.endswith(IDENT_EXT):
        for rx, rep, where in IDENTS + plan.idents:
            if f.startswith(where):
                text = rx.sub(rep, text)
    # header guards of moved headers follow the new name
    if f.endswith(".h") and plan.map.get(f, f) != f:
        so = os.path.splitext(os.path.basename(f))[0].upper().replace("-", "_")
        sn = os.path.splitext(os.path.basename(plan.map[f]))[0].upper().replace("-", "_")
        text = re.sub(r"\b(REMOTIX_)?%s_H\b" % re.escape(so), lambda m: (m.group(1) or "") + sn + "_H", text)
    return text


MAP_SOURCE = "docs/sources/technical/ch22_map.py"
GLOSS = re.compile(r't\("[^"]*"\) \+ ')


def keep_columns(old, new):
    """a «name   # comment» line whose name changed length keeps its comment column (same line count)"""
    a, b = old.split("\n"), new.split("\n")
    if len(a) != len(b):
        return new
    for i, (x, y) in enumerate(zip(a, b)):
        mx, my = re.search(r"\S( {2,})# ", x), re.search(r"\S( {2,})# ", y)
        if x != y and mx and my and mx.end(1) != my.end(1):
            pad = max(1, len(my.group(1)) + mx.end(1) - my.end(1))
            b[i] = y[:my.start(1)] + " " * pad + y[my.end(1):]
    return "\n".join(b)


def drop_glosses(old, new):
    """the file map's t("translation") glosses an Italian file name: gone with the name (and t() with them)"""
    a, b = old.split("\n"), new.split("\n")
    if len(a) != len(b):
        return new
    b = [GLOSS.sub("", y, count=1) if x != y else y for x, y in zip(a, b)]
    out = "\n".join(b)
    if not GLOSS.search(out):
        out = re.sub(r'def t\(parole\):\n    """[^\n]*"""\n    return f"\(<i>\{parole\}</i>\) "\n\n\n', "", out)
    return out


C16_PATCH_DEF = '''
# step 2 of the English migration renamed files and folders.  The history lines of the documents keep the
# paths they were written with; this map (old → new, written by the rename) says those paths are alive.
def old_paths(percorso=os.path.join(os.path.dirname(os.path.abspath(__file__)), "%s")):
    vecchi = set()
    try:
        with open(percorso, encoding="utf-8") as f:
            for riga in f:
                if riga.strip() and not riga.startswith("#"):
                    vecchio = riga.split("\\t")[0].rstrip("/")
                    vecchi.add(vecchio)
                    vecchi.add(vecchio.rsplit("/", 1)[-1])
    except OSError:
        pass
    return vecchi


OLD_PATHS = old_paths()

''' % C16_MAP


def patch_c16(text):
    """teach C16 the old → new map: a cited path (or its name) the rename moved is alive"""
    if "OLD_PATHS" in text:
        return text, True
    m = re.search(r"^(\s*)if (\w+) in (\w+) or \2\.rsplit\(\"/\", 1\)\[-1\] in (\w+):\n", text, re.M)
    d = re.search(r"^def ", text, re.M)
    if not m or not d:
        return text, False
    ind, var = m.group(1), m.group(2)
    ins = "%sif %s.rstrip(\"/\") in OLD_PATHS or %s.rsplit(\"/\", 1)[-1] in OLD_PATHS:\n%s    continue\n" % (
        ind, var, var, ind)
    text = text[:m.start()] + ins + text[m.start():]
    d = re.search(r"^def ", text, re.M)
    return text[:d.start()] + C16_PATCH_DEF.lstrip("\n") + "\n" + text[d.start():], True


def c16_file(plan):
    for o in plan.map:
        if re.search(r"/11-c16-[^/]*\.py$", o):
            return o
    return None


# ---- commands ------------------------------------------------------------------------------------------
def cmd_plan(a):
    plan = Plan(a.root, a.moves)
    sc, edits = scan(plan)
    out = a.out or os.path.join(os.environ.get("TMPDIR", "/tmp"), "fase-c-plan")
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "moves.tsv"), "w") as fh:
        fh.write("old_path\tnew_path\n")
        for o, n in sorted(plan.map.items()):
            if o != n:
                fh.write("%s\t%s\n" % (o, n))
    kinds = collections.Counter()
    how = collections.Counter()
    with open(os.path.join(out, "references.tsv"), "w") as fh:
        fh.write("file:line\tkind\told\tnew\thow\n")
        for f, (kind, _, es) in sorted(edits.items()):
            for a_, z, new, no, old, notes in es:
                kinds[kind] += 1
                h = ",".join(n[0] for n in notes if not n[0].startswith("UNRES"))
                how[h] += 1
                fh.write("%s:%d\t%s\t%s\t%s\t%s\n" % (f, no, kind, old, new, h))
    with open(os.path.join(out, "unresolved.tsv"), "w") as fh:
        fh.write("file\tline\tkind\ttext\tcandidates\n")
        for r in sc.unresolved:
            fh.write("%s\t%d\t%s\t%s\t%s\n" % r)
    for e in plan.errors:
        print("⛔", e)
    for w in plan.warnings[:40]:
        print("⚠", w)
    print("moves: %d files move (%d tracked)" % (sum(1 for o, n in plan.map.items() if o != n), len(plan.map)))
    print("references to rewrite: %d in %d files; by kind: %s" % (
        sum(kinds.values()), len(edits), ", ".join("%s %d" % kv for kv in kinds.most_common())))
    print("resolved by context: %s" % ", ".join("%s %d" % kv for kv in how.most_common() if kv[0]))
    print("unresolved: %d (%s)" % (len(sc.unresolved), os.path.join(out, "unresolved.tsv")))
    print("tables in", out)
    return 1 if plan.errors else 0


def cmd_apply(a):
    root = os.path.abspath(a.root)
    if git(root, "status", "--porcelain", "--untracked-files=no").strip() and not a.dry_run:
        print("⛔ the copy has uncommitted changes to tracked files: start from a clean HEAD")
        return 2
    plan = Plan(root, a.moves)
    if plan.errors:
        for e in plan.errors:
            print("⛔", e)
        return 1
    for w in plan.warnings:
        print("⚠", w)
    sc, edits = scan(plan)
    report = []
    n_ref = 0
    changed = {}
    for f, text in text_files(root, plan.files):
        new = text
        if f in edits:
            new = apply_text(text, edits[f][2])
            n_ref += len(edits[f][2])
        new = site_subs(plan, f, new, report)
        if f.startswith("docs/sources/") and f.endswith(".py") and new != text:
            new = keep_columns(text, new)
        if f == MAP_SOURCE and new != text:
            new = drop_glosses(text, new)
        if f == c16_file(plan):
            new, ok = patch_c16(new)
            if not ok:
                report.append("⛔ C16: the line that accepts a cited path was not found; the old-path map is not read")
        if new != text:
            changed[f] = new
    # sites whose file is skipped or not text are reported by site_subs only when reached
    for sf, _, _ in SITES:
        if sf not in plan.map and plan.np(sf) == sf:
            report.append("⚠ site file not in the tree: " + sf)
    if a.dry_run:
        print("dry run: %d references in %d files would change; %d unresolved" % (n_ref, len(changed),
                                                                                 len(sc.unresolved)))
        for r in report:
            print(r)
        return 0
    for f, t in changed.items():
        with open(os.path.join(root, f), "w", encoding="utf-8") as fh:
            fh.write(t)
    # moves: whole folders first, top-down, then the files
    def run(*args):
        r = subprocess.run(["git", "-C", root] + list(args), capture_output=True, text=True)
        if r.returncode:
            raise SystemExit("⛔ git %s: %s" % (" ".join(args), r.stderr.strip()))
    done_dirs = []
    for d in sorted(plan.dir_rows, key=lambda x: (x.count("/"), x)):
        n = plan.dir_rows[d]
        if n == d:
            continue
        # where the folder is now (its parent may have moved already)
        cur = where(d, done_dirs)
        if cur == n or not os.path.isdir(os.path.join(root, cur)):
            continue
        if os.path.exists(os.path.join(root, n)):
            raise SystemExit("⛔ %s already exists (untracked leftovers?): git mv would put %s inside it" % (n, cur))
        os.makedirs(os.path.dirname(os.path.join(root, n)) or root, exist_ok=True)
        run("mv", "-k", cur, n)
        if os.path.isdir(os.path.join(root, cur)):          # untracked leftovers: move them by hand
            os.rename(os.path.join(root, cur), os.path.join(root, n)) if not os.path.exists(
                os.path.join(root, n)) else None
        done_dirs.append((d, n))
    nf = 0
    for o, n in sorted(plan.map.items()):
        if o == n:
            continue
        cur = where(o, done_dirs)
        if cur == n:
            continue
        os.makedirs(os.path.dirname(os.path.join(root, n)), exist_ok=True)
        run("mv", cur, n)
        nf += 1
    run("add", "-u")
    # the map for C16 and for the history readers
    c16 = c16_file(plan)
    if c16:
        mp = os.path.join(os.path.dirname(plan.map[c16]), C16_MAP)
        with open(os.path.join(root, mp), "w", encoding="utf-8") as fh:
            fh.write("# old path <TAB> new path — written by english-migration/fase_c.py (step 2 of the "
                     "English migration).\n# The history lines of the documents keep the old paths; C16 reads "
                     "this map to know they moved.\n")
            for o, n in sorted(plan.dir_rows.items()):
                if o != n:
                    fh.write("%s/\t%s/\n" % (o, n))
            for o, n in sorted(plan.map.items()):
                if o != n:
                    fh.write("%s\t%s\n" % (o, n))
        run("add", mp)
    man = {"map": plan.map, "dirs": plan.dir_rows, "unresolved": sc.unresolved}
    with open(manifest(root), "w") as fh:
        json.dump(man, fh)
    for r in report:
        print(r)
    print("✅ step 2 applied: %d references rewritten in %d files, %d folders and %d files moved, %d unresolved"
          % (n_ref, len(changed), len(done_dirs), nf, len(sc.unresolved)))
    for u in sc.unresolved[:30]:
        print("   unresolved %s:%d %s %s → %s" % u)
    return 0


def cmd_check(a):
    root = os.path.abspath(a.root)
    mf = manifest(root)
    try:
        man = json.load(open(mf))
    except OSError:
        print("⛔ no manifest (%s): apply was not run on this copy" % mf)
        return 2
    bad = 0
    now = set(tracked(root))
    old_map = man["map"]
    for o, n in old_map.items():
        if n not in now and os.path.exists(os.path.join(root, n)) is False:
            print("⛔ not moved: %s → %s" % (o, n))
            bad += 1
        if o != n and o in now:
            print("⛔ the old path is still tracked: " + o)
            bad += 1
    gone = {d for d, n in man["dirs"].items() if d != n}
    for f in now:
        for d in gone:
            if f.startswith(d + "/") and not any(f.startswith(n + "/") for n in [man["dirs"][d]]):
                print("⛔ tracked under a moved-away folder: " + f)
                bad += 1
                break
    # references: the scanner run with the OLD tree's paths over the NEW texts finds what still names them
    files_now = sorted(now)
    plan = Plan(root, a.moves, files=list(old_map))       # the old tree, as the manifest knows it
    plan.root = root
    sc = Scanner(plan)
    left = []
    back = {n: o for o, n in old_map.items()}
    for f in files_now:
        if skipped(f) or BINARY.search(f) or f.endswith("/" + C16_MAP):
            continue
        try:
            text = open(os.path.join(root, f), encoding="utf-8").read()
        except (UnicodeDecodeError, OSError):
            continue
        # the old spelling of f decides skipping (history docs are judged on links only)
        old_f = back.get(f, f)
        kind = kind_of(old_f, root) if not os.path.exists(os.path.join(root, old_f)) else kind_of(f, root)
        if kind_of(f, root) == "doc-history":
            kind = "doc-history"
        for a_, z, new, no, old, notes in sc.edits(old_f, text, kind):
            if old == new:
                continue
            left.append((f, no, kind, old, new))
    # an independent look, without the scanner's rules: every old path (with a «/») and every old file name
    # with an extension, as a whole token, in the texts that are not history
    olds = {o: n for o, n in old_map.items() if o != n}
    names = collections.defaultdict(set)
    for o, n in olds.items():
        if os.path.basename(o) != os.path.basename(n) and "." in os.path.basename(o):
            names[os.path.basename(o)].add(os.path.basename(n))
    for d, n in man["dirs"].items():
        if d != n:
            olds[d + "/"] = n + "/"
    keep_names = {os.path.basename(f) for f in now}          # a name some file still has is not stale
    alts = sorted(set(olds) | {b for b in names if b not in keep_names}, key=len, reverse=True)
    rx = re.compile(r"(?<![\w.-])(" + "|".join(map(re.escape, alts)) + r")(?![\w-]|\.\w)")
    seen = {(f, no) for f, no, *_ in left}
    for f in files_now:
        if skipped(f) or BINARY.search(f) or f.endswith("/" + C16_MAP) or HIST_DOC.match(f):
            continue
        try:
            text = open(os.path.join(root, f), encoding="utf-8").read()
        except (UnicodeDecodeError, OSError):
            continue
        for no, line in enumerate(text.split("\n"), 1):
            for m in rx.finditer(line):
                pre = line[:m.start()]
                if GITSHOW.search(pre) or re.search(r"((?:^|(?<=[\s\[\"'=()]))/?(etc|usr|var|run|lib)/|\{_?\w+\}|"
                                                   r"\$\{?(pkgdir|DESTDIR|buildroot)\}?)[^\s\"']*$", pre) \
                        or re.search(r"(fondamenta|misure|memoria|english-migration)/\S*$", pre):
                    continue
                if (f, no) in seen or line[m.start():].startswith(KEEP_OLD):
                    continue
                seen.add((f, no))
                left.append((f, no, "grep", m.group(1), olds.get(m.group(1)) or "/".join(sorted(names[m.group(1)]))))
    for f, no, kind, old, new in left[:200]:
        print("⛔ %s:%d [%s] still names %s (→ %s)" % (f, no, kind, old, new))
    if len(left) > 200:
        print("   … %d more" % (len(left) - 200))
    print("unresolved at apply time: %d" % len(man["unresolved"]))
    for u in man["unresolved"][:60]:
        print("   ⚠ unresolved %s:%d [%s] %s (%s)" % tuple(u))
    bad += len(left)
    print(("✅" if not bad else "⛔") + " check: %d moves, %d leftover references" % (
        sum(1 for o, n in old_map.items() if o != n), len(left)))
    return 1 if bad else 0


def manifest(root):
    gd = git(root, "rev-parse", "--git-dir").strip()
    return os.path.join(gd if os.path.isabs(gd) else os.path.join(root, gd), "fase-c-applied.json")


class Mapper:
    """old path names → new, in free text (outputs of the benches, strings of a binary)"""

    def __init__(self, root):
        man = json.load(open(manifest(root)))
        self.map = {o: n for o, n in man["map"].items() if o != n}
        self.back = {n: o for o, n in self.map.items()}
        pairs = {}
        for o, n in self.map.items():
            oc, nc = o.split("/"), n.split("/")
            if oc[-1] != nc[-1] and "." in oc[-1].lstrip("."):
                pairs.setdefault(oc[-1], set()).add(nc[-1])
            so, sn = os.path.splitext(oc[-1])[0], os.path.splitext(nc[-1])[0]
            if so != sn and re.match(r"^[a-z]?\d+[a-z]?\d*-", so):
                pairs.setdefault(so, set()).add(sn)
        words = {o: next(iter(n)) for o, n in pairs.items() if len(n) == 1}
        self.full = dict(self.map)
        for o, n in man["dirs"].items():
            if o != n:
                self.full[o + "/"] = n + "/"
        self.words = words
        alts = sorted(self.full, key=len, reverse=True)
        self.rx_full = re.compile(r"(?<![\w.-])(" + "|".join(map(re.escape, alts)) + r")(?:(?<=/)|(?![\w-]))") if alts else None
        alts = sorted(words, key=len, reverse=True)
        self.rx_word = re.compile(r"(?<![\w-])(" + "|".join(map(re.escape, alts)) + r")(?:(?<=/)|(?![\w-]))") if alts else None

    def text(self, t):
        if self.rx_full:
            t = self.rx_full.sub(lambda m: self.full[m.group(1)], t)
        if self.rx_word:
            t = self.rx_word.sub(lambda m: self.words[m.group(1)], t)
        return t


def cmd_map(a):
    m = Mapper(os.path.abspath(a.root))
    for line in sys.stdin:
        if a.paths:
            tab = m.back if a.back else m.map
            sys.stdout.write(re.sub(r"\S+", lambda x: tab.get(x.group(0), x.group(0)), line))
        else:
            sys.stdout.write(m.text(line))
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("plan", "apply", "check", "map"):
        s = sub.add_parser(name)
        s.add_argument("--root", required=True)
        s.add_argument("--moves", default=MOVES)
        if name == "map":
            s.add_argument("--paths", action="store_true", help="whole tokens that are tracked paths only")
            s.add_argument("--back", action="store_true", help="with --paths: new → old")
        if name == "plan":
            s.add_argument("--out")
        if name == "apply":
            s.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    return {"plan": cmd_plan, "apply": cmd_apply, "check": cmd_check, "map": cmd_map}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
