#!/usr/bin/env python3
"""rinomina2 — the safe mechanical rename of REMOTIX's Italian identifiers (DECISIONI.md §10.38).

  rinomina2.py plan  [--root DIR]          build the table from the names DEFINED in code, check every
                                           collision, write rinomina2-plan.json and RINOMINA.md
  rinomina2.py apply --root DIR            apply the plan to DIR (a scratch copy or the final tree)
  rinomina2.py verify --root DIR --before DIR
                                           compare «…» quotes and protected regions before/after
  rinomina2.py externals                   (re)build esterni-c-*.txt in the build container

Rules (RINOMINA.md says why):
 1. The table holds only names that occur in CODE regions of project sources (C, Go, Python, shell,
    Makefile, page JS/CSS/ids), plus REMOTIX_* variables, long options and the data names listed in
    dati.tsv.  Words that occur only in comments, strings or documents never enter it.
 2. Code regions: every identifier in the table changes.  Comments and string literals: only whole
    tokens that are in the table, never inside «…», never a path component (`x/`, `/x`, `x.c`), never
    in an Italian sentence kept on purpose (protetti.tsv keep-strings) or an Italian sentence at all.
    Markdown: only inside code spans and fenced blocks whose info string names a language; never in a
    span that holds «, an Italian sentence or a log line.  Data/history/vendor/generated files: never.
 3. One mapping for the whole program (old → new).  Two old names may not land on one new name in a
    scope where both occur, and a new name may not hit a name that stays, a keyword, a libc/glib/…
    symbol, a well-known environment variable.  The loser of a collision is NOT renamed until
    interi.tsv (manual, with a comment) or sinonimi.tsv (an alternative English word) resolves it.
The output is deterministic: same tree and same tables give the same plan, byte for byte.
"""
import argparse
import collections
import fnmatch
import json
import keyword
import os
import re
import subprocess
import sys
import builtins

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lessico  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_ROOT = os.path.dirname(HERE)


# ═══ the vocabulary (same rules as rinomina.py) ═════════════════════════════
def read_tsv(name, ncols=2):
    p = os.path.join(HERE, name)
    out = []
    if not os.path.exists(p):
        return out
    for line in open(p, encoding="utf-8"):
        if not line.strip() or line.startswith("#"):
            continue
        cols = line.rstrip("\n").split("\t")
        out.append((cols + [""] * ncols)[:max(ncols, len(cols))])
    return out


VOC = {}
for f in sorted(os.listdir(HERE)):
    if f.startswith("glossario-") and f.endswith(".tsv"):
        for it, en, *_ in read_tsv(f, 3):
            if it and en:
                VOC[it] = en
for it, en, *_ in read_tsv("voc-correzioni.tsv"):
    if en == "=":
        VOC.pop(it, None)
    elif it and en:
        VOC[it] = en

DEBOLI = set("""
di il la da si va le ha al lo io ne se fa ma ci ed ad po li un su gr
del per via media come note piano solo pure metro regime male cure manifesto diverse confine finale
prime costa concede coincide unite residue confuse mandate morse computer deduce conclude decorative
opera grave tale crude terra alto largo viola nero rossi sole era vale vita otto salvo mira tara viva
sana sane una uno due tre prove mette dire dare stare cade padre eta sta est ore mil pan peg fond cas
tent salt ass imp luc par fam rap tit liv pil dip tel dis cal ric toll cons mis cong cart inn sal punt
rig ins ing fig pun dat mas tut prem flu rin ina tac rim quest prof lung cod tot fab lar det usc ist
camp reg bloc chi con dove vista fine data mente sei comprende darla hai farsi mondo ho ad lui sera
diverse cui mia mani dai sped nato grande fai mano alla dei mai casa ciao vive luc imp ma col cosa
dal viva bene ha primo mio verde dice qui che prima nome serve tutti massimo pronto gia gr sono della
dell ci regime pero sara inn sal dare punt
""".split()) - set("""
nome prima dice qui che primo mio verde tutti massimo pronto gia sono della dell dal col cosa bene
alla dei mai casa grande nato mano fai cui mia mani sera lui pero sara serve
""".split())
DEBOLI -= {"metro"}          # 10 Oct ruling: metro → yardstick, a strong word now

# test accounts on the test machines (prova, prova2, provanic…, provadec…, provanr…): never renamed
INTOCCABILI_RX = re.compile(r"^(prova\d*|provanic\w*|provadec\w*|provanr\w*|prova\d+\w*)$")
INTOCCABILI = {l.strip() for l in open(os.path.join(HERE, "intoccabili.txt"), encoding="utf-8")
               if l.strip() and not l.startswith("#")} if os.path.exists(os.path.join(HERE, "intoccabili.txt")) else set()
INTERI = {a: b for a, b, *_ in read_tsv("interi.tsv", 3) if a and b}
# a row whose new name is the old one means «do not rename» (AltLeft, altKey, aria-pressed)
INTERI_WHY = {a: w for a, b, w, *_ in read_tsv("interi.tsv", 3) if a and a == b}
SINONIMI = collections.defaultdict(list)          # italian word → alternative English words, in order
for it, alts, *_ in read_tsv("sinonimi.tsv", 3):
    SINONIMI[it] = [a for a in alts.split(",") if a]

PARTE = re.compile(r"[A-Z]?[a-z]+|[A-Z]+(?![a-z])|[0-9]+")


def forte(p):
    p = p.lower()
    return p in VOC and VOC[p] != p and p not in DEBOLI


def rendi(en, orig, camel_dopo):
    parole = en.split("_")
    if orig.isupper() and len(orig) > 1:
        return [w.upper() for w in parole], "_"
    if orig[0].isupper():
        return ["".join(w.capitalize() for w in parole)], ""
    if camel_dopo:
        return [parole[0] + "".join(w.capitalize() for w in parole[1:])], ""
    return parole, None


def traduci(tok, voc=None):
    """The English form of one name, word by word (rinomina.py's rule, with a vocabulary override)."""
    voc = voc or VOC
    if tok in INTOCCABILI or INTOCCABILI_RX.match(tok):
        return tok
    segmenti = re.split(r"([_-]+)", tok)
    parti = [PARTE.findall(s) for s in segmenti[::2]]
    if not any((p.lower() in voc and voc[p.lower()] != p.lower() and p.lower() not in DEBOLI)
               for ps in parti for p in ps):
        return tok
    out = []
    for i, s in enumerate(segmenti):
        if i % 2:
            out.append(s)
            continue
        ps = PARTE.findall(s)
        if "".join(ps) != s:
            out.append(s)
            continue
        sep_ctx = "-" if "-" in tok and "_" not in tok else "_"
        nuovo = []
        for j, p in enumerate(ps):
            low = p.lower()
            if low in voc and voc[low] != low:
                en = voc[low]
                if en == "-":
                    continue
                camel = len(ps) > 1 and not (p.isupper() and len(p) > 1)
                parole, giunto = rendi(en, p, camel and j > 0 or (camel and len(ps) > 1 and p[0].islower()))
                if giunto is None:
                    nuovo.append(sep_ctx.join(parole))
                elif giunto == "_":
                    nuovo.append((sep_ctx if sep_ctx == "-" else "_").join(parole))
                else:
                    nuovo.append(parole[0])
            else:
                nuovo.append(p)
        out.append("".join(nuovo))
    r = "".join(out)
    r = re.sub(r"([_-])\1+", r"\1", r)
    r = re.sub(r"^[_-]+|[_-]+$", "", r) if not tok.startswith("_") else r
    if tok.startswith("_") and not r.startswith("_"):
        r = "_" + r
    if not r or r[0].isdigit():
        return tok
    if tok[0].isupper() and r[0].islower():
        r = r[0].upper() + r[1:]
    if tok[0].islower() and r[0].isupper() and not r.isupper():
        r = r[0].lower() + r[1:]
    return r


def parole_it(tok):
    """The Italian words of a name that the vocabulary translates (lowercase)."""
    return [p.lower() for s in re.split(r"[_-]+", tok) for p in PARTE.findall(s)
            if p.lower() in VOC and VOC[p.lower()] != p.lower()]


# ═══ files: which language, which are never touched ═════════════════════════
SKIP_BUILTIN = [
    ("*/vendor/*", "third-party code"), ("vendor/*", "third-party code"),
    ("src/protocolli/*", "third-party protocol XML"), ("*_spv.h", "generated SPIR-V"),
    ("*.jsonl", "results / history"), ("*.log", "results / history"), ("*.err", "results / history"),
    ("misure/*", "measured results"), ("memoria/*", "project memory, history"),
    ("anteprime/*", "previews, generated"), ("licenze/*", "licence texts"),
    ("english-migration/*", "the migration's own tables (Italian on purpose)"),
    ("fondamenta/*", "history: the foundations (v0/v1 experiments), not built"),
    ("banchi/prodotto/*", "product snapshots"), ("*rapporto*.html", "bench report, result"),
    ("LICENSE.md", "licence text"), ("THIRD-PARTY-LICENSES", "licence texts"),
    ("go.sum", "generated"), ("*/go.sum", "generated"),
    ("docs/sources/technical/ch24_glossary.py", "the glossary of the Italian names: rewritten by hand after the rename"),
]
BINARY = re.compile(r"\.(png|jpg|jpeg|gif|webp|ico|wasm|gz|tgz|zst|pdf|xz|bin|ttf|otf|woff2?|sha256|mp4|webm|"
                    r"svg|o|so|a|zip|deb|rpm|iso|qcow2|raw|h264|hevc|ivf|y4m|wav|opus)$", re.I)


def load_protected():
    skips, keeps, gens = [], collections.defaultdict(list), []
    for row in read_tsv("protetti.tsv", 4):
        kind = row[0]
        if kind == "skip-glob":
            skips.append((row[1], row[2]))
        elif kind == "keep":
            keeps[row[1]].append((row[2], row[3] or row[2], row[4] if len(row) > 4 else ""))
        elif kind == "generated":
            gens.append((row[1], row[2]))
    return skips, keeps, gens


def skipped(path, skips):
    for g, why in SKIP_BUILTIN + skips:
        if fnmatch.fnmatch(path, g):
            return why
    if BINARY.search(path):
        return "binary"
    return None


