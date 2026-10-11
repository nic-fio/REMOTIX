"""fase_a.py — phase A of the rename: internal code identifiers only, ZERO behaviour change (RINOMINA.md §0).

Phase A changes a name only where it is a program name and nothing else can see its spelling:

  * string literals of every language are never changed;
  * documents are never changed, except a Markdown code span that is exactly one renamed identifier
    holding «_» or an internal capital, outside fasi/, memoria/, misure/ (history);
  * comments: only tokens that are renamed identifiers holding «_» or an internal capital, never on a
    line that is a command example;
  * shell: only variable references ($x, ${x…}), assignments and declarations, `for x in`, `read x`,
    function definitions and calls of our own functions — positions given by the shfmt syntax tree;
  * Makefiles, unit and conf files, JSON, CSS, HTML outside <script>, GLSL: never.

A name is FROZEN — not renamed anywhere — when its exact spelling occurs, as a whole token, anywhere
the tool does not rename (strings of any language, documents, shell words that are not references,
Makefiles, conf/unit/JSON/CSS/HTML attributes, file names of the tree), and in the special cases
listed in frozen() (environment variables, Go untagged JSON fields, stringified C macro arguments,
Python keyword arguments that become data, …).  When in doubt, frozen.

  python3 fase_a.py check --root COPY     the string checker: every changed file keeps, against HEAD,
                                          the same multiset of string-literal contents (and the same
                                          non-identifier skeleton); exit 1 on any difference
"""
import ast
import bisect
import collections
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lessico  # noqa: E402

# git revisions whose files a bench builds together with today's sources (R10 F8, F9): every name in
# them stays, or the link of the bench breaks
HISTORY_SOURCES = [
    ("6bacca7", "src/ripiego.c", "banchi/18-software/18-software-confronto.sh"),
    ("6bacca7", "src/ripiego.h", "banchi/18-software/18-software-confronto.sh"),
    ("545ec55", "src/codificatore.c", "banchi/18-scheda/18-confronto.sh (vecchio/)"),
    ("545ec55", "src/codificatore.h", "banchi/18-scheda/18-confronto.sh (vecchio/)"),
]
SHFMT = os.environ.get("RINOMINA_SHFMT", "/media/REMOTIX/src/full-english-uscite/fase-a/bin/shfmt")

TOK = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
KEBAB = re.compile(r"[A-Za-z_][A-Za-z0-9_]*(?:-[A-Za-z0-9_]+)+")
DFLAG = re.compile(r"-[DU]([A-Za-z_][A-Za-z0-9_]*)")
IDENT_RX = re.compile(r"(?<![A-Za-z0-9_$])[A-Za-z_][A-Za-z0-9_]*(?![A-Za-z0-9_])")
ENVNAME = re.compile(r"^(REMOTIX_|RX_)[A-Z0-9_]*$")

# history and third-party: never rewritten, and they do not freeze names (they describe the past or
# somebody else's code; nothing in them is built or read by the programs)
NOT_A_SOURCE = ("fondamenta/", "english-migration/", "licenze/", "installatore/vendor/", "LICENSE.md",
                "THIRD-PARTY-LICENSES", "packaging/debian/copyright")
HISTORY_DOCS = ("fasi/", "memoria/", "misure/")
BINARY = re.compile(r"\.(png|jpg|jpeg|gif|webp|ico|wasm|gz|tgz|zst|pdf|xz|bin|ttf|otf|woff2?|mp4|webm|o|so|a|zip|"
                    r"deb|rpm|iso|qcow2|raw|h264|hevc|ivf|y4m|wav|opus|pkt|f32|rcpreg)$", re.I)


def tokens(s):
    """Every whole token of a frozen piece of text: identifier runs, kebab compounds (and their snake
    twin: --x-y gives args.x_y), the name after -D/-U, and the same after cutting escape letters."""
    out = set(TOK.findall(s))
    s2 = re.sub(r"\\[ntrfvab0e]", " ", s)
    if s2 != s:
        out |= set(TOK.findall(s2))
    for k in KEBAB.findall(s2):
        out.add(k)
        out.add(k.replace("-", "_"))
    out |= set(DFLAG.findall(s))
    return out


def internal_shape(t):
    """A token that can only be a program name: it holds «_» (not only at the ends) or a capital
    inside (camelCase).  Plain words (serve, accuse, nobody) never qualify."""
    core = t.strip("_")
    return "_" in core or bool(re.search(r"[a-z0-9][A-Z]", core))


