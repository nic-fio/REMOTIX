"""fase_b.py — phase B of the rename: the public, persisted and wire names (RINOMINA.md §0.4).

Phase B is a hand-written table: ten writers each fill one file of the directory TABLES
(`/media/REMOTIX/src/full-english-uscite/fase-b/<CAT>.tsv`) with rows

    old <TAB> new <TAB> kind <TAB> places <TAB> why

where `places` lists, comma-separated, every `file:line` where `old` occurs as that public thing
(`file:a-b` is a range, `file:*` every occurrence in the file).  A row whose kind is `keep` (or whose
new is `-`, empty or equal to old) renames nothing: it tells `check` why the old word legitimately
stays at its places (or everywhere, without places).  Lines starting `#!` are hazards; other `#`
lines and a header line starting `old<TAB>` are ignored.

  python3 fase_b.py merge [--tables DIR] [--root TREE] [--out FILE]
        read every table, check it, write english-migration/fase-b-tabella.tsv (deterministic).
        Errors (exit 1): malformed rows; the same old with two news in one kind; one old with two news
        meeting on one line; two olds → one new meeting in one file; casing twins whose news do not
        spell the same words; a place that does not hold the old token (stale).  Warnings: a new that
        already occurs as a whole token in a place file; style changed (kebab → snake …); places in
        history or generated files (dropped).
  python3 fase_b.py apply --root COPY [--table FILE] [--window N] [--since REV] [--dry-run]
        replace, ONLY at the table's places, the whole-token old by new.  A place whose line no longer
        holds the token is looked for in line ± N (default 5), after mapping it through
        `git diff REV` when --since is given; a place found nowhere fails the whole apply (nothing is
        written).  History (fasi/, memoria/, misure/, fondamenta/, banchi/prodotto/, *.jsonl, the
        bench reports) is never touched; the manual (docs/Technical Manual.html) only by regenerating.
  python3 fase_b.py check --root COPY [--table FILE] [--strict]
        1. structure: every file changed against HEAD has the same lines, and each changed line is its
           HEAD line with some table olds (rows listing that file) replaced by their news — nothing else;
        2. leftovers: every old (non-keep) still occurring as a whole token outside history, with the
           keep row's reason when one covers it.  Unexplained leftovers fail only with --strict.
  python3 fase_b.py new NAME [--kind K]       the new spelling of NAME (NAME itself if the table has none)
  python3 fase_b.py map --side before|after   stdin → stdout, every old (before) or new (after) mapped to
                                              one canonical spelling: output of the same program before
                                              and after phase B compares equal when only names changed

Token boundaries: a token is not glued to a letter, digit or «_»; a «-» glued to a word on the far side
extends it too (`--nome` is not inside `--nome-file`, `nome` not inside `x-nome`), except `->`, and a
«-digit» after an identifier-kind name (`n-1`).  Path kinds (path, file, dir, unit) also take «.ext»:
`pagina` is not inside `pagina.pem`, while a sentence's final dot is not part of the name.
"""
import argparse
import collections
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TREE = os.path.dirname(HERE)
TABLES = os.environ.get("FASE_B_TABLES", "/media/REMOTIX/src/full-english-uscite/fase-b")
MERGED = os.path.join(HERE, "fase-b-tabella.tsv")

# never rewritten: they record the past (or somebody else's text); readers of old data keep their maps
HISTORY = ("fasi/", "memoria/", "misure/", "fondamenta/", "banchi/prodotto/", "english-migration/",
           "licenze/", "installatore/vendor/", "LICENSE.md", "THIRD-PARTY-LICENSES",
           "packaging/debian/copyright")
HISTORY_RX = re.compile(r"(\.jsonl$|^banchi/15-suite/rapporto-[^/]*\.html$)")
# generated from sources: changed only by running the generator
GENERATED = {"docs/Technical Manual.html": "python3 docs/sources/build.py"}
BINARY = re.compile(r"\.(png|jpg|jpeg|gif|webp|ico|wasm|gz|tgz|zst|pdf|xz|bin|ttf|otf|woff2?|mp4|webm|o|so|a|"
                    r"zip|deb|rpm|iso|qcow2|raw|h264|hevc|ivf|y4m|wav|opus|pkt|f32|rcpreg|run)$", re.I)