def language(path):
    b = os.path.basename(path)
    ext = b.rsplit(".", 1)[-1].lower() if "." in b else ""
    if ext in ("c", "h", "comp", "glsl"):
        return "c"
    if ext == "go":
        return "go"
    if ext == "py":
        return "py"
    if ext in ("sh", "bash") or b in ("PKGBUILD", "postinst", "postrm", "prerm") or \
            b.endswith((".postinst", ".postrm", ".prerm", ".install")):
        return "sh"
    if b in ("Makefile", "rules") or ext == "mk":
        return "make"
    if ext in ("html", "htm"):
        return "html"
    if ext in ("js", "mjs"):
        return "js"
    if ext == "css":
        return "css"
    if ext == "md":
        return "md"
    if ext == "json":
        return "json"
    if b.startswith("Contenitore") or ext in ("service", "conf", "tmpfiles", "desktop", "spec", "yml", "yaml",
                                              "ks", "preseed", "user-data", "te", "fc", "if", "cil", "ufw",
                                              "xml", "gitignore", "gitattributes", "rules", "arch", "fedora",
                                              "suse", "pam", "txt", "tsv", "lintian-overrides", "mod") \
            or b in ("control", "copyright", "format", "utenti-negati", "README") or "." not in b:
        return "conf"
    return None


# ═══ tokens ══════════════════════════════════════════════════════════════════
IDENT = re.compile(r"(?<![A-Za-z0-9_$])[A-Za-z_][A-Za-z0-9_]*(?![A-Za-z0-9_])")
# in prose, strings and shell words a name may be kebab-case (an option, a subcommand)
WORD = re.compile(r"(?<![A-Za-z0-9_]-)(?:(?<![A-Za-z0-9_\\])|(?<=\\[ntrfvab0e]))[A-Za-z_][A-Za-z0-9_]*(?:-[A-Za-z0-9_]+)*(?![A-Za-z0-9_])")
# ⇧ "\naltro": a token may start right after an escape letter (\n, \t …) inside a literal
EXT = ("c|h|go|py|sh|md|html|js|mjs|css|json|jsonl|log|txt|tsv|conf|service|spec|rules|pam|desktop|comp|o|so|"
       "mod|sum|png|svg|tgz|xml|yml|yaml|ks|wasm|run|deb|rpm|toml|err|out|csv|pdf|mp4|tmpfiles|install|cil|te|fc")
PATHISH_AFTER = re.compile(r"(/|\.(%s)(?![A-Za-z0-9_]))" % EXT)
ITALIAN_STOP = set("""il lo la gli le una uno di del della dei delle degli che non con sono questo questa
quando anche perché già gia più piu nel nella nei sul sulla alla ai dal dalla fra
è ogni tutto tutti cosa così cosi quindi però pero ancora""".split())     # no per/come/se/ma: English too
LOGLIKE = re.compile(r"^\s*(\[[^\]]*\]|\d\d:\d\d|\d{4}-\d\d-\d\d|[⭐⛔📄⚠✅❌🟢🔴]|[A-Z][A-Z ]{6,}:)")


SHELLWORD = re.compile(r"(?P<dol>\$\{?[#!]?)(?P<v>[A-Za-z_][A-Za-z0-9_]*)|(?P<w>%s)" % WORD.pattern)
REPO_NAMES = set()     # every path component of the tree (dirs and files), filled by plan()
PATHRUN = re.compile(r"[A-Za-z0-9_.~/+-]")


def is_path(seg, s, e):
    """Is the token seg[s:e] part of a path?  x/… …/x x.c — when the run has a slash or an extension and
    either starts at the root (/, ./, ~/) or names something that exists in the tree."""
    a, b = s, e
    while a > 0 and PATHRUN.match(seg[a - 1]):
        a -= 1
    while b < len(seg) and PATHRUN.match(seg[b]):
        b += 1
    run = seg[a:b].strip(".")
    tok = seg[s:e]
    if re.match(r"\.(%s)(?![A-Za-z0-9_])" % EXT, seg[e:]):
        return True        # x.c, sessione.log, appunti.txt: a file name, renamed with the files (step 2)
    if "/" not in run:
        return False
    if run.startswith("~/") or re.match(r"^/(media|mnt|root|srv|run/media|home/nicfio)/", run) or "/REMOTIX/" in run:
        return True     # a real place on the test machines or the laptop (/media/REMOTIX/…): never renamed
    # a product path (/var/lib/remotix/…, /etc/remotix/…) is renamed like the code that builds it with
    # filepath.Join/os.path.join pieces, so the two spellings stay one; its components that name files
    # of the tree wait for step 2 like every other path
    # a relative path: only the components that name something in the tree belong to step 2;
    # anything else in the run (a Go selector after a package path, a variable) is a name like any other
    return tok in REPO_NAMES


PIECE = re.compile(r"[^\"'`,;{}()\[\]|=\n\\]+")


def prose_pieces(seg):
    """Intervals of an Italian sentence inside a literal, between quotes, commas, braces, '='."""
    return [(m.start(), m.end()) for m in PIECE.finditer(seg) if italian_prose(m.group(0))]


def italian_prose(s):
    # a kebab or snake compound (d13-delta-alla-misura-nuova) is ONE word, a name, not a sentence
    # a word glued to a dot is a member, not prose (REMOTIX.tocco.perche, R.giro.quando.size); and the
    # same stop word twice (perche: perche) is a key and its value, not a sentence
    w = [m.group(0) for m in re.finditer(r"(?<!\w)(?<!\w\.)[A-Za-zàèéìòù][\wàèéìòù'-]*(?!\w|\.\w)", s.lower())]
    n = len({x for x in w if x in ITALIAN_STOP})
    return n >= 2 or (n >= 1 and len(w) >= 3) or bool(re.search(r"[àèìòù]", s))


def regions(path, text, lang):
    if lang in ("conf",):
        return lessico.lex_sh(text)
    if lang == "json":
        return lessico._merge([(m.start(), m.end(), "string") for m in
                               re.finditer(r'"(?:\\.|[^"\\])*"', text)], len(text))
    return lessico.LEXERS[lang](text)


def guillemet_spans(text):
    return [(m.start(), m.end()) for m in re.finditer(r"«[^«»]*»", text)]


# ═══ externals: names the programs get from outside ════════════════════════
C_KEYWORDS = set("""auto break case char const continue default do double else enum extern float for goto if inline
int long register restrict return short signed sizeof static struct switch typedef union unsigned void volatile
while _Bool _Complex _Imaginary _Alignas _Alignof _Atomic _Generic _Noreturn _Static_assert _Thread_local bool true
false alignas alignof nullptr static_assert thread_local typeof typeof_unqual constexpr asm main NULL errno
stdin stdout stderr assert offsetof""".split())
GO_KEYWORDS = set("""break default func interface select case defer go map struct chan else goto package switch
const fallthrough if range type continue for import return var bool byte complex64 complex128 error float32
float64 int int8 int16 int32 int64 rune string uint uint8 uint16 uint32 uint64 uintptr true false iota nil
append cap clear close complex copy delete imag len make max min new panic print println real recover any
comparable init main""".split())
PY_KEYWORDS = set(keyword.kwlist) | {"self", "cls"}     # builtins: only when used in scope (a clash)
JS_KEYWORDS = set("""break case catch class const continue debugger default delete do else export extends finally
for function if import in instanceof new return super switch this throw try typeof var void while with yield let
static enum await implements package protected interface private public null true false undefined NaN Infinity
arguments eval""".split())
# window properties: only a TOP-LEVEL function/var/let/const of a classic script would replace them
JS_GLOBALS = set("""window document navigator location history screen status name length parent top
self frames opener closed close open print alert confirm prompt event origin performance console crypto fetch
setTimeout setInterval requestAnimationFrame localStorage sessionStorage Image Audio Map Set WeakMap Promise Date
Math JSON Object Array String Number Boolean Error Symbol""".split())
SH_KEYWORDS = set("""if then else elif fi case esac for while until do done in function select time coproc
alias bg bind break builtin caller cd command compgen complete continue declare dirs disown echo enable eval exec
exit export false fc fg getopts hash help history jobs kill let local logout mapfile popd printf pushd pwd read
readarray readonly return set shift shopt source suspend test times trap true type typeset ulimit umask unalias
unset wait""".split())
SH_RESERVED = set("if then else elif fi case esac for while until do done in function select time coproc".split())
SPECIAL_ENV = set("""PATH HOME USER SHELL TERM DISPLAY WAYLAND_DISPLAY LANG LANGUAGE PWD OLDPWD IFS PS1 PS2 PS4 UID EUID
HOSTNAME HOSTTYPE TMPDIR EDITOR PAGER MAIL LOGNAME SECONDS RANDOM LINENO COLUMNS LINES OPTARG OPTIND REPLY
FUNCNAME PIPESTATUS BASHPID GROUPS DIRSTACK SHLVL PPID TZ CC CFLAGS LDFLAGS CPPFLAGS LDLIBS DESTDIR PREFIX
MAKEFLAGS SOURCE_DATE_EPOCH XDG_RUNTIME_DIR XDG_SESSION_TYPE XDG_CURRENT_DESKTOP XDG_CONFIG_HOME XDG_DATA_HOME
XDG_CACHE_HOME DBUS_SESSION_BUS_ADDRESS GOPATH GOROOT GOFLAGS GOCACHE GOOS GOARCH NAME VERSION ARCH TIME
TIMEFORMAT HISTFILE ENV BASH_ENV CDPATH""".split())


def load_externals():
    def rd(n):
        p = os.path.join(HERE, n)
        return set(open(p).read().split()) if os.path.exists(p) else set()
    # macros: every macro of the system headers the sources include; glob: their file-scope names
    # (functions, variables, typedefs, tags, enum constants) — struct fields are not there on purpose
    return rd("esterni-c-macro.txt"), rd("esterni-c-glob.txt")