# ═══ shell: the syntax tree of shfmt ═════════════════════════════════════════
READ_ARGFLAGS = set("dinNptu")
MAPFILE_ARGFLAGS = set("dnOsuCc")


class ShellFile:
    """Rename positions of one shell file (byte offsets): def/ref/call, and its comments."""

    def __init__(self, path, data):
        self.path = path
        self.data = data                    # bytes
        self.pos = []                       # (start, end, name, kind)  kind: def ref call
        self.calls = []                     # (start, end, name): command words, decided later
        self.comments = []                  # (start, end)
        self.funcs = set()
        self.dispatch = False               # a command word built from a variable: "$1" args
        self.env_in = set()                 # ${X:-…} on an UPPERCASE name: an input from outside
        self.frozen = {}                    # name → reason (indirect, nameref, export -f …)
        self.ok = False

    def parse(self):
        r = subprocess.run([SHFMT, "--to-json", "-ln", "bash"], input=self.data, capture_output=True)
        if r.returncode != 0:
            return False
        self.walk(json.loads(r.stdout))
        self.ok = True
        return True

    def lit(self, node, kind):
        v = node.get("Value")
        if isinstance(v, str) and "ValuePos" in node and re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", v):
            a = node["ValuePos"]["Offset"]
            self.pos.append((a, a + len(v.encode()), v, kind))

    @staticmethod
    def single_lit(word):
        if isinstance(word, dict) and len(word.get("Parts", [])) == 1 and word["Parts"][0].get("Type") == "Lit":
            return word["Parts"][0]
        return None

    def walk(self, o):
        if isinstance(o, list):
            for x in o:
                self.walk(x)
            return
        if not isinstance(o, dict):
            return
        for key in ("Comments", "Last"):
            for c in o.get(key, []) or []:
                if isinstance(c, dict) and "Hash" in c:
                    a = c["Hash"]["Offset"] + 1
                    self.comments.append((a, a + len(c.get("Text", "").encode())))
        t = o.get("Type")
        if t == "FuncDecl":
            n = o["Name"]
            if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", n.get("Value", "")):
                self.funcs.add(n["Value"])
                self.lit(n, "def")
            self.walk(o.get("Body"))
            return
        if t == "ParamExp":
            p = o.get("Param")
            if p:
                if o.get("Names"):
                    self.frozen[p.get("Value", "")] = "shell ${!prefix*}"
                else:
                    self.lit(p, "ref")
                    exp = o.get("Exp")
                    if exp and 68 <= exp.get("Op", 0) <= 75 and p.get("Value", "").isupper():
                        self.env_in.add(p["Value"])
            for k in ("Index", "Slice", "Repl", "Exp"):
                self.walk(o.get(k))
            return
        if t == "CallExpr":
            for a in o.get("Assigns", []) or []:
                self.assign(a)
            args = o.get("Args", []) or []
            if args:
                first = args[0]
                fl = self.single_lit(first)
                if fl is not None:
                    cmd = fl.get("Value", "")
                    if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", cmd):
                        a = fl["ValuePos"]["Offset"]
                        self.calls.append((a, a + len(cmd.encode()), cmd))
                    if cmd in ("read", "unset", "mapfile", "readarray", "getopts"):
                        self.name_args(cmd, args[1:])
                        return
                else:
                    parts = first.get("Parts", [])
                    if any(p.get("Type") in ("ParamExp", "DblQuoted", "CmdSubst") for p in parts):
                        self.dispatch = True
                for w in args[1:] if fl is not None else args:
                    self.walk(w)
            return
        if t == "DeclClause":
            variant = (o.get("Variant") or {}).get("Value", "")
            flags = "".join(self.single_lit(a.get("Value"))["Value"] for a in o.get("Args", [])
                            if a.get("Naked") and self.single_lit(a.get("Value")) is not None
                            and self.single_lit(a.get("Value"))["Value"].startswith("-"))
            odd = variant == "nameref" or any(c in flags for c in "nfF")
            for a in o.get("Args", []) or []:
                if a.get("Name"):
                    if odd:
                        self.frozen[a["Name"].get("Value", "")] = "shell %s %s" % (variant, flags)
                    else:
                        self.lit(a["Name"], "def")
                self.walk(a.get("Value"))
                self.walk(a.get("Index"))
                self.walk(a.get("Array"))
            return
        if t == "ForClause":
            loop = o.get("Loop") or {}
            if loop.get("Type") == "WordIter" and loop.get("Name"):
                self.lit(loop["Name"], "def")
                self.walk(loop.get("Items"))
            else:
                self.walk(loop)
            self.walk(o.get("Do"))
            return
        for k, v in o.items():
            if k in ("Pos", "End", "ValuePos", "ValueEnd"):
                continue
            if isinstance(v, (dict, list)):
                self.walk(v)

    def assign(self, a):
        if a.get("Name"):
            self.lit(a["Name"], "def")
        for k in ("Value", "Index", "Array"):
            self.walk(a.get(k))

    def name_args(self, cmd, args):
        skip = False
        lits = [self.single_lit(w) for w in args]
        for i, (w, l) in enumerate(zip(args, lits)):
            if skip:
                skip = False
                self.walk(w)
                continue
            if l is None:
                self.walk(w)
                continue
            v = l.get("Value", "")
            if v.startswith("-"):
                if cmd == "unset" and "f" in v:
                    return
                if cmd == "read" and v[-1:] in READ_ARGFLAGS:
                    skip = True
                if cmd in ("mapfile", "readarray") and v[-1:] in MAPFILE_ARGFLAGS:
                    skip = True
                if cmd == "read" and v[-1:] == "a" and i + 1 < len(args) and lits[i + 1] is not None:
                    self.lit(lits[i + 1], "def")
                    skip = True
                    continue
                continue
            if cmd == "getopts" and i == 0:
                continue
            if cmd in ("mapfile", "readarray") and i != len(args) - 1:
                continue
            self.lit(l, "def")