IDENT_KINDS = {"identifier", "env", "c", "js", "py", "go", "json", "kv", "log", "field", "reason", "wire",
               "capability", "socket", "marker", "var", "key", "value", "text", "macro", "attr", "property"}
PATH_KINDS = {"path", "file", "dir", "directory", "filename", "unit", "socket-path"}
KEEP = "keep"
PLACE_RX = re.compile(r"^(.+?):(\*|\d+(?:-\d+)?)$")


def is_history(f):
    return f.startswith(HISTORY) or bool(HISTORY_RX.search(f))


def kind_words(kind):
    return set(re.split(r"[-_/ ]+", kind.lower()))


def token_rx(old, kind):
    """The regular expression of `old` as a whole token of its kind."""
    w = kind_words(kind)
    path = bool(w & PATH_KINDS)
    ident = bool(w & IDENT_KINDS) and not path
    before, after = "", ""
    if re.match(r"[A-Za-z0-9_]", old):
        before = r"(?<![A-Za-z0-9_])(?<![A-Za-z0-9_]-)(?<!--)"
        if path:
            before += r"(?<![A-Za-z0-9_]\.)"
    elif old.startswith("-"):
        before = r"(?<![A-Za-z0-9_-])"
    if re.search(r"[A-Za-z0-9_]$", old):
        after = r"(?![A-Za-z0-9_])" + (r"(?!-[A-Za-z_])" if ident else r"(?!-[A-Za-z0-9_])")
        if path:
            after += r"(?!\.[A-Za-z0-9_])"
    return re.compile(before + re.escape(old) + after)


# ═══ reading the tables ══════════════════════════════════════════════════════
class Row:
    __slots__ = ("old", "new", "kind", "places", "why", "cat", "src")

    def __init__(self, old, new, kind, places, why, cat, src):
        self.old, self.new, self.kind, self.places, self.why, self.cat, self.src = old, new, kind, places, why, cat, src

    @property
    def keep(self):
        return self.kind.lower() == KEEP or self.new in ("", "-", self.old)

    def rx(self):
        return token_rx(self.old, self.kind)


def parse_places(s):
    """'a.c:3, b.py:7-9; c.md:*' → ([(file, line or None)], [malformed pieces])"""
    out, bad = [], []
    for p in re.split(r"[,;]\s*|\s+", s.strip()):
        if not p:
            continue
        m = PLACE_RX.match(p)
        if not m:
            bad.append(p)
            continue
        f, l = m.group(1), m.group(2)
        if l == "*":
            out.append((f, None))
        elif "-" in l:
            a, b = map(int, l.split("-"))
            if b < a or b - a > 200:
                bad.append(p)
                continue
            out += [(f, i) for i in range(a, b + 1)]
        else:
            out.append((f, int(l)))
    return out, bad


def fmt_places(places):
    def key(p):
        return (p[0], -1 if p[1] is None else p[1])
    return ",".join("%s:%s" % (f, "*" if l is None else l) for f, l in sorted(set(places), key=key))


def read_tables(paths):
    rows, hazards, errors = [], [], []
    for path in paths:
        cat = os.path.splitext(os.path.basename(path))[0]
        for i, line in enumerate(open(path, encoding="utf-8").read().split("\n"), 1):
            src = "%s:%d" % (os.path.basename(path), i)
            if not line.strip():
                continue
            if line.startswith("#!"):
                hazards.append((cat, line.rstrip()))
                continue
            if line.startswith("#") or line.startswith("old\t"):
                continue
            c = line.split("\t")
            if len(c) < 4 or len(c) > 6:
                errors.append("%s: %d columns (want old, new, kind, places, why)" % (src, len(c)))
                continue
            old, new, kind, places = (x.strip() for x in c[:4])
            why = c[4].strip() if len(c) > 4 else ""
            pl, bad = parse_places(places)
            if bad:
                errors.append("%s: %s: malformed places %s" % (src, old, " ".join(bad[:5])))
            if not old or re.search(r"\s", old) or re.search(r"\s", new) or not kind:
                errors.append("%s: empty or blank-holding old/new/kind: %r → %r (%r)" % (src, old, new, kind))
                continue
            rows.append(Row(old, new, kind, pl, why, c[5].strip() if len(c) > 5 else cat, src))
    return rows, hazards, errors