# ═══ the scan ════════════════════════════════════════════════════════════════
class FileInfo:
    __slots__ = ("path", "lang", "regs", "code", "code_global", "data", "defs", "includes", "imports",
                 "sources", "text", "funcs", "member", "massign", "gopkg", "datalit", "cssown", "attrdefs",
                 "webplat", "envs", "opts", "pynames")

    def __init__(self, path, lang):
        self.path, self.lang = path, lang
        self.code = collections.Counter()      # identifier tokens in code regions
        self.code_global = set()               # C: tokens met at brace depth 0 / in a header
        self.data = collections.Counter()      # whole data-like string literals: tokens
        self.defs = set()                      # tokens this file contributes to the table
        self.includes, self.imports, self.sources = [], [], []
        self.funcs = set()                     # shell functions
        self.member = collections.Counter()    # tokens after . or -> (a separate namespace)
        self.massign = set()                   # members assigned here (self.x = …, obj.x = …): defined
        self.gopkg = None
        self.datalit = collections.Counter()   # whole data-like string literals ("cert.stato", "MANCA")
        self.cssown = set()                    # CSS names of ours: classes, ids, custom properties, keyframes
        self.attrdefs = set()                  # HTML: values of id/class/for/name/data-* attributes
        self.webplat = set()                   # names this file shows to be the Web platform's
        self.envs, self.opts = set(), set()    # REMOTIX_*/RX_* variables, options a parser of ours defines
        self.pynames = None                    # Python: the names of the syntax tree (None: not parsed)


def git_files(root):
    out = subprocess.check_output(["git", "-C", root, "ls-files", "-z"]).decode("utf-8", "surrogateescape")
    return sorted(f for f in out.split("\0") if f)


DATA_LIKE = re.compile(r"^[A-Za-z_][A-Za-z0-9_.:=/-]*$")


OPTION_DEF = [
    r"(?:^|[\s(|])--(%s)(?:=\*?)?\s*[)|]",                               # shell case:  --x-y) | --x-y=*)
    r"\[\[?\s*\"?\$\{?\w+\}?\"?\s*==?\s*[\"']?--(%s)\b",                   # shell test:  [ "$1" = --x-y ]
    r"add_argument\([^)]*?[\"']--(%s)[\"']",                                # argparse
    r"(?:strn?cmp|streq|uguale|eq)\s*\([^;]*?\"--(%s)[\"=]",                # C comparisons
    r"[!=]=\s*[\"']--(%s)[\"']|[\"']--(%s)[\"']\s*[!=]=",                     # == "--x-y"
    r"\bcase\s+[^:]*?[\"`]--(%s)[\"`]",                                    # Go/C/JS case "--x-y":
    r"\bin\s*[\(\[{][^)\]}]*?[\"']--(%s)[\"']",                             # Python: in ("--x-y", …)
    r"\{\s*\"(%s)\"\s*,\s*(?:no_argument|required_argument|optional_argument|[01])",   # getopt_long
    r"flag\.\w+\(\s*(?:&\w+\s*,\s*)?\"(%s)\"",                                     # Go flag
    r"[\"']--(%s)[\"']\s*:",                                                # option tables {"--x-y": …}
]
_OPTNAME = r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*"
OPTION_DEF_RX = [re.compile(r.replace("%s", _OPTNAME), re.M) for r in OPTION_DEF]


def option_defs(text, lang):
    out = set()
    for rx in OPTION_DEF_RX:
        for m in rx.finditer(text):
            out |= {g for g in m.groups() if g}
    return out


def py_names(text):
    """Every name a Python module binds or reads: variables, functions, classes, parameters, imports,
    global/nonlocal, and the keywords of calls to its own functions.  None if it does not parse."""
    import ast
    try:
        tree = ast.parse(text)
    except (SyntaxError, ValueError):
        return None
    out, defs_args, kw = set(), set(), set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Name):
            out.add(n.id)
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            out.add(n.name)
        elif isinstance(n, ast.arg):
            out.add(n.arg)
            defs_args.add(n.arg)
        elif isinstance(n, ast.alias):
            out.add((n.asname or n.name).split(".")[0])
        elif isinstance(n, (ast.Global, ast.Nonlocal)):
            out.update(n.names)
        elif isinstance(n, ast.keyword) and n.arg:
            kw.add(n.arg)
        elif isinstance(n, ast.ExceptHandler) and n.name:
            out.add(n.name)
        elif isinstance(n, (ast.MatchAs, ast.MatchStar)) and getattr(n, "name", None):
            out.add(n.name)
    return out | (kw & defs_args)


SH_CMD = re.compile(r"(?:^|[;&|(`{]|\$\(|\b(?:then|do|else|elif|if|while|until|!)\s)\s*(?:\w+=\S*\s+)*([A-Za-z_][\w.-]*)", re.M)


def sh_commands(fi):
    """Words in command position of a shell file: a function of ours may not take one of these names."""
    return set(SH_CMD.findall(code_only(fi)))


def code_only(fi):
    """The file's text with every non-code region blanked (same length): for regexes over code."""
    t = fi.text
    out = []
    for a, b, k in fi.regs:
        out.append(t[a:b] if k == "code" else re.sub(r"[^\n]", " ", t[a:b]))
    return "".join(out)


# ═══ the Web platform's names: never ours, never renamed ══════════════════════
def load_web_externals():
    """esterni-web.txt: KeyboardEvent code/key values, event and DOM/WebCodecs/WebTransport/WebAudio
    members, protocol parameters.  Plus a prefix rule: aria-* attributes and their ariaX reflections."""
    p = os.path.join(HERE, "esterni-web.txt")
    out = set()
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            out.update(line.split("#")[0].split())
    return out


WEB_PREFIX = re.compile(r"^(aria-[a-z]+|aria[A-Z]\w*)$")
EVENT_PARAM = re.compile(r"""addEventListener\(\s*["'][\w:-]+["']\s*,\s*(?:async\s+)?(?:function\s*\w*\s*\(\s*(\w+)|\(\s*(\w+)\s*[,)]|(\w+)\s*=>)"""
                         r"""|\bon[a-z]+\s*=\s*(?:async\s+)?(?:function\s*\w*\s*\(\s*(\w+)|\(\s*(\w+)\s*\)\s*=>|(\w+)\s*=>)""")


def web_platform_names(fi):
    """Names a page shows, mechanically, to be the platform's:
      - every member of an event object (the parameter of an event listener, or ev/evt/event);
      - every string compared with .code / .key, or a case label of a switch on .code / .key;
      - every attribute name passed to set/get/has/remove/toggleAttribute (data-* excluded: ours)."""
    code = code_only(fi)
    out = set()
    params = {"ev", "evt", "event"}
    for m in EVENT_PARAM.finditer(code):
        params |= {g for g in m.groups() if g}
    if params:
        rx = re.compile(r"(?<![\w$.])(?:%s)\s*\.\s*([A-Za-z_]\w*)" % "|".join(sorted(map(re.escape, params))))
        out |= set(rx.findall(code))
    t = fi.text
    out |= set(re.findall(r"""\.(?:code|key)\s*[!=]==?\s*["']([\w-]+)["']""", t))
    out |= set(re.findall(r"""["']([\w-]+)["']\s*[!=]==?\s*[\w.$]+\.(?:code|key)\b""", t))
    for m in re.finditer(r"switch\s*\([^)]*\.(?:code|key)\s*\)\s*\{", t):
        depth, i = 1, m.end()
        while i < len(t) and depth:
            depth += {"{": 1, "}": -1}.get(t[i], 0)
            i += 1
        out |= set(re.findall(r"""\bcase\s+["']([\w-]+)["']\s*:""", t[m.end():i]))
    for m in re.finditer(r"""\b(?:set|get|has|remove|toggle)Attribute(?:NS|Node)?\(\s*(?:[^,()"']+,\s*)?["']([\w:-]+)["']""", t):
        if not m.group(1).startswith("data-"):
            out.add(m.group(1))
    return out


# a method of ours renamed onto one of these would change which interfaces the type satisfies
GO_IFACE_METHODS = set("""String Error GoString Format Write Read Close Seek Len Less Swap Unwrap Is As
MarshalJSON UnmarshalJSON MarshalText UnmarshalText MarshalBinary UnmarshalBinary ReadFrom WriteTo
WriteString ReadByte WriteByte ReadRune Scan Value Init Update View ServeHTTP Lock Unlock RLock RUnlock
Wait Done Err Deadline Next Reset Size Sum BlockSize Get Set""".split())


def go_types(fis):
    """The structs of one Go package: their fields and methods, the embedding between them, and the
    names that are ONLY fields or methods (their plain occurrences are declarations or composite-literal
    keys; everything else is after a dot)."""
    fields, methods = collections.defaultdict(set), collections.defaultdict(set)
    embeds, ext_embed = collections.defaultdict(set), set()
    decl, keyuse, plain = collections.Counter(), collections.Counter(), collections.Counter()
    for fi in fis:
        code = code_only(fi)
        for x, n in fi.code.items():
            plain[x] += n
        spans = []
        for m in re.finditer(r"\b([A-Za-z_]\w*)(?:\[[^\]\n]*\])?\s+struct\s*\{", code):
            if any(x <= m.start() < y for x, y in spans):
                continue                       # a struct nested in a struct: its fields go to the outer one
            T = m.group(1)
            depth, i = 1, m.end()
            while i < len(code) and depth:
                depth += {"{": 1, "}": -1}.get(code[i], 0)
                i += 1
            spans.append((m.start(), i))
            body = code[m.end():i - 1]
            for line in body.split("\n"):
                line = line.strip().rstrip(";")
                if not line or line in ("}",):
                    continue
                e = re.match(r"^\*?([A-Za-z_][\w.]*)(?:\[[^\]]*\])?$", line)
                if e:
                    (ext_embed.add(T) if "." in e.group(1) else embeds[T].add(e.group(1)))
                    continue
                f = re.match(r"^([A-Za-z_]\w*(?:\s*,\s*[A-Za-z_]\w*)*)\s+\S", line)
                if f:
                    for x in re.split(r"\s*,\s*", f.group(1)):
                        fields[T].add(x)
                        decl[x] += 1
        for m in re.finditer(r"\bfunc\s*\(\s*(?:\w+\s+)?\*?\s*([A-Za-z_]\w*)(?:\[[^\]]*\])?\s*\)\s*([A-Za-z_]\w*)", code):
            methods[m.group(1)].add(m.group(2))
            decl[m.group(2)] += 1
        for line in code.split("\n"):
            if re.match(r"^\s*(case|default)\b", line):
                continue
            for m in re.finditer(r"(?<![\w.])([A-Za-z_]\w*)\s*:(?!=)", line):
                keyuse[m.group(1)] += 1
    field_only = {x for x in decl if plain[x] - decl[x] - keyuse[x] <= 0}
    # embedding joins structs: a field of one is reachable through the other
    types = sorted(set(fields) | set(methods))
    parent = {T: T for T in types}

    def find(x):
        while parent[x] != x:
            x = parent[x]
        return x
    for T in types:
        for E in embeds.get(T, ()):
            if E in parent:
                parent[find(E)] = find(T)
    comps = collections.defaultdict(set)
    for T in types:
        comps[find(T)].add(T)
    return {"fields": fields, "methods": methods, "ext_embed": ext_embed, "field_only": field_only,
            "components": [comps[k] for k in sorted(comps)]}