# ═══ the frozen names ════════════════════════════════════════════════════════
def lang_of(path):
    import rinomina2
    return rinomina2.language(path)


def md_exact_spans(text, path):
    """Markdown code spans that are exactly one identifier with «_» or an internal capital (optionally
    followed by «()»), outside fenced blocks and «…» quotes: the only places phase A changes in a
    document.  History documents: none."""
    if path.startswith(HISTORY_DOCS):
        return []
    fenced = [(m.start(), m.end()) for m in
              re.finditer(r"(?ms)^ {0,3}(`{3,}|~{3,})[^\n]*\n.*?^ {0,3}\1[`~]*[ \t]*$", text)]
    guil = [(m.start(), m.end()) for m in re.finditer(r"«[^«»]*»", text)]
    out = []
    for m in re.finditer(r"(?<!`)`([A-Za-z_][A-Za-z0-9_]*)(?:\(\))?`(?!`)", text):
        a = m.start(1)
        if any(x <= a < y for x, y in fenced) or any(x <= a < y for x, y in guil):
            continue
        if internal_shape(m.group(1)):
            out.append((m.start(1), m.end(1), m.group(1)))
    return out


def blank(text, ranges):
    """text with the given (start, end) ranges replaced by spaces (newlines kept)."""
    if not ranges:
        return text
    out, pos = [], 0
    for a, b in sorted(ranges):
        if a < pos:
            a = pos
        if b <= a:
            continue
        out.append(text[pos:a])
        out.append(re.sub(r"[^\n]", " ", text[a:b]))
        pos = b
    out.append(text[pos:])
    return "".join(out)


def c_functions_naming_themselves(code):
    """C functions whose body uses assert(), g_return_if_fail() & co. or __func__: the name is a string
    in the binary (printed when the check fails)."""
    out, depth, i, start, name = set(), 0, 0, None, None
    for m in re.finditer(r"[{}]", code):
        if m.group(0) == "{":
            if depth == 0:
                h = re.search(r"([A-Za-z_]\w*)\s*\([^;{}]*\)\s*$", code[max(0, m.start() - 600):m.start()])
                name, start = (h.group(1) if h else None), m.end()
            depth += 1
        else:
            depth -= 1
            if depth == 0 and name and re.search(r"\b(assert|g_assert\w*|g_return\w*_if_fail|g_warn_if_\w+)\s*\(|__func__|__FUNCTION__|"
                                                 r"__PRETTY_FUNCTION__|G_STRFUNC",
                                                 code[start:m.start()]):
                out.add(name)
            depth = max(depth, 0)
    return out


def c_macro_args(code):
    """Identifiers passed to a C macro whose body stringifies (#x) or pastes (##) a parameter: renaming
    them would change a string or a pasted name."""
    joined = re.sub(r"\\\n", " ", code)
    macros = set()
    for m in re.finditer(r"(?m)^[ \t]*#[ \t]*define[ \t]+([A-Za-z_]\w*)\(([^)]*)\)(.*)$", joined):
        params = [p.strip() for p in m.group(2).split(",") if p.strip()]
        body = m.group(3)
        if "##" in body or any(re.search(r"(?<!#)#\s*%s\b" % re.escape(p), body) for p in params if p != "..."):
            macros.add(m.group(1))
    out = set()
    for name in macros:
        for m in re.finditer(r"\b%s\s*\(" % re.escape(name), code):
            depth, i = 1, m.end()
            while i < len(code) and depth:
                depth += {"(": 1, ")": -1}.get(code[i], 0)
                i += 1
            out |= set(TOK.findall(code[m.end():i - 1]))
    return out, macros