def read_merged(path):
    rows, hazards, errors = read_tables([path])
    if errors:
        sys.exit("⛔ %s: %s" % (path, "\n".join(errors)))
    return rows


# ═══ words, for the twin check ═══════════════════════════════════════════════
def words(name):
    core = name.lstrip("-$").strip("_")
    core = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", core)
    return tuple(w.lower() for w in re.split(r"[-_. ]+", core) if w)


def style(name):
    core = name.lstrip("-$").strip("_")
    pre = name[:len(name) - len(name.lstrip("-"))]
    if not re.search(r"[A-Za-z]", core):
        return pre + "other"
    if "-" in core and "_" not in core:
        s = "kebab"
    elif "_" in core and "-" not in core:
        s = "snake"
    elif "-" in core or "_" in core:
        s = "mixed"
    else:
        s = "word"
    if core.isupper():
        c = "UPPER"
    elif core.islower():
        c = "lower"
    elif re.match(r"[A-Z][a-z0-9]", core):
        c = "Title"
    else:
        c = "camel"
    return "%s%s-%s" % (pre, s, c)


# ═══ the tree ═════════════════════════════════════════════════════════════════
class Tree:
    def __init__(self, root):
        self.root = root
        self.cache = {}

    def lines(self, f):
        if f not in self.cache:
            p = os.path.join(self.root, f)
            try:
                self.cache[f] = open(p, encoding="utf-8", newline="").read().split("\n")
            except (OSError, UnicodeDecodeError):
                self.cache[f] = None
        return self.cache[f]

    def tracked(self):
        out = subprocess.check_output(["git", "-C", self.root, "ls-files", "-z"]).decode().split("\0")
        return [f for f in out if f and not BINARY.search(f)]


def diff_map(root, rev, f):
    """old line number (in REV) → new line number (in the working tree), None inside a changed hunk"""
    r = subprocess.run(["git", "-C", root, "diff", "-U0", rev, "--", f], capture_output=True, text=True)
    hunks2 = []
    for m in re.finditer(r"^@@ -(\d+)(,\d+)? \+(\d+)(,\d+)? @@", r.stdout, re.M):
        a, b = int(m.group(1)), int(m.group(2)[1:]) if m.group(2) else 1
        c, d = int(m.group(3)), int(m.group(4)[1:]) if m.group(4) else 1
        hunks2.append((a, b, c, d))

    def f_(line):
        off = 0
        for a, b, c, d in hunks2:
            if b and a <= line < a + b:
                return c + (line - a) if line - a < d else None
            nxt_old = a + b if b else a + 1
            if line < nxt_old:
                break
            off = (c + d if d else c + 1) - nxt_old
        return line + off
    return f_