def is_member(seg, start):
    pre = seg[max(0, start - 4):start]
    return bool(re.search(r"(\.|->)\s*$", pre)) and not re.search(r"\.\.\.\s*$", pre) \
        and not re.search(r"[0-9]\.\s*$", pre)


def strip_quotes(s):
    m = re.match(r"^(?:[rbuRBUfF]{0,2})(\"\"\"|'''|\"|'|`)(.*)\1$", s, re.S)
    return m.group(2) if m else s


SH_DEF = [re.compile(r"(?m)^\s*(?:function\s+)?([A-Za-z_][A-Za-z0-9_-]*)\s*\(\)\s*\{?"),
          re.compile(r"(?<![A-Za-z0-9_$./-])([A-Za-z_][A-Za-z0-9_]*)(?:\[[^\]]*\])?\+?="),   # not --x=
          re.compile(r"\b(?:local|declare|typeset|export|readonly|read|unset)\s+(?:-[A-Za-z]+\s+)*([A-Za-z_][A-Za-z0-9_ ]*)"),
          re.compile(r"\bfor\s+([A-Za-z_][A-Za-z0-9_]*)\s+in\b"),
          re.compile(r"\$\{?#?!?([A-Za-z_][A-Za-z0-9_]*)"),
          re.compile(r"(?m)^\s*\(?([A-Za-z_][A-Za-z0-9_|*-]*)\)\s"),       # case labels  word|word)
          ]
MAKE_DEF = [re.compile(r"(?m)^([A-Za-z_][A-Za-z0-9_]*)\s*(?:[:?+]?=|::=)"),
            re.compile(r"\$[({]([A-Za-z_][A-Za-z0-9_]*)[)}:]"),
            re.compile(r"(?m)^([A-Za-z_][A-Za-z0-9_.-]*)\s*:(?!=)")]
OPTION = re.compile(r"(?<![A-Za-z0-9_-])--([a-z][a-z0-9]*(?:-[a-z0-9]+)*)(?![A-Za-z0-9_])")
ENVVAR = re.compile(r"(?<![A-Za-z0-9_])(REMOTIX_[A-Z0-9_]+|RX_[A-Z0-9_]+)(?![A-Za-z0-9_])")


def scan(root, files, skips):
    infos, skipped_files = {}, {}
    for f in files:
        why = skipped(f, skips)
        lang = language(f)
        if why or lang is None:
            skipped_files[f] = why or "not a source"
            continue
        p = os.path.join(root, f)
        if os.path.islink(p) or not os.path.isfile(p):
            continue
        try:
            text = open(p, encoding="utf-8").read()
        except UnicodeDecodeError:
            skipped_files[f] = "not UTF-8"
            continue
        fi = FileInfo(f, lang)
        fi.regs = regions(f, text, lang)
        fi.text = text
        infos[f] = fi
        if lang in ("md", "conf", "json"):
            # documents and data: they are rewritten, but never add names
            for a, b, k in fi.regs:
                if k == "string":
                    s = strip_quotes(text[a:b])
                    if DATA_LIKE.match(s):
                        fi.datalit[s] += 1
                        for m in WORD.finditer(s):
                            fi.data[m.group(0)] += 1
            continue
        depth = 0
        pdepth = 0
        css_text = []
        for a, b, k in fi.regs:
            seg = text[a:b]
            if k == "code-css" or (k == "code" and lang == "css"):
                css_text.append(seg)        # property names and values are the platform's: see css_names
                continue
            if lang in ("css", "html"):
                css_text.append(" ")
            if k == "code":
                rx = WORD if lang in ("sh", "make") else IDENT
                if lang in ("py", "js", "html"):
                    fi.massign |= set(re.findall(r"\.([A-Za-z_][A-Za-z0-9_]*)\s*=(?!=)", seg))
                for m in rx.finditer(seg):
                    tok = m.group(0)
                    if lang in ("c", "go", "py", "js", "html") and is_member(seg, m.start()):
                        fi.member[tok] += 1
                        continue
                    fi.code[tok] += 1
                    if lang == "c":
                        # brace and paren depth at this token: file-scope names only
                        pre = seg[:m.start()]
                        d = depth + pre.count("{") - pre.count("}")
                        pd = pdepth + pre.count("(") - pre.count(")")
                        if d <= 0 and pd <= 0:
                            fi.code_global.add(tok)
                if lang == "c":
                    depth += seg.count("{") - seg.count("}")
                    pdepth += seg.count("(") - seg.count(")")
                    if depth < 0:
                        depth = 0
                    if pdepth < 0:
                        pdepth = 0
                if lang in ("sh", "make", "conf"):
                    if lang == "sh":
                        for m in SH_DEF[0].finditer(seg):
                            fi.funcs.add(m.group(1))
                    for rx2 in (SH_DEF if lang == "sh" else MAKE_DEF):
                        for m in rx2.finditer(seg):
                            for w in re.split(r"[\s|]+", m.group(1)):
                                if w and w != "*" and re.match(r"^[A-Za-z_][A-Za-z0-9_-]*$", w):
                                    fi.defs.add(w)
                elif lang in ("c", "go", "py", "js", "css"):
                    pass
            elif k == "string":
                if lang in ("js", "html") and seg.startswith("`"):
                    # a template literal that is JS source (the page's worker shell): the keys of its
                    # object literals are members of ours, read back as s.key on the other side
                    fi.massign |= set(re.findall(r"(?m)(?:[{,]|\*/|^)\s*([A-Za-z_][A-Za-z0-9_]*)\s*:(?!:)", seg))
                s = strip_quotes(seg)
                if DATA_LIKE.match(s) and not f.startswith("docs/"):     # the manual's strings are text
                    fi.datalit[s] += 1
                    for m in WORD.finditer(s):
                        fi.data[m.group(0)] += 1
                if lang == "sh":
                    for m in re.finditer(r"\$\{?#?!?([A-Za-z_][A-Za-z0-9_]*)", seg):
                        fi.defs.add(m.group(1))
                if lang == "c":
                    m = re.match(r'^"([^"<>]+\.h)"$', seg)
                    if m:
                        fi.includes.append(m.group(1))
            elif k == "comment" and lang == "html":
                pass
        if lang in ("c", "go", "py", "js", "css", "html"):
            # a member used but never declared, assigned or met as a plain name is someone else's
            # (event.altKey, tea.WithAltScreen, st.st_mtime): it is not a name of ours
            fi.defs |= set(fi.code) | fi.massign
        if lang == "py":
            fi.pynames = py_names(text)
            # argparse: --x-y gives args.x_y, a member nobody assigns by hand
            fi.massign |= {o.replace("-", "_") for o in option_defs(text, lang)}
            fi.massign |= set(re.findall(r"dest\s*=\s*[\"']([A-Za-z_][A-Za-z0-9_]*)[\"']", text))
            fi.defs |= fi.massign
        if lang == "go":
            m = re.search(r"(?m)^package\s+([A-Za-z_][A-Za-z0-9_]*)", text)
            fi.gopkg = m.group(1) if m else None
        if lang == "html":
            # ids and classes of the page are names the page defines
            for m in re.finditer(r"""\b(?:id|class|for|name|data-[a-z-]+)\s*=\s*["']([^"']+)["']""", text):
                for w in m.group(1).split():
                    if re.match(r"^%s$" % lessico.CSS_IDENT, w):
                        fi.defs.add(w)
                        fi.attrdefs.add(w)
            for m in re.finditer(r"<[A-Za-z][^>]*>", text):
                for d in re.findall(r"\s(data-%s)\s*=" % lessico.CSS_IDENT, m.group(0)):
                    fi.defs.add(d)
                    fi.attrdefs.add(d)
        if lang in ("css", "html"):
            # only the CSS names that are ours (selectors, custom properties, keyframes): a property, a
            # value, a pseudo-class or [aria-pressed] is the platform's.  The token never ends with '-':
            # `a.mancati--` in the page's JavaScript is a name and an operator, not a class
            fi.cssown, plat = lessico.css_names("".join(css_text))
            fi.defs |= fi.cssown
            fi.webplat |= plat
        if lang in ("html", "js"):
            fi.webplat |= web_platform_names(fi)
        if lang == "py":
            for m in re.finditer(r"(?m)^\s*(?:from\s+([A-Za-z_][A-Za-z0-9_.]*)\s+import|import\s+([A-Za-z_][A-Za-z0-9_., ]*))", text):
                mods = (m.group(1) or m.group(2) or "")
                for x in re.split(r"[,\s]+", mods):
                    if x and x != "as":
                        fi.imports.append(x.split(".")[0])
        if lang == "sh":
            for m in re.finditer(r"(?m)(?:^|[;&|]\s*)(?:source|\.)\s+[\"']?([^\s\"';]+)", text):
                fi.sources.append(os.path.basename(m.group(1)))
        if lang == "go":
            pass
        # options: only those a parser of ours defines or compares (--non-interactive is zypper's)
        for o in option_defs(text, lang):
            fi.defs.add(o)
            fi.opts.add(o)
        for m in ENVVAR.finditer(text):
            fi.defs.add(m.group(1))
            fi.envs.add(m.group(1))
    return infos, skipped_files


