"""Lexers for rinomina2.py: split a file into regions (code, comment, string, skip).

Each lexer returns a list of (start, end, kind) covering the text, kind in
  "code"     identifiers here are program names
  "comment"  prose for a person
  "string"   a literal (data, a format, a path, prose)
  "skip"     never touched (#include <...>, ``«…»`` quotes are cut later)
  "tag"      an HTML start/end tag: element and attribute names are the platform's, values are data
The lexers are deliberately small and conservative: when unsure, a region is
classified as string or comment, where only whole names from the table change.
"""
import io
import re
import tokenize


def _merge(regs, n):
    out = []
    for a, b, k in sorted(regs):
        if a >= b:
            continue
        if out and out[-1][2] == k and out[-1][1] == a:
            out[-1] = (out[-1][0], b, k)
        else:
            out.append((a, b, k))
    # fill gaps as code
    full, pos = [], 0
    for a, b, k in out:
        if a > pos:
            full.append((pos, a, "code"))
        full.append((a, b, k))
        pos = b
    if pos < n:
        full.append((pos, n, "code"))
    return full


# ── C, C++-like (also GLSL, Rust, Go without raw strings) ──────────────────
def lex_c(t, go=False, js=False):
    regs, i, n = [], 0, len(t)
    line_start = True
    last_sig = ""            # last significant char in code, for JS regex detection
    last_word = ""
    while i < n:
        c = t[i]
        if c == "\n":
            line_start = True
            i += 1
            continue
        if line_start and c in " \t":
            i += 1
            continue
        if not go and not js and line_start and c == "#":
            # preprocessor directive: #include <...> is skip, "..." stays a string
            m = re.match(r"#\s*include\s*<[^>\n]*>", t[i:])
            if m:
                regs.append((i, i + m.end(), "skip"))
                i += m.end()
                line_start = False
                continue
        line_start = False
        if t.startswith("//", i):
            j = t.find("\n", i)
            j = n if j < 0 else j
            regs.append((i, j, "comment"))
            i = j
            continue
        if t.startswith("/*", i):
            j = t.find("*/", i + 2)
            j = n if j < 0 else j + 2
            regs.append((i, j, "comment"))
            i = j
            continue
        if c == '"' or (c == "'" and (not go or True)):
            if c == "'" and not js and not go:
                # C char literal: short
                m = re.match(r"'(\\.|[^'\\\n])*'", t[i:])
                if m:
                    regs.append((i, i + m.end(), "string"))
                    i += m.end()
                    last_sig = "'"
                    continue
                i += 1
                continue
            if c == "'" and go:
                m = re.match(r"'(\\.|[^'\\\n])*'", t[i:])
                if m:
                    regs.append((i, i + m.end(), "string"))
                    i += m.end()
                    continue
                i += 1
                continue
            j = i + 1
            while j < n and t[j] != c:
                if t[j] == "\\":
                    j += 1
                elif t[j] == "\n" and not js:
                    break
                j += 1
            j = min(j + 1, n)
            regs.append((i, j, "string"))
            i = j
            last_sig = c
            continue
        if c == "`" and go:
            j = t.find("`", i + 1)
            j = n if j < 0 else j + 1
            regs.append((i, j, "string"))
            i = j
            continue
        if c == "`" and js:
            i = _js_template(t, i, regs)
            last_sig = "`"
            continue
        if js and c == "/" and (last_sig in "(,=:[!&|?{};+-*%<>~^" or last_word in
                                ("return", "typeof", "case", "do", "else", "in", "of", "new", "delete", "void", "throw")):
            m = re.match(r"/(?![*/])(\\.|\[(\\.|[^\]\\\n])*\]|[^/\\\n\[])+/[a-z]*", t[i:])
            if m:
                regs.append((i, i + m.end(), "string"))
                i += m.end()
                last_sig = "/"
                continue
        if c.isalnum() or c == "_" or c == "$":
            m = re.match(r"[A-Za-z0-9_$]+", t[i:])
            last_word = m.group(0)
            last_sig = "a"
            i += m.end()
            continue
        if not c.isspace():
            last_sig = c
            last_word = ""
        i += 1
    return _merge(regs, n)


def _js_template(t, i, regs):
    """`...${expr}...` — literal parts are strings, ${} parts are code (nested)."""
    n = len(t)
    j = i + 1
    seg = i
    while j < n:
        if t[j] == "\\":
            j += 2
            continue
        if t[j] == "`":
            regs.append((seg, j + 1, "string"))
            return j + 1
        if t.startswith("${", j):
            regs.append((seg, j + 2, "string"))
            # find matching }
            depth, k = 1, j + 2
            start = k
            while k < n and depth:
                ch = t[k]
                if ch in "\"'":
                    m = re.match(r"%s(\\.|[^%s\\\n])*%s" % (ch, ch, ch), t[k:])
                    if m:
                        regs.append((k, k + m.end(), "string"))
                        k += m.end()
                        continue
                if ch == "`":
                    k = _js_template(t, k, regs)
                    continue
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        break
                k += 1
            seg = k
            j = k
            continue
        j += 1
    regs.append((seg, n, "string"))
    return n