PY_DATA_CALLS = {"dict", "SimpleNamespace", "Namespace", "namedtuple", "OrderedDict", "Counter", "defaultdict",
                 "format", "format_map", "update", "setdefault", "dumps", "dump", "Template", "substitute",
                 "safe_substitute", "replace", "_replace"}
PY_INTROSPECT = re.compile(r"\blocals\(\)|\bglobals\(\)|\bvars\(|__dict__|\basdict\(|\b_asdict\(|\b_fields\b|__slots__")


def py_facts(text):
    """(defs: function name → params, keyword uses [(func, kw)], data-class fields, uses __name__)"""
    try:
        tree = ast.parse(text)
    except (SyntaxError, ValueError):
        return None
    defs = collections.defaultdict(set)
    kws, fields = [], set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            a = n.args
            for x in a.posonlyargs + a.args + a.kwonlyargs:
                defs[n.name].add(x.arg)
        elif isinstance(n, ast.ClassDef):
            bases = " ".join(ast.unparse(b) for b in n.bases)
            decos = " ".join(ast.unparse(d) for d in n.decorator_list)
            datay = "dataclass" in decos or re.search(r"NamedTuple|TypedDict|Enum|Flag", bases)
            for b in n.body:
                if isinstance(b, (ast.FunctionDef, ast.AsyncFunctionDef)) and b.name == "__init__":
                    a = b.args
                    for x in a.posonlyargs + a.args + a.kwonlyargs:
                        defs[n.name].add(x.arg)
                if datay:
                    if isinstance(b, ast.AnnAssign) and isinstance(b.target, ast.Name):
                        fields.add(b.target.id)
                        defs[n.name].add(b.target.id)
                    elif isinstance(b, ast.Assign):
                        for tg in b.targets:
                            if isinstance(tg, ast.Name):
                                fields.add(tg.id)
        elif isinstance(n, ast.Call):
            f = n.func
            fn = f.id if isinstance(f, ast.Name) else (f.attr if isinstance(f, ast.Attribute) else None)
            for k in n.keywords:
                if k.arg:
                    kws.append((fn, k.arg))
    dunder = bool(re.search(r"__name__(?!\s*==\s*[\"']__main__)|__qualname__|__class__", text.replace(
        'if __name__ == "__main__"', "").replace("if __name__ == '__main__'", "")))
    return defs, kws, fields, dunder