# ═══ scopes ══════════════════════════════════════════════════════════════════
def build_scopes(infos):
    """A scope is a set of files whose names can meet.  Returns {scope_name: [files]}."""
    scopes = {}
    by_dir = collections.defaultdict(list)
    for f, fi in infos.items():
        by_dir[(os.path.dirname(f), fi.lang)].append(f)
    headers = {}
    for f in infos:
        if f.endswith(".h"):
            headers.setdefault(os.path.basename(f), []).append(f)

    def resolve_h(f, inc):
        d = os.path.dirname(f)
        cand = os.path.normpath(os.path.join(d, inc))
        if cand in infos:
            return cand
        for h in headers.get(os.path.basename(inc), []):
            return h
        return None
    for f, fi in infos.items():
        if fi.lang == "c":
            seen, todo = {f}, [f]
            while todo:
                x = todo.pop()
                for inc in infos[x].includes:
                    h = resolve_h(x, inc)
                    if h and h not in seen:
                        seen.add(h)
                        todo.append(h)
            scopes["tu:" + f] = sorted(seen)
        elif fi.lang == "py":
            stems = {}
            d = os.path.dirname(f)
            for g in infos:
                if g.endswith(".py"):
                    stems.setdefault(os.path.basename(g)[:-3], []).append(g)
            seen, todo = {f}, [f]
            while todo:
                x = todo.pop()
                for mod in infos[x].imports:
                    for g in stems.get(mod, []):
                        if g not in seen and (os.path.dirname(g) == os.path.dirname(x) or len(stems[mod]) == 1):
                            seen.add(g)
                            todo.append(g)
            scopes["py:" + f] = sorted(seen)
        elif fi.lang == "sh":
            seen = {f}
            for s in fi.sources:
                for g in infos:
                    if os.path.basename(g) == s and infos[g].lang == "sh":
                        seen.add(g)
            scopes["sh:" + f] = sorted(seen)
        else:
            scopes["file:" + f] = [f]
    for (d, lang), fs in by_dir.items():
        if lang == "go":
            scopes["go-package:" + d] = sorted(fs)
        if lang == "c":
            scopes["c-program:" + d] = sorted(fs)
    return scopes


# ═══ the plan ════════════════════════════════════════════════════════════════
def load_dati():
    """dati.tsv: data names (wire strings, JSON keys, log areas, ...) that enter the table.
    columns: old, new (empty = vocabulary), kind, comment."""
    out = {}
    for row in read_tsv("dati.tsv", 5):
        if row[0]:
            files = [x for x in row[3].split(",") if x] if len(row) > 3 else []
            out[row[0]] = (row[1] or traduci(row[0]), row[2], files, row[4] if len(row) > 4 else "")
    return out


# Off: proved harmful on the copy (10 Oct) — 16-risorse.py builds the same record from keyword arguments
# (renamed, code) and from string keys (frozen), and its self-certification broke.  The registers'
# readers of OLD data are a listed risk instead (RINOMINA.md §2.2).
FREEZE_REGISTERS = False


def frozen_registers(root, files):
    """Keys and short values of the recorded registers (*.jsonl in the tree).  Benches read history with
    them, so in files that handle .jsonl their string literals stay as they are (RINOMINA.md §risks)."""
    keys = set()

    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                keys.add(k)
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
        elif isinstance(o, str) and len(o) <= 40 and re.match(r"^[A-Za-z_][A-Za-z0-9_-]*$", o):
            keys.add(o)
    for f in files:
        if f.endswith(".jsonl") and not f.startswith(("fondamenta/", "english-migration/")):
            try:
                for line in open(os.path.join(root, f), encoding="utf-8"):
                    try:
                        walk(json.loads(line))
                    except ValueError:
                        pass
            except (OSError, UnicodeDecodeError):
                pass
    return {k for k in keys if traduci(k) != k}


def local_modules(infos):
    """Python modules imported by name: renaming the name without the file breaks the import."""
    stems = {os.path.basename(f)[:-3] for f in infos if f.endswith(".py")}
    used = set()
    for fi in infos.values():
        for m in fi.imports:
            if m in stems:
                used.add(m)
    return used