def locate(tree, rows, window, since=None, history_ok=False):
    """[(row, file, physical line index)], [misses]: each place of each row, found in the tree."""
    hits, misses, claimed = [], [], set()
    maps = {}
    for r in rows:
        if r.keep:
            continue
        rx = r.rx()
        for f, l in r.places:
            if not history_ok and (is_history(f) or f in GENERATED):
                continue
            lines = tree.lines(f)
            if lines is None:
                misses.append("%s: %s:%s: file missing or not text" % (r.old, f, l or "*"))
                continue
            if l is None:
                found = [i for i, s in enumerate(lines) if rx.search(s)]
                if not found:
                    misses.append("%s: %s:*: no occurrence in the file" % (r.old, f))
                hits += [(r, f, i) for i in found]
                continue
            want = l
            if since:
                if f not in maps:
                    maps[f] = diff_map(tree.root, since, f)
                want = maps[f](l) or l
            got = None
            for d in sorted(range(-window, window + 1), key=lambda x: (abs(x), x)):
                i = want - 1 + d
                if 0 <= i < len(lines) and (r.old, r.kind, f, i) not in claimed and rx.search(lines[i]):
                    got = i
                    break
            if got is None:
                misses.append("%s: %s:%d: the token is not on the line (± %d)" % (r.old, f, l, window))
                continue
            claimed.add((r.old, r.kind, f, got))
            hits.append((r, f, got))
    return hits, misses


def replace_line(s, rows):
    """every whole-token old of `rows` in s, replaced by its new at once (longest old first, no chains)"""
    spans = []
    for r in sorted(rows, key=lambda r: (-len(r.old), r.old)):
        for m in r.rx().finditer(s):
            a, b = m.span()
            if all(b <= x or a >= y for x, y, _ in spans):
                spans.append((a, b, r.new))
    out, pos = [], 0
    for a, b, n in sorted(spans):
        out += [s[pos:a], n]
        pos = b
    return "".join(out + [s[pos:]]), len(spans)