def lex_go(t):
    return lex_c(t, go=True)


def lex_js(t):
    return lex_c(t, js=True)


# ── CSS ─────────────────────────────────────────────────────────────────────
def lex_css(t):
    regs = []
    for m in re.finditer(r"/\*.*?\*/|\"(\\.|[^\"\\])*\"|'(\\.|[^'\\])*'", t, re.S):
        regs.append((m.start(), m.end(), "comment" if m.group(0).startswith("/*") else "string"))
    return _merge(regs, len(t))


# a CSS name: never ends with a hyphen (`.a--b` is one class, `x--` in JS is an operator, not a name)
CSS_IDENT = r"[A-Za-z_][A-Za-z0-9_]*(?:-+[A-Za-z0-9_]+)*"


def css_names(seg):
    """The names a piece of CSS CODE (comments and strings already cut out) defines or uses that are OURS:
    class and id selectors, custom properties (--x, without the dashes), @keyframes names, data-*
    attribute selectors.  Returns (ours, platform_attributes): property names, values, element names and
    pseudo-classes are the platform's and are never returned as ours; [aria-pressed] and other
    non-data attribute selectors are returned as the platform's."""
    ours, plat = set(), set()
    buf = []
    for part in re.split(r"([{};])", seg):
        if part not in ("{", "}", ";"):
            buf.append(part)
            continue
        text = "".join(buf).strip()
        buf = []
        if not text:
            continue
        if part == "{":                       # a prelude: a selector list or an at-rule
            if text.startswith("@"):
                m = re.match(r"@(?:-\w+-)?keyframes\s+(%s)" % CSS_IDENT, text)
                if m:
                    ours.add(m.group(1))
                continue
            for m in re.finditer(r"(?<![\w-])[.#](%s)" % CSS_IDENT, text):
                if not m.group(1)[:1].isdigit():
                    ours.add(m.group(1))
            for m in re.finditer(r"\[\s*(%s)" % CSS_IDENT, text):
                (ours if m.group(1).startswith("data-") else plat).add(m.group(1))
        else:                                 # a declaration: only custom properties are ours
            m = re.match(r"--(%s)\s*:" % CSS_IDENT, text)
            if m:
                ours.add(m.group(1))
            for m in re.finditer(r"var\(\s*--(%s)" % CSS_IDENT, text):
                ours.add(m.group(1))
    return ours, plat


# ── Python: the real tokenizer ──────────────────────────────────────────────
def lex_py(t):
    starts = [0]
    for m in re.finditer("\n", t):
        starts.append(m.end())

    def off(rc):
        r, c = rc
        return starts[r - 1] + c if r - 1 < len(starts) else len(t)
    regs = []
    try:
        for tok in tokenize.generate_tokens(io.StringIO(t).readline):
            ty = tok.type
            name = tokenize.tok_name.get(ty, "")
            if ty == tokenize.COMMENT:
                regs.append((off(tok.start), off(tok.end), "comment"))
            elif ty == tokenize.STRING or name in ("FSTRING_START", "FSTRING_MIDDLE", "FSTRING_END",
                                                    "TSTRING_START", "TSTRING_MIDDLE", "TSTRING_END"):
                regs.append((off(tok.start), off(tok.end), "string"))
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return lex_sh(t)
    return _merge(regs, len(t))


# ── shell (and Makefile, unit files, spec, conf: hash comments) ────────────
def lex_sh(t, make=False):
    regs, i, n = [], 0, len(t)
    heredocs = []
    while i < n:
        c = t[i]
        if c == "\n":
            i += 1
            # heredoc bodies start after the newline that ends the command
            while heredocs:
                delim, strip = heredocs.pop(0)
                pat = re.compile(r"^%s%s$" % (r"\t*" if strip else "", re.escape(delim)), re.M)
                m = pat.search(t, i)
                j = m.start() if m else n
                regs.append((i, j, "string"))
                i = m.end() if m else n
            continue
        if c == "#" and (i == 0 or t[i - 1] in " \t\n;|&(") and not (i > 0 and t[i - 1] == "$"):
            j = t.find("\n", i)
            j = n if j < 0 else j
            regs.append((i, j, "comment"))
            i = j
            continue
        if c == "\\":
            i += 2
            continue
        if c == "'" and not make:
            if i > 0 and t[i - 1] == "$":
                m = re.match(r"'(\\.|[^'\\])*'", t[i:])
                j = i + (m.end() if m else 1)
            else:
                j = t.find("'", i + 1)
                j = n if j < 0 else j + 1
            regs.append((i, j, "string"))
            i = j
            continue
        if c == '"' and not make:
            j = i + 1
            while j < n and t[j] != '"':
                if t[j] == "\\":
                    j += 1
                j += 1
            j = min(j + 1, n)
            regs.append((i, j, "string"))
            i = j
            continue
        if t.startswith("<<", i) and not t.startswith("<<<", i) and not make:
            m = re.match(r"<<(-?)\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\2", t[i:])
            if m:
                heredocs.append((m.group(3), m.group(1) == "-"))
                i += m.end()
                continue
        i += 1
    return _merge(regs, n)