def frozen(root, files, infos, scopes, M_candidates):
    """name → reason, for every candidate name phase A must not rename."""
    import rinomina2
    F = {}

    def freeze(names, why):
        for n in names:
            if n in M_candidates and n not in F:
                F[n] = why
    shell = {}
    # 1. shell files: parse first (the function names decide which command words are calls)
    for f in files:
        fi = infos.get(f)
        if fi is not None and fi.lang == "sh":
            sf = ShellFile(f, fi.text.encode("utf-8"))
            sf.parse()
            shell[f] = sf
    # functions visible to a shell file: its own and those of the files it sources
    sh_scope_funcs = {}
    for f, sf in shell.items():
        fs = set(sf.funcs)
        for g in scopes.get("sh:" + f, [f]):
            if g in shell:
                fs |= shell[g].funcs
        sh_scope_funcs[f] = fs
    for f, sf in shell.items():
        if not sf.ok:
            continue
        for a, b, name in sf.calls:
            if name in sh_scope_funcs[f] and not sf.dispatch:
                sf.pos.append((a, b, name, "call"))
        if sf.dispatch:
            freeze(sf.funcs, "shell: functions of a file that runs a command named by a variable (%s)" % f)
        freeze(sf.env_in, "shell: ${X:-…} on an upper-case name, an input from the environment (%s)" % f)
        for n, why in sf.frozen.items():
            freeze([n], "%s (%s)" % (why, f))
    sh_defs, sh_refs = set(), set()
    for sf in shell.values():
        for a, b, n, k in sf.pos:
            (sh_defs if k in ("def",) else sh_refs).add(n)
    freeze(sh_refs - sh_defs - {n for sf in shell.values() for n in sf.funcs},
           "shell: read but never assigned in the tree, an input from the environment")

    # 2. the frozen text of every file
    for f in files:
        if f.startswith(NOT_A_SOURCE) or BINARY.search(f):
            continue
        freeze(tokens(f.replace("/", " ")), "a file or directory name of the tree")
        fi = infos.get(f)
        if fi is not None:
            text = fi.text
        else:
            p = os.path.join(root, f)
            if os.path.islink(p) or not os.path.isfile(p):
                continue
            try:
                text = open(p, encoding="utf-8").read()
            except (UnicodeDecodeError, OSError):
                continue
        lang = fi.lang if fi is not None else None
        if lang in ("c", "go", "py", "js") or (lang == "html"):
            parts = []
            if lang == "c" and f.endswith((".comp", ".glsl")):
                freeze(tokens(text), "a shader source (the generated SPIR-V carries its names): " + f)
                continue
            for a, b, k in fi.regs:
                if k in ("code", "comment"):
                    continue
                parts.append(text[a:b])          # strings, tags, html text, css
            if lang == "html":
                # outside <script>: everything (text content, comments, attributes, CSS) is frozen
                for a, b, k in fi.regs:
                    if k == "comment" and not _in_script(text, a):
                        parts.append(text[a:b])
            freeze(tokens("\n".join(parts)), "%s string literal: %s" % (lang, f))
        elif lang == "sh":
            sf = shell[f]
            if not sf.ok:
                freeze(tokens(blank(text, [(a, b) for a, b, k in fi.regs if k == "comment"])),
                       "shell file shfmt cannot parse: " + f)
                continue
            data = sf.data
            rng = [(a, b) for a, b, n, k in sf.pos] + sf.comments
            out, pos = bytearray(), 0
            for a, b in sorted(rng):
                if a < pos:
                    continue
                out += data[pos:a] + b" " * (b - a)
                pos = b
            out += data[pos:]
            freeze(tokens(out.decode("utf-8", "replace")), "shell word that is not a reference: " + f)
        elif lang == "md":
            spans = md_exact_spans(text, f)
            freeze(tokens(blank(text, [(a, b) for a, b, _ in spans])), "document: " + f)
        else:
            freeze(tokens(text), "%s file (never renamed in phase A): %s" % (lang or "data", f))

    # 3. special cases
    # history sources that benches extract from git and compile together with today's files
    for rev, path, who in HISTORY_SOURCES:
        r = subprocess.run(["git", "-C", root, "show", "%s:%s" % (rev, path)], capture_output=True)
        if r.returncode == 0:
            freeze(tokens(r.stdout.decode("utf-8", "replace")),
                   "a history source compiled with today's code (%s:%s, %s)" % (rev, path, who))
        else:
            raise SystemExit("fase_a: cannot read history source %s:%s (%s)" % (rev, path, who))
    freeze([n for n in M_candidates if ENVNAME.match(n)], "REMOTIX_*/RX_* environment variable (public)")
    pyfiles = {f: fi for f, fi in infos.items() if fi.lang == "py"}
    facts = {f: py_facts(fi.text) for f, fi in pyfiles.items()}
    alldefs = collections.defaultdict(set)
    for f, x in facts.items():
        if x:
            for fn, ps in x[0].items():
                alldefs[fn] |= ps
    for f, x in facts.items():
        fi = pyfiles[f]
        if x is None:
            freeze(set(fi.code) | set(fi.member), "Python file that does not parse: " + f)
            continue
        defs, kws, fields, dunder = x
        for fn, k in kws:
            if fn in PY_DATA_CALLS or fn not in alldefs or k not in alldefs[fn]:
                freeze([k], "Python keyword argument that becomes data or goes to someone else's function: "
                       "%s(%s=…) in %s" % (fn, k, f))
        freeze(fields, "Python dataclass/NamedTuple/Enum field (its name is data): " + f)
        if PY_INTROSPECT.search(fi.text):
            freeze(set(fi.code) | set(fi.member) | fi.massign,
                   "Python file that reads names at run time (locals/vars/__dict__/asdict): " + f)
        if dunder:
            for g in scopes.get("py:" + f, [f]):
                y = facts.get(g)
                if y:
                    freeze(set(y[0]), "Python class or function name printed through __name__: " + g)
    for f, fi in infos.items():
        if fi.lang in ("html", "js"):
            freeze(set(re.findall(r"\bdataset\s*\.\s*([A-Za-z_]\w*)", fi.text)),
                   "a dataset member is an HTML data-* attribute: " + f)
            freeze(js_object_keys(rinomina2.code_only(fi)),
                   "JavaScript object key or shorthand property (it becomes data: JSON, logs, messages): " + f)
    # C: stringified or pasted macro arguments
    for f, fi in infos.items():
        if fi.lang == "c":
            code = rinomina2.code_only(fi)
            freeze(c_functions_naming_themselves(code),
                   "C function whose name reaches the binary (assert, __func__): " + f)
            args, macros = c_macro_args(code)
            if args:
                freeze(args, "C argument of a macro that stringifies or pastes it (%s): %s" %
                       (", ".join(sorted(macros))[:60], f))
    # Go: untagged (or name-less tagged) fields of packages that use encoding/json
    pk = collections.defaultdict(list)
    for f, fi in infos.items():
        if fi.lang == "go":
            pk[os.path.dirname(f)].append(fi)
    for d, fis in pk.items():
        if not any("encoding/json" in fi.text for fi in fis):
            continue
        for fi in fis:
            for body in re.findall(r"struct\s*\{([^{}]*)\}", fi.text):
                for line in body.split("\n"):
                    line = line.split("//")[0]
                    m = re.match(r"^\s*([A-Z]\w*(?:\s*,\s*[A-Z]\w*)*)\s+\S", line)
                    if m and ("`" not in line or re.search(r'json:"(,|")', line)):
                        names = re.split(r"\s*,\s*", m.group(1))
                        freeze(names + [n[0].lower() + n[1:] for n in names],
                               "Go field without a JSON name: the key is the field (%s)" % fi.path)
    # names built at run time from a literal piece, where the file looks names up at run time
    dyn = {"py": re.compile(r"\b(getattr|setattr|hasattr|globals\(\)|locals\(\)|vars\()"),
           "sh": re.compile(r"\$\{!|\beval\b"),
           "js": re.compile(r"\b(window|self|globalThis|this)\s*\[|\beval\(|new Function\(")}
    pre_rx = re.compile(r"([A-Za-z][A-Za-z0-9]*(?:_[A-Za-z0-9]+)*_)(?=\$\{?[A-Za-z_0-9@*#]|%[sd]|\{[A-Za-z_]|[\"']\s*\+)")
    suf_rx = re.compile(r"(?:\}|%[sd]|\$[A-Za-z_][A-Za-z0-9_]*|\+\s*[\"'])(_[A-Za-z0-9]+(?:_[A-Za-z0-9]+)*)")
    for f, fi in infos.items():
        L = "js" if fi.lang == "html" else fi.lang
        if L in dyn and (dyn[L].search(fi.text) or (L == "sh" and shell.get(f) and shell[f].dispatch)):
            pres, sufs = set(pre_rx.findall(fi.text)), set(suf_rx.findall(fi.text))
            for n in M_candidates:
                if any(n.startswith(p) and len(n) > len(p) for p in pres) or \
                        any(n.endswith(s) and len(n) > len(s) for s in sufs):
                    freeze([n], "a name a file builds at run time from a literal piece (%s)" % f)
    return F, shell