# ═══ merge ════════════════════════════════════════════════════════════════════
def merge(tables_dir, root, out, window):
    paths = sorted(os.path.join(tables_dir, f) for f in os.listdir(tables_dir) if f.endswith(".tsv"))
    rows, hazards, errors = read_tables(paths)
    warnings = []
    tree = Tree(root)

    # history and generated places are dropped
    for r in rows:
        drop = [p for p in r.places if is_history(p[0]) or p[0] in GENERATED]
        if drop:
            warnings.append("%s: %s: %d places in history/generated files dropped (%s)" %
                            (r.src, r.old, len(drop), fmt_places(drop[:3])))
            r.places = [p for p in r.places if p not in drop]

    # the same row from two writers: one row, places joined
    by = collections.OrderedDict()
    for r in rows:
        k = (r.old, r.kind, r.new)
        if k in by:
            o = by[k]
            o.places = o.places + r.places
            if r.why and r.why not in o.why:
                o.why = (o.why + " | " + r.why).strip(" |")
            if r.cat not in o.cat.split("+"):
                o.cat += "+" + r.cat
        else:
            by[k] = r
    rows = list(by.values())
    for r in rows:
        r.places = sorted(set(r.places), key=lambda p: (p[0], -1 if p[1] is None else p[1]))
    live = [r for r in rows if not r.keep]

    # 1. one old, one kind → one new
    news = collections.defaultdict(set)
    for r in live:
        news[(r.old, r.kind)].add(r.new)
    for (o, k), ns in sorted(news.items()):
        if len(ns) > 1:
            errors.append("%s (%s) has two news: %s" % (o, k, ", ".join(sorted(ns))))

    # 2. one old with two news (different kinds) on the same line
    at = collections.defaultdict(set)
    for r in live:
        for f, l in r.places:
            at[(r.old, f, l)].add(r.new)
    for (o, f, l), ns in sorted(at.items(), key=lambda x: (x[0][0], x[0][1], x[0][2] or 0)):
        if len(ns) > 1:
            errors.append("%s at %s:%s becomes %s: which one?" % (o, f, l or "*", " and ".join(sorted(ns))))

    # 3. two olds → one new, meeting in one file
    files_of = collections.defaultdict(lambda: collections.defaultdict(set))
    for r in live:
        for f, _ in r.places:
            files_of[r.new][f].add(r.old)
    for n in sorted(files_of):
        for f in sorted(files_of[n]):
            if len(files_of[n][f]) > 1:
                errors.append("%s and %s both become %s in %s" %
                              (" ".join(sorted(files_of[n][f])[:-1]), sorted(files_of[n][f])[-1], n, f))

    # chains: a new that is another row's old in the same file
    olds_in = collections.defaultdict(set)
    for r in live:
        for f, _ in r.places:
            olds_in[f].add(r.old)
    for r in live:
        fs = sorted({f for f, _ in r.places if r.new in olds_in[f]})
        if fs:
            warnings.append("%s → %s: %s is also renamed in %s (a swap or a chain: one pass, no double rename)"
                            % (r.old, r.new, r.new, ", ".join(fs[:3])))

    # 4. casing twins: same words, different spelling → their news spell the same words
    twins = collections.defaultdict(list)
    for r in live:
        twins[words(r.old)].append(r)
    for w, rs in sorted(twins.items()):
        spellings = {r.old for r in rs}
        if len(spellings) < 2:
            continue
        nw = collections.defaultdict(list)
        for r in rs:
            if "not a twin" in r.why.lower():
                continue
            nw[words(r.new)].append(r)
        if len(nw) > 1:
            errors.append("casing twins disagree: " + "; ".join(
                "%s → %s" % (r.old, r.new) for x in sorted(nw) for r in nw[x]))
    for r in live:
        if style(r.old) != style(r.new) and "style" not in r.why.lower():
            warnings.append("%s → %s: style %s becomes %s" % (r.old, r.new, style(r.old), style(r.new)))

    # 5. stale places, and a new already in a place file
    hits, misses = locate(tree, live, window)
    errors += ["stale: " + m for m in misses]
    for r in live:
        rx = token_rx(r.new, r.kind)
        for f in sorted({f for f, _ in r.places}):
            lines = tree.lines(f)
            if not lines:
                continue
            ls = [i + 1 for i, s in enumerate(lines) if rx.search(s)]
            if ls:
                warnings.append("%s → %s: %s already occurs in %s:%s" %
                                (r.old, r.new, r.new, f, ",".join(map(str, ls[:5])) + ("…" if len(ls) > 5 else "")))

    # the merged table
    rows.sort(key=lambda r: (r.old.lower().lstrip("-"), r.old, r.kind, r.new))
    out_lines = ["# fase-b-tabella.tsv — written by english-migration/fase_b.py merge from %s/*.tsv; do not edit"
                 % tables_dir.rstrip("/"),
                 "old\tnew\tkind\tplaces\twhy\tcat"]
    for r in rows:
        out_lines.append("\t".join([r.old, r.new, r.kind, fmt_places(r.places),
                                    re.sub(r"[\t\n]", " ", r.why), r.cat]))
    for cat, h in sorted(hazards, key=lambda x: x[0]):
        out_lines.append("#! [%s] %s" % (cat, h[2:].strip()))
    if out:
        with open(out, "w", encoding="utf-8") as fh:
            fh.write("\n".join(out_lines) + "\n")

    for w in sorted(set(warnings)):
        print("⚠ " + w)
    for e in errors:
        print("⛔ " + e)
    print("%s merge: %d tables, %d rows (%d renames, %d keep), %d places, %d hazards; %d warnings, %d errors%s" %
          ("✅" if not errors else "⛔", len(paths), len(rows), len(live), len(rows) - len(live),
           sum(len(r.places) for r in rows), len(hazards), len(set(warnings)), len(errors),
           ("; written " + os.path.relpath(out, root)) if out else ""))
    return 1 if errors else 0