def lex_make(t):
    return lex_sh(t, make=True)


# ── HTML with <script> and <style> ──────────────────────────────────────────
def lex_html(t):
    regs, n = [], len(t)
    pos = 0
    for m in re.finditer(r"<!--.*?-->|<script\b[^>]*>(.*?)</script\s*>|<style\b[^>]*>(.*?)</style\s*>|<[A-Za-z/][^>]*>",
                         t, re.S | re.I):
        if m.start() > pos:
            regs.append((pos, m.start(), "comment"))          # text content: prose
        s = m.group(0)
        if s.startswith("<!--"):
            regs.append((m.start(), m.end(), "comment"))
        elif m.group(1) is not None:
            a = m.start(1)
            regs.append((m.start(), a, "string"))
            for x, y, k in lex_js(m.group(1)):
                regs.append((a + x, a + y, k))
            regs.append((m.end(1), m.end(), "string"))
        elif m.group(2) is not None:
            a = m.start(2)
            regs.append((m.start(), a, "string"))
            for x, y, k in lex_css(m.group(2)):
                regs.append((a + x, a + y, "code-css" if k == "code" else k))
            regs.append((m.end(2), m.end(), "string"))
        else:
            # a tag: the attribute NAMES are the platform's (alt, aria-pressed), only data-* are ours;
            # the values are data (rinomina2.rewrite decides which)
            regs.append((m.start(), m.end(), "tag"))
        pos = m.end()
    if pos < n:
        regs.append((pos, n, "comment"))
    return sorted(regs)


# ── Markdown: only code spans and fenced code blocks ───────────────────────
FENCE_CODE = {"c", "h", "go", "python", "py", "sh", "bash", "shell", "zsh", "js", "javascript", "json", "make",
              "makefile", "ini", "toml", "yaml", "yml", "systemd", "spec", "diff", "html", "css", "glsl", "rust"}


def lex_md(t):
    """Fenced blocks with a code info string → 'code-doc'; bare/text/log/console blocks → skip;
    inline code spans → 'span'; everything else → skip."""
    regs, n = [], len(t)
    i = 0
    fence = re.compile(r"^( {0,3})(`{3,}|~{3,})[ \t]*([^\n`]*)\n", re.M)
    pos = 0
    while True:
        m = fence.search(t, pos)
        if not m:
            _md_inline(t, pos, n, regs)
            break
        _md_inline(t, pos, m.start(), regs)
        marker = m.group(2)
        info = m.group(3).strip().split()[0].lower() if m.group(3).strip() else ""
        close = re.compile(r"^ {0,3}%s%s*[ \t]*$" % (re.escape(marker[0]) * 3, re.escape(marker[0])), re.M)
        c = close.search(t, m.end())
        end = c.end() if c else n
        body_a, body_b = m.end(), (c.start() if c else n)
        body = t[body_a:body_b]
        if info and info not in FENCE_CODE and info not in ("cpp", "java", "markdown"):
            kind = "skip"                      # text, log, console, output …: evidence, word for word
        elif not info and _looks_like_log(body):
            kind = "skip"
        else:
            kind = "code-doc"
        if kind == "skip":
            regs.append((body_a, body_b, "skip"))
        else:
            off = body_a
            for line in body.split("\n"):
                regs.append((off, off + len(line), "code-doc"))
                off += len(line) + 1
        pos = end
    return regs


LOG_LINE = re.compile(r"^\s*(\d\d:\d\d(:\d\d(\.\d+)?)?\b|\[(Mon|Tue|Wed|Thu|Fri|Sat|Sun) |#\d+ |\$ |OK  |NO  |"
                      r"[⭐⛔⚠🔻])|Permission denied|No such file|cannot |warning:|segfault|users:\(\(|qdisc")


def _looks_like_log(body):
    """An untagged fenced block is output (kept word for word) when at least half its lines look like
    log or terminal output: a timestamp, a bench verdict, a marker emoji, a system message."""
    lines = [l for l in body.split("\n") if l.strip()]
    if not lines:
        return True
    return sum(1 for l in lines if LOG_LINE.search(l)) * 2 >= len(lines)


def _md_inline(t, a, b, regs):
    seg = t[a:b]
    for m in re.finditer(r"(?<!`)(`+)(?!`)(.+?)(?<!`)\1(?!`)", seg, re.S):
        regs.append((a + m.start(2), a + m.end(2), "span"))


LEXERS = {"c": lex_c, "go": lex_go, "py": lex_py, "sh": lex_sh, "make": lex_make, "js": lex_js,
          "css": lex_css, "html": lex_html, "md": lex_md}