def plan(root):
    skips, keeps, gens = load_protected()
    files = git_files(root)
    for f in files:
        REPO_NAMES.update(f.split("/"))
    infos, skipped_files = scan(root, files, skips)
    c_macro, c_ident = load_externals()
    dati = load_dati()
    sh_funcs, js_top = set(), set()
    for fi in infos.values():
        sh_funcs |= fi.funcs
        if fi.lang in ("html", "js"):
            # only var and function become properties of window; let/const/class may shadow them
            js_top |= set(re.findall(r"(?m)^(?:async\s+)?(?:function\*?|var)\s+([A-Za-z_$][\w$]*)", fi.text))
    pymods = local_modules(infos)
    # Go struct fields without a json tag, in files that use encoding/json: the key is the field name
    go_untagged = set()
    for fi in infos.values():
        if fi.lang == "go" and "encoding/json" in fi.text:
            for body in re.findall(r"struct\s*\{([^{}]*)\}", fi.text):
                for line in body.split("\n"):
                    line = line.split("//")[0]
                    m = re.match(r"^\s*([A-Z]\w*(?:\s*,\s*[A-Z]\w*)*)\s+\S", line)
                    if m and "`" not in line:
                        go_untagged |= set(re.split(r"\s*,\s*", m.group(1)))
    gopkgs = {fi.gopkg for fi in infos.values() if fi.gopkg and fi.gopkg != "main"}
    gopkgs |= {g + "_test" for g in gopkgs}
    # per language: the names that are ours (plain or assigned); a member outside this set is external
    lang_own = collections.defaultdict(set)
    for fi in infos.values():
        L = "js" if fi.lang == "html" else fi.lang
        lang_own[L] |= set(fi.code) | fi.massign
        lang_own["css"] |= fi.cssown
    scopes = build_scopes(infos)
    web_ext = load_web_externals()
    for fi in infos.values():
        web_ext |= fi.webplat

    # 1. the candidates: names defined in code
    origin = collections.defaultdict(set)        # name → languages that define it
    files_of = collections.defaultdict(set)
    for f, fi in infos.items():
        for t in fi.defs:
            origin[t].add(fi.lang)
            files_of[t].add(f)
    excluded = {}
    go_field_only, go_methods = set(), set()
    M = {}
    for name in sorted(origin):
        langs = origin[name]
        if name in INTOCCABILI:
            continue
        if INTERI.get(name) == name:
            if traduci(name) != name:
                excluded[name] = "interi.tsv: kept as it is (%s)" % INTERI_WHY.get(name, "decided by hand")
            continue
        new = INTERI.get(name) or (dati[name][0] if name in dati and dati[name][0] else None) or traduci(name)
        if new == name:
            continue
        if (name in web_ext or WEB_PREFIX.match(name)) and name not in INTERI:
            excluded[name] = "a Web platform name (esterni-web.txt, or shown by a page: event member, " \
                             ".code/.key value, attribute)"
            continue
        if "c" in langs and (name in c_macro or name in c_ident) and name not in INTERI:
            excluded[name] = "defined outside the project (C headers)"
            continue
        if "go" in langs and name in gopkgs:
            excluded[name] = "a Go package name: renamed with its directory (step 2)"
            continue
        if "py" in langs and name in pymods:
            excluded[name] = "a Python module name: renamed with its file (step 2)"
            continue
        if name.startswith("remotix-") or name.startswith("remotix_"):
            excluded[name] = "a product/binary/package name: renamed with the files (step 2)"
            continue
        M[name] = new

    # 2. where names meet: every scope, by role (RINOMINA.md §3).  A role is a namespace: a new name
    # collides only with a name of the same role in the same scope.
    #   plain   identifiers (C: the translation unit, Go: the package, Python: the module and its local
    #           imports, page: the file; shell/make: the variables, functions and labels DEFINED)
    #   member  a member of ours after . or -> (C, Python, page); someone else's member never collides
    #   sel     the page's ids, classes, custom properties, keyframes, data-* attributes
    #   field   Go: the fields and methods of one struct, with the structs embedding it or embedded
    # plus the data literals ("cert.stato"): two literals of one file (or of one product program)
    # may not become one literal, compared whole, not word by word.
    roles = {}
    for s, fs in scopes.items():
        kind = s.split(":", 1)[0]
        L = infos[fs[0]].lang
        r = collections.defaultdict(set)
        if kind == "c-program":
            for f in fs:
                r["plain"] |= infos[f].code_global
        elif kind == "go-package":
            # the package: every identifier of its files (fields and methods only: see go-struct below)
            for f in fs:
                r["plain"] |= set(infos[f].code)
        elif L in ("sh", "make") or (kind == "file" and L == "conf"):
            for f in fs:
                r["plain"] |= {d for d in infos[f].defs if d not in infos[f].opts and d not in infos[f].envs}
                r["cmd"] |= sh_commands(infos[f])
                r["funcs"] |= infos[f].funcs
        elif L in ("c", "py", "js", "html", "css"):
            own = set()
            for f in fs:
                fi = infos[f]
                # Python: the names the parser binds or reads (a keyword argument of someone else's
                # function, env= of subprocess.run, is not a variable of ours)
                r["plain"] |= fi.pynames if fi.pynames is not None else set(fi.code)
                r["member"] |= set(fi.member)
                own |= set(fi.code) | fi.massign
                r["sel"] |= fi.cssown | fi.attrdefs
            r["member"] &= own
        roles[s] = {k: v for k, v in r.items() if v}
    # Go: a name that is only a field or a method (declared in a struct or as a method, used as a
    # composite-literal key, else always after a dot) lives in its struct, not in the package
    for d, gfs in sorted({(os.path.dirname(f)): [g for g in infos if infos[g].lang == "go" and
                                                os.path.dirname(g) == os.path.dirname(f)]
                          for f in infos if infos[f].lang == "go"}.items()):
        types = go_types([infos[f] for f in sorted(gfs)])
        pkg = "go-package:" + d
        if pkg in roles:
            roles[pkg]["plain"] = roles[pkg].get("plain", set()) - types["field_only"]
        members_pkg = set()
        for f in gfs:
            members_pkg |= set(infos[f].member)
        for i, comp in enumerate(types["components"]):
            names = set()
            for T in comp:
                names |= types["fields"].get(T, set()) | types["methods"].get(T, set())
            if any(T in types["ext_embed"] for T in comp):
                names |= members_pkg        # an embedded type of another package: its members are unknown
            roles["go-struct:%s:%s" % (d, "+".join(sorted(comp)[:3]))] = {"field": names}
        go_field_only.update(types["field_only"])
        for ms in types["methods"].values():
            go_methods.update(ms)
    # global namespaces: environment variables and options are read by name across programs
    # environment variables are read by name anywhere: one namespace; options belong to the parser that
    # defines them (the file), and a caller passes them to that program only
    envs = set()
    for f, fi in sorted(infos.items()):
        envs |= fi.envs
        if fi.opts:
            roles["options:" + f] = {"plain": set(fi.opts)}
    roles["env:all"] = {"plain": envs}
    # data literals: per file, and per product program (the programs that exchange them)
    lit_scopes = {}
    for f, fi in infos.items():
        if fi.datalit:
            lit_scopes["lit:" + f] = set(fi.datalit)
    for name, pre in (("lit:server", ("src/", "banchi/rcp/", "packaging/")),
                      ("lit:installer", ("installatore/", "packaging/"))):
        lit_scopes[name] = set()
        for f, fi in infos.items():
            if f.startswith(pre):
                lit_scopes[name] |= set(fi.datalit)
    lit_toks = {}
    for lits in lit_scopes.values():
        for L in lits:
            if L not in lit_toks:
                lit_toks[L] = [m.group(0) for m in WORD.finditer(L)]
    where = collections.defaultdict(list)          # name → [(scope, role)]
    for s in sorted(roles):
        for role, R in sorted(roles[s].items()):
            if role in ("cmd", "funcs"):
                continue
            for x in R:
                where[x].append((s, role))
    lit_where = collections.defaultdict(set)       # name → {(scope, literal)}
    for s, lits in lit_scopes.items():
        for L in lits:
            for x in set(lit_toks[L]):
                lit_where[x].add((s, L))

    occ = collections.Counter()
    for fi in infos.values():
        for t, n in fi.code.items():
            occ[t] += n
        for t, n in fi.data.items():
            occ[t] += n
        for t, n in fi.member.items():
            occ[t] += n

    # twins: kebab/snake spellings of one option must stay twins
    def twin(n):
        return n.replace("-", "_") if "-" in n else (n.replace("_", "-") if "_" in n and n.islower() else None)

    kept = {}            # name → reason it is not renamed (unresolved)
    resolved_by = {}     # name → how its final name was chosen
    for n in M:
        resolved_by[n] = "interi.tsv" if n in INTERI else ("dati.tsv" if n in dati else "vocabulary")

    def forbidden(name, new):
        langs = origin.get(name, set())
        if "c" in langs:
            if new in C_KEYWORDS or new in c_macro:
                return "C keyword or system macro"
            glob = any(name in (roles[s].get("plain", ())) for s in roles if s.startswith("c-program:"))
            if glob and new in c_ident:
                return "C global onto a libc/glib/system symbol"
        if "go" in langs and new in GO_KEYWORDS:
            return "Go keyword or predeclared name"
        if name in go_methods and new in GO_IFACE_METHODS:
            return "Go method onto a well-known interface method (String, Error, Write…)"
        if "py" in langs and new in PY_KEYWORDS:
            return "Python keyword or builtin"
        if ("js" in langs or "html" in langs) and new in JS_KEYWORDS:
            return "JavaScript reserved word"
        if name in js_top and new in JS_GLOBALS:
            return "top-level page name onto a browser global"
        if ("sh" in langs or "make" in langs) and new in SH_RESERVED:
            return "shell reserved word"
        if name in sh_funcs and new in SH_KEYWORDS:
            return "shell function onto a builtin"
        if (langs & {"sh", "make", "conf"}) and new in SPECIAL_ENV:
            return "well-known environment variable"
        if WEB_PREFIX.match(new):
            return "an ARIA name of the platform"
        return None

    def try_alternatives(name):
        """A different English for a name that lost a collision: sinonimi.tsv, word by word."""
        words = parole_it(name)
        for w in words:
            for alt in SINONIMI.get(w, []):
                voc = dict(VOC)
                voc[w] = alt
                cand = traduci(name, voc)
                if cand != name:
                    yield cand, "sinonimi.tsv: %s → %s" % (w, alt)

    def ren_lit(L, final, extra=None):
        out = []
        for x in lit_toks[L]:
            out.append((extra or {}).get(x) or final.get(x, x))
        return out

    def free(n, cand, final):
        """May n become cand?  cand must be absent from every scope and role where n is."""
        for s, role in where.get(n, ()):
            R = roles[s][role]
            if cand in R:
                return False
            if any(final.get(x) == cand for x in R if x != n and x in final):
                return False
        for s, L in lit_where.get(n, ()):
            r = WORD.sub(lambda m: cand if m.group(0) == n else final.get(m.group(0), m.group(0)), L)
            if r != L and r in lit_scopes[s]:
                return False
        if n in sh_funcs:
            for s in scopes:
                if s.startswith("sh:") and n in roles.get(s, {}).get("funcs", ()) and cand in roles[s].get("cmd", ()):
                    return False
        return True

    def find_conflicts(final):
        inv = {}
        for s in sorted(roles):
            for role, R in sorted(roles[s].items()):
                if role in ("cmd", "funcs"):
                    continue
                olds = sorted(x for x in R if x in final)
                by_new = collections.defaultdict(list)
                for x in olds:
                    by_new[final[x]].append(x)
                for new, group in by_new.items():
                    if len(group) > 1:
                        inv.setdefault((new, tuple(group)), []).append(s)
                for x in olds:
                    new = final[x]
                    if new not in final and new in R:
                        inv.setdefault((new, (x,), "clash"), []).append(s)
            # a shell function may not take the name of a command the file runs
            for x in sorted(roles[s].get("funcs", set()) & set(final)):
                new = final[x]
                if new not in final and new in roles[s].get("cmd", ()):
                    inv.setdefault((new, (x,), "clash"), []).append(s)
        for s in sorted(lit_scopes):
            lits = lit_scopes[s]
            groups = collections.defaultdict(list)
            for L in lits:
                toks = lit_toks[L]
                if any(x in final for x in toks):
                    groups[WORD.sub(lambda m: final.get(m.group(0), m.group(0)), L)].append(L)
            for r, ch in groups.items():
                same = sorted(set(ch) | ({r} if r in lits and r not in ch else set()))
                if len(same) < 2:
                    continue
                for i in range(len(same)):
                    for j in range(i + 1, len(same)):
                        A, B = lit_toks[same[i]], lit_toks[same[j]]
                        pairs = list(zip(A, B)) if len(A) == len(B) else []
                        for x, y in pairs:
                            if x == y:
                                continue
                            if x in final and y in final and final[x] == final[y]:
                                inv.setdefault((final[x], tuple(sorted((x, y)))), []).append(s)
                            elif x in final and y not in final:
                                inv.setdefault((final[x], (x,), "clash"), []).append(s)
                            elif y in final and x not in final:
                                inv.setdefault((final[y], (y,), "clash"), []).append(s)
                        if not pairs:
                            for x in sorted(set(A) | set(B)):
                                if x in final:
                                    inv.setdefault((final[x], (x,), "clash"), []).append(s)
        return inv

    dataset_pairs = set()
    for fi in infos.values():
        if fi.lang in ("html", "js"):
            for c in set(re.findall(r"\bdataset\s*\.\s*([A-Za-z_]\w*)", fi.text)) | \
                    set(re.findall(r"""\bdataset\s*\[\s*["']([A-Za-z_]\w*)["']\s*\]""", fi.text)):
                a = "data-" + re.sub(r"[A-Z]", lambda m: "-" + m.group(0).lower(), c)
                if c in origin or a in origin or a in dati:
                    dataset_pairs.add((c, a))
    dataset_pairs = sorted(dataset_pairs)
    pinned = set()        # names whose English a twin decided: never moved by a collision
    collisions_log = []
    for it in range(50):
        changed = False
        final = {n: v for n, v in M.items() if n not in kept}
        # forbidden targets
        for n in sorted(final):
            why = forbidden(n, final[n])
            if why:
                alt = next((a for a in try_alternatives(n) if not forbidden(n, a[0])), None)
                if alt and n not in INTERI and n not in pinned:
                    M[n], resolved_by[n] = alt[0], alt[1] + " (target was: %s)" % why
                else:
                    kept[n] = "target %s is a %s" % (final[n], why)
                    collisions_log.append({"kind": "forbidden", "old": n, "new": final[n], "why": why})
                changed = True
        if changed:
            continue
        final = {n: v for n, v in M.items() if n not in kept}
        inv_scopes = find_conflicts(final)
        if not inv_scopes:
            break
        for key in sorted(inv_scopes, key=lambda k: (k[0], k[1])):
            new, group = key[0], list(key[1])
            sc = sorted(inv_scopes[key])
            if len(key) == 3:
                n = group[0]
                if n in kept:
                    continue
                if n in INTERI and final.get(n) != INTERI[n]:
                    pass
                alt = next((a for a in try_alternatives(n)
                            if not forbidden(n, a[0]) and a[0] not in final.values() and free(n, a[0], final)),
                           None)
                if alt and n not in pinned:
                    M[n], resolved_by[n] = alt[0], alt[1] + " (target %s already exists)" % new
                else:
                    kept[n] = "target %s already exists in %s" % (new, ", ".join(sc[:3]))
                collisions_log.append({"kind": "clash", "old": n, "new": new, "scopes": sc[:5],
                                       "result": M[n] if n not in kept else None})
                changed = True
                continue
            group = [g for g in group if g not in kept and final.get(g) == new]
            if len(group) < 2:
                continue
            # the winner: chosen by interi.tsv, else the most frequent, else the first in order
            pin_w = [g for g in group if INTERI.get(g) == new]
            winner = pin_w[0] if pin_w else sorted(group, key=lambda g: (-occ[g], g))[0]
            entry = {"kind": "collision", "new": new, "olds": sorted(group), "winner": winner, "scopes": sc[:5],
                     "losers": {}}
            for g in sorted(group):
                if g == winner:
                    continue
                alt = next((a for a in try_alternatives(g)
                            if not forbidden(g, a[0]) and a[0] not in final.values() and free(g, a[0], final)),
                           None)
                if alt and g not in INTERI and g not in pinned:
                    M[g], resolved_by[g] = alt[0], alt[1] + " (lost %s to %s)" % (new, winner)
                    entry["losers"][g] = alt[0]
                else:
                    kept[g] = "loses %s to %s (scopes: %s)" % (new, winner, ", ".join(sc[:3]))
                    entry["losers"][g] = None
            collisions_log.append(entry)
            changed = True
        # twins
        for n in sorted(M):
            tw = twin(n)
            if tw and tw in M:
                if (n in kept) != (tw in kept):
                    kept.setdefault(n, "twin %s is not renamed" % tw)
                    kept.setdefault(tw, "twin %s is not renamed" % n)
                    changed = True
                elif n not in kept and twin(M[n]) != M[tw] and "-" in n:
                    # the snake spelling (the program's) decides, unless the kebab one is pinned by hand
                    # or had to move to a second choice
                    if (n in INTERI and tw not in INTERI) or (resolved_by.get(n, "").startswith("sinonimi")
                                                              and not resolved_by.get(tw, "").startswith("sinonimi")):
                        M[tw], resolved_by[tw] = M[n].replace("-", "_"), "twin of %s (interi.tsv)" % n
                        pinned.add(tw)
                    else:
                        M[n], resolved_by[n] = M[tw].replace("_", "-"), "twin of %s" % tw
                        pinned.add(n)
                    changed = True
        # case twins: Go reads untagged JSON keys by field name, ignoring case (Utente ↔ "utente"),
        # and the page's ids follow its constants: the lowercase spelling follows the capitalized one
        for n in sorted(M):
            if not (n[0].isupper() and not n.isupper()):
                continue
            low = n[0].lower() + n[1:]
            if low not in M or n not in go_untagged:
                continue
            if (n in kept) != (low in kept):
                kept.setdefault(n, "case twin %s is not renamed" % low)
                kept.setdefault(low, "case twin %s is not renamed" % n)
                changed = True
            elif n not in kept and (re.search(r"[a-z][A-Z]", M[n]) or "_" in M[n]):
                # a JSON key matched without case: "labelname" would be the only twin — a person decides
                kept.setdefault(n, "untagged JSON field: its English is two words, the key cannot follow")
                kept.setdefault(low, "untagged JSON field %s: its English is two words" % n)
                changed = True
            elif n not in kept and M[low] != M[n][0].lower() + M[n][1:]:
                moved_low = resolved_by.get(low, "").startswith("sinonimi")
                moved_cap = resolved_by.get(n, "").startswith("sinonimi")
                if (low in INTERI and n not in INTERI) or (moved_low and not moved_cap):
                    M[n], resolved_by[n] = M[low][0].upper() + M[low][1:], "case twin of %s" % low
                    pinned.add(n)
                else:
                    M[low], resolved_by[low] = M[n][0].lower() + M[n][1:], "case twin of %s" % n
                    pinned.add(low)
                changed = True
        # a twin decided «as it is» in interi.tsv keeps the other spelling as it is too
        for n in sorted(M):
            if n in kept:
                continue
            for tw in (twin(n), n[0].lower() + n[1:] if n[0].isupper() and not n.isupper() and n in go_untagged
                       else None, n[0].upper() + n[1:] if n[0].islower() and n[0].upper() + n[1:] in go_untagged
                       else None):
                if tw and tw in INTERI_WHY:
                    kept[n] = "twin %s is kept as it is (interi.tsv)" % tw
                    changed = True
                    break
        # the browser ties el.dataset.fooBar to the attribute data-foo-bar: the two follow each other,
        # and the dataset member (code) decides
        for c, a in dataset_pairs:
            c_new = M[c] if c in M and c not in kept else c
            a_new = M[a] if a in M and a not in kept else a
            want = "data-" + re.sub(r"[A-Z]", lambda m: "-" + m.group(0).lower(), c_new)
            if a_new == want:
                continue
            if want == a:
                kept[a] = "dataset twin %s is not renamed" % c
            else:
                M[a], resolved_by[a] = want, "dataset twin of %s" % c
                kept.pop(a, None)
                pinned.add(a)
            changed = True
        if not changed:
            break
    iterations = it + 1
    # the last word: whatever still conflicts after the iterations is not renamed (kept only grows)
    for _ in range(100):
        final = {n: v for n, v in M.items() if n not in kept}
        bad = {}
        for n in final:
            why = forbidden(n, final[n])
            if why:
                bad[n] = "target %s is a %s" % (final[n], why)
        for key, sc in find_conflicts(final).items():
            group = list(key[1])
            if len(key) == 3:
                bad[group[0]] = "target %s already exists in %s" % (key[0], ", ".join(sorted(sc)[:3]))
            else:
                pinned_w = [g for g in group if INTERI.get(g) == key[0]]
                winner = pinned_w[0] if pinned_w else sorted(group, key=lambda g: (-occ[g], g))[0]
                for g in group:
                    if g != winner:
                        bad[g] = "loses %s to %s (%s)" % (key[0], winner, ", ".join(sorted(sc)[:3]))
        for n in list(final):
            for tw in (twin(n), n[0].lower() + n[1:] if n[0].isupper() and not n.isupper() else None):
                if tw and ((tw in M and tw in kept) or tw in INTERI_WHY):
                    bad[n] = "twin %s is not renamed" % tw
        for c, a in dataset_pairs:
            if final.get(a, a) != "data-" + re.sub(r"[A-Z]", lambda m: "-" + m.group(0).lower(), final.get(c, c)):
                for x in (c, a):
                    if x in final:
                        bad[x] = "dataset twin %s / %s cannot follow" % (c, a)
        new_bad = {n: w for n, w in bad.items() if n not in kept}
        if not new_bad:
            break
        for n, w in new_bad.items():
            kept[n] = w
            collisions_log.append({"kind": "unresolved", "old": n, "new": M[n], "why": w})
    final = {n: v for n, v in M.items() if n not in kept}
    print("collision iterations: %d" % iterations, file=sys.stderr)
    # data names: renamed only in the files the contract analysis found them in
    dati_files = collections.defaultdict(dict)
    for old, (new, kind, fs, note) in dati.items():
        if old in final or old in kept:
            continue                    # the code already decides this name
        for f in fs:
            dati_files[f][old] = new
    return {"dati_files": dati_files, "lang_own": lang_own, "frozen": frozen_registers(root, files), "infos": infos, "skipped": skipped_files, "M": final, "kept": kept, "excluded": excluded,
            "origin": origin, "files_of": files_of, "collisions": collisions_log, "resolved_by": resolved_by,
            "dati": dati, "keeps": keeps, "gens": gens, "occ": occ, "scopes": scopes}