# ═══ apply ════════════════════════════════════════════════════════════════════
def apply(root, table, window, since, dry):
    rows = read_merged(table)
    tree = Tree(root)
    live = [r for r in rows if not r.keep]
    hits, misses = locate(tree, live, window, since)
    if misses:
        for m in misses:
            print("⛔ " + m)
        print("⛔ apply: %d places not found — the table is stale; nothing written" % len(misses))
        return 1
    per = collections.defaultdict(lambda: collections.defaultdict(list))
    for r, f, i in hits:
        per[f][i].append(r)
    total, files = 0, 0
    for f in sorted(per):
        lines = list(tree.lines(f))
        n = 0
        for i, rs in per[f].items():
            lines[i], k = replace_line(lines[i], rs)
            n += k
        if n:
            files += 1
            total += n
            if not dry:
                with open(os.path.join(root, f), "w", encoding="utf-8", newline="") as fh:
                    fh.write("\n".join(lines))
        if dry:
            print("  %5d  %s" % (n, f))
    regen = sorted(g for g, cmd in GENERATED.items()
                   if any(f.startswith(os.path.dirname(g) + "/sources/") for f in per))
    for g in regen:
        print("ℹ %s: its sources changed — regenerate it: %s" % (g, GENERATED[g]))
    print("✅ apply%s: %d replacements in %d files (%d places)" %
          (" (dry run, nothing written)" if dry else "", total, files, len(hits)))
    return 0


# ═══ check ════════════════════════════════════════════════════════════════════
def line_ok(a, b, rows):
    """b is a with some whole-token olds of rows replaced by their news (any subset)"""
    spans = []
    for r in sorted(rows, key=lambda r: (-len(r.old), r.old)):
        for m in r.rx().finditer(a):
            x, y = m.span()
            if all(y <= p or x >= q for p, q, _ in spans):
                spans.append((x, y, r))
    pat, pos = [], 0
    for x, y, r in sorted(spans, key=lambda s: s[0]):
        pat.append(re.escape(a[pos:x]))
        pat.append("(?:%s|%s)" % (re.escape(r.old), re.escape(r.new)))
        pos = y
    pat.append(re.escape(a[pos:]))
    return re.fullmatch("".join(pat), b, re.S) is not None


def check(root, table, strict):
    rows = read_merged(table)
    live = [r for r in rows if not r.keep]
    by_file = collections.defaultdict(list)
    for r in live:
        for f in {f for f, _ in r.places}:
            by_file[f].append(r)
    bad = 0
    changed = [c for c in subprocess.check_output(["git", "-C", root, "diff", "--name-only", "-z"]).decode().split("\0") if c]
    for f in changed:
        if f in GENERATED:
            continue                    # regenerated: its sources are checked
        if is_history(f):
            print("⛔ %s: a history file changed" % f)
            bad += 1
            continue
        old = subprocess.run(["git", "-C", root, "show", "HEAD:" + f], capture_output=True).stdout
        try:
            a = old.decode("utf-8").split("\n")
            b = open(os.path.join(root, f), encoding="utf-8", newline="").read().split("\n")
        except (OSError, UnicodeDecodeError):
            print("⛔ %s: not text, or deleted" % f)
            bad += 1
            continue
        if len(a) != len(b):
            print("⛔ %s: %d lines before, %d after (phase B adds and removes no line)" % (f, len(a), len(b)))
            bad += 1
            continue
        for i, (x, y) in enumerate(zip(a, b)):
            if x != y and not line_ok(x, y, by_file.get(f, [])):
                print("⛔ %s:%d: more than the table's names changed\n     before: %s\n     after:  %s" %
                      (f, i + 1, x.strip()[:160], y.strip()[:160]))
                bad += 1
                break
    print("%s structure: %d changed files, %d with changes outside the table" %
          ("✅" if not bad else "⛔", len(changed), bad))

    # leftovers
    tree = Tree(root)
    keeps = collections.defaultdict(list)
    for r in rows:
        if r.keep:
            keeps[r.old].append(r)
    files = [f for f in tree.tracked() if not is_history(f) and f not in GENERATED]
    texts = {}
    for f in files:
        ls = tree.lines(f)
        if ls is not None:
            texts[f] = ls
    seen, unexplained, kept = set(), 0, 0
    report = []
    for r in sorted(live, key=lambda r: r.old):
        if r.old in seen:
            continue
        seen.add(r.old)
        rx = r.rx()
        occ = []
        for f, ls in texts.items():
            if r.old not in "\n".join(ls):
                continue
            occ += [(f, i + 1) for i, s in enumerate(ls) if rx.search(s)]
        if not occ:
            continue
        why = {}
        for k in keeps.get(r.old, []):
            for f, l in occ:
                if not k.places or any(pf == f and (pl is None or abs(pl - l) <= 5) for pf, pl in k.places):
                    why.setdefault((f, l), k.why or "keep")
        left = [p for p in occ if p not in why]
        kept += len(occ) - len(left)
        unexplained += len(left)
        if left:
            report.append("⚠ %s (→ %s): %d left: %s%s" % (r.old, r.new, len(left),
                          ", ".join("%s:%d" % p for p in left[:6]), " …" if len(left) > 6 else ""))
        for p, w in sorted(why.items())[:3]:
            report.append("  %s kept at %s:%d — %s" % (r.old, p[0], p[1], w))
    print("\n".join(report))
    print("%s leftovers: %d unexplained occurrences of old names outside history, %d kept by a keep row" %
          ("✅" if not unexplained else "⚠", unexplained, kept))
    return 1 if bad or (strict and unexplained) else 0