def js_object_keys(code):
    """Keys of JavaScript object literals and destructuring patterns: {a: 1}, {a}, {a, b}, const {a} = o.
    The key is data as soon as the object is serialised, logged or posted; with a shorthand property the
    variable's name IS the key."""
    out = set()
    stack = []
    toks = list(re.finditer(r"[A-Za-z_$][\w$]*|[{}()\[\],:;?]|\S", code))
    for i, m in enumerate(toks):
        t = m.group(0)
        if t in "{([":
            stack.append(t)
            continue
        if t in "})]":
            if stack:
                stack.pop()
            continue
        if not stack or stack[-1] != "{" or not re.match(r"[A-Za-z_$]", t):
            continue
        prev = toks[i - 1].group(0) if i else ""
        nxt = toks[i + 1].group(0) if i + 1 < len(toks) else ""
        if prev in ("{", ",") and nxt in (":", ",", "}"):
            out.add(t)
    return out


def _in_script(text, a):
    i = text.rfind("<script", 0, a)
    return i >= 0 and text.rfind("</script", 0, a) < i


# ═══ the rewrite ═════════════════════════════════════════════════════════════
COMMAND_LINE = re.compile(r"^\s*(\$ |bash |sh |python3? |\./|sudo |make |podman |git |ssh |cd |export |go |node |"
                          r"[A-Za-z0-9_./-]+\.(sh|py) )|(^|\s)--[a-z]|(^|\s)[A-Z][A-Z0-9_]+=\S")