# ═══ application ═════════════════════════════════════════════════════════════
TAG_ATTR = re.compile(r"""(?P<name>[^\s=/>"'<]+)(?:\s*=\s*(?P<val>"[^"]*"|'[^']*'|[^\s>"']+))?""")
# attributes whose values the platform enumerates (type="checkbox", rel="icon", role="button")
PLATFORM_VALUES = set("""type rel autocomplete inputmode enterkeyhint autocapitalize role dir loading decoding
fetchpriority crossorigin referrerpolicy method enctype target wrap spellcheck draggable translate
contenteditable preload sandbox allow http-equiv charset lang media sizes shape kind scope align valign accept
capture popover popovertargetaction content xmlns version viewbox preserveaspectratio""".split())
ARIA_IDREFS = {"aria-controls", "aria-labelledby", "aria-describedby", "aria-owns", "aria-activedescendant",
               "aria-errormessage", "aria-details", "aria-flowto"}


def rewrite(text, lang, regs, M, keep_lines, path, frozen=None, lang_own=None):
    lang_own = lang_own or {}
    """Return (new_text, count, changes)."""
    starts = [0] + [m.end() for m in re.finditer("\n", text)]
    import bisect

    def lineno(off):
        return bisect.bisect_right(starts, off)
    guil = guillemet_spans(text)
    out, pos, count = [], 0, 0
    changes = collections.Counter()

    def in_guil(a):
        for x, y in guil:
            if x <= a < y:
                return True
        return False

    lines = text.split("\n")
    ranges = []
    for first, last, _ in keep_lines:
        if first == "*":
            ranges.append((1, len(lines)))      # every literal of the file: a reader of old data
            continue
        s = next((i for i, l in enumerate(lines, 1) if first in l), None)
        if s is None:
            continue
        e = next((i for i, l in enumerate(lines[s - 1:], s) if last in l), s)
        ranges.append((s, e))

    def kept_line(a):
        ln = lineno(a)
        return any(x <= ln <= y for x, y in ranges)

    # names built at run time: a literal prefix glued to a variable ("memoria_" + rc, f"memoria_{rc}")
    prefixes = set(re.findall(r"[\"']([A-Za-z][A-Za-z0-9]*[_-])[\"']\s*\+", text)) | \
        set(re.findall(r"\bf[\"']([A-Za-z][A-Za-z0-9]*[_-])\{", text))
    # file names built at run time (n + ".html", f"{n}.html", "%s.html" % n): their bare stems are files
    dyn_ext = set(re.findall(r"\+\s*[\"']\.(%s)[\"']|\}\.(%s)\b|%%s\.(%s)\b" % (EXT, EXT, EXT), text))
    dyn_ext = {x for g in dyn_ext for x in g if x}
    dyn_stems = {s for s, e in re.findall(r"\b([A-Za-z_][A-Za-z0-9_-]*)\.(%s)\b" % EXT, text) if e in dyn_ext} \
        if dyn_ext else set()

    css_own = lang_own.get("css", set())
    # a shell function or variable defined in this file is a name, even when a directory of the tree has
    # its spelling (impronta() vs installatore/prove/impronta)
    sh_own = set(re.findall(r"^[ \t]*(?:function[ \t]+)?([A-Za-z_]\w*)[ \t]*\(\)", text, re.M)) | \
        set(re.findall(r"(?:^|[;\s])(?:local[ \t]+|export[ \t]+|readonly[ \t]+)?([A-Za-z_]\w*)=", text, re.M)) \
        if lang in ("sh", "make", "conf") else set()

    def css_sub(seg):
        # CSS: only our names (selectors, custom properties, keyframes, data-*): a property, a value or
        # a pseudo-class is the platform's even when a name of ours has its spelling
        def subc(m):
            t = m.group(0)
            if t in M and t in css_own:
                changes[(t, M[t])] += 1
                return M[t]
            return t
        return WORD.sub(subc, seg)

    def literal(seg, a, k):
        """Strings, comments, shell words, documents: whole tokens of the table only.  None = untouched."""
        if k == "comment" and italian_prose(seg):
            return None
        # in a literal, only the Italian sentence is protected, not the data around it:
        # {"formato":"remotix-gruppi/1",…,"da":"REMOTIX alla prima connessione"} keeps the
        # sentence and renames the keys like the struct that reads them
        prose = prose_pieces(seg) if k in ("string", "code-doc") else []
        if k in ("span",) and ("«" in seg or "»" in seg or italian_prose(seg) or LOGLIKE.match(seg)):
            return None
        if k in ("string", "comment") and kept_line(a):
            return None
        seg_frozen = bool(k == "string" and frozen and any(m.group(0) in frozen for m in WORD.finditer(seg)))

        def sub2(m):
            if m.group("dol"):
                # a shell variable: $nome, ${nome…} — never a path, never kebab
                v = m.group("v")
                if v in M and not (seg_frozen and v in frozen):      # «$x» is still the variable x
                    changes[(v, M[v])] += 1
                    return m.group("dol") + M[v]
                return m.group(0)
            t = m.group("w")
            s = m.start()
            if t not in M and k == "string":
                # "memoria_" + rc builds memoria_sessioni: the compound follows its renamed tail
                for pre in sorted(prefixes):
                    if t.startswith(pre) and t[len(pre):] in M and not is_path(seg, s, m.end()):
                        changes[(t, pre + M[t[len(pre):]])] += 1
                        return pre + M[t[len(pre):]]
            if t not in M:
                return t
            if s > 0 and seg[s - 1] == "%" and not seg[max(0, s - 2):s] == "%%":
                return t              # "%dx%d": the first letter is a format verb, not a name
            if k == "string" and seg[m.end():m.end() + 1] == "=" and not t.startswith("data-") and \
                    re.search(r"<[A-Za-z][\w:-]*\s[^<>]*$", text[max(0, a + s - 400):a + s]):
                return t              # f'<img src="…" alt="…">': an HTML attribute name in a string
            if seg_frozen and t in frozen:
                return t
            if (k != "string" and in_guil(a + s)) or any(x <= s < y for x, y in prose):
                return t              # «…» protects prose; in a literal it is log punctuation
            if k == "string" and t in dyn_stems:
                return t              # n + ".html" builds testo.html: the bare stem is a file name
            if is_path(seg, s, m.end()):
                return t           # a path: renamed with the files (step 2)
            if k == "code" and lang in ("sh", "make", "conf") and t in REPO_NAMES and t not in sh_own:
                return t           # a bare file or directory name in a command (gofmt -l motore)
            changes[(t, M[t])] += 1
            return M[t]
        return SHELLWORD.sub(sub2, seg)

    def tag_sub(seg, a):
        # <img alt="…" aria-pressed="true" data-schermo="acceso" class="tela" style="…">: the element
        # and the attribute names are the platform's (only data-* are ours); the values of enumerated
        # attributes are the platform's too; style is CSS; the other values are data
        m0 = re.match(r"<\s*/?\s*[A-Za-z][\w:.-]*", seg)
        if not m0:
            return None
        parts, pos2 = [seg[:m0.end()]], m0.end()
        for m in TAG_ATTR.finditer(seg, m0.end()):
            parts.append(seg[pos2:m.start()])
            name, val = m.group("name"), m.group("val")
            low = name.lower()
            if low.startswith("data-") and name in M:
                changes[(name, M[name])] += 1
                parts.append(M[name])
            else:
                parts.append(name)
            parts.append(seg[m.end("name"):m.start("val")] if val is not None else "")
            if val is not None:
                if low in PLATFORM_VALUES or (low.startswith("aria-") and low not in ARIA_IDREFS):
                    parts.append(val)
                elif low == "style":
                    parts.append(css_sub(val))
                else:
                    nv = literal(val, a + m.start("val"), "string")
                    parts.append(val if nv is None else nv)
            pos2 = m.end()
        parts.append(seg[pos2:])
        return "".join(parts)

    for a, b, k in regs:
        seg = text[a:b]
        if k == "skip":
            continue
        new_seg = None
        if k == "code-css" or (k == "code" and lang == "css"):
            new_seg = css_sub(seg)
        elif k == "tag":
            new_seg = tag_sub(seg, a)
        elif k == "code" and lang in ("c", "go", "py", "js", "html"):
            own = lang_own.get("js" if lang == "html" else lang, set())

            def sub(m):
                t = m.group(0)
                if t in M:
                    if t not in own and is_member(seg, m.start()) and \
                            not re.search(r"\bdataset\.\s*$", seg[max(0, m.start() - 12):m.start()]):
                        return t          # an external member (event.altKey): not ours
                    changes[(t, M[t])] += 1
                    return M[t]
                return t
            new_seg = IDENT.sub(sub, seg)
        else:
            new_seg = literal(seg, a, k)
        if new_seg is not None and new_seg != seg:
            out.append(text[pos:a])
            out.append(new_seg)
            pos = b
    out.append(text[pos:])
    count = sum(changes.values())
    return "".join(out), count, changes