# ═══ helpers for the proof script ════════════════════════════════════════════
def canon_rows(rows):
    """old → canonical, new → canonical: the new when an old has one new, «old» when it has several"""
    news = collections.defaultdict(set)
    for r in rows:
        if not r.keep:
            news[r.old].add(r.new)
    return {o: (next(iter(n)) if len(n) == 1 else "«%s»" % o) for o, n in news.items()}, news


def map_text(text, rows, side):
    canon, news = canon_rows(rows)
    pairs = []
    for r in rows:
        if r.keep:
            continue
        if side == "before":
            pairs.append(Row(r.old, canon[r.old], r.kind, [], "", "", ""))
        elif len(news[r.old]) > 1:
            pairs.append(Row(r.new, canon[r.old], r.kind, [], "", "", ""))
    uniq = {(p.old, p.kind): p for p in pairs if p.old != p.new}
    return "\n".join(replace_line(s, list(uniq.values()))[0] for s in text.split("\n"))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("merge")
    m.add_argument("--tables", default=TABLES)
    m.add_argument("--root", default=TREE)
    m.add_argument("--out", default=MERGED)
    m.add_argument("--no-write", action="store_true")
    m.add_argument("--window", type=int, default=5)
    a_ = sub.add_parser("apply")
    a_.add_argument("--root", required=True)
    a_.add_argument("--table", default=MERGED)
    a_.add_argument("--window", type=int, default=5)
    a_.add_argument("--since")
    a_.add_argument("--dry-run", action="store_true")
    c = sub.add_parser("check")
    c.add_argument("--root", required=True)
    c.add_argument("--table", default=MERGED)
    c.add_argument("--strict", action="store_true")
    n = sub.add_parser("new")
    n.add_argument("name")
    n.add_argument("--kind")
    n.add_argument("--table", default=MERGED)
    p = sub.add_parser("map")
    p.add_argument("--side", choices=["before", "after"], required=True)
    p.add_argument("--table", default=MERGED)
    a = ap.parse_args()
    if a.cmd == "merge":
        return merge(a.tables, os.path.abspath(a.root), None if a.no_write else a.out, a.window)
    if a.cmd == "apply":
        return apply(os.path.abspath(a.root), a.table, a.window, a.since, a.dry_run)
    if a.cmd == "check":
        return check(os.path.abspath(a.root), a.table, a.strict)
    rows = read_merged(a.table) if os.path.exists(a.table) else []
    if a.cmd == "new":
        ns = sorted({r.new for r in rows if r.old == a.name and not r.keep and (not a.kind or r.kind == a.kind)})
        if len(ns) > 1:
            sys.exit("⛔ %s has several news (%s): give --kind" % (a.name, ", ".join(ns)))
        print(ns[0] if ns else a.name)
        return 0
    sys.stdout.write(map_text(sys.stdin.read(), rows, a.side))
    return 0


if __name__ == "__main__":
    sys.exit(main())