def comment_sub(seg, M):
    """A comment: only renamed tokens shaped like program names, never on a command-example line,
    never inside «…», never a path piece or an option."""
    out = []
    for line in seg.split("\n"):
        body = line.lstrip("#/*! \t")
        if COMMAND_LINE.search(body) or body.startswith(("go:", "+build", "export ", "#")):
            out.append(line)
            continue
        guil = [(m.start(), m.end()) for m in re.finditer(r"«[^«»]*»", line)]

        def sub(m):
            t = m.group(0)
            s, e = m.start(), m.end()
            if t not in M or not internal_shape(t):
                return t
            if any(x <= s < y for x, y in guil):
                return t
            if line[e:e + 1] == "/" or re.match(r"\.[A-Za-z]", line[e:e + 2]) or line[max(0, s - 1):s] in ("/", "-", "."):
                return t
            return M[t]
        out.append(IDENT_RX.sub(sub, line))
    return "\n".join(out)


def rewrite(path, text, lang, regs, M, keep_lines, lang_own, shellfile):
    """Phase A rewrite of one file.  Returns (new_text, changes Counter)."""
    changes = collections.Counter()
    if path.startswith(NOT_A_SOURCE):
        return text, changes
    lines = text.split("\n")
    ranges = []
    for first, last, _ in keep_lines:
        if first == "*":
            ranges.append((1, len(lines)))
            continue
        s = next((i for i, l in enumerate(lines, 1) if first in l), None)
        if s is None:
            continue
        e = next((i for i, l in enumerate(lines[s - 1:], s) if last in l), s)
        ranges.append((s, e))
    starts = [0] + [m.end() for m in re.finditer("\n", text)]

    def kept(off):
        ln = bisect.bisect_right(starts, off)
        return any(x <= ln <= y for x, y in ranges)

    if lang == "md":
        out, pos = [], 0
        for a, b, name in md_exact_spans(text, path):
            if name in M:
                out += [text[pos:a], M[name]]
                changes[(name, M[name])] += 1
                pos = b
        out.append(text[pos:])
        return "".join(out), changes
    if lang == "sh":
        sf = shellfile
        if sf is None or not sf.ok:
            return text, changes
        data = sf.data
        edits = []
        for a, b, name, k in sf.pos:
            if name in M:
                edits.append((a, b, M[name].encode()))
                changes[(name, M[name])] += 1
        for a, b in sf.comments:
            seg = data[a:b].decode("utf-8")
            if kept(len(data[:a].decode("utf-8", "replace"))):
                continue
            new = comment_sub(seg, M)
            if new != seg:
                for m1, m2 in zip(IDENT_RX.finditer(seg), IDENT_RX.finditer(new)):
                    if m1.group(0) != m2.group(0):
                        changes[(m1.group(0), m2.group(0))] += 1
                edits.append((a, b, new.encode()))
        out, pos = bytearray(), 0
        for a, b, rep in sorted(edits):
            if a < pos:
                raise SystemExit("overlapping shell edits in %s at %d" % (path, a))
            out += data[pos:a] + rep
            pos = b
        out += data[pos:]
        return out.decode("utf-8"), changes
    if lang not in ("c", "go", "py", "js", "html") or path.endswith((".comp", ".glsl")):
        return text, changes
    import rinomina2
    own = lang_own.get("js" if lang == "html" else lang, set())
    out, pos = [], 0
    for a, b, k in regs:
        seg = text[a:b]
        new = None
        if k == "code":
            def sub(m):
                t = m.group(0)
                if t in M:
                    if t not in own and rinomina2.is_member(seg, m.start()):
                        return t          # someone else's member (event.altKey)
                    changes[(t, M[t])] += 1
                    return M[t]
                return t
            new = IDENT_RX.sub(sub, seg)
        elif k == "comment" and (lang != "html" or _in_script(text, a)) and not kept(a):
            new = comment_sub(seg, M)
            if new != seg:
                for m1, m2 in zip(IDENT_RX.finditer(seg), IDENT_RX.finditer(new)):
                    if m1.group(0) != m2.group(0):
                        changes[(m1.group(0), m2.group(0))] += 1
        if new is not None and new != seg:
            out += [text[pos:a], new]
            pos = b
    out.append(text[pos:])
    return "".join(out), changes


# ═══ the string checker ══════════════════════════════════════════════════════
def py_strings(text):
    out = collections.Counter()
    for n in ast.walk(ast.parse(text)):
        if isinstance(n, ast.Constant) and isinstance(n.value, (str, bytes)):
            out[repr(n.value)] += 1
    return out


SH_NAME_FIELDS = ("Param",)