def apply(root, P, verbose=False):
    total = collections.Counter()
    per_file = {}
    for f, fi in sorted(P["infos"].items()):
        p = os.path.join(root, f)
        if not os.path.isfile(p):
            continue
        text = open(p, encoding="utf-8").read()
        regs = regions(f, text, fi.lang) if text != fi.text else fi.regs
        # the benches (and the manual's generators) that read or write the recorded registers keep the
        # registers' words in their string literals; the product and the installer never do (no
        # installed base, both sides change together)
        frozen = P["frozen"] if FREEZE_REGISTERS and f.startswith(("banchi/", "docs/sources/")) and "jsonl" in text \
            else None
        M = P["M"]
        if f in P["dati_files"]:
            M = dict(M)
            M.update(P["dati_files"][f])
        elif fi.lang == "md" and P["dati_files"]:
            M = dict(M)               # the documents follow every data name, in their code spans only
            for d in P["dati_files"].values():
                M.update(d)
        new, n, ch = rewrite(text, fi.lang, regs, M, P["keeps"].get(f, []), f, frozen, P["lang_own"])
        if n:
            open(p, "w", encoding="utf-8").write(new)
            per_file[f] = n
            total.update(ch)
    return per_file, total


# ═══ outputs ═════════════════════════════════════════════════════════════════
def contracts(P):
    """Names that cross a boundary, with every place they occur (documents excluded: they follow).
      - environment variables (REMOTIX_*, RX_*), options and kebab names (subcommands, ids, verbs);
      - code names met in two languages (C ↔ page ↔ benches ↔ installer: wire strings, JSON keys,
        log areas written by one program and read by another);
      - data names of dati.tsv, renamed only in the files listed there."""
    infos, M = P["infos"], P["M"]
    dati_new = {}
    for f, d in P["dati_files"].items():
        dati_new.update(d)
    where = collections.defaultdict(lambda: collections.defaultdict(list))
    for f, fi in sorted(infos.items()):
        if fi.lang == "md":
            continue
        local = P["dati_files"].get(f, {})
        for i, line in enumerate(fi.text.split("\n"), 1):
            for m in WORD.finditer(line):
                t = m.group(0)
                if t in M or t in local:
                    where[t][fi.lang].append("%s:%d" % (f, i))
    out = []
    for t in sorted(set(M) | set(dati_new)):
        langs = set(where[t])
        kind = None
        if t in dati_new and t not in M:
            kind = "data name (dati.tsv: %s)" % P["dati"][t][1]
        elif t.startswith(("REMOTIX_", "RX_")):
            kind = "environment variable"
        elif "-" in t:
            kind = "option / subcommand / kebab name"
        elif len(langs) >= 2:
            kind = "crosses languages"
        if kind:
            locs = [loc for l in where[t].values() for loc in l]
            out.append({"old": t, "new": M.get(t) or dati_new[t], "kind": kind, "languages": sorted(langs),
                        "places": sorted(set(locs))})
    return out


def verify(root):
    """After apply, against the commit the copy was made from: «…» quotes of every document, files
    that must never change, string literals of the protected lines.  Returns the number of faults."""
    def old(f):
        r = subprocess.run(["git", "-C", root, "show", "HEAD:" + f], capture_output=True)
        return r.stdout.decode("utf-8", "replace")
    faults = 0
    changed = subprocess.check_output(["git", "-C", root, "diff", "--name-only"]).decode().split("\n")
    changed = [c for c in changed if c]
    skips, keeps, _ = load_protected()
    nq = 0
    for f in git_files(root):
        if f.endswith(".md"):
            a = guillemet_spans_text(old(f))
            b = guillemet_spans_text(open(os.path.join(root, f), encoding="utf-8").read())
            nq += len(a)
            if a != b:
                faults += 1
                print("⛔ quotes changed in", f, len(a), len(b))
    print("quotes «…» in documents: %d, unchanged" % nq if not faults else "quotes: %d files changed" % faults)
    bad = [f for f in changed if skipped(f, skips)]
    for f in bad:
        print("⛔ a protected file changed:", f)
    faults += len(bad)
    print("protected files changed: %d" % len(bad))
    lit = re.compile(r"\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*'|`[^`]*`")
    nk = 0
    for f, ks in keeps.items():
        if f not in changed:
            nk += len(ks)
            continue
        A = old(f).split("\n")
        B = open(os.path.join(root, f), encoding="utf-8").read().split("\n")
        for first, last, why in ks:
            s = 0 if first == "*" else next((i for i, l in enumerate(A) if first in l), None)
            if first == "*":
                last = None
            if s is None:
                continue
            e = len(A) - 1 if last is None else next((i for i, l in enumerate(A[s:], s) if last in l), s)
            for i in range(s, min(e + 1, len(A), len(B))):
                if lit.findall(A[i]) != lit.findall(B[i]):
                    faults += 1
                    print("⛔ protected line %s:%d changed:\n   %s\n   %s" % (f, i + 1, A[i].strip(), B[i].strip()))
            nk += 1
    print("protected regions checked: %d" % nk)
    return faults


def guillemet_spans_text(t):
    return re.findall(r"«[^«»]*»", t)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=["plan", "apply", "verify"])
    ap.add_argument("--root", default=DEFAULT_ROOT)
    ap.add_argument("--before")
    ap.add_argument("--out", default=HERE)
    a = ap.parse_args()
    root = os.path.abspath(a.root)
    if a.cmd == "verify":
        sys.exit(1 if verify(root) else 0)
    P = plan(root)
    if a.cmd == "plan":
        import rinomina2_report
        rinomina2_report.write(P, contracts(P), a.out, root)
    elif a.cmd == "apply":
        per_file, total = apply(root, P)
        json.dump({"files": per_file, "pairs": {"%s→%s" % k: v for k, v in sorted(total.items())}},
                  open(os.path.join(root, ".rinomina2-applied.json"), "w"), ensure_ascii=False, indent=1)
        print("files changed: %d  replacements: %d  distinct pairs: %d" %
              (len(per_file), sum(total.values()), len(total)))


if __name__ == "__main__":
    main()