def sh_strings(data):
    """Every literal of a shell file except the name positions phase A may change: the parameter of a
    ${…}, the name of an assignment/declaration/function/for loop, a command word, and the name
    arguments of read/unset/mapfile/getopts."""
    r = subprocess.run([SHFMT, "--to-json", "-ln", "bash"], input=data, capture_output=True)
    if r.returncode:
        return None
    out = collections.Counter()

    def lits(o, skip=False):
        if isinstance(o, list):
            for x in o:
                lits(x)
            return
        if not isinstance(o, dict):
            return
        t = o.get("Type")
        if t == "SglQuoted":
            out["'" + o.get("Value", "")] += 1
            return
        if t == "Lit" and not skip:
            out[o.get("Value", "")] += 1
            return
        if t == "CallExpr":
            for a in o.get("Assigns", []) or []:
                lits(a.get("Value"))
                lits(a.get("Index"))
                lits(a.get("Array"))
            args = o.get("Args", []) or []
            if args:
                cmd = ShellFile.single_lit(args[0])
                rest = args[1:] if cmd is not None else args
                if cmd is not None and cmd.get("Value") in ("read", "unset", "mapfile", "readarray", "getopts"):
                    for w in rest:      # names and flags alike: compared without names
                        l = ShellFile.single_lit(w)
                        if l is None or l.get("Value", "").startswith("-"):
                            lits(w)
                    return
                lits(rest)
            return
        for k, v in o.items():
            if k in ("Name",) and isinstance(v, dict) and "Value" in v and "Type" not in v:
                continue                # assignment / function / loop name
            if k in SH_NAME_FIELDS:
                continue
            if isinstance(v, (dict, list)):
                lits(v)
        for key in ("Comments", "Last"):
            pass
    lits(json.loads(r.stdout))
    return out


def lexer_strings(text, lang):
    import rinomina2
    regs = rinomina2.regions("x", text, lang)
    out = collections.Counter()
    for a, b, k in regs:
        if k in ("string", "tag", "skip", "code-css"):
            out[text[a:b]] += 1
        elif k == "comment" and lang == "html" and not _in_script(text, a):
            out[text[a:b]] += 1
    return out


def skeleton(text):
    """The text with every identifier replaced by one placeholder: two versions of a file that differ
    only in names have the same skeleton."""
    return re.sub(r"(?<![A-Za-z0-9_])[A-Za-z_][A-Za-z0-9_]*", "\x00", text)


def holes(text, spans):
    out, pos = [], 0
    for x, y, _ in spans:
        out += [text[pos:x], "\x00"]
        pos = y
    return "".join(out) + text[pos:]


def check(root):
    import rinomina2
    changed = [c for c in subprocess.check_output(["git", "-C", root, "diff", "--name-only"]).decode().split("\n") if c]
    bad, n = 0, 0
    for f in changed:
        old = subprocess.run(["git", "-C", root, "show", "HEAD:" + f], capture_output=True).stdout
        new = open(os.path.join(root, f), "rb").read()
        a, b = old.decode("utf-8"), new.decode("utf-8")
        lang = rinomina2.language(f)
        n += 1
        why = None
        if skeleton(a) != skeleton(b):
            why = "more than identifiers changed"
        elif lang == "py":
            if py_strings(a) != py_strings(b):
                why = "Python string constants differ"
        elif lang == "sh":
            x, y = sh_strings(old), sh_strings(new)
            if x is None or y is None or x != y:
                why = "shell literals differ" if x is not None else "shfmt cannot parse"
        elif lang in ("c", "go", "js", "html"):
            if lexer_strings(a, lang) != lexer_strings(b, lang):
                why = "string literals differ"
        elif lang == "md":
            if holes(a, md_exact_spans(a, f)) != holes(b, md_exact_spans(b, f)):
                why = "a document changed outside its exact identifier spans"
        else:
            why = "a %s file changed (phase A never changes it)" % lang
        if why:
            bad += 1
            print("⛔ %s: %s" % (f, why))
            if why.endswith("differ"):
                X = py_strings(a) if lang == "py" else (sh_strings(old) if lang == "sh" else lexer_strings(a, lang))
                Y = py_strings(b) if lang == "py" else (sh_strings(new) if lang == "sh" else lexer_strings(b, lang))
                for s in list((X - Y).keys())[:3]:
                    print("     before only: %r" % s[:160])
                for s in list((Y - X).keys())[:3]:
                    print("     after only:  %r" % s[:160])
    print("%s strings: %d changed files, %d with string or structure changes" % ("✅" if not bad else "⛔", n, bad))
    return bad


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["check"])
    ap.add_argument("--root", required=True)
    a = ap.parse_args()
    sys.exit(1 if check(os.path.abspath(a.root)) else 0)
